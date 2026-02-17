# CLAI — AI Development Team Orchestrator

## Project Overview

CLAI is a multi-agent orchestration system that coordinates different AI models (Claude, GPT, Gemini) as specialized team members. Each role uses a specific model optimized for their task: Claude for architecture/coding, GPT for business analysis, Gemini for coding and QA.

Agents have **real tool-calling capabilities** — they use native function calling (not prompt-based) to read/write files, interact with GitHub, create Excel test plans, and run tests. The tool-call loop supports up to 25 iterations per request.

**Core Patterns**: Mediator pattern via `Orchestrator` — agents never interact directly. Template Method in `BaseAgent` for consistent provider interfaces. Factory in `AgentFactory` for role→provider→agent creation.

## Architecture

### Component Layers
```
shell.py (Entry Point)
    ↓
shell/main.py (Interactive UI, @mentions, commands)
    ↓
core/orchestrator.py (Mediator — ask, workflows, roundtable, tool injection)
    ↓
agents/factory.py (Factory) → agents/{claude,gpt,gemini}_agent.py (Concrete Agents)
    ↓
agents/base.py (Tool-call loop, message history)
    ↓
roles/*.py (System Prompts + Config)
    ↓
core/tool_registry.py (Provider-agnostic tool definitions + format converters)
    ↓
┌──────────────────┬───────────────────┬──────────────────┬─────────────────┐
│ filesystem_tools │ mcp_bridge.py     │ excel_tools.py   │ test_runner.py  │
│ (9 file ops)     │ (GitHub MCP)      │ (Excel plans)    │ (pytest)        │
└──────────────────┴───────────────────┴──────────────────┴─────────────────┘
```

Additionally:
- `core/pipeline.py` — `ProjectPipeline` with 6-phase project lifecycle (used by `kickoff` command)
- `core/mcp_client.py` — `MCPClient` wrapping MCP SDK's `ClientSession` via stdio transport
- `core/mcp_bridge.py` — Converts MCP tools to `ToolRegistry` entries; role-scoped GitHub tool filtering

**Critical**: `Orchestrator._build_tool_registry(role)` merges filesystem + GitHub + Excel + test tools per role. All agents can read/write files in `workspace/` directory (sandboxed).

### Agent Creation Flow
1. `AgentFactory.create_by_role(Role.SENIOR_DEV)` 
2. Factory looks up role → provider mapping in `ROLE_PROVIDERS`
3. Loads `RoleConfig` from `roles/senior_dev.py` (system prompt, temperature, etc.)
4. Instantiates appropriate agent class (`ClaudeAgent`, `GPTAgent`, `GeminiAgent`)
5. Agent's `_initialize_client()` pulls API key from `config/settings.py` (Pydantic Settings)

## Key Conventions

### Role-Provider Mapping (agents/factory.py)
```python
ROLE_PROVIDERS = {
    Role.SENIOR_DEV: Provider.ANTHROPIC,  # claude-opus-4-5-20251101
    Role.CODER: Provider.ANTHROPIC,       # claude-sonnet-4-5-20250929
    Role.CODER_2: Provider.GOOGLE,        # gemini-3-pro-preview
    Role.QA: Provider.GOOGLE,             # gemini-3-flash-preview
    Role.BA: Provider.OPENAI,             # gpt-5.2-2025-12-11
    Role.REVIEWER: Provider.ANTHROPIC,    # claude-sonnet-4-5-20250929
}
```
**When adding roles**: Update this dict + create `roles/new_role.py` with `register_role()` call + add to `_FS_TOOL_ROLES` in orchestrator + add mention alias in `shell/constants.py`.

### Tool-Call Architecture
Defined in `agents/base.py`:
- `ToolCall(id, name, arguments)` / `ToolResult(tool_call_id, content, is_error)` dataclasses
- `MAX_TOOL_CALL_ITERATIONS = 25`
- `chat()` loops: send → check tool_calls → execute → append results → send again
- Provider-specific message conversion: `_to_anthropic_messages()`, `_to_openai_messages()`, `_to_gemini_messages()`
- Each provider extracts `ToolCall` objects in its own `_send_request()`

