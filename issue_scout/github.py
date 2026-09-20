"""Minimal GitHub REST API client for IssueScout."""

import os
import sys
from typing import Any

import requests


API_BASE = "https://api.github.com"


def _headers() -> dict[str, str]:
    """Build request headers. Uses GITHUB_TOKEN if available."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(path: str, params: dict[str, Any] | None = None) -> requests.Response:
    """GET a GitHub API path. Raises for HTTP errors."""
    url = f"{API_BASE}{path}"
    response = requests.get(url, headers=_headers(), params=params, timeout=30)
    response.raise_for_status()
    return response


def list_issues(owner: str, repo: str, state: str = "all") -> list[dict[str, Any]]:
    """Fetch all issues for a repo, paginated. Excludes pull requests.

    The /issues endpoint returns both issues and PRs. We drop PRs here.
    """
    results: list[dict[str, Any]] = []
    page = 1
    while True:
        response = _get(
            f"/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": 100, "page": page},
        )
        batch = response.json()
        if not batch:
            break
        for item in batch:
            if "pull_request" in item:
                continue  # it's a PR, not an issue
            results.append(item)
        if len(batch) < 100:
            break
        page += 1
    return results


def list_pulls(owner: str, repo: str, state: str = "closed") -> list[dict[str, Any]]:
    """Fetch all pull requests for a repo, paginated."""
    results: list[dict[str, Any]] = []
    page = 1
    while True:
        response = _get(
            f"/repos/{owner}/{repo}/pulls",
            params={"state": state, "per_page": 100, "page": page},
        )
        batch = response.json()
        if not batch:
            break
        results.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return results


def issue_timeline(owner: str, repo: str, number: int) -> list[dict[str, Any]]:
    """Fetch timeline events for a single issue."""
    response = _get(f"/repos/{owner}/{repo}/issues/{number}/timeline")
    return response.json()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m issue_scout.github <owner> <repo>")
        sys.exit(1)

    owner, repo = sys.argv[1], sys.argv[2]
    issues = list_issues(owner, repo)
    pulls = list_pulls(owner, repo)
    print(f"issues: {len(issues)}")
    print(f"pulls:  {len(pulls)}")
    if issues:
        sample = issues[0]
        print(f"sample issue: #{sample['number']} {sample['title'][:60]}")