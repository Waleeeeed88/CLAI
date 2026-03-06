# CLAI — Developer Onboarding

This document explains how CLAI works under the hood. Read this if you're contributing, debugging, or extending the system.

---

## How It Works (30-Second Version)

1. User opens the web UI at `http://localhost:3000`
2. Types a requirement and hits Send — selects which phases to run (planning, implementation, github_mcp)
3. Frontend POSTs to `/api/chat`, gets a `session_id`, opens an SSE stream
4. Backend spawns a `ProjectPipeline` in a `ThreadPoolExecutor` thread
5. Pipeline runs 3 phases sequentially, each calling `orchestrator.ask(role, prompt)`
6. Each agent gets filesystem + GitHub tools via `ToolRegistry`, calls its provider API in a tool-call loop (up to 25x)
7. SSE events stream back: `agent_start`, `tool_call`, `tool_result`, `agent_done`, `phase_start`, `phase_done`
8. Frontend renders live: PhaseTimeline, AgentActivityCard (thinking dots + tool pills), then MessageBubble on completion

For the CLI shell, agents run in sequence with `depends_on` chains. For `kickoff`, a multi-phase pipeline coordinates all roles.

---

## Project Structure

```
CLAI/
├── shell.py                  # Entry point — imports and runs shell/main.py
├── cli.py                    # Click-based CLI for non-interactive use
├── web.py                    # Entry point — runs FastAPI backend (uvicorn)
│
├── shell/
│   ├── main.py               # CLAIShell class: commands, @mentions, kickoff, UI
│   ├── constants.py          # COMMANDS, MENTION_ALIASES, WORKFLOWS, STAGES lists
│   └── completer.py          # Tab completion for @mentions and commands
│
├── agents/
│   ├── base.py               # BaseAgent: tool-call loop, retry logic, message history
│   ├── claude_agent.py       # Anthropic: _send_request(), input compaction, retries
│   ├── gpt_agent.py          # OpenAI: _send_request(), retry via _retry_request()
│   ├── gemini_agent.py       # Google: _send_request(), retry via _retry_request()
│   ├── kimi_agent.py         # Kimi/Moonshot: subclasses GPTAgent, OpenAI-compatible API
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
│   ├── pipeline.py           # ProjectPipeline: 3-phase lifecycle with 8-step implementation
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
│   ├── __init__.py           # Re-exports Settings, get_settings, clear_settings_cache
│   ├── settings.py           # Pydantic Settings: API keys, models, overrides, cache control
│   └── overrides.json        # Runtime role→provider+model overrides (written by web UI)
│
├── web/
│   ├── app.py                # FastAPI app factory, CORS, lifespan cleanup task
│   ├── routers/
│   │   ├── chat.py           # POST /api/chat, GET /stream, POST /cancel
│   │   ├── config.py         # GET/POST /api/config/models — role-model assignments
│   │   ├── workflows.py      # GET /api/workflows — phase metadata
│   │   └── filesystem.py     # GET /api/filesystem/roots, /list — directory browsing
│   ├── models/
│   │   └── schemas.py        # ChatRequest, RoleConfig, ModelConfigResponse, etc.
│   └── services/
│       ├── event_bus.py       # Queue-backed SSE bus with cancellation support
│       ├── session_manager.py # Thread-safe session store with TTL cleanup
│       ├── runner.py          # Bridges sync orchestrator to async SSE layer
│       └── observable_registry.py # Wraps ToolRegistry to emit tool_call/result events
│
├── frontend/                 # Next.js 15 / React 19 / TypeScript / Tailwind CSS
│   └── src/
│       ├── app/
│       │   ├── page.tsx      # Main page: TopBar + ChatWindow + ChatInput + drawers
│       │   ├── layout.tsx    # Root layout with fonts
│       │   └── globals.css   # Design tokens, animations, typography
│       ├── components/
│       │   ├── TopBar.tsx         # Logo, status, drawer toggles, new chat
│       │   ├── ChatWindow.tsx     # WelcomeScreen (idle) or message stream (active)
│       │   ├── ChatInput.tsx      # Textarea, phase chips, config panel, stop button
│       │   ├── WelcomeScreen.tsx   # "Welcome back" + suggestion cards
│       │   ├── MessageBubble.tsx   # Agent avatar, markdown content, tool calls
│       │   ├── MarkdownRenderer.tsx # react-markdown with CodeBlock integration
│       │   ├── CodeBlock.tsx      # Shiki syntax highlighting + copy button
│       │   ├── ToolCallBlock.tsx   # Expandable tool call with framer-motion
│       │   ├── AgentBadge.tsx     # Colored icon badge per agent
│       │   ├── AgentActivityCard.tsx # Live "thinking" card with tool pills
│       │   ├── PhaseTimeline.tsx   # Horizontal stepper (done/running/pending)
│       │   ├── FilesPanel.tsx     # Slide-over drawer showing generated files
│       │   ├── SettingsDrawer.tsx  # Editable model config per role (provider + model)
│       │   ├── ConversationHistory.tsx # Left drawer with past conversations
│       │   └── DirectoryPickerModal.tsx # File/folder browser modal
│       ├── hooks/
│       │   └── useSSE.ts     # EventSource hook with stable ref + retry
│       ├── store/
│       │   └── chatStore.ts  # Zustand store: messages, phases, files, events
│       └── lib/
│           ├── api.ts        # REST + SSE API functions
│           ├── types.ts      # TypeScript interfaces
│           ├── constants.ts  # Agent metadata, phases, providers, default models
│           ├── cn.ts         # clsx utility
│           └── highlighter.ts # Shiki singleton loader
│
├── workspace/                # Sandboxed directory — all agent file ops happen here
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

All agents share retry logic via `_retry_request()` in BaseAgent — exponential backoff on rate limits (3 attempts, 8s base delay). All clients have a 5-minute request timeout.

Key dataclasses:
- `ToolCall(id, name, arguments)` — what the model wants to call
- `ToolResult(tool_call_id, content, is_error)` — result sent back

Each provider implementation extracts `ToolCall` in its own `_send_request()`:
- **Claude**: `tool_use` content blocks
- **GPT**: `tool_calls` array on the message
- **Gemini**: `function_call` parts in the response
### core/pipeline.py — The Project Pipeline

`ProjectPipeline` coordinates a 3-phase project lifecycle with an 8-step implementation phase:

```
Phase 1: _phase_planning
  └─► BA creates plan, stories, issue backlog

