#!/usr/bin/env python3
"""Interactive GitHub access automation tool.

Run:
    python github_access_tool.py

Environment variables:
    GITHUB_TOKEN   (required; can also be entered interactively)
    GITHUB_ORG     (optional; defaults to 'csx-technology')
"""

from __future__ import annotations

import getpass
import json
import os
import re
import sys
from typing import List, Optional, Tuple
from urllib import error, request


BASE_API = "https://api.github.com"
DEFAULT_ORG = "csx-technology"
ARTIFACTORY_SECRET_NAMES = ("ARTIFACTORY_USERNAME", "ARTIFACTORY_PASSWORD")
ALLOWED_PERMISSIONS = {"read", "write", "maintain", "admin", "triage", "pull", "push"}
PERMISSION_NORMALIZATION = {
    "read": "pull",
    "write": "push",
    "pull": "pull",
    "push": "push",
    "triage": "triage",
    "maintain": "maintain",
    "admin": "admin",
}


def header(title: str) -> None:
    print("=" * 33 + f" {title} " + "=" * 33)


def section(title: str) -> None:
    print("-" * 33 + f" {title} " + "-" * 33)


def ask_non_empty(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Input cannot be empty. Please try again.")


def ask_yes_no(prompt: str) -> bool:
    while True:
        value = input(prompt).strip().lower()
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please enter y or n.")


def ask_permission() -> str:
    while True:
        value = input("Permission (read/write/maintain/admin): ").strip().lower()
        if value not in ALLOWED_PERMISSIONS:
            print("Invalid permission. Use one of: read, write, triage, maintain, admin")
            continue
        return PERMISSION_NORMALIZATION[value]


def parse_repo_name(line: str, default_org: str) -> Optional[str]:
    line = line.strip()
    if not line:
        return None

    # Accept full URL: https://github.com/org/repo or git@github.com:org/repo.git
    https_match = re.match(r"^https?://github\.com/([^/]+)/([^/]+)/?$", line)
    ssh_match = re.match(r"^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", line)

    if https_match:
        org, repo = https_match.group(1), https_match.group(2)
        if org.lower() != default_org.lower():
            print(f"Skipping URL in different org: {line}")
            return None
        return repo

    if ssh_match:
        org, repo = ssh_match.group(1), ssh_match.group(2)
        if org.lower() != default_org.lower():
            print(f"Skipping URL in different org: {line}")
            return None
        return repo

    # Accept org/repo format.
    if "/" in line:
        org, repo = line.split("/", 1)
        if org.lower() != default_org.lower():
            print(f"Skipping repository in different org: {line}")
            return None
        return repo.rstrip(".git")

    # Treat bare value as repo name.
    return line


def read_repositories(org: str) -> List[str]:
    print("Enter repositories or GitHub URLs (one per line)")
    print("Press ENTER twice when done:")

    repos: List[str] = []
    seen = set()
    empty_count = 0

    while True:
        line = input("> ")
        if not line.strip():
            empty_count += 1
            if empty_count >= 2:
                break
            continue
        empty_count = 0

        repo = parse_repo_name(line, org)
        if not repo:
            continue
        if repo in seen:
            continue

        seen.add(repo)
        repos.append(repo)

    return repos


class GitHubClient:
    def __init__(self, token: str, org: str) -> None:
        self.org = org
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "github-access-tool",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs) -> Tuple[bool, str, Optional[dict]]:
        url = f"{BASE_API}{path}"
        payload = kwargs.get("json")
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = request.Request(url=url, data=data, method=method, headers=self.headers)
        try:
            with request.urlopen(req, timeout=30) as response:
                body = response.read().decode("utf-8", errors="replace")
                if body.strip():
                    try:
                        return True, "", json.loads(body)
                    except ValueError:
                        return True, "", None
                return True, "", None
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            message = "Request failed"
            if body.strip():
                try:
                    err = json.loads(body)
                    message = err.get("message", message)
                except ValueError:
                    message = body.strip()
            return False, f"{exc.code}: {message}", None
        except error.URLError as exc:
            return False, f"Network error: {exc}", None

    def team_exists(self, team_slug: str) -> Tuple[bool, str]:
        ok, error, _ = self._request("GET", f"/orgs/{self.org}/teams/{team_slug}")
        return ok, error

    def add_team_repo(self, team_slug: str, repo: str, permission: str) -> Tuple[bool, str]:
        body = {"permission": permission}
        return self._request(
            "PUT",
            f"/orgs/{self.org}/teams/{team_slug}/repos/{self.org}/{repo}",
            json=body,
        )[:2]

    def remove_team_repo(self, team_slug: str, repo: str) -> Tuple[bool, str]:
        return self._request(
            "DELETE",
            f"/orgs/{self.org}/teams/{team_slug}/repos/{self.org}/{repo}",
        )[:2]

    def add_user_to_team(self, team_slug: str, username: str) -> Tuple[bool, str]:
        body = {"role": "member"}
        return self._request(
            "PUT",
            f"/orgs/{self.org}/teams/{team_slug}/memberships/{username}",
            json=body,
        )[:2]

    def remove_user_from_team(self, team_slug: str, username: str) -> Tuple[bool, str]:
        return self._request(
            "DELETE",
            f"/orgs/{self.org}/teams/{team_slug}/memberships/{username}",
        )[:2]

    def check_team_repo(self, team_slug: str, repo: str) -> Tuple[bool, str]:
        ok, error, data = self._request(
            "GET",
            f"/orgs/{self.org}/teams/{team_slug}/repos/{self.org}/{repo}",
        )
        if not ok:
            return False, error

        if not data:
            return True, "Access exists (permission details unavailable)."

        perms = data.get("permissions", {})
        active = [name for name, enabled in perms.items() if enabled]
        return True, f"Access exists. Permissions: {', '.join(active) if active else 'unknown'}"

    def get_repo_id(self, repo: str) -> Tuple[bool, str, Optional[int]]:
        ok, error, data = self._request("GET", f"/repos/{self.org}/{repo}")
        if not ok:
            return False, error, None
        if not data or "id" not in data:
            return False, "Repository ID not found.", None
        return True, "", data["id"]

    def add_org_secret_repo(self, secret_name: str, repo_id: int) -> Tuple[bool, str]:
        return self._request(
            "PUT",
            f"/orgs/{self.org}/actions/secrets/{secret_name}/repositories/{repo_id}",
        )[:2]

    def enable_copilot_on_repo(self, repo_id: int) -> Tuple[bool, str]:
        return self._request(
            "PUT",
            f"/orgs/{self.org}/copilot/selected_repositories/{repo_id}",
        )[:2]


