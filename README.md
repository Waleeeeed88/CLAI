# CLAI — Command Line AI Team

> Your AI dev team in the terminal. Claude architects, GPT analyses, Gemini codes — and they all use real tools.

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   You ──► kickoff my-api                                            │
│                │                                                    │
│   📋 Planning ──► 🏗️ Setup ──► ⚡ Build ──► 🧪 QA ──► 🔍 Review    │
│                                                                     │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│   │  Claude   │  │  GPT     │  │  Gemini  │  │  Claude   │          │
│   │  Opus 4.5 │  │  5.2     │  │  3 Pro   │  │  Sonnet   │          │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│   Senior Dev     BA            Coder 2       Reviewer               │
│                                                                     │
│   📦 Result: GitHub repo + branches + PRs + tests + delivery doc    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Clone & install
git clone <repo-url> CLAI && cd CLAI
python -m venv venv && .\venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt

# 2. Add API keys
cp .env.example .env   # Then edit with your keys

# 3. Launch
python shell.py
```

---

## The Team

| Role | @Mention | Model | Specialty |
|------|----------|-------|-----------|
| **Senior Dev** | `@senior` | Claude Opus 4.8 | Architecture, system design, tech leadership |
| **Coder** | `@dev` | Claude Sonnet 4.6 | Primary implementation, features, bug fixes |
| **Coder 2** | `@dev2` | Gemini 3.1 Pro | Large-context secondary coder |
| **QA** | `@qa` | Gemini 3.5 Flash | Testing, bug hunting, Excel test plans |
| **BA** | `@ba` | GPT 5.5 | Requirements, user stories, GitHub issues |
| **Reviewer** | `@reviewer` | Claude Sonnet 4.6 | Code review, PR feedback |

---

## What Can It Do?

### Talk to Individual Agents

```
clai> @senior design a REST API for user auth
clai> @dev implement that in Python > api.py
clai> @qa review this < api.py
```

### Run Multi-Agent Workflows

```
clai> workflow feature
> Requirement: User authentication with OAuth

   BA ──► QA ──► Senior Dev ──► Coder ──► Coder 2
   stories  tests  architecture  implement  refine
```

**8 workflows:** `feature` · `review` · `bugfix` · `architecture` · `project_setup` · `full_feature` · `pr_review` · `test_and_verify`

### Kick Off a Full Project

```
clai> kickoff my-auth-api
> Describe the project: REST API with JWT auth, roles, and OAuth

📋 Planning    → BA creates user stories + GitHub issues
🏗️ Setup       → Senior Dev architects, scaffolds repo + branches
⚡ Build       → Two coders implement on feature branches, create PRs
🧪 Quality     → QA writes tests, Excel test plan, runs pytest
🔍 Review      → Reviewer reviews PRs on GitHub
📦 Delivery    → Senior Dev writes DELIVERY.md + localhost instructions
```

### Team Roundtable Discussions

```
clai> @team Should we use REST or GraphQL?
```

Each agent responds in turn, reacting to previous answers.

---

## Tool System

Agents don't just generate text — they **use real tools**:

| Category | Tools | Who Gets Them |
|----------|-------|---------------|
| **Filesystem** | `read_file`, `write_file`, `get_tree`, `grep`, ... | All agents |
| **Enterprise Data** | `data_source_search`, `semantic_search`, `knowledge_graph_query`, `agent_memory_search`, ... | All agents |
| **Governance & Cost** | `governance_check`, `audit_log_tail`, `cost_estimate`, `model_route_recommend`, `prompt_cache_lookup` | All agents |
| **GitHub** | `create_repository`, `create_branch`, `push_files`, `create_pull_request`, ... | Role-scoped |
| **QA** | `create_test_plan_excel`, `run_tests` | QA |

All tool usage is **native function calling** — not prompt-based hacks. Each provider uses its own format (Anthropic `tool_use`, OpenAI `tool_calls`, Gemini `function_call`).

```
clai> tools              # See all tools
clai> tools senior_dev   # See Senior Dev's tools
clai> github             # Check GitHub connection
```

### Enterprise Data Foundation

CLAI includes a local, durable enterprise data layer under `workspace/.clai_data`:

- Metadata catalog for databases, APIs, documents, tools, and enterprise systems
- Knowledge graph facts for business entities and relationships
- Lightweight semantic retrieval for grounding agents before they answer
- Cross-session agent memory and workflow checkpoints
- Governance checks, audit log, prompt cache, and model cost recommendations

This is dependency-free for local use. The tool interfaces are shaped so the backing store can later move to Neo4j, pgvector, OpenSearch, Milvus, Weaviate, Pinecone, or MCP-backed enterprise tools.

---

## GitHub Integration

When configured, agents interact with GitHub directly:

- **BA** creates repositories and issues for user stories
- **Senior Dev** creates branches and manages repo structure
- **Coders** push code to feature branches and create PRs
- **QA** files issues for bugs found during testing
- **Reviewer** posts reviews on pull requests

```ini
# .env
GITHUB_TOKEN=ghp_your_token
GITHUB_MCP_ENABLED=true
```

Uses the official [Model Context Protocol](https://modelcontextprotocol.io/) GitHub server.

---

## File I/O

```
@dev write a CLI tool > mycli.py      # Save output to file
@qa look at this < broken.py          # Load file as input
@senior review < src/                 # Load entire folder
save output.md                        # Save last response
```

All file paths are relative to `workspace/` (sandboxed).

---

## Configuration

### Provider Keys

```ini
# .env - add only the providers you route roles to
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...
KIMI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
```

### Optional

```ini
# GitHub
GITHUB_TOKEN=ghp_...
GITHUB_MCP_ENABLED=true

