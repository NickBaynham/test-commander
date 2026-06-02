"""Append-only audit journal (Phase 10.5 Step 10.5.9).

Every action that runs through the pipeline writes one line to
`<workspace>/audit/actions.jsonl`. A bypass — a direct adapter call with no plan
— is refused by the adapter and writes nothing, so an empty journal is proof
nothing executed outside the pipeline.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"

# The full audit field set (Phase 10.5 spec).
FIELDS = (
    "user", "timestamp", "request", "intent", "command", "approval_status",
    "approver", "level", "files_read", "files_changed", "artifacts",
    "tests_run", "target_urls", "status", "summary", "evidence",
)


def _audit_path(project_root: Path) -> Path:
    return Path(project_root) / WORKSPACE_DIRNAME / "audit" / "actions.jsonl"


def record(project_root: Path, entry: dict, now: datetime | None = None) -> dict:
    """Append one audit entry (timestamp added if absent). Returns the entry."""
    full = {key: entry.get(key) for key in FIELDS}
    full.update(entry)
    if not full.get("timestamp"):
        full["timestamp"] = (now or datetime.now()).isoformat()
    path = _audit_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(full, sort_keys=True) + "\n")
    return full


def read_entries(project_root: Path) -> list[dict]:
    """Read every audit entry. Empty (or missing) journal -> []."""
    path = _audit_path(project_root)
    if not path.is_file():
        return []
    return [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
