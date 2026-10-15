import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundException
from app.models.eval_set import EvalSet, TestCase
from app.schemas.eval_set import (
    EvalSetCreate,
    EvalSetResponse,
    EvalSetUpdate,
)
from app.schemas.test_case import TestCaseCreate, TestCaseResponse

router = APIRouter()


@router.get("", response_model=List[EvalSetResponse])
async def list_eval_sets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    domain: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(EvalSet)
    if domain:
        query = query.where(EvalSet.domain == domain)
    query = query.offset(skip).limit(limit).order_by(EvalSet.created_at.desc())
    result = await db.execute(query)
    eval_sets = result.scalars().all()

    response_items = []
    for es in eval_sets:
        item = EvalSetResponse.model_validate(es)
        item.total_test_cases = len(es.test_cases)
        response_items.append(item)
    return response_items


@router.post("", response_model=EvalSetResponse, status_code=status.HTTP_201_CREATED)
async def create_eval_set(
    payload: EvalSetCreate,
    db: AsyncSession = Depends(get_db),
):
    eval_set = EvalSet(
        title=payload.title,
        description=payload.description,
        domain=payload.domain,
        eval_type=payload.eval_type,
        target_capability=payload.target_capability,
    )
    db.add(eval_set)
    await db.flush()

    for tc_data in payload.initial_test_cases:
        tc = TestCase(
            eval_set_id=eval_set.id,
            prompt_input=tc_data.prompt_input,
            expected_output=tc_data.expected_output,
            context=tc_data.context,
            rubric=tc_data.rubric,
            difficulty=tc_data.difficulty,
            tags=tc_data.tags,
            assertions=[a.model_dump() for a in tc_data.assertions],
        )
        db.add(tc)

    await db.commit()
    await db.refresh(eval_set)

    response = EvalSetResponse.model_validate(eval_set)
    response.total_test_cases = len(eval_set.test_cases)
    return response


@router.get("/{eval_set_id}", response_model=EvalSetResponse)
async def get_eval_set(
    eval_set_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = select(EvalSet).where(EvalSet.id == eval_set_id)
    result = await db.execute(query)
    eval_set = result.scalar_one_or_none()
    if not eval_set:
        raise ResourceNotFoundException("EvalSet", eval_set_id)

    response = EvalSetResponse.model_validate(eval_set)
    response.total_test_cases = len(eval_set.test_cases)
    return response


@router.delete("/{eval_set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_eval_set(
    eval_set_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = select(EvalSet).where(EvalSet.id == eval_set_id)
    result = await db.execute(query)
    eval_set = result.scalar_one_or_none()
    if not eval_set:
        raise ResourceNotFoundException("EvalSet", eval_set_id)

    await db.delete(eval_set)
    await db.commit()
    return None


@router.post("/{eval_set_id}/test-cases", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED)
async def add_test_case(
    eval_set_id: str,
    payload: TestCaseCreate,
    db: AsyncSession = Depends(get_db),
):
    query = select(EvalSet).where(EvalSet.id == eval_set_id)
    result = await db.execute(query)
    eval_set = result.scalar_one_or_none()
    if not eval_set:
        raise ResourceNotFoundException("EvalSet", eval_set_id)

    tc = TestCase(
        eval_set_id=eval_set.id,
        prompt_input=payload.prompt_input,
        expected_output=payload.expected_output,
        context=payload.context,
        rubric=payload.rubric,
        difficulty=payload.difficulty,
        tags=payload.tags,
        assertions=[a.model_dump() for a in payload.assertions],
    )
    db.add(tc)
    await db.commit()
    await db.refresh(tc)
    return TestCaseResponse.model_validate(tc)


@router.get("/{eval_set_id}/export/csv")
async def export_csv(
    eval_set_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = select(EvalSet).where(EvalSet.id == eval_set_id)
    result = await db.execute(query)
    eval_set = result.scalar_one_or_none()
    if not eval_set:
        raise ResourceNotFoundException("EvalSet", eval_set_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Prompt Input", "Expected Output", "Context", "Rubric", "Difficulty", "Tags"])

    for tc in eval_set.test_cases:
        writer.writerow([
            tc.id,
            tc.prompt_input,
            tc.expected_output,
            tc.context or "",
            tc.rubric or "",
            tc.difficulty,
            ", ".join(tc.tags or []),
        ])

    filename = f"evalset_{eval_set.title.replace(' ', '_').lower()}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
