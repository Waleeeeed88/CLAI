# CLAI — Developer Onboarding

This document explains how CLAI works under the hood. Read this if you're contributing, debugging, or extending the system.

---

## How It Works (30-Second Version)

1. You type `@senior design an auth API`
2. Shell parses `@senior` → `Role.SENIOR_DEV`
3. Orchestrator gets (or creates) a `ClaudeAgent` for that role
4. Agent receives filesystem + GitHub tools via `ToolRegistry`
5. Agent calls Anthropic API with tools, may call them in a loop (up to 25x)
6. Final response displayed in a rich panel

For workflows, agents run in sequence with `depends_on` chains. For `kickoff`, a 6-phase pipeline coordinates all roles.

---

## Project Structure

```
CLAI/
├── shell.py                  # Entry point — imports and runs shell/main.py
├── cli.py                    # Click-based CLI for non-interactive use
│
├── shell/
│   ├── main.py               # CLAIShell class: commands, @mentions, kickoff, UI
│   ├── constants.py          # COMMANDS, MENTION_ALIASES, WORKFLOWS, STAGES lists
│   └── completer.py          # Tab completion for @mentions and commands
│
├── agents/
│   ├── base.py               # BaseAgent: tool-call loop, message history, chat()
│   ├── claude_agent.py       # Anthropic: _send_request(), _to_anthropic_messages()
│   ├── gpt_agent.py          # OpenAI: _send_request(), _to_openai_messages()
│   ├── gemini_agent.py       # Google: _send_request(), _to_gemini_messages()
│   └── factory.py            # Role/Provider enums, ROLE_PROVIDERS, AgentFactory
│
├── roles/
│   ├── base.py               # RoleConfig dataclass, register_role(), ROLE_REGISTRY
│   ├── senior_dev.py         # Claude Opus — architecture, scaffolding
│   ├── coder.py              # Claude Sonnet — primary implementation
│   ├── coder_2.py            # Gemini Pro — secondary implementation
│   ├── qa.py                 # Gemini Flash — testing, Excel test plans
│   ├── ba.py                 # GPT — requirements, GitHub issues
│   └── reviewer.py           # Claude Sonnet — PR reviews
│
├── core/
│   ├── orchestrator.py       # Orchestrator: ask(), run_workflow(), roundtable, tool injection
│   ├── pipeline.py           # ProjectPipeline: 6-phase kickoff lifecycle
│   ├── tool_registry.py      # ToolRegistry: define, convert, execute tools
│   ├── filesystem_tools.py   # build_filesystem_registry() — 9 sandboxed file tools
│   ├── mcp_client.py         # MCPClient: stdio transport, list_tools_sync(), call_tool_sync()
│   ├── mcp_bridge.py         # build_github_registry_for_role() — role-scoped GitHub tools
│   ├── excel_tools.py        # create_test_plan_excel tool (openpyxl)
│   ├── test_runner.py        # run_tests tool (subprocess pytest)
│   ├── workflows.py          # WorkflowStep, WorkflowResult, WorkflowStatus
│   └── filesystem.py         # FileSystemTools: sandboxed read/write/list/grep
│
├── config/
│   └── settings.py           # Pydantic Settings: API keys, models, github config
│
├── workspace/                # Sandboxed directory — all agent file ops happen here
├── docs/
│   └── USAGE_GUIDE.md        # Comprehensive user-facing documentation
└── .env                      # API keys (gitignored)
```

---

## Key Files Deep Dive

### agents/base.py — The Tool-Call Loop

The heart of CLAI. `BaseAgent.chat()` does this:

```python
def chat(self, prompt, tool_registry=None):
    # 1. Add user message to history
    # 2. Send to API with tool definitions
    # 3. If response has tool_calls:
    #      a. Execute each tool via tool_registry.execute()
    #      b. Append tool results to history
    #      c. Send again (loop, max 25 iterations)
    # 4. Return final AgentResponse
```

Key dataclasses:
- `ToolCall(id, name, arguments)` — what the model wants to call
- `ToolResult(tool_call_id, content, is_error)` — result sent back

Each provider implementation extracts `ToolCall` in its own `_send_request()`:
- **Claude**: `tool_use` content blocks
- **GPT**: `tool_calls` array on the message  
- **Gemini**: `function_call` parts in the response

