from datetime import datetime, timedelta
from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.core.exceptions import QuotaExceededException
from app.models.eval_set import EvalSet


def get_session_id(request: Request) -> str:
    """
    Extracts the anonymous persistent session ID from the X-Session-ID header.
    Falls back to 'anonymous' if not provided (e.g., direct API docs test).
    """
    session_id = request.headers.get("x-session-id") or request.headers.get("X-Session-ID") or ""
    session_id = session_id.strip()
    return session_id if session_id else "anonymous"


def get_session_cutoff() -> datetime:
    """Returns the oldest datetime for an active session dataset based on SESSION_EXPIRY_DAYS."""
    return datetime.utcnow() - timedelta(days=settings.SESSION_EXPIRY_DAYS)


async def check_session_quota(db: AsyncSession, session_id: str) -> int:
    """
    Verifies that the session has not exceeded MAX_DATASETS_PER_SESSION within SESSION_EXPIRY_DAYS.
    Raises QuotaExceededException if quota is full.
    Returns current count.
    """
    cutoff = get_session_cutoff()
    query = (
        select(func.count(EvalSet.id))
        .where(EvalSet.session_id == session_id)
        .where(EvalSet.created_at >= cutoff)
    )
    result = await db.execute(query)
    current_count = result.scalar() or 0

    if current_count >= settings.MAX_DATASETS_PER_SESSION:
        raise QuotaExceededException(
            f"Session limit reached ({settings.MAX_DATASETS_PER_SESSION} datasets maximum). "
            f"Active datasets persist for {settings.SESSION_EXPIRY_DAYS} days. "
            f"Please delete an existing dataset to import or synthesize a new one.",
            details={
                "current_count": current_count,
                "max_allowed": settings.MAX_DATASETS_PER_SESSION,
                "expiry_days": settings.SESSION_EXPIRY_DAYS,
            },
        )

    return current_count
