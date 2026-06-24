# github_access_tool

Single-file Python terminal tool for automating GitHub team/repository access from VS Code terminal.

Requirements: Python 3.8+ (no third-party packages required).

## Run

1. Set environment variables (PowerShell):

```powershell
$env:GITHUB_TOKEN="<your_github_token>"
$env:GITHUB_ORG="csx-technology"
```

2. Start the tool:

```powershell
python github_access_tool.py
```

If `GITHUB_TOKEN` is not set, the tool will securely prompt for it at runtime.

## Available Actions

1. Add Team Access to Repositories
2. Remove Team Access from Repositories
3. Add User to Team
4. Remove User from Team
5. Check Repository Permissions
6. Exit
