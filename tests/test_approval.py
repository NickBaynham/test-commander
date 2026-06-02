"""Step 10.5.6 - the approval gate (card + record).

Requires approval for the privileged levels (configurable for safe-write via
approvals.yaml), renders an approval card, and records the decision under
audit/approvals/ with approver + timestamp.
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime"))
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"

from governance import approval, planner  # noqa: E402

NOW = datetime(2026, 6, 1, 9, 30, 0)


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    shutil.copytree(SEEDED_WEB, ws)
    (ws / "policy").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "approvals").mkdir(parents=True, exist_ok=True)
    return project


def test_requires_approval_by_level(tmp_path: Path):
    project = seed_project(tmp_path)
    assert approval.requires_approval(planner.plan("/tc:automate"), project) is True
    assert approval.requires_approval(planner.plan("/tc:review-requirements"), project) is False
    assert approval.requires_approval(planner.plan("read-only"), project) is False


def test_approvals_yaml_can_require_safe_write(tmp_path: Path):
    project = seed_project(tmp_path)
    (project / ".test-commander" / "policy" / "approvals.yaml").write_text(
        "require_approval:\n  - safe-write\n  - code-write\n", encoding="utf-8"
    )
    assert approval.requires_approval(planner.plan("/tc:review-requirements"), project) is True


def test_render_card_shows_the_plan(tmp_path: Path):
    card = approval.render_card(planner.plan("/tc:automate"))
    assert "/tc:automate" in card
    assert "code-write" in card
    assert "tests/" in card
    assert "Approve?" in card


def test_record_writes_decision_with_approver_and_timestamp(tmp_path: Path):
    project = seed_project(tmp_path)
    path = approval.record(project, planner.plan("/tc:automate"), approved=True,
                           approver="maintainer", now=NOW)
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["approved"] is True
    assert data["approver"] == "maintainer"
    assert data["timestamp"] == NOW.isoformat()
    assert data["command"] == "/tc:automate"
    assert data["level"] == "code-write"
