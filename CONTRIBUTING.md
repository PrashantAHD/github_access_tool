# Contributing

## Branching

- Create a feature branch from `main`.
- Keep changes focused and small.
- Use descriptive commit messages.

## Local Validation

Run before opening a pull request:

```powershell
python -m py_compile .\github_access_tool.py
```

## Pull Request Expectations

- Describe the problem and solution.
- Include sample terminal output for CLI behavior changes.
- Link related ticket/work item if available.
- Ensure CI checks pass.

## Security

- Do not commit tokens, secrets, or credentials.
- Use environment variables for local auth (`GITHUB_TOKEN`, `GITHUB_ORG`).