MENU = (
    "1. Add User to Team",
    "2. Remove User from Team",
    "3. Add Team Access to Repositories",
    "4. Remove Team Access from Repositories",
    "5. Check Repository Permissions to a Team",
    "6. Grant Artifactory Actions Secrets to Repositories",
    "7. Enable Copilot Cloud Agent on Repositories",
    "8. Exit",
)


def print_menu() -> None:
    header("GitHub Access Automation")
    for item in MENU:
        print(item)


def print_repo_summary(team: str, permission: Optional[str], repos: List[str]) -> None:
    section("Summary")
    print(f"Team: {team}")
    if permission:
        friendly = "read" if permission == "pull" else "write" if permission == "push" else permission
        print(f"Permission: {friendly}")
    print("Repositories:")
    for repo in repos:
        print(f"- {repo}")


def normalize_team_slug(team_name: str) -> str:
    return team_name.strip().lower().replace(" ", "-")


def action_add_team_access(client: GitHubClient) -> None:
    team_name = ask_non_empty("Enter Team Name: ")
    team_slug = normalize_team_slug(team_name)

    permission = ask_permission()
    repos = read_repositories(client.org)

    if not repos:
        print("No repositories entered. Nothing to do.")
        return

    print_repo_summary(team_name, permission, repos)
    if not ask_yes_no("Proceed? (y/n): "):
        print("Operation canceled.")
        return

    print("Granting access...")
    success_count = 0
    for repo in repos:
        ok, error = client.add_team_repo(team_slug, repo, permission)
        if ok:
            print(f"\u2713 {repo}")
            success_count += 1
        else:
            print(f"x {repo} ({error})")

    if success_count == len(repos):
        print("Completed Successfully")
        friendly = "read" if permission == "pull" else "write" if permission == "push" else permission
        print(
            f"Team {team_name} was granted {friendly} access to {success_count} "
            f"repositor{'y' if success_count == 1 else 'ies'} successfully."
        )
    else:
        print(f"Completed with issues ({success_count}/{len(repos)} succeeded)")
        failed_count = len(repos) - success_count
        print(
            f"Team {team_name} was granted access to {success_count} repositories, "
            f"and {failed_count} failed."
        )


