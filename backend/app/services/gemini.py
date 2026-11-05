import asyncio
import json
import logging
from typing import Optional, Tuple
from tenacity import RetryError
from app.config import settings
from app.core.exceptions import (
    LLMGenerationException,
    RateLimitExceededException,
    ModelCapacityExceededException,
    GeminiConfigurationException,
)
from app.core.retry import with_retry, is_retryable_exception
from app.schemas.generation import GenerationRequest, SyntheticGenerationResult, GeneratedTestCase

logger = logging.getLogger("evalgen.gemini")

class GeminiService:
    """Service wrapping Google Gemini API with 3-attempt exponential backoff."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = (model_name or settings.GEMINI_MODEL).strip()
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

    def _sync_generate(
        self,
        prompt: str,
        system_instruction: str = "",
        response_mime_type: Optional[str] = "application/json",
        model_name: Optional[str] = None,
    ) -> str:
        """Synchronous invocation of Gemini API with automated fallback model resilience."""
        client = self._get_client()
        target_model = (model_name or self.model_name).strip()

        # Prioritize target model, followed by known stable production models
        models_to_try = [target_model]
        for candidate in ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.1-flash-lite"]:
            if candidate not in models_to_try:
                models_to_try.append(candidate)

        last_error = None
        for current_model in models_to_try:
            try:
                # Handle modern google-genai Client
                if hasattr(client, "models") and hasattr(client.models, "generate_content"):
                    from google.genai import types

                    config_kwargs = {
                        "system_instruction": system_instruction,
                        "temperature": 0.7,
                    }
                    if response_mime_type:
                        config_kwargs["response_mime_type"] = response_mime_type

                    config = types.GenerateContentConfig(**config_kwargs)
                    response = client.models.generate_content(
                        model=current_model,
                        contents=prompt,
                        config=config,
                    )
                    return response.text or ""

                # Handle classic google.generativeai
                import google.generativeai as gai

                gen_config = {"temperature": 0.7}
                if response_mime_type:
                    gen_config["response_mime_type"] = response_mime_type

                model = gai.GenerativeModel(
                    model_name=current_model,
                    system_instruction=system_instruction,
                    generation_config=gen_config,
                )
                response = model.generate_content(prompt)
                return response.text or ""
            except Exception as e:
                err_msg = str(e)
                # If model is unavailable (503 high demand spike) or not found (404), try fallback model
                if any(k in err_msg for k in ("503", "UNAVAILABLE", "404", "NOT_FOUND", "high demand", "no longer available")):
                    logger.warning("Gemini model '%s' failed with: %s. Trying fallback model...", current_model, err_msg[:120])
                    last_error = e
                    continue
                raise e

        if last_error:
            raise last_error
        return ""

    @with_retry(max_attempts=3, min_backoff=1.0, max_backoff=6.0)
    async def _call_gemini_raw(
        self,
        prompt: str,
        system_instruction: str = "",
        response_mime_type: Optional[str] = "application/json",
        model_name: Optional[str] = None,
    ) -> str:
        """Call Gemini API asynchronously in threadpool to avoid blocking FastAPI event loop."""
        return await asyncio.to_thread(self._sync_generate, prompt, system_instruction, response_mime_type, model_name)

    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> str:
        """Generate a candidate text response under evaluation."""
        if not self.api_key or self.api_key.strip() in ("", "your_gemini_api_key_here", "dummy", "test"):
            raise GeminiConfigurationException(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment to benchmark against Google Gemini."
            )

        try:
            return await self._call_gemini_raw(
                prompt=prompt,
                system_instruction=system_prompt or "",
                response_mime_type=None,
                model_name=model_name,
            )
        except RetryError as re:
            last_err = str(re.last_attempt.exception() if re.last_attempt else "Unknown")
            raise LLMGenerationException(
                message=f"Gemini API generation failed after 3 automated retries: {last_err}",
                details={"model": model_name or self.model_name, "error": last_err},
                retry_count=3,
            )
        except Exception as e:
            err_str = str(e)
            logger.error("Error generating candidate response from Gemini: %s", err_str)
            if any(k in err_str.lower() for k in ("429", "quota", "rate limit")):
                raise RateLimitExceededException(
                    message=f"Google Gemini quota or rate limit exceeded: {err_str}",
                    details={"model": model_name or self.model_name, "error": err_str},
                    retry_count=3,
                )
            if any(k in err_str.lower() for k in ("503", "unavailable", "high demand")):
                raise ModelCapacityExceededException(
                    message=f"Google Gemini model '{model_name or self.model_name}' is currently unavailable due to high demand: {err_str}",
                    details={"model": model_name or self.model_name, "error": err_str},
                    retry_count=3,
                )
            raise LLMGenerationException(
                message=f"Candidate response generation failed: {err_str}",
                details={"model": model_name or self.model_name, "error": err_str},
                retry_count=0,
            )

    async def generate_eval_set(
        self, request: GenerationRequest
    ) -> Tuple[SyntheticGenerationResult, int]:
        """
        Generate synthetic evaluation test cases with max 3 automatic retries.
        Returns the parsed result and the retry attempts count.
        """
        if not self.api_key or self.api_key.strip() in ("", "your_gemini_api_key_here", "dummy", "test"):
            raise GeminiConfigurationException(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in your .env file or container environment to synthesize evaluation suites with Google Gemini."
            )

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
            last_exc = re.last_attempt.exception() if re.last_attempt else None
            last_err_str = str(last_exc) if last_exc else "Transient failure"
            logger.error("Maximum 3 retries exhausted for Gemini API call: %s", last_err_str)
            if any(k in last_err_str.lower() for k in ("429", "resource_exhausted", "quota", "rate limit")):
                raise RateLimitExceededException(
                    message=f"Google Gemini rate limit or quota exceeded for model '{self.model_name}'. 3 automated retries exhausted.",
                    details={"model": self.model_name, "raw_error": last_err_str},
                    retry_count=3,
                )
            if any(k in last_err_str.lower() for k in ("503", "unavailable", "high demand", "capacity")):
                raise ModelCapacityExceededException(
                    message=f"Google Gemini model '{self.model_name}' is experiencing high demand. 3 automated retries exhausted.",
                    details={"model": self.model_name, "raw_error": last_err_str},
                    retry_count=3,
                )
            raise LLMGenerationException(
                message=f"Failed to generate evaluation dataset after 3 retries: {last_err_str}",
                details={"model": self.model_name, "raw_error": last_err_str},
                retry_count=3,
            )
        except Exception as e:
            err_str = str(e)
            logger.error("Gemini synthesis error: %s", err_str, exc_info=True)
            if any(k in err_str.lower() for k in ("429", "resource_exhausted", "quota", "rate limit")):
                raise RateLimitExceededException(
                    message=f"Google Gemini quota or rate limit exceeded for model '{self.model_name}': {err_str}",
                    details={"model": self.model_name, "raw_error": err_str},
                    retry_count=3,
                )
            if any(k in err_str.lower() for k in ("503", "unavailable", "high demand")):
                raise ModelCapacityExceededException(
                    message=f"Google Gemini model '{self.model_name}' is currently unavailable due to high demand: {err_str}",
                    details={"model": self.model_name, "raw_error": err_str},
                    retry_count=3,
                )
            if any(k in err_str.lower() for k in ("api_key", "api key", "unauthenticated", "permission denied")):
                raise GeminiConfigurationException(
                    message=f"Gemini API authentication failed: {err_str}. Please verify GEMINI_API_KEY.",
                    details={"model": self.model_name, "raw_error": err_str},
                )
            raise LLMGenerationException(
                message=f"Failed to generate evaluation dataset: {err_str}",
                details={"model": self.model_name, "raw_error": err_str},
                retry_count=retry_count,
            )


gemini_service = GeminiService()
