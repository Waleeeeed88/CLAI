# CLAI

<p align="center">
  <strong>A configurable multi-agent AI engineering team for your terminal and browser.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-3776AB.svg">
  <img alt="FastAPI" src="https://img.shields.io/badge/api-FastAPI-009688.svg">
  <img alt="Next.js" src="https://img.shields.io/badge/ui-Next.js-000000.svg">
  <img alt="Agents" src="https://img.shields.io/badge/agents-configurable-7C3AED.svg">
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> |
  <a href="#features">Features</a> |
  <a href="docs/USAGE_GUIDE.md">Docs</a> |
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

<p align="center">
  <img alt="CLAI terminal demo" src="docs/assets/clai-terminal.gif" width="900">
</p>

CLAI turns a product request into a coordinated engineering workflow. A senior
architect, business analyst, coders, QA, and reviewer can plan, implement, test,
review, and document work while using real tools against your local workspace.

## Features

- Multi-agent delivery workflows for planning, implementation, QA, review, and handoff.
- Configurable model teams: `cheap`, `optimal`, and `expensive` presets.
- Provider routing across Anthropic, OpenAI, Google Gemini, Kimi, and OpenRouter.
- Structured tool calls for filesystem access, scratchpad memory, QA tools, and GitHub MCP.
- Native cost-saving mode with Ponytail-style minimal implementation rules, Caveman-style terse replies, output caps, and trimmed chat history.
- Local enterprise data layer for catalog search, semantic retrieval, knowledge graph facts, audit logs, memory, prompt cache, and cost estimates.
- Terminal shell, Click CLI, FastAPI backend, and Next.js browser UI.

## Workflow

<p align="center">
  <img alt="CLAI workflow" src="docs/assets/clai-workflow.gif" width="900">
</p>

```text
You describe the goal
        |
        v
BA -> Senior Dev -> Coder -> QA -> Reviewer
        |
        v
Issues, files, tests, PR notes, delivery docs
```

## Quick Start

```powershell
git clone https://github.com/Waleeeeed88/CLAI.git
cd CLAI

python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env
# Edit .env with the provider keys you want to use.

python shell.py
```

For the web UI:

```powershell
python web.py
cd frontend
npm install
npm run dev
```

Then open `http://localhost:3000`.

## Agent Team

| Role | Mention | Default responsibility |
| --- | --- | --- |
| Senior Dev | `@senior` | Architecture, tradeoffs, delivery direction |
| Coder | `@dev` | Primary implementation |
| Coder 2 | `@dev2` | Secondary implementation and large-context coding |
| Coder 3 | `@dev3` | Extra coding pass with alternate provider routing |
| QA | `@qa` | Test strategy, test plans, verification |
| BA | `@ba` | Requirements, user stories, issue shaping |
| Reviewer | `@reviewer` | Code review and release confidence |

## Model Teams

CLAI ships with three complete routing presets:

| Preset | Use it for |
| --- | --- |
| Cheap Team | Low-cost triage, drafts, and routine iterations |
| Optimal Team | Balanced day-to-day product work |
| Expensive Team | Architecture, high-risk changes, and final review |

You can override each role manually from `.env`, `config/overrides.json`, or the web Settings drawer.

```ini
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...
KIMI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...

ROLE_PROVIDER_OVERRIDES={"coder": "openrouter"}
ROLE_MODEL_OVERRIDES={"coder": "~anthropic/claude-sonnet-latest"}
```

## Tooling

Agents use provider-native function calling instead of prompt-only simulations.

| Tool set | What it enables |
| --- | --- |
| Filesystem | Read, write, search, and inspect workspace files |
| Scratchpad | Cross-step working memory |
| Enterprise Data | Catalog, graph, semantic search, memory, governance, audit, cost controls |
| QA Tools | Excel test plans and test runner access |
| GitHub MCP | Repository, branch, issue, pull request, and review workflows |

Tool access can be toggled from configuration so a cheap drafting run does not need the same capabilities as a full delivery run.

## Cost Saving

The Settings drawer includes a Cost Saving section. Enabling Token Saver:

- Adds Ponytail-style rules that prefer existing code, stdlib, native platform features, installed dependencies, and the smallest correct implementation.
- Adds Caveman-style brevity that removes filler while preserving exact code, commands, paths, API names, errors, and safety guidance.
- Caps output tokens per role.
- Keeps only the newest chat history messages before each model call.

## Common Commands

```text
@senior design a REST API for user auth
@dev implement that in Python > auth_api.py
@qa review this < auth_api.py

workflow feature
kickoff my-auth-api
@team should this be REST or GraphQL?

tools
config
team
workspace
```

## Project Layout

```text
CLAI/
  agents/      Provider adapters and agent factory
  config/      Settings, model routing, team presets
  core/        Orchestrator, pipeline, tools, enterprise data layer
  frontend/    Next.js UI
  roles/       Role prompts and runtime defaults
  shell/       Interactive terminal shell
  web/         FastAPI routes and schemas
  workspace/   Local agent workspace, ignored by git
```

## Documentation

- [Usage Guide](docs/USAGE_GUIDE.md) - commands, workflows, tools, config, and extension points.
- [Contributing](CONTRIBUTING.md) - local setup, verification, and pull request expectations.
- [Security](SECURITY.md) - supported reporting path for vulnerabilities.
- [Changelog](CHANGELOG.md) - notable changes by release.
- [Onboarding](onboarding.md) - developer walkthrough for the codebase.

## Development

```powershell
python -m pytest

cd frontend
npm run build
```

## Contributing

Issues and pull requests are welcome. Keep changes focused, include verification, and prefer existing patterns over new abstractions.

## License

MIT. See [LICENSE](LICENSE).