def action_remove_team_access(client: GitHubClient) -> None:
    team_name = ask_non_empty("Enter Team Name: ")
    team_slug = normalize_team_slug(team_name)
    repos = read_repositories(client.org)

    if not repos:
        print("No repositories entered. Nothing to do.")
        return

    print_repo_summary(team_name, None, repos)
    if not ask_yes_no("Proceed? (y/n): "):
        print("Operation canceled.")
        return

    print("Removing access...")
    success_count = 0
    for repo in repos:
        ok, error = client.remove_team_repo(team_slug, repo)
        if ok:
            print(f"\u2713 {repo}")
            success_count += 1
        else:
            print(f"x {repo} ({error})")

    if success_count == len(repos):
        print("Completed Successfully")
        print(
            f"Team {team_name} access was removed from {success_count} "
            f"repositor{'y' if success_count == 1 else 'ies'} successfully."
        )
    else:
        print(f"Completed with issues ({success_count}/{len(repos)} succeeded)")
        failed_count = len(repos) - success_count
        print(
            f"Team {team_name} access was removed from {success_count} repositories, "
            f"and {failed_count} failed."
        )


def action_add_user_to_team(client: GitHubClient) -> None:
    team_name = ask_non_empty("Enter Team Name: ")
    team_slug = normalize_team_slug(team_name)
    username = ask_non_empty("Enter GitHub Username: ")

    section("Summary")
    print(f"Team: {team_name}")
    print(f"User: {username}")

    if not ask_yes_no("Proceed? (y/n): "):
        print("Operation canceled.")
        return

    ok, error = client.add_user_to_team(team_slug, username)
    if ok:
        print("Completed Successfully")
        print(f"User {username} was successfully added to team {team_name}.")
    else:
        print(f"Failed: {error}")
        print(f"User {username} could not be added to team {team_name}.")


def action_remove_user_from_team(client: GitHubClient) -> None:
    team_name = ask_non_empty("Enter Team Name: ")
    team_slug = normalize_team_slug(team_name)
    username = ask_non_empty("Enter GitHub Username: ")

    section("Summary")
    print(f"Team: {team_name}")
    print(f"User: {username}")

    if not ask_yes_no("Proceed? (y/n): "):
        print("Operation canceled.")
        return

    ok, error = client.remove_user_from_team(team_slug, username)
    if ok:
        print("Completed Successfully")
        print(f"User {username} was successfully removed from team {team_name}.")
    else:
        print(f"Failed: {error}")
        print(f"User {username} could not be removed from team {team_name}.")


def action_check_repo_permissions(client: GitHubClient) -> None:
    team_name = ask_non_empty("Enter Team Name: ")
    team_slug = normalize_team_slug(team_name)
    repos = read_repositories(client.org)

    if not repos:
        print("No repositories entered. Nothing to do.")
        return

    section("Permission Check")
    print(f"Team: {team_name}")

    success_count = 0
    for repo in repos:
        ok, msg = client.check_team_repo(team_slug, repo)
        symbol = "\u2713" if ok else "x"
        print(f"{symbol} {repo}: {msg}")
        if ok:
            success_count += 1

    if success_count == len(repos):
        print(f"Permission check completed successfully for all {len(repos)} repositories.")
    else:
        failed_count = len(repos) - success_count
        print(
            f"Permission check completed with issues: {success_count} succeeded, "
            f"{failed_count} failed."
        )


