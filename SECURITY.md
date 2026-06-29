# Security Policy

## Reporting a Vulnerability

Please do not open a public issue for a suspected vulnerability.

Send a private report to the project maintainer with:

- Affected component or file
- Reproduction steps
- Expected impact
- Any relevant logs with secrets removed

If you do not have a private contact path, open a GitHub issue that says you need to report a security issue privately, without including exploit details.

## Secret Handling

CLAI uses local `.env` files for provider credentials. Do not commit:

- API keys
- GitHub tokens
- Provider request/response logs containing private prompts
- Workspace outputs containing confidential code or data

The repository ignores `.env`, `workspace/`, `.clai_history`, and `.pi/` by default.

## Supported Scope

Security reports are most useful when they involve:

- Unsafe filesystem access
- Secret leakage
- Tool permission bypasses
- Prompt cache or memory exposure
- GitHub MCP misuse
- Web API or SSE vulnerabilities