Phase 2: _phase_implementation (8 steps)
  ├─► Step 1: BA — task breakdown + acceptance criteria
  ├─► Step 2: Senior Dev — architecture + coding guidelines
  ├─► Step 3: QA — upfront test strategy + quality gates
  ├─► Step 4: Coder — primary implementation
  ├─► Step 5: Coder 2 — gap filling + integration code
  ├─► Step 6: Reviewer — code review
  ├─► Step 7: Senior Dev — final sign-off
  └─► Step 8: QA — test assets + Excel plan + defect report

Phase 3: _phase_github_mcp
  └─► BA syncs issues to GitHub (or creates local fallback files)
```

Context (`ctx` dict) accumulates across phases. Cancellation is checked before each step via `_check_cancelled()`.

### web/services/event_bus.py — SSE Bridge

The `EventBus` bridges synchronous pipeline threads to async SSE:
- Background threads call `bus.put(event)` to emit events
- FastAPI drains the queue via `async stream()` generator
- Supports cancellation via `threading.Event` — `bus.cancel()` signals the pipeline to stop
- Heartbeat pings every 15s to keep the connection alive

### web/routers/config.py — Runtime Model Configuration

The config API lets users change which model handles which role from the web UI:
- `GET /api/config/models` — returns current role→provider+model mapping for all 6 roles
- `POST /api/config/models` — saves overrides to `config/overrides.json`, clears the Settings `lru_cache`

Overrides persist across server restarts (stored in JSON file). The next pipeline run automatically uses the updated assignments.

---

## Current AI Models (Defaults)

| Role | Model ID | Provider |
|------|----------|----------|
| Senior Dev | `claude-opus-4-5-20251101` | Anthropic |
| Coder | `claude-sonnet-4-5-20250929` | Anthropic |
| Coder 2 | `gemini-3.1-pro-preview` | Google |
| QA | `gemini-3-flash-preview` | Google |
| BA | `gpt-5.2-2025-12-11` | OpenAI |
| Reviewer | `claude-sonnet-4-5-20250929` | Anthropic |

**Available providers**: Anthropic, OpenAI, Google, Kimi

Override models via:
1. **Web UI** — Settings drawer → change provider/model per role → Save
2. **Environment** — `ROLE_MODEL_OVERRIDES` / `ROLE_PROVIDER_OVERRIDES` JSON in `.env`
3. **File** — Edit `config/overrides.json` directly

---

## Web App Architecture

### Request Flow

```
Browser                    FastAPI                    Pipeline Thread
  │                          │                              │
  ├── POST /api/chat ──────►│                              │
  │                          ├── create session + EventBus  │
  │                          ├── submit to ThreadPoolExecutor
  │◄── {session_id} ────────│                              │
  │                          │                              │
  ├── GET /stream ──────────►│                              │
  │   (EventSource)          │◄── bus.put(agent_start) ────│
  │◄── SSE: agent_start ────│                              │
  │◄── SSE: tool_call ──────│◄── bus.put(tool_call) ──────│
  │◄── SSE: tool_result ────│◄── bus.put(tool_result) ────│
  │◄── SSE: agent_done ─────│◄── bus.put(agent_done) ─────│
  │◄── SSE: done ────────────│◄── bus.close() ─────────────│
