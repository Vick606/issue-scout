"""Tests for issue_scout.dataset."""

import json
from pathlib import Path

from issue_scout.dataset import (
    SCHEMA_VERSION,
    build_dataset,
    write_dataset,
)


def _sample_records() -> list[dict]:
    return [
        {
            "issue_number": 123,
            "issue_title": "Fix something",
            "linked_pr_number": 456,
            "linked_pr_title": "Fix it",
            "merged_at": "2026-09-01T00:00:00Z",
            "issue_closed_at": "2026-09-01T00:01:00Z",
            "features": {"files_changed": 2},
            "suitability_score": 7.5,
        }
    ]


def test_build_dataset_has_expected_keys() -> None:
    dataset = build_dataset("owner", "repo", _sample_records())
    assert dataset["schema_version"] == SCHEMA_VERSION
    assert dataset["source"]["owner"] == "owner"
    assert dataset["source"]["repo"] == "repo"
    assert dataset["source"]["url"] == "https://github.com/owner/repo"
    assert dataset["record_count"] == 1
    assert len(dataset["records"]) == 1
    assert "timestamp" in dataset


def test_build_dataset_empty_records() -> None:
    dataset = build_dataset("owner", "repo", [])
    assert dataset["record_count"] == 0
    assert dataset["records"] == []


def test_write_dataset_creates_file(tmp_path: Path) -> None:
    dataset = build_dataset("owner", "repo", _sample_records())
    out = tmp_path / "nested" / "out.json"
    written = write_dataset(dataset, out)
    assert written == out
    assert out.is_file()


def test_write_dataset_roundtrips_json(tmp_path: Path) -> None:
    dataset = build_dataset("owner", "repo", _sample_records())
    out = tmp_path / "out.json"
    write_dataset(dataset, out)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == SCHEMA_VERSION
    assert loaded["records"][0]["issue_number"] == 123
    assert loaded["records"][0]["suitability_score"] == 7.5