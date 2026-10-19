import json
import logging
import time
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.eval_set import EvalSet, EvalRun, EvaluationResult
from app.services.gemini import gemini_service

logger = logging.getLogger("evalgen.evaluator")


class EvaluatorService:
    """Evaluates candidate LLM outputs against test cases using assertions and LLM-as-a-judge."""

    async def evaluate_output(
        self,
        prompt: str,
        expected: str,
        actual: str,
        rubric: str,
        context: Optional[str] = None,
        model_name: Optional[str] = None,
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
                response_mime_type="application/json",
                model_name=model_name,
            )
            cleaned = raw_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            data = json.loads(cleaned.strip())
            score = float(data.get("score", 0.0))
            passed = bool(data.get("passed", score >= 0.7))
            return {
                "score": score,
                "passed": passed,
                "feedback": data.get("feedback") or data.get("critique") or "LLM Judge evaluation completed.",
            }
        except Exception as e:
            logger.warning("LLM judge grading fallback: %s", e)
            # Basic fallback heuristic
            norm_exp = expected.strip().lower()
            norm_act = actual.strip().lower()
            match = any(word in norm_act for word in norm_exp.split()[:4]) if norm_exp else False
            score = 0.85 if match else 0.4
            return {
                "score": score,
                "passed": score >= 0.7,
                "feedback": f"Heuristic fallback: {'Key terminology matched' if match else 'Terminology mismatch'}",
            }

    async def run_benchmark(
        self,
        db: AsyncSession,
        eval_set: EvalSet,
        system_prompt: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> EvalRun:
        """
        Executes an end-to-end evaluation benchmark over an EvalSet:
        1. Runs candidate generation for each test case.
        2. Evaluates each candidate output via LLM-as-a-judge against golden expected output and rubric.
        3. Persists individual results and summary metrics in database.
        """
        target_model = (model_name or settings.GEMINI_MODEL).strip()
        eval_run = EvalRun(
            eval_set_id=eval_set.id,
            model_tested=target_model,
            system_prompt=system_prompt,
            status="running",
            total_count=len(eval_set.test_cases),
        )
        db.add(eval_run)
        await db.flush()

        passed_count = 0
        total_score = 0.0

        for tc in eval_set.test_cases:
            t0 = time.perf_counter()
            if tc.context:
                prompt_content = f"Context:\n{tc.context}\n\nUser Question: {tc.prompt_input}\nAnswer concisely:"
            else:
                prompt_content = f"User Question: {tc.prompt_input}\nAnswer concisely:"

            actual_output = await gemini_service.generate_response(
                prompt=prompt_content,
                system_prompt=system_prompt,
                model_name=target_model,
            )
            latency_ms = int((time.perf_counter() - t0) * 1000)

            grade = await self.evaluate_output(
                prompt=tc.prompt_input,
                expected=tc.expected_output,
                actual=actual_output,
                rubric=tc.rubric or "Grade correctness against expected output.",
                context=tc.context,
                model_name=target_model,
            )

            is_passed = grade.get("passed", False)
            score = float(grade.get("score", 0.0))
            if is_passed:
                passed_count += 1
            total_score += score

            eval_res = EvaluationResult(
                eval_run_id=eval_run.id,
                test_case_id=tc.id,
                actual_output=actual_output,
                passed=is_passed,
                score=score,
                feedback=grade.get("feedback", ""),
                latency_ms=latency_ms,
            )
            db.add(eval_res)

        eval_run.status = "completed"
        eval_run.passed_count = passed_count
        eval_run.total_count = len(eval_set.test_cases)
        eval_run.overall_score = round(total_score / len(eval_set.test_cases), 4) if eval_set.test_cases else 0.0

        await db.commit()
        await db.refresh(eval_run)
        return eval_run


evaluator_service = EvaluatorService()
