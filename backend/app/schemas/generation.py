from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.test_case import TestCaseCreate


class GenerationRequest(BaseModel):
    """Specification requested by user to generate synthetic evals."""
    title: str = Field(..., description="Title of the evaluation set")
    prompt_scenario: str = Field(
        ...,
        description="Detailed description of the application behavior, constraints, and test scenarios",
    )
    domain: str = Field(default="General QA", description="Domain of application")
    eval_type: str = Field(default="rag_qa", description="rag_qa, reasoning, tool_calling, safety, edge_cases")
    num_samples: int = Field(default=5, ge=1, le=25, description="Number of synthetic test cases to generate")
    include_adversarial: bool = Field(default=True, description="Whether to include edge and jailbreak/adversarial cases")
    context_documents: Optional[List[str]] = Field(default=None, description="Optional reference documentation for RAG evals")
    auto_save: bool = Field(default=True, description="Automatically persist created EvalSet to database")


class GeneratedTestCase(BaseModel):
    prompt_input: str
    expected_output: str
    context: Optional[str] = None
    rubric: str
    difficulty: str = "medium"
    tags: List[str] = Field(default_factory=list)


class SyntheticGenerationResult(BaseModel):
    title: str
    description: str
    domain: str
    eval_type: str
    target_capability: str
    test_cases: List[GeneratedTestCase]


class GenerationResponse(BaseModel):
    success: bool = True
    eval_set_id: Optional[str] = None
    message: str
    dataset: SyntheticGenerationResult
    retry_count: int = 0
