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