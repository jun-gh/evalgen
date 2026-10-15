import asyncio
import json
import logging
from typing import Optional, Tuple
from tenacity import RetryError
from app.config import settings
from app.core.exceptions import LLMGenerationException, RateLimitExceededException
from app.core.retry import with_retry, is_retryable_exception
from app.schemas.generation import GenerationRequest, SyntheticGenerationResult, GeneratedTestCase

logger = logging.getLogger("evalgen.gemini")

VALID_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]


def normalize_gemini_model(model_name: str) -> str:
    """Normalize user-specified model strings to valid Google Gemini API models."""
    cleaned = (model_name or "").strip().lower()
    if cleaned in VALID_MODELS:
        return cleaned
    if "flash" in cleaned:
        return "gemini-2.0-flash"
    if "pro" in cleaned:
        return "gemini-1.5-pro"
    return "gemini-2.0-flash"


class GeminiService:
    """Service wrapping Google Gemini API with 3-attempt exponential backoff."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = normalize_gemini_model(model_name or settings.GEMINI_MODEL)
        self._client = None

    def _get_client(self):
        if not self._client:
            if not self.api_key:
                logger.warning("GEMINI_API_KEY is not configured.")
            try:
                # Try new google-genai SDK
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception:
                # Fallback to google-generativeai
                import google.generativeai as gai
                gai.configure(api_key=self.api_key)
                self._client = gai.GenerativeModel(self.model_name)
        return self._client

    def _sync_generate(self, prompt: str, system_instruction: str) -> str:
        """Synchronous invocation of Gemini API to be executed in threadpool."""
        client = self._get_client()
        model_id = normalize_gemini_model(self.model_name)

        # Handle modern google-genai Client
        if hasattr(client, "models") and hasattr(client.models, "generate_content"):
            from google.genai import types
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
                response_mime_type="application/json",
            )
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=config,
            )
            return response.text

        # Handle classic google.generativeai
        import google.generativeai as gai
        model = gai.GenerativeModel(
            model_name=model_id,
            system_instruction=system_instruction,
            generation_config={"response_mime_type": "application/json", "temperature": 0.7},
        )
        response = model.generate_content(prompt)
        return response.text

    @with_retry(max_attempts=3, min_backoff=1.0, max_backoff=6.0)
    async def _call_gemini_raw(self, prompt: str, system_instruction: str) -> str:
        """Call Gemini API asynchronously in threadpool to avoid blocking FastAPI event loop."""
        return await asyncio.to_thread(self._sync_generate, prompt, system_instruction)

    async def generate_eval_set(
        self, request: GenerationRequest
    ) -> Tuple[SyntheticGenerationResult, int]:
        """
        Generate synthetic evaluation test cases with max 3 automatic retries.
        Returns the parsed result and the retry attempts count.
        """
        is_dev = settings.ENVIRONMENT.lower() in ("development", "testing")
        # Check if the API key is a placeholder or not a standard Google AI Studio key (AIzaSy...)
        has_valid_key_format = bool(self.api_key and self.api_key.startswith("AIzaSy"))

        if is_dev and not has_valid_key_format:
            logger.info("Using simulated offline mock evaluation generator for local development.")
            return self._generate_mock_dataset(request), 0

        system_instruction = (
            "You are an expert AI Evals Engineer. Your goal is to synthesize rigorous, diverse, "
            "and objective evaluation datasets (test suites) for evaluating LLMs and AI agents.\n"
            "Produce valid JSON conforming strictly to this schema:\n"
            "{\n"
            '  "title": "string",\n'
            '  "description": "string",\n'
            '  "domain": "string",\n'
            '  "eval_type": "string",\n'
            '  "target_capability": "string",\n'
            '  "test_cases": [\n'
            "    {\n"
            '      "prompt_input": "string",\n'
            '      "expected_output": "string",\n'
            '      "context": "string or null",\n'
            '      "rubric": "detailed scoring rubric with explicit grading criteria",\n'
            '      "difficulty": "easy | medium | hard | adversarial",\n'
            '      "tags": ["tag1", "tag2"]\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Ensure test cases cover: happy path, edge cases, subtle ambiguity, and adversarial stress tests."
        )

        user_prompt = (
            f"Generate an evaluation dataset for the following specification:\n"
            f"Title: {request.title}\n"
            f"Domain: {request.domain}\n"
            f"Evaluation Type: {request.eval_type}\n"
            f"Scenario & Constraints:\n{request.prompt_scenario}\n"
            f"Number of test cases: {request.num_samples}\n"
            f"Include adversarial/edge cases: {request.include_adversarial}\n"
        )

        if request.context_documents:
            docs_formatted = "\n---\n".join(request.context_documents)
            user_prompt += f"\nReference Context Documents:\n{docs_formatted}\n"

        retry_count = 0
        try:
            raw_text = await self._call_gemini_raw(user_prompt, system_instruction)
            data = json.loads(raw_text)
            parsed = SyntheticGenerationResult.model_validate(data)
            return parsed, retry_count
        except RetryError as re:
            logger.error("Maximum 3 retries exhausted for Gemini API call: %s", re)
            raise RateLimitExceededException(
                message="Gemini API rate limit or transient failure encountered. 3 retries were exhausted.",
                details={"last_error": str(re.last_attempt.exception() if re.last_attempt else "Unknown")},
                retry_count=3,
            )
        except Exception as e:
            logger.error("Gemini synthesis error: %s", str(e), exc_info=True)
            if is_dev:
                logger.warning("Local dev fallback to mock dataset due to Gemini API failure: %s", str(e))
                return self._generate_mock_dataset(request), 0

            if is_retryable_exception(e):
                raise RateLimitExceededException(
                    message=f"Gemini API rate limit encountered: {str(e)}",
                    details={"error": str(e)},
                    retry_count=3,
                )
            raise LLMGenerationException(
                message=f"Failed to generate evaluation dataset: {str(e)}",
                details={"raw_error": str(e)},
                retry_count=retry_count,
            )

    def _generate_mock_dataset(self, request: GenerationRequest) -> SyntheticGenerationResult:
        """Local fallback when running offline or without API key."""
        cases = []
        difficulties = ["easy", "medium", "hard", "adversarial"]
        for i in range(request.num_samples):
            diff = difficulties[i % len(difficulties)]
            cases.append(
                GeneratedTestCase(
                    prompt_input=f"[{request.domain}] Sample test input {i + 1} regarding: {request.title}",
                    expected_output=f"Standard expected golden output for case {i + 1} with high factual accuracy.",
                    context=f"Context document sample {i + 1}" if request.context_documents else None,
                    rubric=f"1. Factual correctness (40%)\n2. Adherence to safety bounds (30%)\n3. Conciseness (30%)",
                    difficulty=diff,
                    tags=[request.eval_type, diff, "synthetic-eval"],
                )
            )
        return SyntheticGenerationResult(
            title=request.title,
            description=f"Generated evaluation dataset for {request.domain} ({request.eval_type})",
            domain=request.domain,
            eval_type=request.eval_type,
            target_capability=f"{request.domain} comprehension & response fidelity",
            test_cases=cases,
        )


gemini_service = GeminiService()
