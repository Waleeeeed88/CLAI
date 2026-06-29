# CLAI Usage Guide

CLAI is a local multi-agent engineering workspace. It can run in a terminal shell,
through a scripting CLI, or through a FastAPI and Next.js web app. All interfaces
share the same orchestrator, role definitions, provider adapters, and tools.

## Table of Contents

1. [Install](#install)
2. [Run CLAI](#run-clai)
3. [Configure Providers](#configure-providers)
4. [Roles](#roles)
5. [Commands](#commands)
6. [Workflows](#workflows)
7. [Stages](#stages)
8. [Tools](#tools)
9. [GitHub MCP](#github-mcp)
10. [Cost Saving Mode](#cost-saving-mode)
11. [Configuration Reference](#configuration-reference)
12. [Architecture](#architecture)
13. [Extending CLAI](#extending-clai)
14. [Troubleshooting](#troubleshooting)

## Install

### Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer for the web UI and GitHub MCP
- API key for at least one configured provider

### Python

```powershell
git clone https://github.com/Waleeeeed88/CLAI.git
cd CLAI

python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS and Linux:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Run CLAI

### Interactive Shell

```bash
python shell.py
```

### CLI

```bash
python cli.py team
python cli.py ask senior_dev "Design a cache layer"
python cli.py workflow feature -r "OAuth login"
```

### Web App

Start the backend:

```bash
python web.py
```

Start the frontend:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

## Configure Providers

Copy the example environment file and fill in only the providers you plan to use:

```powershell
Copy-Item .env.example .env
```

```ini
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...
KIMI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
```

Check configuration from the shell:

```text
clai> config
```

## Roles

| Role | Mentions | Responsibility |
| --- | --- | --- |
| Senior Dev | `@senior`, `@architect`, `@lead` | Architecture, tradeoffs, delivery direction |
| Coder | `@dev`, `@coder`, `@code` | Primary implementation |
| Coder 2 | `@dev2`, `@coder2`, `@gemini` | Secondary implementation and large-context work |
| Coder 3 | `@dev3`, `@coder3` | Additional implementation pass with alternate routing |
| QA | `@qa`, `@test`, `@tester` | Test planning and verification |
| BA | `@ba`, `@analyst`, `@specs` | Requirements and acceptance criteria |
| Reviewer | `@reviewer`, `@review`, `@cr` | Review and release confidence |

Use `@team` for a structured roundtable.

## Commands

### Shell

| Command | Description |
| --- | --- |
| `help` | Show available commands |
| `team` | Show role roster and model routing |
| `config` | Show API key and tool status |
| `tools [role]` | Show registered tools |
| `workflow <name>` | Run a workflow |
| `stage <name>` | Run a structured discussion stage |
| `kickoff [name]` | Run the full project pipeline |
| `workspace` | Show workspace root |
| `files [path]` | List workspace files |
| `tree [path]` | Show workspace tree |
| `readfile <path>` | Print a workspace file |
| `clear` | Clear terminal context |
| `exit` | Quit |

### File I/O

Save output:

```text
clai> @dev write a FastAPI hello world > hello.py
```

Load input:

```text
clai> @qa review this < hello.py
```

Paths are relative to the configured workspace root, which defaults to `./workspace`.

## Workflows

Workflows chain roles in sequence and pass prior outputs to dependent steps.

| Workflow | Route | Use case |
| --- | --- | --- |
| `feature` | BA -> QA -> Senior Dev -> Coder -> Coder 2 -> Coder 3 | Full feature development |
| `full_feature` | BA -> Senior Dev -> Coder -> Coder 2 -> Coder 3 -> QA -> Reviewer | End-to-end delivery |
| `bugfix` | QA -> Senior Dev -> Coder | Bug analysis and fix |
| `review` | Reviewer -> Senior Dev | Review with refactoring guidance |
| `architecture` | BA -> Senior Dev -> QA | System design |
| `project_setup` | BA -> Senior Dev -> Coder | New project setup |
| `pr_review` | Reviewer | Pull request review |
| `test_and_verify` | QA | Test writing and execution |

Example:

```text
clai> workflow feature
> Requirement: Add passwordless login with email codes
```

## Stages

Stages are guided team conversations with short turn budgets and a synthesis step.

| Stage | Use case |
| --- | --- |
| `planning_discussion` | Align scope, risks, and next actions |
| `architecture_alignment` | Validate architecture decisions |
| `implementation_breakdown` | Convert a plan into tasks |
| `verification_hardening` | Define tests, edge cases, and release gates |
| `release_handoff` | Prepare release checklist and rollback plan |

Example:

```text
clai> stage architecture_alignment
> Describe the system or feature to architect: realtime notifications
```

## Tools

CLAI gives agents structured tools through provider-native function calling.

| Tool set | Description |
| --- | --- |
| Filesystem | Read, write, append, delete, search, and inspect workspace files |
| Scratchpad | Shared working memory for agent coordination |
| Enterprise Data | Catalog, semantic search, knowledge facts, memory, governance, audit, cost tools |
| QA Tools | Excel test plans and `pytest` execution |
| GitHub MCP | Repository, branch, issue, pull request, and review operations |

Tool access can be toggled in the web Settings drawer and persisted in `config/overrides.json`.

## GitHub MCP

Enable GitHub tools with a personal access token:

```ini
GITHUB_TOKEN=ghp_...
GITHUB_MCP_ENABLED=true
GITHUB_MCP_COMMAND=npx
GITHUB_MCP_ARGS=-y @modelcontextprotocol/server-github
```

The GitHub MCP server starts lazily when GitHub tools are first needed.

## Cost Saving Mode

The web Settings drawer includes a Cost Saving section.

| Control | Effect |
| --- | --- |
| Token Saver | Enables native cost-saving behavior |
| Max Output | Caps each role's max output tokens |
| History Messages | Keeps only the newest chat history messages before the model call |

When enabled, CLAI adds:

- Ponytail-style minimal implementation rules: reuse existing code, prefer stdlib and native platform features, use installed dependencies, then write the smallest correct implementation.
- Caveman-style brevity rules: remove filler while preserving code, commands, paths, API names, errors, safety, validation, and explicit user requirements.
- LangGraph-inspired trim-before-call behavior for chat history.

The same settings can be controlled by environment variables:

```ini
COST_SAVER_ENABLED=true
COST_SAVER_MAX_OUTPUT_TOKENS=1600
COST_SAVER_HISTORY_MESSAGES=8
COST_SAVER_HISTORY_CHAR_LIMIT=2000
```

## Configuration Reference

Common settings:

```ini
DEFAULT_MAX_TOKENS=8192
DEFAULT_TEMPERATURE=0.7
VERBOSE=true
LOG_LEVEL=DEBUG
MCP_ENABLED=true
MCP_WORKSPACE_ROOT=./workspace
ENTERPRISE_DATA_ENABLED=true
SCRATCHPAD_ENABLED=true
QA_TOOLS_ENABLED=true
```

Role routing:

```ini
ROLE_PROVIDER_OVERRIDES={"qa":"openai","coder":"openrouter"}
ROLE_MODEL_OVERRIDES={"coder":"~anthropic/claude-sonnet-latest"}
```

Valid providers:

```text
anthropic, openai, google, kimi, openrouter
```

## Architecture

```text
shell.py / cli.py / web.py
          |
          v
core.orchestrator.Orchestrator
          |
          +-- agents.factory.AgentFactory
          +-- roles/*.py
          +-- core.tool_registry.ToolRegistry
          +-- core.filesystem_tools
          +-- core.enterprise_data
          +-- core.mcp_bridge
```

Key patterns:

- `BaseAgent` owns the provider-independent chat and tool loop.
- Provider adapters translate messages and tools for Anthropic, OpenAI, Gemini, Kimi, and OpenRouter.
- `Orchestrator` builds role-scoped tool registries and runs workflows/stages.
- The web runner wraps orchestration events into SSE for the Next.js UI.

## Extending CLAI

### Add a Role

1. Create a role module in `roles/`.
2. Register a `RoleConfig`.
3. Add the enum value and default provider/model in `agents/factory.py`.
4. Add model settings in `config/settings.py`.
5. Add shell aliases in `shell/constants.py`.
6. Add frontend metadata if the role should appear in the UI.

### Add a Workflow

Register a list of `WorkflowStep` objects in `core/orchestrator.py`.

### Add a Provider

1. Create a `BaseAgent` subclass in `agents/`.
2. Implement `_initialize_client()` and `_send_request()`.
3. Register it in `Provider` and `PROVIDER_AGENTS`.
4. Add settings and docs for API keys and model routing.

## Troubleshooting

### API key not found

- Confirm `.env` is in the repository root.
- Run `clai> config`.
- Make sure the selected role provider has a matching API key.

### Web frontend cannot connect

- Start the backend with `python web.py`.
- Confirm it listens on `http://localhost:8000`.
- Start the frontend from `frontend/` with `npm run dev`.

### Tools are missing

- Run `clai> tools <role>`.
- Confirm the relevant tool toggle is enabled.
- Restart the shell or web backend after config changes.

### GitHub MCP fails

- Confirm Node.js is installed with `node --version`.
- Confirm `GITHUB_TOKEN` and `GITHUB_MCP_ENABLED=true`.
- The MCP package is launched through `npx`, so the first run may take longer.

### Gemini warning

The current Google adapter imports `google.generativeai`, which may emit a deprecation warning. Existing tests allow this warning; migrating to `google.genai` is tracked as provider maintenance work.
