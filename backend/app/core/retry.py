import asyncio
import logging
from typing import Any, Callable, TypeVar
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception,
    before_sleep_log,
    after_log,
)

logger = logging.getLogger("evalgen.retry")

T = TypeVar("T")

# Maximum retry attempts as required by best practices
MAX_RETRY_ATTEMPTS = 3
MIN_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 8.0


def is_retryable_exception(exc: Exception) -> bool:
    """Determine whether an exception is transient and eligible for retry."""
    exc_name = exc.__class__.__name__
    exc_str = str(exc).lower()

    # Explicitly do NOT retry client errors: 400 bad request, 401 unauth, 403 forbidden, 404 not found
    non_retryable = ["400", "401", "403", "404", "invalid argument", "api_key_invalid", "not found"]
    if any(nr in exc_str for nr in non_retryable):
        return False

    # Rate limiting and transient network errors
    retryable_indicators = [
        "429",
        "resourceexhausted",
        "quota",
        "rate limit",
        "502",
        "503",
        "504",
        "timeout",
        "connection reset",
        "temporarily unavailable",
    ]

    return any(ind in exc_str or ind in exc_name.lower() for ind in retryable_indicators)


def with_retry(
    max_attempts: int = MAX_RETRY_ATTEMPTS,
    min_backoff: float = MIN_BACKOFF_SECONDS,
    max_backoff: float = MAX_BACKOFF_SECONDS,
):
    """
    Decorator that applies exponential backoff with jitter.
    Guarantees a strict maximum of 3 attempts for transient/retryable errors.
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_random_exponential(multiplier=min_backoff, max=max_backoff),
        retry=retry_if_exception(is_retryable_exception),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True,
    )
