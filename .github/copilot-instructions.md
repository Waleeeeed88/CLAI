# CLAI - AI Development Team Orchestrator

## Project Overview

CLAI coordinates multiple AI providers as specialized engineering roles. The core roles are Senior Dev, Coder, Coder 2, Coder 3, QA, BA, and Reviewer. Each role has its own prompt, default model, temperature, and tool access.

Agents use real provider-native tool calling. They can read and write workspace files, use scratchpad memory, query local enterprise data tools, create Excel test plans, run tests, and interact with GitHub through MCP when configured.

## Architecture

```text
shell.py / cli.py / web.py
          |
          v
core.orchestrator.Orchestrator
          |
          +-- agents.factory.AgentFactory
          +-- agents.base.BaseAgent
          +-- agents.token_saver
          +-- roles/*.py
          +-- core.tool_registry.ToolRegistry
          +-- core.filesystem_tools
          +-- core.enterprise_data
          +-- core.mcp_bridge
```

Key patterns:

- `Orchestrator` is the mediator. Agents do not call each other directly.
- `BaseAgent` owns the provider-independent chat loop, history handling, retry behavior, and tool-call loop.
- Provider agents translate CLAI messages and tools into Anthropic, OpenAI, Gemini, Kimi, or OpenRouter formats.
- `AgentFactory` resolves role to provider and model.
- `ToolRegistry` stores provider-agnostic tool definitions and converts them to provider schemas.

## Important Files

| Path | Purpose |
| --- | --- |
| `agents/base.py` | Shared agent chat loop and tool execution |
| `agents/token_saver.py` | Native cost-saving prompt, output cap, and history trimming helpers |
| `agents/factory.py` | Role, provider, model, and agent resolution |
| `config/settings.py` | Environment settings and local override loading |
| `core/orchestrator.py` | Workflows, stages, role-scoped tools, fallback routing |
| `core/pipeline.py` | Full kickoff project lifecycle |
| `core/tool_registry.py` | Tool definitions and provider schema conversion |
| `web/routers/config.py` | Model, tool, and cost-saving settings API |
| `frontend/src/components/SettingsDrawer.tsx` | Web settings UI |

## Agent Flow

1. The caller selects a role.
2. `AgentFactory.create_by_role()` resolves provider and model.
3. `Orchestrator._build_tool_registry()` merges role-appropriate tools.
4. `BaseAgent.chat()` builds messages and applies cost-saver history trimming when enabled.
5. Provider `_send_request()` sends the request with system prompt, messages, tools, max tokens, and temperature.
6. If the model requests tools, `BaseAgent` executes them and loops up to `MAX_TOOL_CALL_ITERATIONS`.
7. The final assistant message is returned as `AgentResponse`.

## Cost Saver

Cost Saver is native to the agent layer.

- Config fields live in `config/settings.py`.
- Runtime policy helpers live in `agents/token_saver.py`.
- `BaseAgent.__init__()` appends the token-saver prompt and caps max output tokens when enabled.
- `BaseAgent._history_for_request()` trims and compacts old history before provider calls.
- Web API schema uses `CostSavingConfig`.
- Web UI controls are in the Settings drawer.

Do not duplicate token-saver logic in provider-specific agents unless a provider requires a format-specific conversion.

## Tool Categories

- Filesystem: `read_file`, `write_file`, `append_file`, `delete_file`, `list_directory`, `create_directory`, `get_tree`, `search_files`, `grep`
- Scratchpad: shared per-run coordination memory
- Enterprise data: catalog, semantic search, knowledge facts, memory, governance, audit, cost estimate, prompt cache
- QA: Excel test plan creation and pytest execution
- GitHub MCP: role-scoped repo, issue, branch, PR, and review tools

## Workflows and Stages

Workflows chain `WorkflowStep` entries and pass dependency outputs between roles. Register new workflows in `Orchestrator._register_default_workflows()`.

Stages are guided roundtables with short role turns and a synthesis response. Register new stages in `Orchestrator._register_default_stages()` and route them in `run_stage()`.

## Conventions

- Keep provider-specific API details inside provider agents.
- Keep role behavior in `roles/*.py`.
- Keep settings persistence in `config/settings.py` and `web/routers/config.py`.
- Keep frontend API types aligned with `web/models/schemas.py`.
- Prefer focused tests in `tests/` for config, orchestration, and shared agent behavior.
- Avoid committing local workspaces, `.env`, generated logs, or `.pi/`.

## Verification

Run:

```bash
python -m pytest
cd frontend && npm run build
```

Current tests intentionally allow the Google Gemini SDK deprecation warning from `google.generativeai`.