### core/orchestrator.py — The Mediator

`Orchestrator` is the central coordinator. Key methods:

| Method | What It Does |
|--------|-------------|
| `ask(role, prompt)` | Single agent request with tools |
| `run_workflow(name, context)` | Multi-step workflow with `depends_on` chains |
| `consult_team_discussion(prompt, roles)` | BA-first roundtable (~170 words each) |
| `_build_tool_registry(role)` | Merges fs + github + excel + test tools per role |
| `_init_github_mcp()` | Lazy-init GitHub MCP client + per-role registries |

Tool injection flow:
```
ask(Role.CODER, prompt)
  └─► _build_tool_registry(Role.CODER)
       ├── filesystem_tools (read_file, write_file, ...)
       ├── github_tools (create_branch, push_files, create_pull_request)
       └── (merged into one ToolRegistry)
  └─► agent.chat(prompt, tool_registry)
```

### core/tool_registry.py — Provider-Agnostic Tools

Tools are defined once, converted to any provider format:

```python
registry = ToolRegistry()
registry.register("my_tool", "Description", params=[...], handler=my_func)

# Convert to provider-specific format:
registry.to_anthropic_format()  # → Anthropic tool schema
registry.to_openai_format()     # → OpenAI function schema  
registry.to_gemini_format()     # → Gemini FunctionDeclaration
```

Key types:
- `ToolParameter(name, type, description, required, enum)`
- `ToolDefinition(name, description, parameters, handler)`
- `ToolRegistry` — container with `register()`, `execute()`, `merge()`

### core/pipeline.py — The Kickoff Pipeline

`ProjectPipeline` coordinates a 6-phase project lifecycle:

```
Phase 1: _phase_planning(ctx)  → BA stories + team roundtable
Phase 2: _phase_setup(ctx)     → Senior architecture + scaffolding
Phase 3: _phase_build(ctx)     → Coder + Coder2 implementation
Phase 4: _phase_quality(ctx)   → QA tests + Excel plan + pytest
Phase 5: _phase_review(ctx)    → Reviewer feedback + PR reviews
Phase 6: _phase_delivery(ctx)  → Senior summary + DELIVERY.md
```

Context (`ctx` dict) accumulates across phases — each phase reads prior outputs and writes its own. Callbacks (`on_phase_start`, `on_step_done`, `on_phase_done`) drive the shell's live UI.

### core/mcp_bridge.py — GitHub Tool Scoping

Each role gets only the GitHub tools they need:

| Role | Tools |
|------|-------|
| **Senior Dev** | `create_repository`, `create_branch`, `list_branches`, `push_files`, `create_pull_request`, `list_pull_requests`, `get_pull_request`, `merge_pull_request`, `create_or_update_file`, `get_file_contents`, `list_issues`, `search_issues`, `get_issue` |
| **BA** | `create_repository`, `create_issue`, `list_issues`, `search_issues`, `get_issue`, `update_issue`, `add_issue_comment` |
| **Coder / Coder 2** | `create_branch`, `list_branches`, `create_or_update_file`, `get_file_contents`, `push_files`, `create_pull_request` |
| **QA** | `list_issues`, `search_issues`, `create_issue`, `add_issue_comment`, `get_file_contents` |
| **Reviewer** | `get_pull_request`, `list_pull_requests`, `create_pull_request_review`, `get_pull_request_diff`, `get_pull_request_files`, `list_pull_request_files`, `add_pull_request_review_comment` |

---

## Current AI Models

| Role | Model ID | Provider |
|------|----------|----------|
| Senior Dev | `claude-opus-4-5-20251101` | Anthropic |
| Coder | `claude-sonnet-4-5-20250929` | Anthropic |
| Coder 2 | `gemini-3-pro-preview` | Google |
| QA | `gemini-3-flash-preview` | Google |
| BA | `gpt-5.2-2025-12-11` | OpenAI |
| Reviewer | `claude-sonnet-4-5-20250929` | Anthropic |

Override in `.env` or via `ROLE_MODEL_OVERRIDES` / `ROLE_PROVIDER_OVERRIDES` (JSON).

---

## Default Workflows (8 total)

Defined in `core/orchestrator.py` → `_register_default_workflows()`:

