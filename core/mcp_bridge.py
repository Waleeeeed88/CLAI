"""MCP Bridge — converts MCP server tools into a ToolRegistry.

Connects to an MCP server (via ``MCPClient``), discovers its tools,
and creates ``ToolDefinition`` entries with handlers that delegate
back to ``MCPClient.call_tool_sync()``.

Usage::

    from core.mcp_client import MCPClient
    from core.mcp_bridge import build_mcp_registry

    client = MCPClient(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": token},
    )
    client.connect_sync()
    registry = build_mcp_registry(client)
    # registry now has all GitHub MCP tools, callable by agents
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core.tool_registry import ToolDefinition, ToolParameter, ToolRegistry
from core.mcp_client import MCPClient, MCPToolInfo

logger = logging.getLogger(__name__)


def _json_schema_to_parameters(schema: Dict[str, Any]) -> List[ToolParameter]:
    """Convert a JSON Schema ``object`` to a flat list of ToolParameter."""
    properties = schema.get("properties", {})
    required_set = set(schema.get("required", []))
    params: List[ToolParameter] = []
    for name, prop in properties.items():
        param_type = prop.get("type", "string")
        if isinstance(param_type, list):
            # JSON Schema union, pick the first non-null type
            param_type = next((t for t in param_type if t != "null"), "string")

        # Preserve array items schema — required by OpenAI/Anthropic
        items = None
        if param_type == "array":
            items = prop.get("items", {"type": "string"})

        params.append(
            ToolParameter(
                name=name,
                type=param_type,
                description=prop.get("description", ""),
                required=name in required_set,
                enum=prop.get("enum"),
                items=items,
            )
        )
    return params


def _make_handler(client: MCPClient, tool_name: str):
    """Create a closure that calls the MCP tool synchronously."""
    def handler(**kwargs: Any) -> str:
        return client.call_tool_sync(tool_name, kwargs)
    return handler


def build_mcp_registry(
    client: MCPClient,
    tool_filter: Optional[List[str]] = None,
) -> ToolRegistry:
    """Discover MCP tools and wrap them in a ``ToolRegistry``.

    Args:
        client: A connected ``MCPClient``.
        tool_filter: If provided, only include tools whose names are in
            this list.  Useful for scoping which GitHub tools a role
            receives (e.g. only issue tools for the BA).
    """
    registry = ToolRegistry()

    tools: List[MCPToolInfo] = client.list_tools_sync()
    logger.info(f"Building registry from {len(tools)} MCP tools")

    for tool in tools:
        if tool_filter and tool.name not in tool_filter:
            continue

        params = _json_schema_to_parameters(tool.input_schema)
        handler = _make_handler(client, tool.name)

        registry.register(
            name=tool.name,
            description=tool.description,
            parameters=params,
            handler=handler,
        )
        logger.debug(f"Registered MCP tool: {tool.name}")

    return registry


# ── Convenience: role-scoped GitHub tool sets ────────────────────────

# Tool names from the official GitHub MCP server that each role needs.
GITHUB_BA_TOOLS = [
    "create_repository",
    "create_issue",
    "list_issues",
    "search_issues",
    "get_issue",
    "update_issue",
    "add_issue_comment",
]

GITHUB_REVIEWER_TOOLS = [
    "get_pull_request",
    "list_pull_requests",
    "create_pull_request_review",
    "get_pull_request_files",
    "get_pull_request_status",
    "get_pull_request_comments",
    "get_pull_request_reviews",
]

GITHUB_CODER_TOOLS = [
    "create_branch",
    "list_branches",
    "create_or_update_file",
    "get_file_contents",
    "push_files",
    "create_pull_request",
]

GITHUB_QA_TOOLS = [
    "list_issues",
    "search_issues",
    "create_issue",
    "add_issue_comment",
    "get_file_contents",
]

GITHUB_SENIOR_TOOLS = [
    # Repo management
    "create_repository",
    "create_issue",
    "list_issues",
    "search_issues",
    "get_issue",
    "update_issue",
    "add_issue_comment",
    # Branch & file operations
    "create_branch",
    "list_branches",
    "create_or_update_file",
    "get_file_contents",
    "push_files",
    # PRs
    "create_pull_request",
    "list_pull_requests",
    "get_pull_request",
    "update_pull_request_branch",
    "merge_pull_request",
]


def build_github_registry_for_role(
    client: MCPClient,
    role_name: str,
) -> ToolRegistry:
    """Build a GitHub ToolRegistry scoped to a specific role.

    Args:
        client: A connected ``MCPClient`` for the GitHub MCP server.
        role_name: One of ``ba``, ``reviewer``, ``coder``, ``coder_2``,
            ``coder_3``, ``senior_dev``, ``qa``.
    """
    filter_map = {
        "ba": GITHUB_BA_TOOLS,
        "reviewer": GITHUB_REVIEWER_TOOLS,
        "coder": GITHUB_CODER_TOOLS,
        "coder_2": GITHUB_CODER_TOOLS,
        "coder_3": GITHUB_CODER_TOOLS,
        "senior_dev": GITHUB_SENIOR_TOOLS,
        "qa": GITHUB_QA_TOOLS,
    }
    tool_filter = filter_map.get(role_name)
    return build_mcp_registry(client, tool_filter=tool_filter)
