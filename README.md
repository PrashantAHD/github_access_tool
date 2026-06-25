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
$env:GITHUB_ORG="csx-technology"
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
$env:GITHUB_TOKEN="your_token"; $env:GITHUB_ORG="csx-technology"; python .\github_access_tool.py
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

The tool uses a modular architecture with a single entry point and reusable components:

### Main Components

**GitHubClient Class**
- Wraps the GitHub REST API v2022-11-28
- Handles all API communication with Bearer token authentication
- Uses Python's built-in `urllib` for HTTPS requests (no external dependencies)
- 30-second timeout on all requests
- Key methods:
  - `add_team_repo()` / `remove_team_repo()` — Manage team-to-repo access
  - `add_user_to_team()` / `remove_user_from_team()` — Manage team membership
  - `check_team_repo()` — Verify team permissions
  - `add_org_secret_repo()` — Grant Artifactory secrets access
  - `enable_copilot_on_repo()` — Enable Copilot Cloud Agent
  - `get_repo_id()` — Resolve repo name to GitHub ID

**Input Processing**
- `parse_repo_name()` — Converts URLs (https/ssh), org/repo format, or bare names to `owner/repo`
- `read_repositories()` — Accepts repositories in any format (one-per-line, comma-separated, space-separated)

**Action Dispatchers** (8 functions)
- `action_add_user_to_team()` — Prompts for user and team, adds membership
- `action_remove_user_from_team()` — Removes user from team
- `action_add_team_access()` — Grants team access to repositories
- `action_remove_team_access()` — Revokes team access from repositories
- `action_check_permissions()` — Displays team access level per repository
- `action_grant_secrets()` — Grants Artifactory Actions secrets to repositories
- `action_enable_copilot()` — Enables Copilot Cloud Agent on repositories
- Each function tracks per-repo results and displays context-specific completion messages

### Execution Flow

```
1. Start Tool
   ↓
2. Read GitHub Token
   (from GITHUB_TOKEN env var or prompt)
   ↓
3. Read Organization Name
   (from GITHUB_ORG env var or prompt, default: csx-technology)
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
