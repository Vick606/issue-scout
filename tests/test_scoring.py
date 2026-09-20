"""Tests for issue_scout.scoring."""

from issue_scout.scoring import (
    is_doc_file,
    is_test_file,
    score_files,
    suitability_score,
)


def test_test_dir_in_path() -> None:
    assert is_test_file("tests/test_foo.py")
    assert is_test_file("my_project/tests/helpers.py")
    assert is_test_file("src/pkg/test/foo.py")


def test_test_file_prefix() -> None:
    assert is_test_file("test_foo.py")
    assert is_test_file("src/pkg/test_bar.py")


def test_test_file_suffix() -> None:
    assert is_test_file("foo_test.py")


def test_source_file_is_not_test() -> None:
    assert not is_test_file("src/pkg/foo.py")
    assert not is_test_file("README.md")
    assert not is_test_file("conftest.py")


def test_is_doc_file() -> None:
    assert is_doc_file("docs/index.md")
    assert is_doc_file("CHANGES.rst")
    assert is_doc_file("NOTES.txt")


def test_source_file_is_not_doc() -> None:
    assert not is_doc_file("src/foo.py")
    assert not is_doc_file("tests/test_foo.py")


def test_score_files_categorizes_correctly() -> None:
    files = [
        {"filename": "src/foo.py", "additions": 5, "deletions": 2},
        {"filename": "tests/test_foo.py", "additions": 10, "deletions": 1},
        {"filename": "docs/index.md", "additions": 3, "deletions": 0},
    ]
    features = score_files(files)
    assert features["files_changed"] == 3
    assert features["source_files_changed"] == 1
    assert features["test_files_changed"] == 1
    assert features["doc_files_changed"] == 1
    assert features["additions"] == 18
    assert features["deletions"] == 3
    assert features["total_lines_changed"] == 21
    assert features["test_file_names"] == ["tests/test_foo.py"]


def test_score_files_handles_missing_stats() -> None:
    files = [{"filename": "src/foo.py"}]
    features = score_files(files)
    assert features["additions"] == 0
    assert features["deletions"] == 0


def test_suitability_prefers_test_touched_prs() -> None:
    with_test = {
        "files_changed": 2,
        "test_files_changed": 1,
        "doc_files_changed": 0,
        "source_files_changed": 1,
        "additions": 10,
        "deletions": 2,
        "total_lines_changed": 12,
        "test_file_names": ["tests/test_foo.py"],
    }
    without_test = {
        "files_changed": 2,
        "test_files_changed": 0,
        "doc_files_changed": 0,
        "source_files_changed": 2,
        "additions": 10,
        "deletions": 2,
        "total_lines_changed": 12,
        "test_file_names": [],
    }
    assert suitability_score(with_test) > suitability_score(without_test)


def test_suitability_penalizes_docs_only() -> None:
    docs_only = {
        "files_changed": 1,
        "test_files_changed": 0,
        "doc_files_changed": 1,
        "source_files_changed": 0,
        "additions": 10,
        "deletions": 0,
        "total_lines_changed": 10,
        "test_file_names": [],
    }
    source_only = {
        "files_changed": 1,
        "test_files_changed": 0,
        "doc_files_changed": 0,
        "source_files_changed": 1,
        "additions": 10,
        "deletions": 0,
        "total_lines_changed": 10,
        "test_file_names": [],
    }
    assert suitability_score(docs_only) < suitability_score(source_only)


def test_suitability_penalizes_large_diffs() -> None:
    small = {
        "files_changed": 2,
        "test_files_changed": 1,
        "doc_files_changed": 0,
        "source_files_changed": 1,
        "additions": 10,
        "deletions": 2,
        "total_lines_changed": 12,
        "test_file_names": ["tests/test_foo.py"],
    }
    large = {
        "files_changed": 20,
        "test_files_changed": 1,
        "doc_files_changed": 0,
        "source_files_changed": 19,
        "additions": 800,
        "deletions": 400,
        "total_lines_changed": 1200,
        "test_file_names": ["tests/test_foo.py"],
    }
    assert suitability_score(small) > suitability_score(large)


def test_suitability_score_is_clamped() -> None:
    perfect = {
        "files_changed": 2,
        "test_files_changed": 10,
        "doc_files_changed": 0,
        "source_files_changed": 1,
        "additions": 5,
        "deletions": 0,
        "total_lines_changed": 5,
        "test_file_names": [],
    }
    assert suitability_score(perfect) <= 10.0

    worst = {
        "files_changed": 500,
        "test_files_changed": 0,
        "doc_files_changed": 100,
        "source_files_changed": 0,
        "additions": 50000,
        "deletions": 50000,
        "total_lines_changed": 100000,
        "test_file_names": [],
    }
    assert suitability_score(worst) >= 0.0