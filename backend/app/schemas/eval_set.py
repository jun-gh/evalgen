from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.test_case import TestCaseResponse, TestCaseCreate


class EvalSetBase(BaseModel):
    title: str = Field(..., max_length=255, description="Name of the evaluation dataset")
    description: Optional[str] = Field(default=None, description="Detailed purpose and scenario description")
    domain: str = Field(default="General QA", description="Domain: e.g. Customer Support, Coding, Healthcare, Finance")
    eval_type: str = Field(default="rag_qa", description="Type: rag_qa, reasoning, tool_calling, safety, edge_cases")
    target_capability: Optional[str] = Field(default=None, description="Key model capability tested")


class EvalSetCreate(EvalSetBase):
    initial_test_cases: List[TestCaseCreate] = Field(
        default_factory=list,
        description="Optional initial test cases to populate",
    )


class EvalSetUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    eval_type: Optional[str] = None
    target_capability: Optional[str] = None


class EvalSetResponse(EvalSetBase):
    id: str
    created_at: datetime
    updated_at: datetime
    test_cases: List[TestCaseResponse] = Field(default_factory=list)
    total_test_cases: int = 0

    class Config:
        from_attributes = True
