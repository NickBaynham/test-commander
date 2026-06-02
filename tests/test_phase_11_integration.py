"""Step 11.6 - Phase 11 integration finalization.

The consolidated end-to-end smoke for the Runtime API and the MCP server: both
front-ends drive the same governance pipeline in one workspace, and the no-bypass
security properties hold on both. Also pins the verifier state at Phase 11
(`DEFAULT_PHASE_CAP >= 11`, so `tc-mcp` is PRESENT, not UNEXPECTED).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime"))
sys.path.insert(0, str(REPO / "apps" / "api"))
sys.path.insert(0, str(REPO / "apps" / "mcp"))
sys.path.insert(0, str(REPO / "scripts"))
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"

import tcweb.main as main  # noqa: E402
import verify_skills  # noqa: E402
from agent_adapters.mock_agent import MockAgentAdapter  # noqa: E402
from governance import audit  # noqa: E402
from tcmcp import server  # noqa: E402


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    shutil.copytree(SEEDED_WEB, ws)
    (ws / "policy").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "approvals").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "actions.jsonl").touch()
    return project


def api(project: Path) -> TestClient:
    return TestClient(main.create_app(project_root=project))


def mcp(project: Path, name: str, arguments: dict) -> dict:
    return server.dispatch(
        {"method": "tools/call", "params": {"name": name, "arguments": arguments}},
        project_root=project,
        adapter=MockAgentAdapter(),
    )["result"]


# ---------------------------------------------------------------------------
# Verifier state pinned at Phase 11
# ---------------------------------------------------------------------------


def test_default_phase_cap_at_least_11():
    assert verify_skills.DEFAULT_PHASE_CAP >= 11


def test_tc_mcp_in_catalog_at_11():
    assert verify_skills.CATALOG["tc-mcp"] == 11


# ---------------------------------------------------------------------------
# Runtime API end to end
# ---------------------------------------------------------------------------


def test_runtime_api_info_and_dry_run_then_execute(tmp_path: Path):
    project = seed_project(tmp_path)
    c = api(project)
    assert len(c.get("/api/runtime/info").json()["permission_levels"]) == 7

    # Dry run: code-write, allowed, requires approval; no audit entry.
    plan = c.post("/api/runtime/plan", json={
        "request": "generate playwright tests for sign-in", "role": "Automation Engineer",
    }).json()
    assert plan["level"] == "code-write" and plan["allowed"] is True
    assert plan["requires_approval"] is True
    assert audit.read_entries(project) == []

    # Execute with approval: runs, one audit entry.
    done = c.post("/api/runtime/execute", json={
        "request": "generate playwright tests for sign-in", "role": "Automation Engineer",
        "approve": True, "approver": "maintainer", "user": "alice",
    }).json()
    assert done["executed"] is True and done["command"] == "/tc:automate"
    assert len(audit.read_entries(project)) == 1


def test_runtime_api_blocks_denied_and_holds_unattributed(tmp_path: Path):
    project = seed_project(tmp_path)
    c = api(project)
    blocked = c.post("/api/runtime/execute", json={
        "request": "delete all evidence", "role": "Viewer", "level": "read-only",
    }).json()
    assert blocked["blocked"] is True and blocked["level"] == "destructive"

    held = c.post("/api/runtime/execute", json={
        "request": "generate playwright tests for sign-in", "role": "Automation Engineer",
        "approve": True,  # no approver
    }).json()
    assert held["executed"] is False and held["requires_approval"] is True
    assert audit.read_entries(project) == []


# ---------------------------------------------------------------------------
# MCP server end to end
# ---------------------------------------------------------------------------


def test_mcp_round_trip_and_gating(tmp_path: Path):
    project = seed_project(tmp_path)
    # Handshake + catalog.
    init = server.dispatch(
        {"method": "initialize"}, project_root=project, adapter=MockAgentAdapter()
    )
    assert init["serverInfo"]["name"] == "test-commander"
    names = {t["name"] for t in server.tools()}
    assert {"tc_status", "tc_plan", "tc_run_command"} <= names

    # Denied + held are refused without an audit entry; approved runs.
    assert mcp(project, "tc_run_command", {"request": "delete all evidence", "role": "Viewer"})[
        "blocked"
    ] is True
    assert mcp(project, "tc_run_command", {
        "request": "generate playwright tests for sign-in", "role": "Automation Engineer",
    })["executed"] is False
    assert audit.read_entries(project) == []

    ran = mcp(project, "tc_run_command", {
        "request": "generate playwright tests for sign-in", "role": "Automation Engineer",
        "approve": True, "approver": "maintainer",
    })
    assert ran["executed"] is True
    assert len(audit.read_entries(project)) == 1


# ---------------------------------------------------------------------------
# No bypass on either front-end
# ---------------------------------------------------------------------------


def test_no_front_end_can_bypass_the_pipeline(tmp_path: Path):
    project = seed_project(tmp_path)
    c = api(project)
    # A client-supplied level cannot lower the classification on the API...
    assert c.post("/api/runtime/execute", json={
        "request": "delete all evidence", "role": "Viewer", "level": "read-only",
    }).json()["blocked"] is True
    # ...nor can an unattributed approval execute via the MCP tool.
    assert mcp(project, "tc_run_command", {
        "request": "delete all evidence", "role": "Maintainer", "approve": True,
    })["executed"] is False
    assert audit.read_entries(project) == []
