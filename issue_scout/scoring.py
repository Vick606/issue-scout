"""Classify changed files and score issues for LLM bug-fix evaluation."""

from typing import Any


TEST_DIR_MARKERS = ("/tests/", "/test/", "tests/", "test/")
TEST_FILE_PREFIX = "test_"
TEST_FILE_SUFFIX = "_test.py"
DOC_EXTENSIONS = (".md", ".rst", ".txt")


def is_test_file(path: str) -> bool:
    """Heuristic: does this path look like a test file?"""
    lower = path.lower()
    if any(marker in lower for marker in TEST_DIR_MARKERS):
        return True
    name = lower.rsplit("/", 1)[-1]
    if name.startswith(TEST_FILE_PREFIX):
        return True
    if name.endswith(TEST_FILE_SUFFIX):
        return True
    return False


def is_doc_file(path: str) -> bool:
    """Heuristic: does this path look like documentation?"""
    return path.lower().endswith(DOC_EXTENSIONS)


def score_files(files: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute enrichment features from a PR's file list."""
    file_names = [f.get("filename", "") for f in files]
    test_files = [n for n in file_names if is_test_file(n)]
    doc_files = [n for n in file_names if is_doc_file(n)]
    source_files = [
        n for n in file_names if not is_test_file(n) and not is_doc_file(n)
    ]
    additions = sum(f.get("additions", 0) for f in files)
    deletions = sum(f.get("deletions", 0) for f in files)
    return {
        "files_changed": len(files),
        "test_files_changed": len(test_files),
        "doc_files_changed": len(doc_files),
        "source_files_changed": len(source_files),
        "additions": additions,
        "deletions": deletions,
        "total_lines_changed": additions + deletions,
        "test_file_names": test_files[:5],
    }


def suitability_score(features: dict[str, Any]) -> float:
    """Score 0-10. Higher is better for LLM bug-fix evaluation.

    Design rationale:
      + Start at 5.0 neutral.
      + Add 2.0 per test file changed. Tests let us verify a fix.
      + Subtract 0.1 per file changed. Large diffs are hard to evaluate.
      + Subtract 0.01 per line changed. Same reason.
      + Subtract 3.0 for doc-only changes. No code to test.
      + Clamp the result to [0, 10].
    """
    score = 5.0
    score += 2.0 * features["test_files_changed"]
    score -= 0.1 * features["files_changed"]
    score -= 0.01 * features["total_lines_changed"]
    if features["test_files_changed"] == 0 and features["source_files_changed"] == 0:
        score -= 3.0
    return round(max(0.0, min(10.0, score)), 2)