"""Find issues that were closed by a merged pull request."""

import sys
from typing import Any

from issue_scout.github import (
    extract_issue_numbers,
    get_issue,
    search_merged_prs_linked_to_issues,
)


def filter_issues_with_merged_prs(
    owner: str,
    repo: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Return issues that were closed by a merged PR.

    Two-stage approach:
      1. Search merged PRs that are linked to issues.
      2. Extract the linked issue number from each PR body.
      3. Fetch the issue details to enrich the result.
    """
    prs = search_merged_prs_linked_to_issues(owner, repo, limit=limit)

    results: list[dict[str, Any]] = []
    seen: set[int] = set()
    for pr in prs:
        issue_numbers = extract_issue_numbers(pr.get("body") or "")
        if not issue_numbers:
            continue
        for issue_number in issue_numbers:
            if issue_number in seen:
                continue
            seen.add(issue_number)
            try:
                issue = get_issue(owner, repo, issue_number)
            except Exception:
                continue
            if issue.get("state") != "closed":
                continue
            results.append(
                {
                    "issue_number": issue_number,
                    "issue_title": issue.get("title", ""),
                    "linked_pr_number": pr["number"],
                    "linked_pr_title": pr.get("title", ""),
                    "merged_at": pr.get("closed_at"),
                    "issue_closed_at": issue.get("closed_at"),
                }
            )
    return results


if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 4:
        print("Usage: python -m issue_scout.linker <owner> <repo> [limit]")
        sys.exit(1)
    owner, repo = sys.argv[1], sys.argv[2]
    cap = int(sys.argv[3]) if len(sys.argv) == 4 else 20

    hits = filter_issues_with_merged_prs(owner, repo, limit=cap)
    print(f"checked {cap} merged PRs, found {len(hits)} linked closed issues")
    for hit in hits[:10]:
        print(f"  #{hit['issue_number']} <- PR #{hit['linked_pr_number']}")
        print(f"     {hit['issue_title'][:70]}")