| Workflow | Steps | Context Keys |
|----------|-------|-------------|
| `feature` | BA → QA → Senior → Coder → Coder2 | `{requirement}` |
| `review` | Reviewer → Senior | `{code}` |
| `bugfix` | QA → Senior → Coder | `{bug_description}`, `{code}` |
| `architecture` | BA → Senior → QA | `{project_description}` |
| `project_setup` | BA → Senior → Coder | `{requirement}` |
| `full_feature` | BA → Senior → Coder → QA → Reviewer | `{requirement}` |
| `pr_review` | Reviewer | `{pr_info}` |
| `test_and_verify` | QA | `{code_path}` |

Each step receives prior outputs via `depends_on` — e.g., `depends_on=["step_0_ba"]` means the step gets BA's output prepended to its prompt.

---

## Shell Commands (All)

| Command | Handler Method | Description |
|---------|---------------|-------------|
| `help` | `print_help()` | Show command list |
| `team` | `print_team()` | Show team roster |
| `config` | `handle_config()` | API key status |
| `workflows` | `print_workflows()` | List workflows |
| `workflow <name>` | `handle_workflow()` | Run workflow |
| `stages` | `print_stages()` | List stages |
| `stage <name>` | `handle_stage()` | Run stage |
| `kickoff [name]` | `handle_kickoff()` | Full project pipeline |
| `tools [role]` | `handle_tools()` | List tools |
| `github` | `handle_github()` | GitHub MCP status |
| `projects` | `handle_projects()` | List workspace projects |
| `newproject <name>` | `handle_new_project()` | Create project |
| `files [path]` | `handle_files()` | List files |
| `tree [path]` | `handle_tree()` | Directory tree |
| `readfile <path>` | `handle_read_file()` | Show file |
| `save <file>` | inline | Save last response |
| `workspace` | inline | Show workspace path |
| `history` | inline | Show agent history |
| `clear` | inline | Clear screen |
| `@<mention>` | `handle_mention()` | Route to agent |
| `@team` | roundtable | All agents discuss |

---

## Adding a New Role (Step by Step)

1. Create `roles/new_role.py` with `RoleConfig` + `register_role()` call
2. Add `Role.NEW_ROLE` to enum in `agents/factory.py`
3. Add to `ROLE_PROVIDERS` dict in `agents/factory.py`
4. Add model field in `config/settings.py`
5. Add to `model_map` in `agents/factory.py` → `_resolve_model()`
6. Import in `roles/__init__.py`
7. Add `@mention` alias in `shell/constants.py` → `MENTION_ALIASES`
8. Add to `_FS_TOOL_ROLES` set in `core/orchestrator.py` (for filesystem tools)
9. (Optional) Add GitHub tool scope in `core/mcp_bridge.py`

---

## Common Gotchas

1. **Agent state is NOT preserved** between `orchestrator.ask()` calls — each call is stateless unless using workflows with `depends_on`.
2. **Gemini strict alternation** — Gemini requires strict user/model message alternation. The agent handles this by merging consecutive tool results into a single user entry.
3. **File paths** — All workspace file operations are relative to `MCP_WORKSPACE_ROOT` (`./workspace/`), not the project root.
4. **Role registration** happens at import time. If you add a role, ensure `roles/__init__.py` imports it.
5. **Tool-call iterations** are capped at 25 (`MAX_TOOL_CALL_ITERATIONS` in `agents/base.py`).
6. **GitHub MCP** is lazy-initialized on first use — `_init_github_mcp()` runs only when an agent needs GitHub tools.

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| "Config error: Field required" | Check `.env` has all three API keys |
| "Model not found" | Verify model names in `config/settings.py` |
| "Path escapes workspace sandbox" | Use relative paths within `workspace/` |
| "GitHub MCP not connected" | Ensure Node.js installed + `GITHUB_MCP_ENABLED=true` |
| Empty agent responses | Check API credits, set `VERBOSE=true` for debug logs |
| Gemini message ordering error | Likely a bug — file an issue |

---

## Quick Test

```python
from core.orchestrator import Orchestrator
from agents.factory import Role

orch = Orchestrator(verbose=True)
response = orch.ask(Role.SENIOR_DEV, "What is a design pattern?")
print(response.content)
```

If this prints a response, all API keys and dependencies are correctly configured.
