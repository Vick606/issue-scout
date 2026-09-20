"""Tests for issue_scout.github.

Network calls are mocked with the responses library. No real HTTP
requests are made.
"""

import responses

from issue_scout.github import (
    extract_issue_numbers,
    list_pull_files,
    search_merged_prs_linked_to_issues,
)


def test_extract_issue_numbers_all_keywords() -> None:
    body = "This fixes #123 and closes #456. Also resolves #789."
    assert extract_issue_numbers(body) == [123, 456, 789]


def test_extract_issue_numbers_case_insensitive() -> None:
    assert extract_issue_numbers("FIXES #100") == [100]
    assert extract_issue_numbers("Fixed #200") == [200]
    assert extract_issue_numbers("Closes #300") == [300]


def test_extract_issue_numbers_ignores_unrelated_numbers() -> None:
    assert extract_issue_numbers("See #1 for discussion, PR #2 is unrelated") == []


def test_extract_issue_numbers_returns_empty_on_none() -> None:
    assert extract_issue_numbers("") == []


@responses.activate
def test_search_returns_parsed_items() -> None:
    responses.add(
        responses.GET,
        "https://api.github.com/search/issues",
        json={
            "items": [
                {"number": 1, "title": "PR one", "body": "fixes #10"},
                {"number": 2, "title": "PR two", "body": "closes #20"},
            ]
        },
        status=200,
    )
    results = search_merged_prs_linked_to_issues("fake", "repo", limit=5)
    assert len(results) == 2
    assert results[0]["number"] == 1
    assert results[1]["title"] == "PR two"


@responses.activate
def test_search_handles_empty_response() -> None:
    responses.add(
        responses.GET,
        "https://api.github.com/search/issues",
        json={"items": []},
        status=200,
    )
    results = search_merged_prs_linked_to_issues("fake", "repo", limit=5)
    assert results == []


@responses.activate
def test_list_pull_files_returns_file_entries() -> None:
    responses.add(
        responses.GET,
        "https://api.github.com/repos/fake/repo/pulls/1/files",
        json=[
            {"filename": "src/foo.py", "additions": 5, "deletions": 2},
            {"filename": "tests/test_foo.py", "additions": 10, "deletions": 1},
        ],
        status=200,
    )
    files = list_pull_files("fake", "repo", 1)
    assert len(files) == 2
    assert files[0]["filename"] == "src/foo.py"
    assert files[1]["additions"] == 10