import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.core.database import init_db
from app.core.exceptions import register_exception_handlers
from app.api.v1.router import api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("evalgen.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to handle startup & shutdown events."""
    logger.info("Initializing EvalGen backend service...")
    try:
        await init_db()
        logger.info("Database schemas verified & initialized successfully.")
    except Exception as e:
        logger.error("Database initialization warning: %s", e)
    yield
    logger.info("Shutting down EvalGen backend service...")


app = FastAPI(
    title=settings.APP_NAME,
    description="EvalGen: AI Evaluation Set Generator with Gemini & MCP",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware: Configured securely via CORS_ORIGINS environment variable
cors_origins = (
    settings.CORS_ORIGINS
    if isinstance(settings.CORS_ORIGINS, list)
    else [o.strip() for o in str(settings.CORS_ORIGINS).split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*(\.pages\.dev|\.workers\.dev)",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def trace_and_timing_middleware(request: Request, call_next):
    """Injects a unique trace_id into every request and records execution duration."""
    trace_id = request.headers.get("X-Trace-ID", f"req-{uuid.uuid4().hex[:12]}")
    request.state.trace_id = trace_id

    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    response.headers["X-Trace-ID"] = trace_id
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    return response


# Register standardized error handlers
register_exception_handlers(app)

# Include API v1 router
app.include_router(api_router, prefix="/api/v1")


@app.get("/", summary="Root status")
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
        "health": "/api/v1/health",
        "version": "0.1.0",
    }
