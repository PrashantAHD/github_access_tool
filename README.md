# github_access_tool

Single-file Python terminal tool for automating GitHub organization access operations.

This tool helps reduce manual admin work by handling common GitHub tasks in one interactive flow:

- Add or remove users from teams
- Grant or remove team access to repositories
- Check team permissions on repositories
- Grant Artifactory GitHub Actions secrets access to repositories
- Enable Copilot Cloud Agent access for repositories

Designed for quick bulk operations with confirmation prompts, clear per-repo results, and consistent terminal-first usage.

Requirements: Python 3.8+ (no third-party packages required).

## Getting Started

### Step 1: Install Git (if not already installed)

Open PowerShell and run:

```powershell
winget install --id Git.Git -e --source winget
```

Once complete, close PowerShell and open a new one to apply changes.

Verify installation:

```powershell
git --version
```

### Step 2: Install Python (if not already installed)

Open PowerShell and run:

```powershell
winget install --id Python.Python.3.12 -e --source winget
```

Close PowerShell and open a new one.

Verify installation:

```powershell
python --version
```

If `python` is not recognized, try:

```powershell
py --version
```

### Step 3: Clone the Repository

Navigate to your desired folder and clone:

```powershell
cd C:\Users\YourUsername
git clone https://github.com/PrashantAHD/github_access_tool.git
cd .\github_access_tool
```

### Step 4: Set Up GitHub Authentication

#### Option A: Set environment variables (per session)

```powershell
$env:GITHUB_TOKEN="your_github_personal_access_token"
$env:GITHUB_ORG="your-org"
```

To create a GitHub Personal Access Token (PAT):
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `admin:org` and `repo`
4. Copy the generated token and paste into the command above

#### Option B: Prompt for token at runtime (no env vars)

Simply run the tool; it will securely prompt for your token:

```powershell
python .\github_access_tool.py
```

### Step 5: Run the Tool

From the repo folder:

```powershell
python .\github_access_tool.py
```

Or with environment variables pre-set:

```powershell
$env:GITHUB_TOKEN="your_token"; $env:GITHUB_ORG="your-org"; python .\github_access_tool.py
```

Select an option (1-8) from the menu and follow the interactive prompts.

## Repository Input

Accept both formats when entering repositories:
- **One per line** (press ENTER twice to finish):
```
> repo1
> repo2
> 
```
- **Comma-separated** on single line:
```
> repo1, repo2, repo3
```
- **Space-separated** on single line:
```
> repo1 repo2 repo3
```

Also supports full GitHub URLs and org/repo format automatically.

## Available Actions

1. Add User to Team
2. Remove User from Team
3. Add Team Access to Repositories
4. Remove Team Access from Repositories
5. Check Repository Permissions to a Team
6. Grant Artifactory Actions Secrets to Repositories
7. Enable Copilot Cloud Agent on Repositories
8. Exit

## How It Works

The tool follows a modular execution flow:

### Execution Flow

```
1. Start Tool
   ↓
2. Read GitHub Token
   (from GITHUB_TOKEN env var or prompt)
   ↓
3. Read Organization Name
   (from GITHUB_ORG env var or prompt)
   ↓
4. Display Menu (Actions 1-8)
   ↓
5. User Selects Action
   ↓
6. Dispatcher Function
   - Prompts for required inputs (users, teams, repos)
   - Parses repository names
   - Calls GitHubClient methods for each repo
   - Collects success/failure results
   ↓
7. Display Results
   (action-specific completion message)
   ↓
8. Exit
```

### Token Scope Requirements

The GitHub Personal Access Token must have these scopes:
- `admin:org` — Manage organization teams and members
- `repo` — Access repositories, manage secrets

### Authentication

Token is sourced from (in order):
1. `GITHUB_TOKEN` environment variable
2. Runtime prompt (masked input via `getpass`)

The token is never stored or logged; it's used only for the current session.
