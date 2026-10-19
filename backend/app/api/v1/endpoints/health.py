from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.core.database import get_db

router = APIRouter()


@router.get("/health", summary="Health and readiness check")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint used by Render Blueprint healthCheckPath and
    frontend cold-start detection banners.
    """
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database_type": "sqlite" if settings.is_sqlite else "postgresql",
        "database_status": db_status,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "gemini_model": settings.GEMINI_MODEL,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/config", summary="Public runtime configuration")
async def get_config():
    """
    Returns public non-sensitive configuration, including the active Gemini model
    and session/sample quotas read from .env, consumed dynamically by the frontend.
    """
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "gemini_model": settings.GEMINI_MODEL,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "max_datasets_per_session": settings.MAX_DATASETS_PER_SESSION,
        "session_expiry_days": settings.SESSION_EXPIRY_DAYS,
        "max_sample_count": settings.MAX_SAMPLE_COUNT,
        "default_sample_count": settings.DEFAULT_SAMPLE_COUNT,
    }
