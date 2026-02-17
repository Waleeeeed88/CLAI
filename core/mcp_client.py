"""MCP Client — connects to an MCP server over stdio transport.

Uses the official ``mcp`` Python SDK to launch an MCP server as a
subprocess, discover its tools, and invoke them.  This is the low-level
transport layer; see ``mcp_bridge.py`` for the ToolRegistry integration.

Example — connect to the GitHub MCP server::

    client = MCPClient(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx"},
    )
    await client.connect()
    tools = await client.list_tools()
    result = await client.call_tool("create_issue", {...})
    await client.disconnect()
"""
from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MCPToolInfo:
    """Metadata for a single tool discovered from the MCP server."""
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)


class MCPClient:
    """Wraps the ``mcp`` Python SDK's ``ClientSession`` for stdio transport.

    All public methods are ``async``.  Use the synchronous wrappers
    (``connect_sync``, ``call_tool_sync``, etc.) from non-async code.
    """

    def __init__(
        self,
        command: str = "npx",
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        server_name: str = "mcp-server",
    ):
        self.command = command
        self.args = args or ["-y", "@modelcontextprotocol/server-github"]
        self.env = env or {}
        self.server_name = server_name

        self._session: Any = None
        self._read_stream: Any = None
        self._write_stream: Any = None
        self._process_ctx: Any = None  # context-manager from stdio_client
        self._session_ctx: Any = None
        self._connected = False
        self._tools_cache: Optional[List[MCPToolInfo]] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    # ── async lifecycle ──────────────────────────────────────────────

    async def connect(self, timeout: float = 30.0) -> None:
        """Launch the MCP server subprocess and open a session.
        
        Args:
            timeout: Maximum seconds to wait for the server to connect.
                     Raises TimeoutError if exceeded.
        """
        if self._connected:
            return
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as exc:
            raise ImportError(
                "The 'mcp' package is required for MCP server integration. "
                "Install it with: pip install mcp"
            ) from exc

        merged_env = {**os.environ, **self.env}
        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
            env=merged_env,
        )

        logger.info(f"Launching MCP server: {self.command} {' '.join(self.args)}")

        async def _do_connect():
            # stdio_client and ClientSession are async context managers;
            # we enter them manually so the connection stays open across calls.
            self._process_ctx = stdio_client(server_params)
            self._read_stream, self._write_stream = await self._process_ctx.__aenter__()

            self._session_ctx = ClientSession(self._read_stream, self._write_stream)
            self._session = await self._session_ctx.__aenter__()

            # Handshake
            await self._session.initialize()

        try:
            await asyncio.wait_for(_do_connect(), timeout=timeout)
        except asyncio.TimeoutError:
            # Clean up partial state
            logger.error(
                f"MCP server '{self.server_name}' connection timed out "
                f"after {timeout}s"
            )
            await self._cleanup_partial()
            raise TimeoutError(
                f"MCP server '{self.server_name}' failed to connect within "
                f"{timeout} seconds. Check that '{self.command}' is installed "
                f"and the server is reachable."
            )

        self._connected = True
        logger.info(f"MCP server '{self.server_name}' connected")

    async def disconnect(self) -> None:
        """Gracefully close the session and stop the subprocess."""
        if not self._connected:
            return
        try:
            if self._session_ctx:
                await self._session_ctx.__aexit__(None, None, None)
            if self._process_ctx:
                await self._process_ctx.__aexit__(None, None, None)
        except Exception as e:
            logger.warning(f"Error during MCP disconnect: {e}")
        finally:
            self._session = None
            self._connected = False
            self._tools_cache = None
            logger.info(f"MCP server '{self.server_name}' disconnected")

    async def _cleanup_partial(self) -> None:
        """Clean up partially-initialized resources after a failed connect."""
        try:
            if self._session_ctx:
                await self._session_ctx.__aexit__(None, None, None)
        except Exception:
            pass
        try:
            if self._process_ctx:
                await self._process_ctx.__aexit__(None, None, None)
        except Exception:
            pass
        self._session = None
        self._session_ctx = None
        self._process_ctx = None
        self._read_stream = None
        self._write_stream = None

    # ── tool discovery ───────────────────────────────────────────────

    async def list_tools(self, force_refresh: bool = False) -> List[MCPToolInfo]:
        """Discover all tools exposed by the MCP server."""
        if self._tools_cache and not force_refresh:
            return self._tools_cache

        if not self._connected:
            await self.connect()

        response = await self._session.list_tools()
        self._tools_cache = [
            MCPToolInfo(
                name=tool.name,
                description=getattr(tool, "description", "") or "",
                input_schema=dict(getattr(tool, "inputSchema", {})) if getattr(tool, "inputSchema", None) else {},
            )
            for tool in response.tools
        ]
        logger.info(f"Discovered {len(self._tools_cache)} MCP tools")
        return self._tools_cache

    # ── tool invocation ──────────────────────────────────────────────

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Invoke an MCP tool and return the text result."""
        if not self._connected:
            await self.connect()

        logger.debug(f"MCP call_tool: {name}")
        result = await self._session.call_tool(name, arguments=arguments)

        # result.content is a list of content blocks
        parts = []
        for block in result.content:
            if hasattr(block, "text"):
                parts.append(block.text)
            else:
                parts.append(str(block))
        return "\n".join(parts)

    # ── synchronous wrappers (for non-async code) ────────────────────

    def _get_or_create_loop(self) -> asyncio.AbstractEventLoop:
        """Return a persistent event loop for all sync operations.

        The MCP session's IO streams are bound to the loop they were
        created on, so we must reuse the same loop for every call.
        """
        # If we already have a stored loop that isn't closed, reuse it
        if self._loop is not None and not self._loop.is_closed():
            return self._loop

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # Already in async context — use nest_asyncio
            import nest_asyncio  # type: ignore
            nest_asyncio.apply()
            self._loop = loop
            return loop

        self._loop = asyncio.new_event_loop()
        return self._loop

    def _run(self, coro):  # noqa: ANN001
        loop = self._get_or_create_loop()
        return loop.run_until_complete(coro)

    def connect_sync(self) -> None:
        self._run(self.connect())

    def disconnect_sync(self) -> None:
        self._run(self.disconnect())

    def list_tools_sync(self, force_refresh: bool = False) -> List[MCPToolInfo]:
        return self._run(self.list_tools(force_refresh))

    def call_tool_sync(self, name: str, arguments: Dict[str, Any]) -> str:
        return self._run(self.call_tool(name, arguments))

    # ── context manager ──────────────────────────────────────────────

    @property
    def connected(self) -> bool:
        return self._connected

    def __repr__(self) -> str:
        status = "connected" if self._connected else "disconnected"
        return f"MCPClient(server={self.server_name!r}, status={status})"