```

### Frontend State Management

Zustand store (`chatStore.ts`) processes SSE events:
- `agent_start` → creates a streaming message placeholder
- `tool_call` → attaches tool pill to current message, tracks file writes
- `tool_result` → marks tool as done/error, updates file status (FIFO matching)
- `agent_done` → finalizes message with content, tokens, model
- `phase_start/done` → updates PhaseTimeline stepper
- `pipeline_complete` → sets `isRunning: false`, shows error if status is "failed"
- `error` → displays error message, stops running state

### Cancellation

Real cancellation flows through the full stack:
1. User clicks Stop → `POST /api/chat/{id}/cancel`
2. Backend calls `bus.cancel()` (sets `threading.Event`) + `bus.close()`
3. Pipeline checks `_check_cancelled()` before each `_ask()` step
4. Raises `RuntimeError("Pipeline cancelled by user")` — stops making API calls

---

## Adding a New Provider (Step by Step)

Example: Adding any OpenAI-compatible provider (Kimi is included as a reference).

1. Create `agents/new_provider_agent.py` — subclass `GPTAgent` for OpenAI-compatible APIs:
   ```python
   class NewAgent(GPTAgent):
       @property
       def provider_name(self) -> str:
           return "new_provider"
       def _initialize_client(self) -> None:
           self._client = OpenAI(api_key=key, base_url="https://api.example.com/v1")
   ```
2. Add `NEW_PROVIDER = "new_provider"` to `Provider` enum in `agents/factory.py`
3. Add `Provider.NEW_PROVIDER: NewAgent` to `PROVIDER_AGENTS` dict
4. Add `new_provider_api_key: Optional[SecretStr]` to `config/settings.py`
5. Export from `agents/__init__.py`
6. Add to `PROVIDERS` list in `frontend/src/lib/constants.ts`
7. Add default models to `DEFAULT_MODELS` in `constants.ts`

## Adding a New Role (Step by Step)

1. Create `roles/new_role.py` with `RoleConfig` + `register_role()` call
2. Add `Role.NEW_ROLE` to enum in `agents/factory.py`
3. Add to `ROLE_PROVIDERS` dict in `agents/factory.py`
4. Add model field in `config/settings.py`
5. Add to `model_map` in `agents/factory.py` → `_resolve_model()`
6. Import in `roles/__init__.py`
7. Add `@mention` alias in `shell/constants.py` → `MENTION_ALIASES`
8. Add to `_FS_TOOL_ROLES` set in `core/orchestrator.py` (for filesystem tools)
9. Add to `AGENTS` in `frontend/src/lib/constants.ts` (for UI display)
10. (Optional) Add GitHub tool scope in `core/mcp_bridge.py`

---

## Common Gotchas

1. **Settings cache** — `get_settings()` is cached via `@lru_cache`. Changes to `.env` or `overrides.json` require calling `clear_settings_cache()` (the web UI config endpoint does this automatically).
2. **Gemini strict alternation** — Gemini requires strict user/model message alternation. The agent handles this by merging consecutive tool results into a single user entry.
3. **Gemini schema types** — Gemini's `FunctionDeclaration` expects protobuf `Type` enums, not JSON Schema strings. `_convert_schema_for_gemini()` in `tool_registry.py` handles the conversion.
4. **File paths** — All workspace file operations are relative to `MCP_WORKSPACE_ROOT` (`./workspace/`), not the project root.
5. **Role registration** happens at import time. If you add a role, ensure `roles/__init__.py` imports it.
6. **Tool-call iterations** are capped at 25 (`MAX_TOOL_CALL_ITERATIONS` in `agents/base.py`).
7. **GitHub MCP** is lazy-initialized on first use — `_init_github_mcp()` runs only when an agent needs GitHub tools.
8. **Orchestrator is per-run** — A new `Orchestrator` is created per pipeline run in `runner.py`, so settings changes take effect on the next run.
9. **Output files use `.markdown`** — Pipeline prompts specify `.markdown` extension for all generated markdown files (not `.md`).

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| "Config error: Field required" | Check `.env` has `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY` |
| "KIMI_API_KEY is not set" | Add `KIMI_API_KEY=...` to `.env` (only needed if you route a role to Kimi) |
| "Invalid provider override" | Valid providers: `anthropic`, `openai`, `google`, `kimi` |
| "Model not found" | Verify model names in Settings drawer or `config/settings.py` |
| "Path escapes workspace sandbox" | Use relative paths within `workspace/` |
| "GitHub MCP not connected" | Ensure Node.js installed + `GITHUB_MCP_ENABLED=true` |
| Empty agent responses | Check API credits, set `VERBOSE=true` for debug logs |
| "Lost connection to server" | Backend not running — start with `python web.py` |
| Pipeline shows success but failed | Check agent messages for `[error]` prefixed content |
| Settings changes not taking effect | The web UI clears the cache automatically; for `.env` changes, restart the server |

---

## Quick Test

### Backend
```python
from core.orchestrator import Orchestrator
from agents.factory import Role

orch = Orchestrator(verbose=True)
response = orch.ask(Role.SENIOR_DEV, "What is a design pattern?")
print(response.content)
```

### Web App
```bash
# Terminal 1 — Backend
python web.py

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open `http://localhost:3000`. You should see the welcome screen with suggestion cards. Click one, type a requirement, and hit Send to start a pipeline run.
