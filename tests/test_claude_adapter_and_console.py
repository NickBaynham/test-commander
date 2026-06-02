"""Step 10.5.10 - ClaudeCodeCliAdapter + wiring the Phase-10 console.

The real Claude adapter implements the same interface and is gated identically
(refuses an unplanned call; the real shell-out is refused under pytest). The web
console gains a single /api/execute route that runs an approved request through
the governance pipeline; no other UI path executes anything.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime"))
sys.path.insert(0, str(REPO / "apps" / "api"))
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"

import tcweb.main as main  # noqa: E402
from agent_adapters.base import (  # noqa: E402
    AgentAdapter,
    BoundedInstruction,
    UnplannedExecutionError,
)
from agent_adapters.claude_code_cli import (  # noqa: E402
    ClaudeCodeCliAdapter,
    ClaudeExecutionRefusedError,
)
from governance import audit  # noqa: E402


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    shutil.copytree(SEEDED_WEB, ws)
    (ws / "policy").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "approvals").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "actions.jsonl").touch()
    return project


def _instr(project: Path) -> BoundedInstruction:
    return BoundedInstruction(
        command="/tc:automate", scope="code-write", project_root=project,
        allowed_paths=("tests/",), expected_outputs=("tests/e2e/sign-in.spec.ts",),
        approved=True,
    )


# ---------------------------------------------------------------------------
# ClaudeCodeCliAdapter - gated identically to the mock
# ---------------------------------------------------------------------------


def test_claude_adapter_implements_interface():
    assert issubclass(ClaudeCodeCliAdapter, AgentAdapter)


def test_claude_adapter_refuses_unplanned_call():
    with pytest.raises(UnplannedExecutionError):
        ClaudeCodeCliAdapter().execute_command(None)


def test_claude_real_execution_refused_under_pytest(tmp_path: Path):
    project = seed_project(tmp_path)
    with pytest.raises(ClaudeExecutionRefusedError):
        ClaudeCodeCliAdapter().execute_command(_instr(project))


# ---------------------------------------------------------------------------
# Console wired to the pipeline
# ---------------------------------------------------------------------------


def client_for(project: Path) -> TestClient:
    return TestClient(main.create_app(project_root=project))


def test_console_execute_traverses_the_pipeline(tmp_path: Path):
    project = seed_project(tmp_path)
    c = client_for(project)
    resp = c.post("/api/execute", json={
        "request": "generate playwright tests for sign-in",
        "role": "Automation Engineer", "approve": True, "approver": "maintainer", "user": "alice",
    }).json()
    assert resp["executed"] is True
    assert resp["command"] == "/tc:automate"
    # The pipeline wrote an audit entry — execution went through governance.
    assert len(audit.read_entries(project)) == 1


def test_console_execute_blocks_unsafe(tmp_path: Path):
    project = seed_project(tmp_path)
    c = client_for(project)
    resp = c.post("/api/execute", json={"request": "delete all evidence", "role": "Viewer"}).json()
    assert resp["blocked"] is True
    assert resp["executed"] is False


def test_console_chat_never_executes(tmp_path: Path):
    project = seed_project(tmp_path)
    c = client_for(project)
    resp = c.post("/api/chat", json={"question": "run the tests now"}).json()
    assert resp["executed"] is False
    # No audit entry: chat is read-only, the only execution path is /api/execute.
    assert audit.read_entries(project) == []
