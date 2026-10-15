from fastapi import APIRouter
from app.api.v1.endpoints import health, eval_sets, generator, mcp_tools

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(eval_sets.router, prefix="/eval-sets", tags=["Evaluation Sets"])
api_router.include_router(generator.router, prefix="/generator", tags=["Synthetic Generator"])
api_router.include_router(mcp_tools.router, prefix="/mcp-tools", tags=["Model Context Protocol Tools"])
