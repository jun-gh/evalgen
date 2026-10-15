import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.eval_set import EvalSet, TestCase
from app.schemas.generation import GenerationRequest, GenerationResponse
from app.services.gemini import gemini_service

logger = logging.getLogger("evalgen.api.generator")
router = APIRouter()


@router.post(
    "/generate",
    response_model=GenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Synthesize an evaluation set using Google Gemini with 3-retry resilience",
)
async def generate_synthetic_evals(
    request: GenerationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Synthesize high-fidelity test cases, rubrics, and edge cases with Gemini.
    Decorated with a maximum 3-attempt exponential backoff retry.
    """
    dataset, retry_count = await gemini_service.generate_eval_set(request)

    eval_set_id = None
    if request.auto_save:
        eval_set = EvalSet(
            title=dataset.title,
            description=dataset.description,
            domain=dataset.domain,
            eval_type=dataset.eval_type,
            target_capability=dataset.target_capability,
        )
        db.add(eval_set)
        await db.flush()
        eval_set_id = eval_set.id

        for tc_data in dataset.test_cases:
            tc = TestCase(
                eval_set_id=eval_set.id,
                prompt_input=tc_data.prompt_input,
                expected_output=tc_data.expected_output,
                context=tc_data.context,
                rubric=tc_data.rubric,
                difficulty=tc_data.difficulty,
                tags=tc_data.tags,
            )
            db.add(tc)

        await db.commit()

    return GenerationResponse(
        success=True,
        eval_set_id=eval_set_id,
        message=f"Successfully generated {len(dataset.test_cases)} evaluation test cases.",
        dataset=dataset,
        retry_count=retry_count,
    )
