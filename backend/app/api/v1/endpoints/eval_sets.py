import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.models.eval_set import EvalSet, TestCase, EvalRun
from app.schemas.eval_run import BenchmarkRunRequest, EvalRunResponse, EvaluationResultResponse
from app.schemas.eval_set import (
    EvalSetCreate,
    EvalSetResponse,
)
from app.schemas.test_case import TestCaseCreate, TestCaseResponse
from app.services.evaluator import evaluator_service

router = APIRouter()


@router.get("", response_model=List[EvalSetResponse])
async def list_eval_sets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
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


def _build_eval_run_response(eval_run: EvalRun, eval_set: Optional[EvalSet] = None) -> EvalRunResponse:
    tc_lookup = {tc.id: tc for tc in eval_set.test_cases} if eval_set and eval_set.test_cases else {}
    results = []
    for res in eval_run.results:
        tc = tc_lookup.get(res.test_case_id)
        results.append(
            EvaluationResultResponse(
                id=res.id,
                test_case_id=res.test_case_id,
                prompt_input=tc.prompt_input if tc else "",
                expected_output=tc.expected_output if tc else "",
                context=tc.context if tc else None,
                rubric=tc.rubric if tc else None,
                difficulty=tc.difficulty if tc else None,
                actual_output=res.actual_output,
                passed=res.passed,
                score=res.score,
                feedback=res.feedback,
                latency_ms=res.latency_ms,
                created_at=res.created_at,
            )
        )
    accuracy_rate = (
        round((eval_run.passed_count / eval_run.total_count * 100), 1)
        if eval_run.total_count > 0
        else 0.0
    )
    return EvalRunResponse(
        id=eval_run.id,
        eval_set_id=eval_run.eval_set_id,
        model_tested=eval_run.model_tested,
        system_prompt=eval_run.system_prompt,
        status=eval_run.status,
        overall_score=eval_run.overall_score,
        passed_count=eval_run.passed_count,
        total_count=eval_run.total_count,
        accuracy_rate=accuracy_rate,
        created_at=eval_run.created_at,
        results=results,
    )


@router.post("/import-csv", response_model=EvalSetResponse, status_code=status.HTTP_201_CREATED)
async def import_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise ValidationException("Only .csv files are supported for import.")

    contents = await file.read()
    try:
        text = contents.decode("utf-8")
    except UnicodeDecodeError:
        text = contents.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    test_cases_data = []

    for row in reader:
        # Normalize key names
        normalized_row = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items() if k}
        prompt = (
            normalized_row.get("prompt input")
            or normalized_row.get("prompt_input")
            or normalized_row.get("prompt")
            or normalized_row.get("question")
            or normalized_row.get("input")
            or ""
        )
        expected = (
            normalized_row.get("expected output")
            or normalized_row.get("expected_output")
            or normalized_row.get("expected")
            or normalized_row.get("answer")
            or normalized_row.get("golden_output")
            or ""
        )
        if not prompt or not expected:
            continue

        context = normalized_row.get("context") or None
        rubric = normalized_row.get("rubric") or "Grade factual and structural accuracy against expected output."
        difficulty = normalized_row.get("difficulty") or "medium"
        tags_raw = normalized_row.get("tags") or ""
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

        test_cases_data.append(
            {
                "prompt_input": prompt,
                "expected_output": expected,
                "context": context,
                "rubric": rubric,
                "difficulty": difficulty if difficulty in ("easy", "medium", "hard", "adversarial") else "medium",
                "tags": tags or ["imported-csv"],
            }
        )

    if not test_cases_data:
        raise ValidationException(
            "No valid test cases found in CSV. Ensure 'Prompt Input' and 'Expected Output' columns exist."
        )

    clean_name = file.filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()
    title = f"Imported: {clean_name}"
    eval_set = EvalSet(
        title=title,
        description=f"Imported from {file.filename} with {len(test_cases_data)} test cases.",
        domain="General QA",
        eval_type="rag_qa" if any(tc["context"] for tc in test_cases_data) else "reasoning",
        target_capability="Imported Benchmark Suite",
    )
    db.add(eval_set)
    await db.flush()

    for tc_dict in test_cases_data:
        tc = TestCase(
            eval_set_id=eval_set.id,
            prompt_input=tc_dict["prompt_input"],
            expected_output=tc_dict["expected_output"],
            context=tc_dict["context"],
            rubric=tc_dict["rubric"],
            difficulty=tc_dict["difficulty"],
            tags=tc_dict["tags"],
        )
        db.add(tc)

    await db.commit()
    await db.refresh(eval_set)

    resp = EvalSetResponse.model_validate(eval_set)
    resp.total_test_cases = len(eval_set.test_cases)
    return resp


@router.post("/{eval_set_id}/run", response_model=EvalRunResponse, status_code=status.HTTP_200_OK)
async def run_eval_set_benchmark(
    eval_set_id: str,
    payload: BenchmarkRunRequest = BenchmarkRunRequest(),
    db: AsyncSession = Depends(get_db),
):
    query = select(EvalSet).where(EvalSet.id == eval_set_id)
    result = await db.execute(query)
    eval_set = result.scalar_one_or_none()
    if not eval_set:
        raise ResourceNotFoundException("EvalSet", eval_set_id)
    if not eval_set.test_cases:
        raise ValidationException("Cannot benchmark an empty evaluation set. Please add test cases first.")

    eval_run = await evaluator_service.run_benchmark(
        db=db,
        eval_set=eval_set,
        system_prompt=payload.system_prompt,
        model_name=payload.model_name,
    )
    return _build_eval_run_response(eval_run, eval_set)


@router.get("/{eval_set_id}/runs", response_model=List[EvalRunResponse])
async def list_eval_set_runs(
    eval_set_id: str,
    db: AsyncSession = Depends(get_db),
):
    query = select(EvalSet).where(EvalSet.id == eval_set_id)
    result = await db.execute(query)
    eval_set = result.scalar_one_or_none()
    if not eval_set:
        raise ResourceNotFoundException("EvalSet", eval_set_id)

    runs_query = select(EvalRun).where(EvalRun.eval_set_id == eval_set_id).order_by(EvalRun.created_at.desc())
    runs_res = await db.execute(runs_query)
    runs = runs_res.scalars().all()

    return [_build_eval_run_response(r, eval_set) for r in runs]


@router.get("/runs/{run_id}", response_model=EvalRunResponse)
async def get_eval_run_detail(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    run_query = select(EvalRun).where(EvalRun.id == run_id)
    run_res = await db.execute(run_query)
    eval_run = run_res.scalar_one_or_none()
    if not eval_run:
        raise ResourceNotFoundException("EvalRun", run_id)

    set_query = select(EvalSet).where(EvalSet.id == eval_run.eval_set_id)
    set_res = await db.execute(set_query)
    eval_set = set_res.scalar_one_or_none()

    return _build_eval_run_response(eval_run, eval_set)
