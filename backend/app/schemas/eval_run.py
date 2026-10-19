from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class BenchmarkRunRequest(BaseModel):
    system_prompt: Optional[str] = Field(
        default="",
        description="Candidate system instructions / prompt behavior under test",
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Model to use for generating candidate responses (defaults to GEMINI_MODEL)",
    )


class EvaluationResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    test_case_id: str
    prompt_input: Optional[str] = None
    expected_output: Optional[str] = None
    context: Optional[str] = None
    rubric: Optional[str] = None
    difficulty: Optional[str] = None
    actual_output: Optional[str] = None
    passed: bool = False
    score: float = 0.0
    feedback: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: datetime


class EvalRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    eval_set_id: str
    model_tested: str
    system_prompt: Optional[str] = None
    status: str
    overall_score: Optional[float] = None
    passed_count: int = 0
    total_count: int = 0
    accuracy_rate: float = 0.0
    created_at: datetime
    results: List[EvaluationResultResponse] = Field(default_factory=list)
