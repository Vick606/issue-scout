"""Find issues that were closed by a merged pull request."""

import sys
from typing import Any

from issue_scout.github import (
    extract_issue_numbers,
    get_issue,
    list_pull_files,
    search_merged_prs_linked_to_issues,
)
from issue_scout.scoring import score_files, suitability_score


def filter_issues_with_merged_prs(
    owner: str,
    repo: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Return issues closed by a merged PR, enriched with diff features.

    Pipeline:
      1. Search merged PRs that are linked to issues.
      2. Extract the linked issue number from each PR body.
      3. Fetch the issue to confirm it is closed.
      4. Fetch the PR file list and compute features and score.
      5. Sort by suitability score descending.
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
            try:
                files = list_pull_files(owner, repo, pr["number"])
            except Exception:
                continue
            features = score_files(files)
            results.append(
                {
                    "issue_number": issue_number,
                    "issue_title": issue.get("title", ""),
                    "linked_pr_number": pr["number"],
                    "linked_pr_title": pr.get("title", ""),
                    "merged_at": pr.get("closed_at"),
                    "issue_closed_at": issue.get("closed_at"),
                    "features": features,
                    "suitability_score": suitability_score(features),
                }
            )
    results.sort(key=lambda r: r["suitability_score"], reverse=True)
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
        score = hit["suitability_score"]
        tests = hit["features"]["test_files_changed"]
        files = hit["features"]["files_changed"]
        print(f"  score={score:5}  #{hit['issue_number']}  tests={tests} files={files}")
        print(f"      {hit['issue_title'][:70]}")