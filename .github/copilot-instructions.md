# CLAI — AI Development Team Orchestrator

## Project Overview

CLAI is a multi-agent orchestration system that coordinates different AI models (Claude, GPT, Gemini) as specialized team members. Each role uses a specific model optimized for their task: Claude for architecture/coding, GPT for QA, Gemini for requirements analysis.

**Core Pattern**: Mediator pattern via `Orchestrator` — agents never interact directly. Template Method pattern in `BaseAgent` for consistent provider interfaces.

## Architecture

### Component Layers
```
shell.py (Interactive UI)
    ↓
orchestrator.py (Mediator)
    ↓
agents/factory.py (Factory) → agents/{claude,gpt,gemini}_agent.py (Concrete Agents)
    ↓
roles/*.py (System Prompts + Config)
```

**Critical**: `Orchestrator` provides MCP filesystem tools to agents via `mcp_filesystem.py`. All agents can read/write files in `workspace/` directory (sandboxed).

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
**When adding roles**: Update this dict + create `roles/new_role.py` with `register_role()` call.

### System Prompts Pattern
Each role file (`roles/*.py`) defines:
- `ROLE_PROMPT` (multi-line string with role persona, capabilities, communication style)
- `RoleConfig` dataclass with `temperature` (0.5 for senior_dev, 0.7 default)
- `register_role("role_name", config)` at module level

See [roles/senior_dev.py](roles/senior_dev.py#L8-L41) for reference implementation.

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

### @Mention Parsing (shell.py#L74-L107)
Aliases like `@senior`, `@dev`, `@qa` map to `Role` enums via `MENTION_ALIASES` dict. Parser uses regex to extract mentions and route to correct agent.

### File I/O Syntax
- `> filename.py` — Save agent output to file
- `< filename.py` — Load file content into prompt
- `< directory/` — Load all files in directory (recursive)

Implemented in `shell.py` with regex `r'>>\s*(\S+)'` and `r'<\s*(\S+)'`.

### MCP Filesystem Integration
- All file ops go through `FileSystemTools` class (sandboxed to `workspace/` dir)
- Agents receive these tools in their context (see `orchestrator.py#L110-L117`)
- Security: Paths validated via `_resolve_path()` to prevent directory traversal

## Development Workflows

### Adding a New AI Provider
1. Create `agents/new_provider_agent.py` extending `BaseAgent`
2. Implement abstract methods: `_initialize_client()`, `_prepare_messages()`, `_make_request()`
3. Add to `PROVIDER_AGENTS` in `agents/factory.py`
4. Update `config/settings.py` with API key field

See [agents/claude_agent.py](agents/claude_agent.py) for reference (uses Anthropic SDK with `messages.create()`).

### Adding a Workflow
```python
orchestrator.register_workflow("my_workflow", [
    WorkflowStep(role=Role.BA, instruction="Analyze: {input}"),
    WorkflowStep(role=Role.CODER, instruction="Implement", depends_on=["step_0_ba"]),
])
```
Register in `_register_default_workflows()` or dynamically via `orchestrator.register_workflow()`.

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
MCP_WORKSPACE_ROOT=./workspace  # Sandbox for file operations
```

Loaded via Pydantic Settings in [config/settings.py](config/settings.py). API keys stored as `SecretStr` to prevent logging.

### Model Configuration
Models defined in `settings.py` (e.g., `senior_dev_model`, `coder_model`). Can override per role in `RoleConfig`. Defaults: Claude Opus 4.5 for architecture, Claude Sonnet 4.5 for coding, Gemini 3 Pro/Flash for context and QA, GPT 5.2 for analysis.

## Common Gotchas

1. **Agent state is NOT preserved** between `orchestrator.ask()` calls. Each call is stateless unless using workflows with `depends_on`.
2. **Workflow step outputs** stored in `WorkflowResult.outputs` dict, keyed by auto-generated step names (`step_0_ba`, `step_1_senior_dev`).
3. **File paths in shell** are relative to `MCP_WORKSPACE_ROOT` (`./workspace/` by default), not project root.
4. **Role registration** happens at module import. If adding a role, ensure `roles/__init__.py` imports the new module.

## Testing the Setup

```python
# Quick test if everything is configured
from orchestrator import Orchestrator
orch = Orchestrator(verbose=True)
response = orch.ask(Role.SENIOR_DEV, "What is a design pattern?")
print(response.content)
```

If this works, all API keys and dependencies are correctly configured.
