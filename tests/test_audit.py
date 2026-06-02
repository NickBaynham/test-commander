"""Step 10.5.9 - the append-only audit journal.

Every executed action writes one audit entry with the full field set. A bypass
(a direct adapter call with no plan) writes nothing.
"""

from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime"))
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"

from agent_adapters.mock_agent import MockAgentAdapter  # noqa: E402
from governance import audit, pipeline  # noqa: E402

NOW = datetime(2026, 6, 1, 9, 30, 0)

FIELDS = {
    "user", "timestamp", "request", "intent", "command", "approval_status",
    "approver", "level", "files_read", "files_changed", "artifacts",
    "tests_run", "target_urls", "status", "summary",
}


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    shutil.copytree(SEEDED_WEB, ws)
    (ws / "policy").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "approvals").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "actions.jsonl").touch()
    return project


def test_read_entries_empty_when_no_audit(tmp_path: Path):
    project = seed_project(tmp_path)
    assert audit.read_entries(project) == []


def test_record_appends_one_entry(tmp_path: Path):
    project = seed_project(tmp_path)
    audit.record(project, {"command": "/tc:report", "status": "succeeded"}, now=NOW)
    audit.record(project, {"command": "/tc:run", "status": "succeeded"}, now=NOW)
    entries = audit.read_entries(project)
    assert len(entries) == 2
    assert entries[0]["timestamp"] == NOW.isoformat()


def test_executed_action_writes_full_audit_entry(tmp_path: Path):
    project = seed_project(tmp_path)
    adapter = MockAgentAdapter()
    pipeline.handle_request(
        "generate playwright tests for sign-in", role="Automation Engineer",
        project_root=project, adapter=adapter, approve=True, approver="maintainer",
        user="alice", now=NOW,
    )
    entries = audit.read_entries(project)
    assert len(entries) == 1
    entry = entries[0]
    assert set(entry) >= FIELDS, f"missing audit fields: {FIELDS - set(entry)}"
    assert entry["command"] == "/tc:automate"
    assert entry["approval_status"] == "approved"
    assert entry["approver"] == "maintainer"
    assert entry["user"] == "alice"
    assert entry["status"] == "succeeded"