### Tool Registry (core/tool_registry.py)
- `ToolParameter(name, type, description, required, enum)`
- `ToolDefinition(name, description, parameters, handler)`
- `ToolRegistry.register()`, `.execute()`, `.merge()`, `.list_tools()`, `.get_definition()`
- Format converters: `.to_anthropic_format()`, `.to_openai_format()`, `.to_gemini_format()`

### Tool Categories
- **Filesystem** (all roles): `read_file`, `write_file`, `append_file`, `delete_file`, `list_directory`, `create_directory`, `get_tree`, `search_files`, `grep`
- **GitHub** (role-scoped via `core/mcp_bridge.py`): Senior gets repo+branch+PR management, BA gets issues, Coders get branch+push+PR, Reviewer gets PR review, QA gets issues+file reading
- **Excel** (QA): `create_test_plan_excel` — creates `.xlsx` test plans
- **Test Runner** (QA): `run_tests` — executes pytest

### GitHub MCP Integration
- `core/mcp_client.py` — `MCPClient` wraps MCP SDK, stdio transport to `npx @modelcontextprotocol/server-github`
- `core/mcp_bridge.py` — `build_github_registry_for_role()` filters tools per role
- Lazy-initialized in `Orchestrator._init_github_mcp()` on first use
- Config: `github_token`, `github_mcp_enabled`, `github_mcp_command`, `github_mcp_args` in `config/settings.py`

### System Prompts Pattern
Each role file (`roles/*.py`) defines:
- `ROLE_PROMPT` — multi-line string with role persona, tools listing, pipeline workflow section, communication style
- `RoleConfig` dataclass with `temperature` (0.5 for senior_dev, 0.4 for qa, 0.6-0.7 others)
- `register_role("role_name", config)` at module level

Role prompts include:
- Tools Available section listing specific tools per role
- Pipeline Workflow section explaining their duties during `kickoff`

See [roles/senior_dev.py](roles/senior_dev.py) for reference implementation.

### Workflow Definitions (orchestrator.py#L338-L415)
Workflows chain agents with `depends_on` references to previous step outputs:
```python
WorkflowStep(
    role=Role.CODER,
    instruction="Implement based on architecture",
    depends_on=["step_1_senior_dev"]  # Gets senior dev's output
)
```
Step names are auto-generated as `step_{index}_{role.value}`.

## Shell Features

### @Mention Parsing (shell/main.py)
Aliases like `@senior`, `@dev`, `@qa` map to `Role` enums via `MENTION_ALIASES` dict in `shell/constants.py`. Parser uses regex to extract mentions and route to correct agent.

### Key Shell Commands
- `kickoff [name]` — Full 6-phase project pipeline (Planning → Setup → Build → Quality → Review → Delivery)
- `workflow <name>` — Run a named workflow (8 available: feature, review, bugfix, architecture, project_setup, full_feature, pr_review, test_and_verify)
- `stage <name>` — Run a structured team discussion stage
- `@team <prompt>` — BA-first roundtable discussion
- `tools [role]` — Inspect registered tools
- `github` — GitHub MCP connection status

### File I/O Syntax
- `> filename.py` — Save agent output to file
- `< filename.py` — Load file content into prompt
- `< directory/` — Load all files in directory (recursive)

### Kickoff Pipeline (core/pipeline.py)
The `kickoff` command runs `ProjectPipeline` with 6 phases:
1. **Planning** — BA creates user stories + GitHub issues; team roundtable
2. **Setup** — Senior Dev architects, creates repo, branches, scaffolding
3. **Build** — Coder + Coder 2 implement on feature branches, create PRs
4. **Quality** — QA writes tests, Excel test plan, runs pytest, files bug issues
5. **Review** — Reviewer examines PRs, posts review comments
6. **Delivery** — Senior Dev writes DELIVERY.md with run instructions

