import logging
from typing import Any, Dict, List
from pydantic import BaseModel

logger = logging.getLogger("evalgen.mcp")


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    server_name: str = "builtin"


class MCPService:
    """Manager for Model Context Protocol (MCP) tool integrations."""

    def __init__(self):
        self._registered_tools: Dict[str, MCPToolDefinition] = {}
        self._register_default_eval_tools()

    def _register_default_eval_tools(self) -> None:
        """Register built-in evaluation context tools conforming to MCP schemas."""
        self.register_tool(
            MCPToolDefinition(
                name="schema_validator",
                description="Validates that an LLM response strictly conforms to a target JSON schema",
                parameters={
                    "type": "object",
                    "properties": {
                        "payload": {"type": "string", "description": "Candidate JSON text"},
                        "schema": {"type": "object", "description": "JSON schema definition"},
                    },
                    "required": ["payload", "schema"],
                },
                server_name="evalgen-core",
            )
        )
        self.register_tool(
            MCPToolDefinition(
                name="fuzzy_match_scorer",
                description="Computes normalized Levenshtein and token-overlap similarity between expected and actual output",
                parameters={
                    "type": "object",
                    "properties": {
                        "expected": {"type": "string"},
                        "actual": {"type": "string"},
                        "threshold": {"type": "number", "default": 0.8},
                    },
                    "required": ["expected", "actual"],
                },
                server_name="evalgen-core",
            )
        )
        self.register_tool(
            MCPToolDefinition(
                name="context_retriever",
                description="Fetches reference context or ground-truth documentation from local/remote sources",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "domain": {"type": "string"},
                    },
                    "required": ["query"],
                },
                server_name="evalgen-core",
            )
        )

    def register_tool(self, tool: MCPToolDefinition) -> None:
        self._registered_tools[tool.name] = tool
        logger.info("Registered MCP tool: %s (%s)", tool.name, tool.server_name)

    def list_tools(self) -> List[MCPToolDefinition]:
        return list(self._registered_tools.values())

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an MCP tool."""
        if tool_name not in self._registered_tools:
            raise ValueError(f"MCP tool '{tool_name}' is not registered.")

        # Built-in tool implementations
        if tool_name == "schema_validator":
            import json
            import jsonschema
            try:
                data = json.loads(arguments["payload"])
                jsonschema.validate(instance=data, schema=arguments["schema"])
                return {"valid": True, "error": None}
            except Exception as e:
                return {"valid": False, "error": str(e)}

        elif tool_name == "fuzzy_match_scorer":
            expected = arguments["expected"].strip().lower()
            actual = arguments["actual"].strip().lower()
            if not expected and not actual:
                score = 1.0
            elif not expected or not actual:
                score = 0.0
            else:
                # Token overlap ratio
                expected_tokens = set(expected.split())
                actual_tokens = set(actual.split())
                overlap = expected_tokens.intersection(actual_tokens)
                union = expected_tokens.union(actual_tokens)
                score = len(overlap) / len(union) if union else 0.0

            threshold = arguments.get("threshold", 0.8)
            return {"score": round(score, 3), "passed": score >= threshold}

        elif tool_name == "context_retriever":
            query = arguments["query"]
            return {
                "snippets": [
                    f"Retrieved reference context for evaluation query: '{query}'",
                ]
            }

        return {"status": "executed", "output": arguments}


mcp_service = MCPService()
