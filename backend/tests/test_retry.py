import pytest
from unittest.mock import MagicMock
from app.core.retry import with_retry, MAX_RETRY_ATTEMPTS


@pytest.mark.asyncio
async def test_retry_mechanism_executes_up_to_max_3_attempts():
    mock_func = MagicMock(side_effect=ValueError("Simulated 429 Rate limit"))

    @with_retry(max_attempts=3, min_backoff=0.01, max_backoff=0.05)
    async def flaky_operation():
        mock_func()

    with pytest.raises(ValueError) as exc_info:
        await flaky_operation()

    assert "Simulated 429 Rate limit" in str(exc_info.value)
    # Verify exactly 3 attempts occurred before failure
    assert mock_func.call_count == MAX_RETRY_ATTEMPTS


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt():
    call_count = 0

    @with_retry(max_attempts=3, min_backoff=0.01, max_backoff=0.05)
    async def transient_operation():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionResetError("Transient network drop")
        return "success"

    result = await transient_operation()
    assert result == "success"
    assert call_count == 2
