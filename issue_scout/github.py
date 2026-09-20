"""Minimal GitHub REST API client for IssueScout."""

import os
import re
import sys
from typing import Any

import requests


API_BASE = "https://api.github.com"

CLOSE_KEYWORDS = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)\b",
    re.IGNORECASE,
)


def _headers() -> dict[str, str]:
    """Build request headers. Uses GH_TOKEN or GITHUB_TOKEN if available."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(path: str, params: dict[str, Any] | None = None) -> requests.Response:
    """GET a GitHub API path. Raises for HTTP errors."""
    url = f"{API_BASE}{path}"
    response = requests.get(url, headers=_headers(), params=params, timeout=30)
    if response.status_code == 403 and "rate limit" in response.text.lower():
        raise RuntimeError(
            "GitHub API rate limit exceeded. Set GH_TOKEN for higher limits."
        )
    response.raise_for_status()
    return response


def list_issues(owner: str, repo: str, state: str = "all") -> list[dict[str, Any]]:
    """Fetch all issues for a repo, paginated. Excludes pull requests."""
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
                continue
            results.append(item)
        if len(batch) < 100:
            break
        page += 1
    return results


def get_issue(owner: str, repo: str, number: int) -> dict[str, Any]:
    """Fetch a single issue by number."""
    response = _get(f"/repos/{owner}/{repo}/issues/{number}")
    return response.json()


def search_merged_prs_linked_to_issues(
    owner: str, repo: str, limit: int = 30
) -> list[dict[str, Any]]:
    """Find merged PRs that are linked to issues.

    Uses GitHub search with linked:issue, which matches PRs whose body
    or linked issues reference an issue via close keywords.
    """
    results: list[dict[str, Any]] = []
    page = 1
    while len(results) < limit:
        per_page = min(100, limit - len(results))
        response = _get(
            "/search/issues",
            params={
                "q": f"repo:{owner}/{repo} is:pr is:merged linked:issue",
                "per_page": per_page,
                "page": page,
                "sort": "updated",
                "order": "desc",
            },
        )
        batch = response.json().get("items", [])
        if not batch:
            break
        results.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return results[:limit]


def extract_issue_numbers(text: str) -> list[int]:
    """Extract issue numbers from close keywords in a PR body."""
    return [int(n) for n in CLOSE_KEYWORDS.findall(text or "")]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m issue_scout.github <owner> <repo>")
        sys.exit(1)

    owner, repo = sys.argv[1], sys.argv[2]
    prs = search_merged_prs_linked_to_issues(owner, repo, limit=5)
    print(f"merged PRs linked to issues: {len(prs)}")
    for pr in prs:
        issues = extract_issue_numbers(pr.get("body") or "")
        print(f"  PR #{pr['number']}: {pr['title'][:50]} -> issues {issues}")