# Model overrides
SENIOR_DEV_MODEL=claude-opus-4-8
CODER_MODEL=claude-sonnet-4-6

# Enterprise data foundation
ENTERPRISE_DATA_ENABLED=true
ENTERPRISE_DATA_DIR=.clai_data

# OpenRouter metadata
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_APP_NAME=CLAI

# Per-role provider override (JSON)
ROLE_PROVIDER_OVERRIDES={"coder": "openrouter"}
ROLE_MODEL_OVERRIDES={"coder": "~anthropic/claude-sonnet-latest"}
```

Get keys from: [Anthropic](https://console.anthropic.com) · [OpenAI](https://platform.openai.com/api-keys) · [Google](https://aistudio.google.com/apikey) · [OpenRouter](https://openrouter.ai/keys) · [GitHub](https://github.com/settings/tokens)

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `@<role> <prompt>` | Talk to a specific agent |
| `@team <prompt>` | Roundtable discussion |
| `kickoff [name]` | Full project pipeline (6 phases) |
| `workflow <name>` | Run a named workflow |
| `stage <name>` | Run a structured discussion |
| `tools [role]` | Inspect agent tools |
| `github` | GitHub MCP status |
| `team` | Show team roster |
| `config` | Check API key status |
| `workspace` | Show workspace path |
| `files` / `tree` | Browse workspace files |
| `save <file>` | Save last response |
| `help` | Full command list |

---

## Project Structure

```
CLAI/
├── shell.py                  # Entry point
├── cli.py                    # CLI (non-interactive)
├── shell/
│   ├── main.py               # Shell logic, commands, @mention parsing
│   ├── constants.py          # Commands, aliases, workflow lists
│   └── completer.py          # Tab completion
├── agents/
│   ├── base.py               # BaseAgent — tool-call loop, message mgmt
│   ├── claude_agent.py       # Anthropic provider
│   ├── gpt_agent.py          # OpenAI provider
│   ├── gemini_agent.py       # Google provider
│   └── factory.py            # Role → Provider → Agent creation
├── roles/                    # System prompts per role
│   ├── senior_dev.py
│   ├── coder.py / coder_2.py
│   ├── qa.py / ba.py / reviewer.py
│   └── base.py              # RoleConfig dataclass
├── core/
│   ├── orchestrator.py       # Mediator — ask(), run_workflow(), roundtable
│   ├── pipeline.py           # ProjectPipeline — 6-phase kickoff
│   ├── tool_registry.py      # Tool definitions + provider format converters
│   ├── filesystem_tools.py   # Sandboxed file operations
│   ├── mcp_client.py         # MCP SDK client wrapper
│   ├── mcp_bridge.py         # MCP → ToolRegistry bridge (role-scoped)
│   ├── excel_tools.py        # Excel test plan generation
│   ├── test_runner.py        # pytest execution
│   ├── enterprise_data.py    # Catalog, graph, retrieval, memory, governance, cost tools
│   ├── workflows.py          # WorkflowStep/Result dataclasses
│   └── filesystem.py         # Low-level file ops
├── config/
│   └── settings.py           # Pydantic Settings, .env loading
├── workspace/                # Sandboxed agent file area
├── docs/
│   └── USAGE_GUIDE.md        # Comprehensive usage documentation
└── .env                      # Your API keys (gitignored)
```

---

## Documentation

- **[Usage Guide](docs/USAGE_GUIDE.md)** — Complete reference: all commands, workflows, pipeline, tools, configuration, extension guide
- **[Onboarding](onboarding.md)** — Developer onboarding: codebase walkthrough, how things connect

---

## License

MIT — do whatever you want with it.
