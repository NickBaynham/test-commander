"""Step 10.5.12 - Phase 10.5 integration smoke (consolidated).

Drives the whole governance pipeline end to end against one workspace with the
mock adapter and confirms the Step 10.5 contract in one place: the four security
properties (block-before-agent, deny-no-change, approve-diff-matches,
no-plan-bypass), secret redaction, the Claude adapter gated identically, and
PHASE_OWNERSHIP["10.5"] == ["policy", "audit"].
"""

from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime"))
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"

import workspace_state  # noqa: E402
from agent_adapters.base import UnplannedExecutionError  # noqa: E402
from agent_adapters.claude_code_cli import (  # noqa: E402
    ClaudeCodeCliAdapter,
    ClaudeExecutionRefusedError,
)
from agent_adapters.mock_agent import MockAgentAdapter  # noqa: E402
from governance import audit, pipeline, validation  # noqa: E402

NOW = datetime(2026, 6, 1, 9, 30, 0)


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    shutil.copytree(SEEDED_WEB, ws)
    (ws / "policy").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "approvals").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "actions.jsonl").touch()
    return project


def outside_audit(project: Path) -> dict:
    ws = project / ".test-commander"
    return {
        p.relative_to(ws): p.read_bytes()
        for p in sorted(ws.rglob("*"))
        if p.is_file() and "audit" not in p.relative_to(ws).parts
        and ".web" not in p.relative_to(ws).parts
    }


def test_phase_ownership_10_5():
    assert workspace_state.PHASE_OWNERSHIP["10.5"] == ["policy", "audit"]


def test_full_governance_pipeline(tmp_path: Path):
    project = seed_project(tmp_path)

    # 1. Block before the agent.
    adapter = MockAgentAdapter()
    blocked = pipeline.handle_request("delete all evidence", role="Viewer",
                                      project_root=project, adapter=adapter, now=NOW)
    assert blocked.blocked is True and adapter.calls == []

    # 2. Deny a code-write -> nothing changes.
    before = outside_audit(project)
    adapter = MockAgentAdapter()
    denied = pipeline.handle_request("generate playwright tests for sign-in",
                                     role="Automation Engineer", project_root=project,
                                     adapter=adapter, approve=False, now=NOW)
    assert denied.requires_approval is True and denied.executed is False
    assert adapter.calls == [] and outside_audit(project) == before

    # 3. Approve -> execute -> diff matches plan -> audited.
    adapter = MockAgentAdapter()
    ok = pipeline.handle_request("generate playwright tests for sign-in",
                                 role="Automation Engineer", project_root=project,
                                 adapter=adapter, approve=True, approver="maintainer",
                                 user="alice", now=NOW)
    assert ok.executed is True and ok.validation.ok is True
    entries = audit.read_entries(project)
    assert len(entries) == 1 and entries[0]["approval_status"] == "approved"

    # 4. No-plan bypass refused (and the Claude adapter is gated identically).
    with pytest.raises(UnplannedExecutionError):
        MockAgentAdapter().execute_command(None)
    with pytest.raises(UnplannedExecutionError):
        ClaudeCodeCliAdapter().execute_command(None)


def test_secret_redaction_and_env_flagging():
    assert "sk-live-XYZ" not in validation.redact("API_KEY=sk-live-XYZ")
    assert validation.flags_env_var_print("printenv") is True


def test_claude_real_execution_refused_under_pytest(tmp_path: Path):
    from agent_adapters.base import BoundedInstruction

    instr = BoundedInstruction(command="/tc:automate", scope="code-write",
                               project_root=tmp_path, approved=True)
    with pytest.raises(ClaudeExecutionRefusedError):
        ClaudeCodeCliAdapter().execute_command(instr)
