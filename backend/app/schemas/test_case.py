from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AssertionSchema(BaseModel):
    type: str = Field(..., description="e.g. contains, regex, json_schema, llm_judge, latency")
    value: Optional[str] = Field(default=None, description="Expected value or pattern")
    rubric: Optional[str] = Field(default=None, description="Grading rubric for LLM-as-a-judge")


class TestCaseBase(BaseModel):
    prompt_input: str = Field(..., description="Input prompt provided to the LLM")
    expected_output: str = Field(..., description="Golden/ideal reference answer")
    context: Optional[str] = Field(default=None, description="Reference context, retrieved docs, or system instructions")
    rubric: Optional[str] = Field(default=None, description="Grading criteria for evaluation")
    difficulty: str = Field(default="medium", description="easy, medium, hard, adversarial")
    tags: List[str] = Field(default_factory=list, description="Categorical tags e.g. edge-case, safety, reasoning")
    assertions: List[AssertionSchema] = Field(default_factory=list, description="Automated validation assertions")


class TestCaseCreate(TestCaseBase):
    pass


class TestCaseResponse(TestCaseBase):
    id: str
    eval_set_id: str
    created_at: datetime

    class Config:
        from_attributes = True
