import logging
from typing import Dict, Any, List
from app.services.gemini import gemini_service
from app.schemas.test_case import TestCaseResponse

logger = logging.getLogger("evalgen.evaluator")


class EvaluatorService:
    """Evaluates candidate LLM outputs against test cases using assertions and LLM-as-a-judge."""

    async def evaluate_output(
        self,
        prompt: str,
        expected: str,
        actual: str,
        rubric: str,
        context: str = None,
    ) -> Dict[str, Any]:
        """
        Grade actual LLM response against expected and rubric.
        Returns passed, score (0.0 to 1.0), and critique.
        """
        judge_prompt = (
            f"You are an impartial, expert AI Judge.\n"
            f"Input Prompt: {prompt}\n"
            f"Context: {context or 'None'}\n"
            f"Reference Golden Answer: {expected}\n"
            f"Candidate Actual Output: {actual}\n"
            f"Grading Rubric:\n{rubric}\n\n"
            f"Grade the candidate output from 0.0 to 1.0 and provide concise feedback.\n"
            f"Respond with JSON: {{\"score\": 0.95, \"passed\": true, \"feedback\": \"...\"}}"
        )

        try:
            raw_text = await gemini_service._call_gemini_raw(
                prompt=judge_prompt,
                system_instruction="You are a strict, objective evaluation judge. Return valid JSON only.",
            )
            import json
            data = json.loads(raw_text)
            return {
                "score": float(data.get("score", 0.0)),
                "passed": bool(data.get("passed", False)),
                "feedback": data.get("feedback", ""),
            }
        except Exception as e:
            logger.warning("LLM judge grading fallback: %s", e)
            # Basic fallback heuristic
            norm_exp = expected.strip().lower()
            norm_act = actual.strip().lower()
            is_match = norm_exp in norm_act or norm_act in norm_exp
            return {
                "score": 1.0 if is_match else 0.0,
                "passed": is_match,
                "feedback": f"Heuristic fallback: {'Substring match' if is_match else 'No direct match'}",
            }


evaluator_service = EvaluatorService()
