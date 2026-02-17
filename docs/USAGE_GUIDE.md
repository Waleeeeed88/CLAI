# CLAI — Comprehensive Usage Guide

> Your AI development team in the terminal. Architect, code, test, review, and ship — all from one CLI.

---

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [The Team — Who Does What](#the-team--who-does-what)
3. [Getting Started — Your First Commands](#getting-started--your-first-commands)
4. [Shell Commands Reference](#shell-commands-reference)
5. [@Mentions — Talking to Your Team](#mentions--talking-to-your-team)
6. [File I/O — Reading & Writing Files](#file-io--reading--writing-files)
7. [Workflows — Multi-Agent Pipelines](#workflows--multi-agent-pipelines)
8. [Stages — Structured Team Conversations](#stages--structured-team-conversations)
9. [Kickoff — Full Project Pipeline](#kickoff--full-project-pipeline)
10. [Tool System — What Agents Can Do](#tool-system--what-agents-can-do)
11. [GitHub Integration](#github-integration)
12. [Configuration Reference](#configuration-reference)
13. [Architecture Overview](#architecture-overview)
14. [Extending CLAI](#extending-clai)
15. [Troubleshooting](#troubleshooting)

---

## Installation & Setup

### Prerequisites

- Python 3.10+
- API keys from at least one of: [Anthropic](https://console.anthropic.com), [OpenAI](https://platform.openai.com/api-keys), [Google AI Studio](https://aistudio.google.com/apikey)
- (Optional) [Node.js](https://nodejs.org) for GitHub MCP server
- (Optional) A [GitHub Personal Access Token](https://github.com/settings/tokens) for GitHub integration

### Install

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
| `stages` | List all available stages |
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

Stages are **guided discussion formats** where the team talks through a topic in a structured way.

### Running a Stage

```
clai> stage planning_discussion
> Topic: How should we handle user authentication?
```

### Available Stages

| Stage | Purpose |
|-------|---------|
| **planning_discussion** | Cross-role planning: BA → QA → Senior → Coders | Active |
| **architecture_alignment** | Validate architecture decisions and tradeoffs |
| **implementation_breakdown** | Convert plan into concrete tasks and ownership |
| **verification_hardening** | Consolidate testing and quality gates |
| **release_handoff** | Final release checklist and rollout plan |

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

### Live Output

During execution, you see:
- **Phase headers** with icons and descriptions
- **Step completions** with model name and token count
- **Response previews** in bordered panels
- **Phase timings** (e.g., "Phase planning complete (45.2s)")
- **Final delivery summary** in a double-bordered panel

### Offline Mode

If GitHub isn't configured, `kickoff` runs in **offline mode** — everything still works, but without GitHub repo/issues/PRs. Code is written to the workspace only.

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
shell.py                          ← Entry point (imports shell/main.py)
    │
shell/main.py                    ← Interactive UI, @mention parsing, commands
    │
core/orchestrator.py             ← Mediator: ask(), run_workflow(), consult_team_discussion()
    │
agents/factory.py                ← Factory: Role → Provider → Agent creation
    │
agents/{claude,gpt,gemini}_agent.py   ← Provider-specific implementations
    │
agents/base.py                   ← BaseAgent: tool-call loop, message management
    │
roles/*.py                       ← System prompts (persona, capabilities, style)
    │
core/tool_registry.py            ← ToolRegistry: define, convert, execute tools
    │
┌───────────────────┬───────────────────┬─────────────────────────┐
│ core/filesystem_tools.py │ core/mcp_bridge.py  │ core/excel_tools.py     │
│ (read/write files)       │ (GitHub integration) │ (Excel test plans)      │
└───────────────────┴───────────────────┴─────────────────────────┘
```

### Design Patterns

- **Mediator** — `Orchestrator` coordinates all agents; they never interact directly
- **Template Method** — `BaseAgent` defines the chat/tool loop; providers implement `_send_request()`
- **Factory** — `AgentFactory.create_by_role()` maps roles to providers and models
- **Strategy** — Each provider's `_send_request()` handles API differences

### Request Flow

```
1. You type:  @senior design a cache layer
2. Shell:     Parse @mention → Role.SENIOR_DEV
3. Shell:     Call orchestrator.ask(Role.SENIOR_DEV, "design a cache layer")
4. Orch:      Get/create agent for role (factory if first use, cached after)
5. Orch:      Build tool registry (filesystem + github + excel per role)
6. Orch:      Call agent.chat(prompt, tool_registry)
7. Agent:     Convert messages to provider format
8. Agent:     Send to API with tool definitions
9. API:       Returns text or tool_use request
10. Agent:    If tool_use → execute tool → send result back → loop (max 25x)
11. Agent:    Return final AgentResponse
12. Shell:    Display in rich panel with model/token info
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

4. **Add model to factory** — update `_resolve_model()` in `agents/factory.py`:

```python
model_map = {
    # ... existing ...
    Role.DEVOPS: settings.devops_model,
}
```

5. **Import the role** — `roles/__init__.py`:

```python
from . import devops
```

6. **Add mention alias** — `shell/constants.py`:

```python
MENTION_ALIASES["@devops"] = Role.DEVOPS
MENTION_ALIASES["@ops"] = Role.DEVOPS
```

7. **Add to tools** — `core/orchestrator.py`:

```python
_FS_TOOL_ROLES = {... Role.DEVOPS}
```

### Adding a New Workflow

```python
# In core/orchestrator.py → _register_default_workflows()
self.register_workflow("deploy", [
    WorkflowStep(Role.SENIOR_DEV, "Plan deployment for:\n\n{requirement}"),
    WorkflowStep(Role.DEVOPS, "Create CI/CD pipeline.", depends_on=["step_0_senior_dev"]),
    WorkflowStep(Role.QA, "Create smoke tests.", depends_on=["step_1_devops"]),
])
```

Then add `"deploy"` to `WORKFLOWS` in `shell/constants.py`.

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

Gemini requires strict user/model message alternation. If you see errors about message ordering, it's likely a bug in message conversion — file an issue.

### Tool calls not working

- Run `clai> tools <role>` to verify tools are registered
- Ensure `MCP_ENABLED=true` in `.env`
- Check logs for tool execution errors (set `LOG_LEVEL=DEBUG`)

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

### CLI vs Shell

| Feature | CLI (`cli.py`) | Shell (`shell.py`) |
|---------|----------------|-------------------|
| Single questions | ✓ | ✓ |
| @mentions | ✗ | ✓ |
| File I/O (`>` / `<`) | `--file` flag | ✓ |
| Workflows | 4 built-in | All 8 |
| Stages | ✓ | ✓ |
| Kickoff | ✗ | ✓ |
| Rich UI | Basic | Full panels + progress |
| Scripting | ✓ (piping) | ✗ |
