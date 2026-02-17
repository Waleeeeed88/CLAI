"""Test runner — executes tests in a sandboxed subprocess.

Provides a ``run_tests`` tool that agents can call to execute ``pytest``
(or another test command) inside the workspace and capture results.
"""
from __future__ import annotations

import logging
import subprocess
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.tool_registry import ToolParameter, ToolRegistry

logger = logging.getLogger(__name__)

# Maximum output returned to the model (characters)
_MAX_OUTPUT_CHARS = 8000

# Allowed base commands (security whitelist)
_ALLOWED_COMMANDS = {"pytest", "python", "python3", "node", "npm", "npx"}

# Default timeout (seconds)
_DEFAULT_TIMEOUT = 120


def _run_tests(
    command: str = "pytest",
    args: str = "-v --tb=short",
    working_dir: str = ".",
    workspace_root: Optional[Path] = None,
) -> str:
    """Execute a test command in the workspace.

    Args:
        command: Base command (e.g. 'pytest', 'python').
        args: Additional arguments as a single space-separated string.
        working_dir: Relative directory within the workspace.
        workspace_root: Absolute workspace root.

    Returns:
        Combined stdout+stderr output, truncated if too long.
    """
    if workspace_root is None:
        from config import get_settings
        workspace_root = get_settings().workspace_path

    # Validate command
    base_cmd = command.strip().split()[0]
    if base_cmd not in _ALLOWED_COMMANDS:
        return (
            f"Error: Command '{base_cmd}' is not allowed. "
            f"Allowed commands: {', '.join(sorted(_ALLOWED_COMMANDS))}"
        )

    # Resolve working directory
    clean_dir = working_dir.lstrip("/").lstrip("\\")
    cwd = (workspace_root / clean_dir).resolve()
    try:
        cwd.relative_to(workspace_root)
    except ValueError:
        return f"Error: Working directory '{working_dir}' escapes workspace sandbox."
    if not cwd.exists():
        return f"Error: Directory '{working_dir}' does not exist."

    # Build full command
    full_cmd = f"{command} {args}".strip()
    logger.info(f"Running tests: {full_cmd} in {cwd}")

    try:
        result = subprocess.run(
            full_cmd,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=_DEFAULT_TIMEOUT,
            env=None,  # inherit env
        )

        output_parts = []
        if result.stdout:
            output_parts.append(f"=== STDOUT ===\n{result.stdout}")
        if result.stderr:
            output_parts.append(f"=== STDERR ===\n{result.stderr}")

        output = "\n".join(output_parts) or "(no output)"
        exit_info = f"\n=== EXIT CODE: {result.returncode} ==="

        # Truncate if necessary
        combined = output + exit_info
        if len(combined) > _MAX_OUTPUT_CHARS:
            combined = combined[:_MAX_OUTPUT_CHARS] + "\n... (truncated)"

        return combined

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {_DEFAULT_TIMEOUT} seconds."
    except FileNotFoundError:
        return f"Error: Command '{base_cmd}' not found. Is it installed?"
    except Exception as e:
        return f"Error running tests: {e}"


def build_test_runner_registry(workspace_root: Optional[Path] = None) -> ToolRegistry:
    """Build a ToolRegistry with the test runner tool."""
    registry = ToolRegistry()

    def handler(
        command: str = "pytest",
        args: str = "-v --tb=short",
        working_dir: str = ".",
    ) -> str:
        return _run_tests(command, args, working_dir, workspace_root)

    registry.register(
        name="run_tests",
        description=(
            "Execute a test command (e.g. pytest) inside the workspace and return "
            "the output. Use this to verify implementations, run unit tests, or "
            "check linting. The command runs in a sandboxed subprocess."
        ),
        parameters=[
            ToolParameter(
                "command", "string",
                f"Base test command. Allowed: {', '.join(sorted(_ALLOWED_COMMANDS))}. Default: pytest",
                required=False,
            ),
            ToolParameter(
                "args", "string",
                "Additional arguments (e.g. '-v --tb=short', 'test_file.py'). Default: '-v --tb=short'",
                required=False,
            ),
            ToolParameter(
                "working_dir", "string",
                "Working directory relative to workspace root. Default: '.'",
                required=False,
            ),
        ],
        handler=handler,
    )

    return registry
