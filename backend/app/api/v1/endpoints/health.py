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
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
