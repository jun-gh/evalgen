from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="Human-friendly explanation to render on UI")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Diagnostic payload")
    retryable: bool = Field(default=False, description="Whether client should attempt retry")
    retry_count: int = Field(default=0, description="Number of automated server retries executed")
    trace_id: str = Field(..., description="Unique request tracing ID")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="UTC ISO timestamp",
    )


class ErrorEnvelope(BaseModel):
    """Standardized error envelope returned to UI clients."""
    success: bool = False
    error: ErrorDetail
