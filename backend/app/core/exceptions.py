import uuid
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.schemas.error import ErrorEnvelope, ErrorDetail


class EvalGenException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        retryable: bool = False,
        retry_count: int = 0,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        self.retryable = retryable
        self.retry_count = retry_count


class LLMGenerationException(EvalGenException):
    def __init__(
        self,
        message: str = "Failed to generate evaluation dataset via Gemini API",
        details: Optional[Dict[str, Any]] = None,
        retry_count: int = 3,
    ):
        super().__init__(
            message=message,
            code="LLM_GENERATION_FAILED",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
            retryable=True,
            retry_count=retry_count,
        )


class RateLimitExceededException(EvalGenException):
    def __init__(
        self,
        message: str = "Rate limit reached. Maximum 3 automatic retries were exhausted.",
        details: Optional[Dict[str, Any]] = None,
        retry_count: int = 3,
    ):
        super().__init__(
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
            retryable=True,
            retry_count=retry_count,
        )


class ResourceNotFoundException(EvalGenException):
    def __init__(self, resource: str, resource_id: Any):
        super().__init__(
            message=f"{resource} with ID '{resource_id}' was not found.",
            code="RESOURCE_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            retryable=False,
        )


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform error handlers for all exceptions."""

    @app.exception_handler(EvalGenException)
    async def handle_evalgen_exception(request: Request, exc: EvalGenException) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
        envelope = ErrorEnvelope(
            success=False,
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                retryable=exc.retryable,
                retry_count=exc.retry_count,
                trace_id=trace_id,
            ),
        )
        return JSONResponse(status_code=exc.status_code, content=envelope.model_dump())

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
        envelope = ErrorEnvelope(
            success=False,
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Invalid request payload or query parameters.",
                details={"errors": exc.errors()},
                retryable=False,
                retry_count=0,
                trace_id=trace_id,
            ),
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=envelope.model_dump())

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
        envelope = ErrorEnvelope(
            success=False,
            error=ErrorDetail(
                code="UNEXPECTED_ERROR",
                message="An unexpected server error occurred. Please try again or check logs.",
                details={"exception_type": exc.__class__.__name__, "info": str(exc)},
                retryable=True,
                retry_count=0,
                trace_id=trace_id,
            ),
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=envelope.model_dump())
