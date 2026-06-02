"""Phase 10.5 - the four canonical security integration tests (the phase spine).

Written RED at Step 10.5.1 as executable acceptance criteria, each marked xfail
with the sub-step that turns it green. As each control lands, its xfail marker is
removed (strict=True turns an unexpected pass into a failure, forcing the flip):

- block-before-agent      -> GREEN at 10.5.3 (permission policy engine)
- deny-no-change          -> GREEN at 10.5.6 (approval gate, deny path)
- approve-diff-matches    -> GREEN at 10.5.8 (output validation)
- no-plan-bypass-refused  -> GREEN at 10.5.9 (audit + no backdoor)

Imports are in-body so a not-yet-existing module surfaces as the expected
failure rather than a collection error.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime"))
FIXTURE = REPO / "tests" / "fixtures" / "seeded-governance"
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"


def seed_project(tmp_path: Path) -> Path:
    """A workspace with policy/audit dirs and some real artifacts to act on."""
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    shutil.copytree(SEEDED_WEB, ws)
    (ws / "policy").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "approvals").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "actions.jsonl").touch()
    return project


def workspace_snapshot(project: Path) -> dict:
    ws = project / ".test-commander"
    return {
        p.relative_to(ws): p.read_bytes()
        for p in sorted(ws.rglob("*"))
        if p.is_file() and ".web" not in p.relative_to(ws).parts
        and "audit" not in p.relative_to(ws).parts
    }


def test_unsafe_request_blocked_before_agent(tmp_path: Path):
    from agent_adapters.mock_agent import MockAgentAdapter
    from governance import pipeline

    project = seed_project(tmp_path)
    adapter = MockAgentAdapter()
    res = pipeline.handle_request(
        "delete all evidence", role="Viewer", project_root=project, adapter=adapter,
    )
    assert res.blocked is True
    assert adapter.calls == [], "an unsafe request must never reach the agent"


def test_code_write_denied_changes_nothing(tmp_path: Path):
    from agent_adapters.mock_agent import MockAgentAdapter
    from governance import pipeline

    project = seed_project(tmp_path)
    before = workspace_snapshot(project)
    adapter = MockAgentAdapter()
    res = pipeline.handle_request(
        "generate playwright tests for sign-in", role="Automation Engineer",
        project_root=project, adapter=adapter, approve=False,
    )
    assert res.requires_approval is True
    assert res.approved is False
    assert res.executed is False
    assert adapter.calls == []
    assert workspace_snapshot(project) == before, "a denied action must change nothing"


def test_approved_action_diff_matches_plan(tmp_path: Path):
    from agent_adapters.mock_agent import MockAgentAdapter
    from governance import pipeline

    project = seed_project(tmp_path)
    adapter = MockAgentAdapter()
    res = pipeline.handle_request(
        "generate playwright tests for sign-in", role="Automation Engineer",
        project_root=project, adapter=adapter, approve=True, approver="maintainer",
    )
    assert res.approved is True
    assert res.executed is True
    assert res.validation is not None and res.validation.ok is True, (
        "the post-execution diff must match the planned scope"
    )


def test_no_plan_direct_adapter_call_is_refused(tmp_path: Path):
    from agent_adapters.base import UnplannedExecutionError
    from agent_adapters.mock_agent import MockAgentAdapter
    from governance import audit  # only exists once the audit journal ships (10.5.9)

    project = seed_project(tmp_path)
    adapter = MockAgentAdapter()
    with pytest.raises(UnplannedExecutionError):
        adapter.execute_command(None)  # no bounded instruction / no plan
    assert adapter.calls == [], "a refused call must not execute"
    # The bypass left no trace: the runtime audited nothing.
    assert audit.read_entries(project) == [], "a refused bypass must write no audit entry"
