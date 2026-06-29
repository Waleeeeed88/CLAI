# Contributing to CLAI

Thanks for taking the time to improve CLAI. This project is still moving quickly, so the best contributions are focused, verified, and easy to review.

## Development Setup

```powershell
git clone https://github.com/Waleeeeed88/CLAI.git
cd CLAI

python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

cd frontend
npm install
```

Copy `.env.example` to `.env` and add only the provider keys needed for the area you are testing.

## Verification

Run these before opening a pull request:

```powershell
python -m pytest

cd frontend
npm run build
```

Add focused tests when behavior changes. If a change cannot be covered by an automated test, include the exact manual verification steps in the pull request.

## Pull Request Guidelines

- Keep each PR scoped to one clear change.
- Prefer existing project patterns over new abstractions.
- Avoid committing generated output, local workspaces, API keys, model logs, or `.pi/`.
- Update docs when behavior, configuration, commands, or setup steps change.
- Include screenshots or short recordings for visible UI changes.

## Commit Style

Use concise imperative commits:

```text
Add native cost saver mode
Fix workflow stage validation
Document GitHub MCP setup
```

## Reporting Issues

When filing an issue, include:

- CLAI version or commit SHA
- Operating system
- Python and Node versions
- Command or workflow that failed
- Relevant logs with secrets removed
