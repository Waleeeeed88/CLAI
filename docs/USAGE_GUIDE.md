# CLAI — Comprehensive Usage Guide

> Your AI development team in the terminal — or the browser. Architect, code, test, review, and ship.

---

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Choosing Your Interface — CLI vs Web](#choosing-your-interface--cli-vs-web)
3. [The Team — Who Does What](#the-team--who-does-what)
4. [Getting Started — Your First Commands](#getting-started--your-first-commands)
5. [Shell Commands Reference](#shell-commands-reference)
6. [@Mentions — Talking to Your Team](#mentions--talking-to-your-team)
7. [File I/O — Reading & Writing Files](#file-io--reading--writing-files)
8. [Workflows — Multi-Agent Pipelines](#workflows--multi-agent-pipelines)
9. [Stages — Structured Team Conversations](#stages--structured-team-conversations)
10. [Kickoff — Full Project Pipeline](#kickoff--full-project-pipeline)
11. [Web App Interface](#web-app-interface)
12. [Tool System — What Agents Can Do](#tool-system--what-agents-can-do)
13. [GitHub Integration](#github-integration)
14. [Configuration Reference](#configuration-reference)
15. [Architecture Overview](#architecture-overview)
16. [Extending CLAI](#extending-clai)
17. [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Prerequisites

- Python 3.10+
- API keys from at least one of: [Anthropic](https://console.anthropic.com), [OpenAI](https://platform.openai.com/api-keys), [Google AI Studio](https://aistudio.google.com/apikey)
- (Optional) [Node.js 18+](https://nodejs.org) — required for the web app frontend and GitHub MCP server
- (Optional) A [GitHub Personal Access Token](https://github.com/settings/tokens) for GitHub integration

### Install Python dependencies

```bash
git clone <your-repo-url> CLAI
cd CLAI
python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### Install frontend dependencies (web app only)

```bash
cd frontend
npm install
cd ..
```

### Configure API Keys

Create a `.env` file in the project root:

```ini
# Required — one per provider you want to use
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...

# Optional — GitHub integration
GITHUB_TOKEN=ghp_...
GITHUB_MCP_ENABLED=true

# Optional — Override default models
# SENIOR_DEV_MODEL=claude-opus-4-5-20251101
# CODER_MODEL=claude-sonnet-4-5-20250929
```

### Verify Setup

```bash
python shell.py
# In the shell:
clai> config
# Should show ✓ for each configured provider
```

---

## Choosing Your Interface — CLI vs Web

CLAI offers two fully equivalent interfaces that share the same backend:

| | CLI (`shell.py`) | Web App (`web.py` + `frontend/`) |
|---|---|---|
| **Launch** | `python shell.py` | `python web.py` + `npm run dev` |
| **Interface** | Terminal with Rich panels | Browser chat UI |
| **Streaming** | Synchronous (shows on completion) | Real-time SSE streaming |
| **File panel** | `files` / `tree` commands | Live animated file tree |
| **Workflows** | All 8 | All 8 |
| **Stages** | All 5 | All 5 |
| **Kickoff** | ✓ with GitHub prompts | ✓ |
| **@Mentions** | ✓ | Via stage/workflow selection |
| **Scripting** | `cli.py` for piping | REST API at `localhost:8000` |

Both interfaces access the **same orchestrator, agents, tools, and workspace** — they are two views of the same system.

---

## The Team — Who Does What

CLAI gives you six AI specialists, each powered by the model best suited for their role:

| Role | @Mention | Model | Specialty |
|------|----------|-------|-----------|
| **Senior Dev** | `@senior` `@architect` `@lead` | Claude Opus 4.5 | Architecture, system design, tech decisions, project scaffolding |
| **Coder** | `@dev` `@coder` `@code` | Claude Sonnet 4.5 | Primary implementation, feature development, bug fixes |
| **Coder 2** | `@dev2` `@coder2` `@gemini` | Gemini 3 Pro | Secondary coder, large-context tasks, multi-file work |
| **QA** | `@qa` `@test` `@tester` | Gemini 3 Flash | Testing, bug hunting, edge cases, test plans |
| **Business Analyst** | `@ba` `@analyst` `@specs` | GPT 5.2 | Requirements, user stories, specifications |
| **Reviewer** | `@reviewer` `@review` `@cr` | Claude Sonnet 4.5 | Code review, PR feedback, quality assessment |

### Why Different Models?

- **Claude Opus 4.5** — Best reasoning for architecture decisions
- **Claude Sonnet 4.5** — Fast + accurate for code generation and reviews
- **Gemini 3 Pro** — Massive context window for large codebases
- **Gemini 3 Flash** — Fast + cheap for systematic test generation
- **GPT 5.2** — Strong analytical capabilities for requirements

---

## Getting Started — Your First Commands

### Launch the Shell

```bash
python shell.py
```

You'll see a banner and the `clai>` prompt.

### Ask a Team Member

```
clai> @senior What's the best way to structure a Python REST API?
```

The Senior Dev (Claude Opus) responds with architecture guidance in a rich panel.

### Ask Multiple Members

```
clai> @dev write a FastAPI hello world > hello.py
clai> @qa review this < hello.py
clai> @team What testing framework should we use?
```

`@team` triggers a **roundtable discussion** — each role responds in turn, reacting to what previous roles said.

### Run a Workflow

```
clai> workflow feature
> Requirement: User authentication with JWT tokens
```

This chains BA → QA → Senior Dev → Coder → Coder 2 automatically.

### Kick Off a Full Project

```
clai> kickoff my-auth-api
> Describe the project: Build a REST API for user auth with JWT, OAuth, roles
```

This runs the **6-phase pipeline**: Planning → Setup → Build → Quality → Review → Delivery. If GitHub is configured, it creates a real repo, branches, issues, and PRs.

---

## Shell Commands Reference

### Navigation & Info

| Command | Description |
|---------|-------------|
| `help` | Show all available commands |
| `team` | Display team roster with roles and models |
| `config` | Check API key status and configuration |
| `clear` | Clear the terminal |
| `exit` / `quit` | Exit CLAI |

### Workspace & Files

| Command | Description |
|---------|-------------|
| `workspace` | Show workspace root path |
| `projects` | List projects in the workspace |
| `newproject <name> [python\|node\|basic]` | Create a new project with boilerplate |
| `files [path]` | List files in workspace (or subpath) |
| `tree [path]` | Show directory tree |
| `readfile <path>` | Display file with syntax highlighting |
| `save <filename>` | Save last agent response to a file |

### Agent Interaction

| Command | Description |
|---------|-------------|
| `@<role> <prompt>` | Ask a specific agent (see @Mentions below) |
| `@team <prompt>` | BA-first roundtable with all agents |
| `history` | Show conversation history per agent |

### Multi-Agent Pipelines

| Command | Description |
|---------|-------------|
| `workflow <name>` | Run a named workflow (see Workflows) |
| `workflows` | List all available workflows |
| `stage <name>` | Run a named stage (see Stages) |
| `stages` | List all available stages and their status |
| `kickoff [name]` | Full project pipeline (see Kickoff) |

### Tool Inspection

| Command | Description |
|---------|-------------|
| `tools [role]` | List tools available to an agent (or all agents) |
| `github` | Show GitHub MCP connection status and tools |

---

## @Mentions — Talking to Your Team

### Direct Mentions

Prefix your message with `@role` to talk to a specific agent:

```
clai> @senior design a microservices architecture for e-commerce
clai> @dev implement the user service in Python
clai> @qa find edge cases in the login flow
clai> @ba write user stories for the checkout feature
clai> @reviewer review the auth module
```

### All Aliases

| Alias | Routes to |
|-------|-----------|
| `@senior` `@seniordev` `@architect` `@lead` `@tech` | Senior Dev |
| `@dev` `@coder` `@dev1` `@developer` `@code` | Coder |
| `@dev2` `@coder2` `@gemini` | Coder 2 |
| `@qa` `@test` `@tester` `@quality` `@bug` | QA |
| `@ba` `@analyst` `@specs` `@reqs` | Business Analyst |
| `@reviewer` `@review` `@cr` | Reviewer |
| `@team` `@all` `@devteam` `@everyone` | All (roundtable) |

### Team Roundtable (@team)

When you use `@team`, CLAI runs a **BA-first roundtable discussion**:

1. Each agent responds in order: BA → QA → Senior Dev → Coder → Coder 2
2. Each agent sees what previous agents said
3. Every response uses structured headings: **Position**, **Reply to Team**, **Next Action**
4. Responses are kept short (~170 words) for focused discussion

```
clai> @team Should we use REST or GraphQL for this project?
```

---

## File I/O — Reading & Writing Files

### Save Output to File

Append `> filename` to any command to save the agent's response:

```
clai> @dev write a CLI tool > mycli.py
clai> @senior design auth API > docs/auth-design.md
```

### Load File as Input

Use `< filename` to inject file contents into your prompt:

```
clai> @qa review this code < src/auth.py
clai> @reviewer check this < src/
```

Loading a **directory** (`< src/`) recursively loads all files in it.

### Save Last Response

```
clai> save output.md
```

Saves the most recent agent response to a file.

### File Paths

All file paths are relative to `workspace/` (default: `./workspace/`). This is the sandboxed area where agents read and write files.

---

## Workflows — Multi-Agent Pipelines

Workflows chain multiple agents in sequence. Each agent receives the output of previous agents as context.

### Running a Workflow

```
clai> workflow feature
> Requirement: <describe the feature>
```

Or via CLI:

```bash
python cli.py workflow feature -r "User authentication with OAuth"
```

### Available Workflows

| Workflow | Agents | Use Case |
|----------|--------|----------|
| **feature** | BA → QA → Senior → Coder → Coder 2 | Full feature development |
| **review** | Reviewer → Senior | Code review with improvement suggestions |
| **bugfix** | QA → Senior → Coder | Bug analysis and fix |
| **architecture** | BA → Senior → QA | System design with quality review |
| **project_setup** | BA → Senior → Coder | New project with GitHub repo + issues |
| **full_feature** | BA → Senior → Coder → QA → Reviewer | End-to-end with tests and review |
| **pr_review** | Reviewer | Pull request review (uses GitHub tools) |
| **test_and_verify** | QA | Write and run tests for existing code |

### How Workflows Work

```
workflow feature -r "OAuth login"

┌─── Step 0: BA (GPT 5.2) ─────────────────────────────┐
│  "Analyze this feature and create user stories"        │
│  → Output: user stories with acceptance criteria        │
└───────────────────┬────────────────────────────────────┘
                    │ BA's output
┌─── Step 1: QA (Gemini Flash) ─────────────────────────┐
│  "Create test plan and edge-case strategy"              │
│  → Output: test cases, Excel test plan                  │
└───────────────────┬────────────────────────────────────┘
                    │ BA's + QA's output
┌─── Step 2: Senior Dev (Claude Opus) ──────────────────┐
│  "Design architecture and delivery approach"            │
│  → Output: technical design, component breakdown        │
└───────────────────┬────────────────────────────────────┘
                    │ All previous outputs
┌─── Step 3: Coder (Claude Sonnet) ─────────────────────┐
│  "Implement the feature. Write actual files."           │
│  → Output: source code written to workspace             │
└───────────────────┬────────────────────────────────────┘
                    │ Coder's output
┌─── Step 4: Coder 2 (Gemini Pro) ─────────────────────┐
│  "Refine, add complementary code, integration checks"   │
│  → Output: additional source files, improvements        │
└────────────────────────────────────────────────────────┘
```

Each step receives outputs from the steps listed in its `depends_on` array.

---

## Stages — Structured Team Conversations

Stages are **guided discussion formats** where the full team talks through a topic in a structured, turn-based way. Every stage follows the same pattern:

1. Each agent takes a turn in a defined order
2. Every agent sees all prior turns before responding
3. Responses are structured with required headings (~180 words each)
4. A synthesis agent closes with a compact summary

All 5 stages are fully active.

### Running a Stage

```
clai> stage planning_discussion
> What should the team plan/discuss? Build a real-time notification system
```

### Available Stages

| Stage | Turn Order | Synthesis | Prompt |
|-------|-----------|-----------|--------|
| **planning_discussion** | BA → QA → Senior → Coder → Coder 2 | Senior Dev | *What should the team plan/discuss?* |
| **architecture_alignment** | Senior → Coder → Coder 2 → QA → Reviewer | Senior Dev | *Describe the system or feature to architect* |
| **implementation_breakdown** | BA → Senior → Coder → Coder 2 → QA | BA | *What should the team break down into tasks?* |
| **verification_hardening** | QA → Senior → Coder → Coder 2 → Reviewer | QA | *What feature or system needs verification planning?* |
| **release_handoff** | Senior → Reviewer → QA → BA → Coder | Senior Dev | *Describe the release scope (feature, version, or date)* |

### Stage Headings

Each stage enforces specific headings per turn so responses stay structured and scannable:

| Stage | Turn headings | Synthesis headings |
|-------|-------------|-------------------|
| **planning_discussion** | Position · Feedback to Team · Concrete Output | Agreed Plan · QA Gate Criteria · Engineering Sequencing · Open Risks |
| **architecture_alignment** | Architecture Position · Feedback to Prior Roles · Concrete Decision | Agreed Architecture · Key Technical Decisions · Risk Register · Definition of Done |
| **implementation_breakdown** | Task Breakdown · Sequencing/Dependencies · Ownership | Sprint 1 Deliverables · Task Ownership Matrix · Dependencies & Blockers · Milestone Criteria |
| **verification_hardening** | Testing Strategy · Risk Coverage · Quality Gate | Test Coverage Plan · Quality Gates · Edge Cases & Risk Areas · Release Readiness Criteria |
| **release_handoff** | Release Position · Checklist Items · Sign-off Criteria | Go / No-Go Decision · Release Checklist · Rollback Plan · Post-Release Monitoring |

### Example: architecture_alignment

```
clai> stage architecture_alignment
> Describe the system or feature to architect: Real-time notification service

── SENIOR_DEV ──────────────────────────────────────────
Architecture Position: WebSocket hub with Redis pub/sub…
Feedback to Prior Roles: No prior discussion yet.
Concrete Decision: Use FastAPI + Redis Streams + WebSocket.

── CODER ────────────────────────────────────────────────
Architecture Position: Agree on WebSocket, flag connection…
Feedback to Prior Roles: Senior's Redis choice is sound…
Concrete Decision: Will own WebSocket connection manager.

… (QA, Coder 2, Reviewer turns) …

── SYNTHESIS (SENIOR_DEV) ──────────────────────────────
1) Agreed Architecture: FastAPI WebSocket + Redis Streams…
2) Key Technical Decisions: Redis for fan-out, JWT auth…
3) Risk Register: Connection scaling at 10k+…
4) Definition of Done: Load test passing at 5k concurrent…
```

---

## Kickoff — Full Project Pipeline

The `kickoff` command is the **flagship experience** — it orchestrates the entire AI team through 6 phases to deliver a complete project from a single description.

### Running Kickoff

```
clai> kickoff my-project
> Project name: my-project
> Describe the project: Build a task management API with auth, teams, and real-time notifications
> Create GitHub repo? yes
> GitHub owner: your-username
```

### The 6 Phases

```
┌─────────────────────────────────────────────────────────────────────┐
│                     KICKOFF PIPELINE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📋 Phase 1: PLANNING                                               │
│     └─ BA creates user stories + GitHub issues                      │
│     └─ Team roundtable (QA, Senior, Coders discuss)                 │
│                         │                                           │
│  🏗️ Phase 2: SETUP                                                  │
│     └─ Senior Dev designs architecture                              │
│     └─ Creates repo structure, README, configs                      │
│     └─ Establishes branching strategy (main → develop → feature/*)  │
│                         │                                           │
│  ⚡ Phase 3: BUILD                                                  │
│     └─ Coder implements core features on feature branch             │
│     └─ Coder 2 implements secondary modules on separate branch      │
│     └─ Both create PRs to develop                                   │
│                         │                                           │
│  🧪 Phase 4: QUALITY                                                │
│     └─ QA reads implementation, writes test files                   │
│     └─ Creates Excel test plan (.xlsx)                              │
│     └─ Runs pytest, files GitHub issues for failures                │
│                         │                                           │
│  🔍 Phase 5: REVIEW                                                 │
│     └─ Reviewer examines code + PRs                                 │
│     └─ Posts review comments on GitHub PRs                          │
│     └─ Grades code quality (A-F)                                    │
│                         │                                           │
│  📦 Phase 6: DELIVERY                                               │
│     └─ Senior Dev writes DELIVERY.md                                │
│     └─ Localhost setup instructions                                 │
│     └─ Summary of repo, branches, PRs, tests                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### What Gets Created

| Artifact | Location | Description |
|----------|----------|-------------|
| GitHub Repository | `github.com/<owner>/<project>` | Real repo with README, .gitignore |
| GitHub Issues | On the repo | One per user story, with labels + acceptance criteria |
| Feature Branches | `feature/core-implementation`, etc. | Code pushed by each coder |
| Pull Requests | On the repo | PRs from feature branches to `develop` |
| Source Code | `workspace/<project>/` | All implementation files |
| Test Files | `workspace/<project>/tests/` | pytest test suites |
| Excel Test Plan | `workspace/<project>/` | `.xlsx` with all test cases |
| Architecture Docs | `workspace/<project>/architecture.md` | System design document |
| Delivery Summary | `workspace/<project>/DELIVERY.md` | Run instructions + project status |
| PR Reviews | On GitHub PRs | Reviewer comments + approval/changes |

### Offline Mode

If GitHub isn't configured, `kickoff` runs in **offline mode** — everything still works, but without GitHub repo/issues/PRs. Code is written to the workspace only.

---

## Web App Interface

The web app provides a browser-based alternative to the CLI with real-time streaming and a live file panel.

### Starting the Web App

```bash
# Terminal 1 — Python backend
python web.py
# → FastAPI server at http://localhost:8000
# → API docs at http://localhost:8000/docs

# Terminal 2 — Next.js frontend
cd frontend
npm run dev
# → UI at http://localhost:3000
```

### Layout

```
┌──────────────┬──────────────────────────────┬──────────────┐
│   Sidebar    │         Chat window          │  Files panel │
│              │                              │              │
│  ▾ Stages    │  ● Senior Dev                │  auth.py  ✓  │
│    planning  │    thinking...               │  models.py ● │
│    arch. ●   │                              │  tests.py ✓  │
│    impl. ●   │  ● Dev                       │              │
│    verif. ●  │    Here's the implementation │              │
│    release ● │    ┌──────────────────┐      │              │
│              │    │ write_file ✓  ▼  │      │              │
│  ▾ Workflows │    └──────────────────┘      │              │
│    feature   │                              │              │
│    review    │  ● QA                        │              │
│    ...       │    Test coverage plan…       │              │
│              │                              │              │
│  ▾ Pipeline  │                              │              │
│    Kickoff   │                              │              │
│              │                              │              │
│  Topic:      │                              │              │
│  [________]  │                              │              │
│  [ Run  ]    │                              │              │
└──────────────┴──────────────────────────────┴──────────────┘
```

### Sidebar

- **Stages** section lists all 5 stages (green dot = active, gray = placeholder). Click a stage to select it.
- **Workflows** section lists all 8 workflows.
- **Pipeline** section exposes the kickoff pipeline with a project name field.
- Type your topic/requirement in the text area and press **Run**.

### Chat Window

- Each agent response appears as a card with an animated badge (colored per role).
- While an agent is thinking, three bouncing dots are shown.
- Tool calls appear as expandable rows — click to see arguments and result.
- Markdown is rendered (headings, code blocks, lists).
- For the pipeline, phase progress bars appear at the top as each phase completes.

### Live Files Panel (right)

The **Files** panel shows every file written by any agent in real time:

| State | Indicator | Meaning |
|-------|-----------|---------|
| Writing | Blue card + spinning icon | Agent is currently writing |
| Done | Green card + ✓ | File written successfully |
| Error | Red card + ✗ | Write failed |

Each entry shows: filename, directory path, which agent wrote it, and whether it was `created` (`write_file`) or `updated` (`append_file`). Files animate in from the right as they appear.

### REST API

The backend exposes a simple SSE-based API:

```bash
# Start a stage run, get back a session_id
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"type":"stage","stage":"planning_discussion","context":{"requirement":"Build a notification service"}}'
# → {"session_id": "abc-123"}

# Stream events for that session
curl -N http://localhost:8000/api/chat/abc-123/stream
# → data: {"type":"agent_start","agent":"ba",...}
# → data: {"type":"tool_call","agent":"ba","tool":"write_file",...}
# → data: {"type":"agent_done","agent":"ba","content":"...","tokens":412}
# → data: {"type":"done"}

# List all workflows and stages
curl http://localhost:8000/api/workflows
```

### SSE Event Reference

| Event type | Key fields | Meaning |
|------------|-----------|---------|
| `agent_start` | `agent` | Agent begins responding |
| `agent_done` | `agent`, `content`, `tokens`, `model` | Agent response complete |
| `tool_call` | `agent`, `tool`, `args` | Tool execution started |
| `tool_result` | `agent`, `tool`, `preview`, `success` | Tool finished |
| `phase_start` | `phase` | Pipeline phase begins |
| `phase_done` | `phase`, `status`, `duration` | Pipeline phase complete |
| `stage_complete` | `stage`, `status`, `steps`, `duration` | Stage run finished |
| `workflow_complete` | `workflow`, `status`, `steps`, `duration` | Workflow finished |
| `pipeline_complete` | `status` | Full pipeline finished |
| `error` | `message` | An error occurred |
| `done` | — | Stream closed |

---

## Tool System — What Agents Can Do

Agents don't just generate text — they can **use tools** to perform real actions. The tool system supports all three providers (Anthropic, OpenAI, Google) with native function calling.

### Filesystem Tools (All Agents)

Every agent has access to sandboxed workspace tools:

| Tool | Parameters | Description |
|------|-----------|-------------|
| `read_file` | `file_path` | Read a file from workspace |
| `write_file` | `file_path`, `content` | Write/create a file |
| `append_file` | `file_path`, `content` | Append to a file |
| `delete_file` | `file_path` | Delete a file |
| `list_directory` | `dir_path` | List directory contents |
| `create_directory` | `dir_path` | Create directories |
| `get_tree` | `dir_path` | Show directory tree |
| `search_files` | `pattern` | Find files by name glob |
| `grep` | `search_term` | Search within file contents |

### GitHub Tools (Role-Scoped)

When GitHub MCP is enabled, each role gets a curated subset of GitHub tools:

| Role | GitHub Tools |
|------|-------------|
| **Senior Dev** | `create_repository`, `create_branch`, `list_branches`, `push_files`, `create_pull_request`, `list_pull_requests`, `get_pull_request`, `merge_pull_request`, `get_file_contents`, `list_issues`, `search_issues`, `get_issue`, `create_or_update_file` |
| **BA** | `create_repository`, `create_issue`, `list_issues`, `search_issues`, `get_issue`, `update_issue`, `add_issue_comment` |
| **Coder / Coder 2** | `create_branch`, `list_branches`, `create_or_update_file`, `get_file_contents`, `push_files`, `create_pull_request` |
| **QA** | `list_issues`, `search_issues`, `create_issue`, `add_issue_comment`, `get_file_contents` |
| **Reviewer** | `get_pull_request`, `list_pull_requests`, `create_pull_request_review`, `get_pull_request_diff`, `get_pull_request_files`, `list_pull_request_files`, `add_pull_request_review_comment` |

### QA-Specific Tools

| Tool | Description |
|------|-------------|
| `create_test_plan_excel` | Generate a formatted `.xlsx` test plan with test cases, priorities, status |
| `run_tests` | Execute `pytest` and return results |

### Inspecting Tools

```
clai> tools                  # List all tools across all roles
clai> tools senior_dev       # List tools for Senior Dev
clai> tools qa               # List tools for QA
```

### How Tool Calling Works

1. Agent receives your prompt + available tool definitions
2. Agent decides to call a tool (e.g., `write_file(file_path="app.py", content="...")`)
3. CLAI executes the tool and returns the result to the agent
4. Agent may call more tools or produce a final response
5. Loop continues for up to 25 iterations per request

This is **native function calling** — not prompt-based. Each provider uses its own format (Anthropic `tool_use`, OpenAI `tool_calls`, Gemini `function_call`).

---

## GitHub Integration

### Setup

1. Create a [GitHub Personal Access Token](https://github.com/settings/tokens) with `repo` scope
2. Install Node.js (needed for the MCP server)
3. Add to `.env`:

```ini
GITHUB_TOKEN=ghp_your_token_here
GITHUB_MCP_ENABLED=true
```

The GitHub MCP server (`@modelcontextprotocol/server-github`) is started automatically when CLAI launches.

### Check Status

```
clai> github
```

Shows connection status, available tools, and configured token.

### How It Works

CLAI uses the official [Model Context Protocol](https://modelcontextprotocol.io/) to communicate with GitHub:

```
Agent ──► Orchestrator ──► MCP Bridge ──► MCP Client ──► GitHub MCP Server ──► GitHub API
                              │
                     Role-scoped tool filtering
                     (each role sees only their tools)
```

The MCP server runs as a subprocess communicating over stdio. The `MCPClient` wraps the MCP SDK's `ClientSession`, and `MCPBridge` converts MCP tools into CLAI's `ToolRegistry` format with per-role filtering.

---

## Configuration Reference

### .env File — All Options

```ini
# ── API Keys (required) ──────────────────────────
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...

# ── GitHub Integration (optional) ────────────────
GITHUB_TOKEN=ghp_...
GITHUB_MCP_ENABLED=true
GITHUB_MCP_COMMAND=npx                                    # Command to start MCP server
GITHUB_MCP_ARGS=-y @modelcontextprotocol/server-github    # Arguments for MCP server

# ── Model Overrides (optional) ───────────────────
SENIOR_DEV_MODEL=claude-opus-4-5-20251101
CODER_MODEL=claude-sonnet-4-5-20250929
CODER_MODEL_2=gemini-3-pro-preview
QA_MODEL=gemini-3-flash-preview
BA_MODEL=gpt-5.2-2025-12-11
REVIEWER_MODEL=claude-sonnet-4-5-20250929

# ── General Settings ─────────────────────────────
DEFAULT_MAX_TOKENS=8192
DEFAULT_TEMPERATURE=0.7
VERBOSE=true
LOG_LEVEL=DEBUG
MCP_ENABLED=true
MCP_WORKSPACE_ROOT=./workspace

# ── Per-Role Overrides (JSON) ────────────────────
# ROLE_MODEL_OVERRIDES={"senior_dev": "claude-opus-4-5-20251101"}
# ROLE_PROVIDER_OVERRIDES={"qa": "openai"}
```

### Default Models

| Role | Default Model | Provider |
|------|---------------|----------|
| Senior Dev | `claude-opus-4-5-20251101` | Anthropic |
| Coder | `claude-sonnet-4-5-20250929` | Anthropic |
| Coder 2 | `gemini-3-pro-preview` | Google |
| QA | `gemini-3-flash-preview` | Google |
| BA | `gpt-5.2-2025-12-11` | OpenAI |
| Reviewer | `claude-sonnet-4-5-20250929` | Anthropic |

### Role-Provider Overrides

You can change which AI provider handles a role:

```ini
ROLE_PROVIDER_OVERRIDES={"qa": "openai", "ba": "anthropic"}
```

Valid providers: `anthropic`, `openai`, `google`

---

## Architecture Overview

### Component Layers

```
Entry Points
├── shell.py          ← python shell.py  — terminal interface
└── web.py            ← python web.py   — starts FastAPI (port 8000)
    └── frontend/     ← npm run dev      — Next.js UI (port 3000)

                    ┌───────────────────────────────────┐
                    │         Shared Core                │
                    │                                   │
shell/main.py       │  core/orchestrator.py             │
(CLI: Rich panels)  │  core/pipeline.py                 │
                    │  agents/{claude,gpt,gemini}        │
web/routers/        │  agents/base.py                   │
(HTTP: SSE stream)  │  roles/*.py                       │
                    │  core/tool_registry.py             │
                    │  core/filesystem_tools.py          │
                    │  core/mcp_bridge.py                │
                    └───────────────────────────────────┘

web/services/
├── runner.py           ← Runs orchestrator in thread pool, emits SSE events
├── event_bus.py        ← queue.Queue → async SSE generator
├── observable_registry.py  ← Intercepts tool calls → SSE events
└── session_manager.py  ← session_id → EventBus mapping
```

### Design Patterns

- **Mediator** — `Orchestrator` coordinates all agents; they never interact directly
- **Template Method** — `BaseAgent` defines the chat/tool loop; providers implement `_send_request()`
- **Factory** — `AgentFactory.create_by_role()` maps roles to providers and models
- **Strategy** — Each provider's `_send_request()` handles API differences
- **Observer** — `ObservableToolRegistry` fires callbacks on every tool call for SSE streaming

### CLI Request Flow

```
1. You type:  @senior design a cache layer
2. Shell:     Parse @mention → Role.SENIOR_DEV
3. Shell:     orchestrator.ask(Role.SENIOR_DEV, "design a cache layer")
4. Orch:      Get/create agent for role (cached after first use)
5. Orch:      Build tool registry (filesystem + github + excel per role)
6. Agent:     Send to API with tool definitions
7. API:       Returns text or tool_use request
8. Agent:     If tool_use → execute tool → send result → loop (max 25x)
9. Shell:     Display in Rich panel with model/token info
```

### Web Request Flow

```
1. Browser:   POST /api/chat {type:"stage", stage:"planning_discussion", context:{...}}
2. Backend:   Create EventBus + session_id, submit to ThreadPoolExecutor
3. Browser:   GET /api/chat/{session_id}/stream  (EventSource)
4. Thread:    Create Orchestrator, patch _ask_with_limits to emit agent_start/done
5. Thread:    Wrap tool registries with ObservableToolRegistry → emits tool_call/result
6. Thread:    Run stage → events flow through EventBus queue → SSE stream
7. Frontend:  useSSE hook → processEvent() → Zustand store → React re-renders
8. UI:        Agent cards appear, tool calls expand, files animate in on the right
```

---

## Extending CLAI

### Adding a New Role

1. **Create the role file** — `roles/devops.py`:

```python
from .base import RoleConfig, register_role

DEVOPS_PROMPT = """You are a DevOps engineer..."""

DEVOPS_CONFIG = RoleConfig(
    name="DevOps Engineer",
    description="Infrastructure and deployment specialist",
    system_prompt=DEVOPS_PROMPT,
    max_tokens=4096,
    temperature=0.6,
    capabilities=("infrastructure", "deployment", "ci_cd"),
)

register_role("devops", DEVOPS_CONFIG)
```

2. **Register in factory** — `agents/factory.py`:

```python
class Role(Enum):
    # ... existing ...
    DEVOPS = "devops"

ROLE_PROVIDERS[Role.DEVOPS] = Provider.OPENAI
```

3. **Add model** — `config/settings.py`:

```python
devops_model: str = "gpt-5.2-2025-12-11"
```

4. **Add mention alias** — `shell/constants.py`:

```python
MENTION_ALIASES["@devops"] = Role.DEVOPS
MENTION_ALIASES["@ops"] = Role.DEVOPS
```

5. **Import the role** — `roles/__init__.py`:

```python
from . import devops
```

6. **Add to filesystem tools** — `core/orchestrator.py`:

```python
_FS_TOOL_ROLES = {... Role.DEVOPS}
```

### Adding a New Workflow

```python
# In core/orchestrator.py → _register_default_workflows()
self.register_workflow("deploy", [
    WorkflowStep(Role.SENIOR_DEV, "Plan deployment for:\n\n{requirement}"),
    WorkflowStep(Role.CODER, "Create CI/CD pipeline.", depends_on=["step_0_senior_dev"]),
    WorkflowStep(Role.QA, "Create smoke tests.", depends_on=["step_1_coder"]),
])
```

Then add `"deploy"` to `WORKFLOWS` in `shell/constants.py`.

### Adding a New Stage

Follow the pattern of `_run_planning_discussion_stage` in `core/orchestrator.py`:

```python
def _run_my_stage(self, context: Dict[str, str]) -> WorkflowResult:
    topic = context.get("requirement") or context.get("topic") or ""
    turn_plan = [
        (Role.BA, "Your instruction for BA", 700),
        (Role.SENIOR_DEV, "Your instruction for Senior", 750),
    ]
    # ... loop + synthesis + return WorkflowResult
```

Then:
1. Add `elif stage_name == "my_stage": return self._run_my_stage(context)` in `run_stage()`
2. Call `register_stage("my_stage", "Description", status="active")` in `_register_default_stages()`
3. Add an `elif` in `shell/main.py → handle_stage()` to prompt for the topic

### Adding a New AI Provider

1. Create `agents/new_provider_agent.py` extending `BaseAgent`
2. Implement: `_initialize_client()`, `_send_request()`, `_to_*_messages()`
3. Add `Provider.NEW_PROVIDER` enum value
4. Add to `PROVIDER_AGENTS` dict in `agents/factory.py`
5. Add API key field in `config/settings.py`

See `agents/claude_agent.py` for reference.

---

## Troubleshooting

### "API key not found"

Check `clai> config` — make sure your `.env` file is in the CLAI project root and the key names match exactly.

### "GitHub MCP not connected"

1. Ensure Node.js is installed: `node --version`
2. Check `.env` has `GITHUB_MCP_ENABLED=true` and `GITHUB_TOKEN=ghp_...`
3. Run `clai> github` to see detailed status

### Agent returns empty / error

- Check the model name is valid in `config/settings.py`
- Ensure you have API credits with the provider
- Try `VERBOSE=true` in `.env` to see detailed logs

### File operations fail

- File paths are relative to `workspace/` — not the project root
- The workspace directory is auto-created on first use
- Check `clai> workspace` to see the resolved path

### Gemini model errors

Gemini requires strict user/model message alternation. If you see errors about message ordering, it's a message conversion issue — check `agents/gemini_agent.py`.

### Tool calls not working

- Run `clai> tools <role>` to verify tools are registered
- Ensure `MCP_ENABLED=true` in `.env`
- Check logs for tool execution errors (set `LOG_LEVEL=DEBUG`)

### Web app — frontend can't connect to backend

- Ensure the backend is running: `python web.py` (port 8000)
- Check CORS — the backend allows `localhost:3000` by default
- Check browser console for EventSource errors
- Verify `BASE` URL in `frontend/src/lib/api.ts` matches your backend port

### Web app — files don't appear in the panel

- Files only appear when agents call `write_file` or `append_file`
- Not all stages or workflows produce file writes — workflows like `feature` and `full_feature` do; planning stages do not
- Check the browser console for SSE event logs

### Stage shows as "placeholder"

All 5 stages are now active. If a stage still shows as placeholder, it may be a cached import. Restart the shell or web server.

---

## CLI Reference (Non-Interactive)

For scripting or one-off questions, use the CLI directly:

```bash
# Ask a specific agent
python cli.py ask senior_dev "Design a cache layer"
python cli.py ask qa "Review this code" --file src/auth.py

# Run a workflow
python cli.py workflow feature -r "OAuth authentication"
python cli.py workflow bugfix -b "Login returns 500" -c "auth.py code here"

# Show info
python cli.py team
python cli.py workflows
python cli.py config

# Interactive chat with one agent
python cli.py chat senior_dev
```

### CLI vs Shell vs Web

| Feature | CLI (`cli.py`) | Shell (`shell.py`) | Web (`web.py`) |
|---------|----------------|-------------------|----------------|
| Single questions | ✓ | ✓ | Via stage/workflow |
| @mentions | ✗ | ✓ | ✗ |
| File I/O (`>` / `<`) | `--file` flag | ✓ | Files panel |
| Workflows | 4 built-in | All 8 | All 8 |
| Stages | ✓ | All 5 | All 5 |
| Kickoff | ✗ | ✓ | ✓ |
| Real-time streaming | ✗ | ✗ | ✓ (SSE) |
| Live file panel | ✗ | ✗ | ✓ |
| Rich UI | Basic | Full panels | Browser UI |
| Scripting / piping | ✓ | ✗ | REST API |
