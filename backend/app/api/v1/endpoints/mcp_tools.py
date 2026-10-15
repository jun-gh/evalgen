from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.services.mcp_client import mcp_service, MCPToolDefinition

router = APIRouter()


class ToolExecutionRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


@router.get("", response_model=List[MCPToolDefinition], summary="List available MCP evaluation tools")
async def list_mcp_tools():
    return mcp_service.list_tools()


@router.post("/execute", summary="Execute an MCP evaluation tool")
async def execute_mcp_tool(payload: ToolExecutionRequest):
    try:
        result = await mcp_service.execute_tool(payload.tool_name, payload.arguments)
        return {"success": True, "result": result}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