Context accumulates across phases via a shared `ctx` dict. Callbacks drive the shell's live output (phase headers, step previews, timing).

## Development Workflows

### Adding a New AI Provider
1. Create `agents/new_provider_agent.py` extending `BaseAgent`
2. Implement abstract methods: `_initialize_client()`, `_send_request(messages, tools)` (must return `AgentResponse` and extract `ToolCall` list)
3. Implement `_to_*_messages()` for message format conversion (handle tool_use/tool_result entries)
4. Add `Provider.NEW` enum value and to `PROVIDER_AGENTS` in `agents/factory.py`
5. Update `config/settings.py` with API key field

See [agents/claude_agent.py](agents/claude_agent.py) for reference (uses Anthropic SDK with `messages.create()`).

### Adding a Workflow
```python
orchestrator.register_workflow("my_workflow", [
    WorkflowStep(role=Role.BA, instruction="Analyze: {input}"),
    WorkflowStep(role=Role.CODER, instruction="Implement", depends_on=["step_0_ba"]),
])
```
Register in `_register_default_workflows()` or dynamically. Add to `WORKFLOWS` list in `shell/constants.py`.

### Running the Project
```bash
# Activate venv (PowerShell)
.\venv\Scripts\Activate.ps1

# Launch interactive shell
python shell.py

# Or use CLI directly
python cli.py ask senior_dev "your question"
python cli.py workflow feature -r "feature description"
```

## Configuration

### Environment Variables (.env)
```ini
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...

# GitHub integration (optional)
GITHUB_TOKEN=ghp_...
GITHUB_MCP_ENABLED=true
GITHUB_MCP_COMMAND=npx
GITHUB_MCP_ARGS=-y @modelcontextprotocol/server-github

MCP_WORKSPACE_ROOT=./workspace  # Sandbox for file operations
```

Loaded via Pydantic Settings in [config/settings.py](config/settings.py). API keys stored as `SecretStr` to prevent logging.

### Model Configuration
Models defined in `settings.py` (e.g., `senior_dev_model`, `coder_model`). Can override per role via `ROLE_MODEL_OVERRIDES` JSON dict or individual env vars. Defaults: Claude Opus 4.5 for architecture, Claude Sonnet 4.5 for coding/review, Gemini 3 Pro for secondary coding, Gemini 3 Flash for QA, GPT 5.2 for business analysis.

## Common Gotchas

1. **Agent state is NOT preserved** between `orchestrator.ask()` calls. Each call is stateless unless using workflows with `depends_on`.
2. **Workflow step outputs** stored in `WorkflowResult.outputs` dict, keyed by auto-generated step names (`step_0_ba`, `step_1_senior_dev`).
3. **File paths in shell** are relative to `MCP_WORKSPACE_ROOT` (`./workspace/` by default), not project root.
4. **Role registration** happens at module import. If adding a role, ensure `roles/__init__.py` imports the new module.
5. **Tool-call iterations** capped at 25 (`MAX_TOOL_CALL_ITERATIONS` in `agents/base.py`).
6. **Gemini strict alternation** — Gemini requires strict user/model message alternation. The agent merges consecutive tool results into a single user entry.
7. **GitHub MCP** is lazy-initialized — `_init_github_mcp()` runs only when an agent needs GitHub tools.
8. **Pipeline context** — `ProjectPipeline` accumulates outputs in a `ctx` dict across phases; each phase reads prior outputs and writes its own.

## Testing the Setup

```python
# Quick test if everything is configured
from orchestrator import Orchestrator
orch = Orchestrator(verbose=True)
response = orch.ask(Role.SENIOR_DEV, "What is a design pattern?")
print(response.content)
```

If this works, all API keys and dependencies are correctly configured.
