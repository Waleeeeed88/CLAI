# CLAI — Command Line AI Team

> Your AI dev team in the terminal. Claude architects, GPT codes, Gemini specs.

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   You ──► @senior design auth API                                   │
│                │                                                    │
│                ▼                                                    │
│           ┌─────────┐    ┌─────────┐    ┌─────────┐                │
│           │ Claude  │───▶│  GPT    │───▶│ Gemini  │                │
│           │ Sonnet  │    │  4o     │    │  2.0    │                │
│           └─────────┘    └─────────┘    └─────────┘                │
│           Senior Dev      Coder          BA                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Add your API keys
cp .env.example .env   # Then edit .env

# 3. Launch the shell
python shell.py
```

---

## The Team

| Role | Model | What They Do |
|------|-------|--------------|
| **@senior** | Claude opus 4.5 | Architecture, complex problems, tech decisions |
| **@dev** | sonnet 4.5, gemini-3-pro | Fast implementation, features, utilities |
| **@qa** | GPT-5.2-high | Bug hunting, test cases, edge cases |
| **@ba** | Gemini 3 pro | Requirements, user stories, specs |
| **@reviewer** | Claude Sonnet | Quick code reviews, style feedback |

---

## How to Talk to Them

### @Mentions (Natural)

```
clai> @senior design a REST API for user auth
clai> @dev implement that in Python > api.py
clai> @qa review this < api.py
clai> @team thoughts on microservices?
```

### File I/O

```
@dev write a CLI tool > mycli.py      # Save output to file
@qa look at this < broken.py          # Load file as input  
@senior review < src/                 # Load entire folder
save output.md                        # Save last response
```

### Workflows (Multi-Agent Pipelines)

```
clai> workflow feature
> Feature requirement: User authentication with OAuth

   BA ──────► Senior Dev ──────► Coder ──────► QA
   specs       architecture      implement     test
```

**Available workflows:**
- `feature` — Full feature dev (BA → Senior → Coder → QA)
- `review` — Code review (Reviewer → Senior)
- `bugfix` — Bug analysis (QA → Senior → Coder)
- `architecture` — System design (BA → Senior → QA)

---

## Project Structure

```
CLAI/
├── shell.py              # Interactive UI (start here)
├── configure.py          # CLI entry point
├── orchestrator.py       # Coordinates multi-agent workflows
│
├── agents/               # AI provider wrappers
│   ├── base.py           # Common interface (Template pattern)
│   ├── claude_agent.py   # Anthropic
│   ├── gpt_agent.py      # OpenAI  
│   ├── gemini_agent.py   # Google
│   └── factory.py        # Creates agents by role
│
├── roles/                # Team member personalities
│   ├── senior_dev.py     # System prompts & config
│   ├── coder.py
│   ├── qa.py
│   ├── ba.py
│   └── reviewer.py
│
├── config/
│   └── settings.py       # API keys & model config
│
└── .env                  # Your API keys (git-ignored)
```

---

## How It Works

```
┌──────────────────────────────────────────────────────────────────┐
│                         FLOW                                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   1. You type: @senior design a cache layer                      │
│                    │                                              │
│   2. Shell parses @mention ──► Role.SENIOR_DEV                   │
│                    │                                              │
│   3. Orchestrator gets/creates agent for that role               │
│                    │                                              │
│   4. AgentFactory ──► ClaudeAgent (with senior_dev prompt)       │
│                    │                                              │
│   5. ClaudeAgent sends to Anthropic API                          │
│                    │                                              │
│   6. Response displayed in rich panel                            │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

### Workflows go deeper:

```
workflow feature -r "OAuth login"

   Step 1: BA (Gemini)
           └─► "Create user stories for OAuth login"
           └─► Output: specs & acceptance criteria
                    │
   Step 2: Senior Dev (Claude)  
           └─► "Design architecture" + [BA's output]
           └─► Output: technical design
                    │
   Step 3: Coder (GPT)
           └─► "Implement" + [BA + Senior outputs]
           └─► Output: working code
                    │
   Step 4: QA (GPT)
           └─► "Test & review" + [Coder's output]
           └─► Output: test cases, issues found
```

---

## Configuration

### Required API Keys

Get them from:
- **Anthropic**: https://console.anthropic.com
- **OpenAI**: https://platform.openai.com/api-keys
- **Google**: https://aistudio.google.com/apikey

### .env File

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...

# Optional: override models
SENIOR_DEV_MODEL=claude-sonnet-4-20250514
CODER_MODEL=gpt-4o
QA_MODEL=gpt-4o
BA_MODEL=gemini-2.0-flash-exp
```

---

## Commands Reference

| In Shell | What It Does |
|----------|--------------|
   
| `team` | Show team status |
| `config` | Check API keys |
| `clear` | Clear screen |
| `exit` | Quit |

---

## Adding Your Own Role

1. Create `roles/devops.py`:
```python
from .base import RoleConfig, register_role

DEVOPS_CONFIG = RoleConfig(
    name="DevOps Engineer",
    description="Infrastructure and deployment",
    system_prompt="You are a DevOps engineer...",
    max_tokens=4096,
    temperature=0.6,
)

register_role("devops", DEVOPS_CONFIG)
```

2. Add to `agents/factory.py`:
```python
class Role(Enum):
    DEVOPS = "devops"

ROLE_PROVIDERS[Role.DEVOPS] = Provider.OPENAI
```

3. Add mention in `shell.py`:
```python
MENTION_ALIASES["@devops"] = Role.DEVOPS
```

---

## License

MIT — do whatever you want with it.