def action_grant_artifactory_secrets(client: GitHubClient) -> None:
    repos = read_repositories(client.org)

    if not repos:
        print("No repositories entered. Nothing to do.")
        return

    section("Summary")
    print("Action: Grant Artifactory Actions secrets to repositories")
    print("Secrets:")
    for secret_name in ARTIFACTORY_SECRET_NAMES:
        print(f"- {secret_name}")
    print("Repositories:")
    for repo in repos:
        print(f"- {repo}")

    if not ask_yes_no("Proceed? (y/n): "):
        print("Operation canceled.")
        return

    print("Granting secrets access...")
    success_count = 0
    for repo in repos:
        ok, error_message, repo_id = client.get_repo_id(repo)
        if not ok or repo_id is None:
            print(f"x {repo} ({error_message})")
            continue

        repo_ok = True
        for secret_name in ARTIFACTORY_SECRET_NAMES:
            ok, error_message = client.add_org_secret_repo(secret_name, repo_id)
            if not ok:
                print(f"x {repo} ({secret_name}: {error_message})")
                repo_ok = False
                break

        if repo_ok:
            print(f"\u2713 {repo}")
            success_count += 1

    if success_count == len(repos):
        print("Completed Successfully")
        print(
            f"Artifactory GitHub Actions secrets were successfully granted to "
            f"{success_count} repositor{'y' if success_count == 1 else 'ies'}."
        )
    else:
        failed_count = len(repos) - success_count
        print(f"Completed with issues ({success_count}/{len(repos)} succeeded)")
        print(
            f"Artifactory GitHub Actions secrets were granted to {success_count} repositories, "
            f"and {failed_count} failed."
        )


def action_enable_copilot_on_repos(client: GitHubClient) -> None:
    repos = read_repositories(client.org)

    if not repos:
        print("No repositories entered. Nothing to do.")
        return

    section("Summary")
    print("Action: Enable Copilot Cloud Agent on repositories")
    print("Repositories:")
    for repo in repos:
        print(f"- {repo}")

    if not ask_yes_no("Proceed? (y/n): "):
        print("Operation canceled.")
        return

    print("Enabling Copilot Cloud Agent...")
    success_count = 0
    for repo in repos:
        ok, error_message, repo_id = client.get_repo_id(repo)
        if not ok or repo_id is None:
            print(f"x {repo} ({error_message})")
            continue

        ok, error_message = client.enable_copilot_on_repo(repo_id)
        if ok:
            print(f"\u2713 {repo}")
            success_count += 1
        else:
            print(f"x {repo} ({error_message})")

    if success_count == len(repos):
        print("Completed Successfully")
        print(
            f"Copilot Cloud Agent was successfully enabled on {success_count} "
            f"repositor{'y' if success_count == 1 else 'ies'}."
        )
    else:
        failed_count = len(repos) - success_count
        print(f"Completed with issues ({success_count}/{len(repos)} succeeded)")
        print(
            f"Copilot Cloud Agent was enabled on {success_count} repositories, "
            f"and {failed_count} failed."
        )


def choose_option() -> str:
    while True:
        value = input("Select Option: ").strip()
        if value in {"1", "2", "3", "4", "5", "6", "7", "8"}:
            return value
        print("Please choose a valid option (1-8).")


def get_runtime_config() -> Tuple[str, str]:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    org = os.getenv("GITHUB_ORG", DEFAULT_ORG).strip() or DEFAULT_ORG

    if not token:
        print("GITHUB_TOKEN not found in environment.")
        token = getpass.getpass("Enter GitHub token: ").strip()

    if not token:
        raise ValueError("GitHub token is required.")

    return token, org


def main() -> int:
    header("GitHub Access Automation Tool")

    try:
        token, org = get_runtime_config()
    except ValueError as exc:
        print(str(exc))
        return 1

    client = GitHubClient(token, org)
    print()
    print_menu()
    option = choose_option()

    if option == "1":
        action_add_user_to_team(client)
    elif option == "2":
        action_remove_user_from_team(client)
    elif option == "3":
        action_add_team_access(client)
    elif option == "4":
        action_remove_team_access(client)
    elif option == "5":
        action_check_repo_permissions(client)
    elif option == "6":
        action_grant_artifactory_secrets(client)
    elif option == "7":
        action_enable_copilot_on_repos(client)
    else:
        print("Goodbye.")
        return 0

    print("Goodbye.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        raise SystemExit(130)
