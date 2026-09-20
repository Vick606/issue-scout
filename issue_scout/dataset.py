"""Write linked issue records to a versioned JSON dataset."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from issue_scout.linker import filter_issues_with_merged_prs


SCHEMA_VERSION = "1.0"


def build_dataset(
    owner: str,
    repo: str,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Wrap linked issue records in a versioned dataset envelope."""
    return {
        "schema_version": SCHEMA_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": {
            "owner": owner,
            "repo": repo,
            "url": f"https://github.com/{owner}/{repo}",
        },
        "record_count": len(records),
        "records": records,
    }


def write_dataset(dataset: dict[str, Any], output_path: Path) -> Path:
    """Write the dataset to disk as JSON. Returns the path."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(dataset, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3 or len(sys.argv) > 5:
        print(
            "Usage: python -m issue_scout.dataset <owner> <repo> [limit] [output]"
        )
        sys.exit(1)
    owner, repo = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    output = (
        Path(sys.argv[4])
        if len(sys.argv) > 4
        else Path("datasets") / f"{owner}-{repo}.json"
    )

    records = filter_issues_with_merged_prs(owner, repo, limit=limit)
    dataset = build_dataset(owner, repo, records)
    written = write_dataset(dataset, output)
    print(f"{len(records)} records written to {written}")