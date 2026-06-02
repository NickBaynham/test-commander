"""Step 11.4 - server-side permission gates across the Runtime API + MCP.

The seven escalating permission levels are enforced server-side: a role without
a level is denied (default deny), a destructive action is refused for an
unauthorized role, and an approval without an approver is not an approval. Both
front-ends (the Runtime API `/api/runtime/execute` and the MCP `tc_run_command`
tool) inherit the same enforcement because both enter the same pipeline; there is
no bypass.
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
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"

import tcweb.main as main  # noqa: E402
from agent_adapters.mock_agent import MockAgentAdapter  # noqa: E402
from governance import audit, pipeline  # noqa: E402
from tcmcp import server  # noqa: E402


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    shutil.copytree(SEEDED_WEB, ws)
    (ws / "policy").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "approvals").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "actions.jsonl").touch()
    return project


def api_execute(project: Path, **payload) -> dict:
    return TestClient(main.create_app(project_root=project)).post(
        "/api/runtime/execute", json=payload
    ).json()


def mcp_run(project: Path, **arguments) -> dict:
    return server.dispatch(
        {"method": "tools/call", "params": {"name": "tc_run_command", "arguments": arguments}},
        project_root=project,
        adapter=MockAgentAdapter(),
    )["result"]


# ---------------------------------------------------------------------------
# Per-level enforcement matrix (default deny). request -> level, allowed role,
# and a role that lacks the level (None for read-only, which every role has).
# ---------------------------------------------------------------------------

LEVEL_MATRIX = [
    ("what is the current status", "read-only", "Viewer", None),
    ("review these requirements", "safe-write", "Tester", "Viewer"),
    ("generate playwright tests for sign-in", "code-write", "Automation Engineer", "Tester"),
    ("run the regression tests", "execute-tests", "Tester", "Viewer"),
    ("explore the staging site", "external-network", "Maintainer", "Automation Engineer"),
    ("delete all evidence", "destructive", "Maintainer", "Automation Engineer"),
    ("rotate the api key", "admin", "Admin", "Maintainer"),
]


def test_every_level_classifies_and_permits_its_role(tmp_path: Path):
    for request, level, allowed_role, _ in LEVEL_MATRIX:
        pv = pipeline.preview(request, role=allowed_role, project_root=tmp_path)
        assert pv.level == level, f"{request!r} -> {pv.level}"
        assert pv.allowed is True, f"{allowed_role} should be allowed {level}"


def test_every_level_denies_a_role_that_lacks_it(tmp_path: Path):
    for request, level, _, denied_role in LEVEL_MATRIX:
        if denied_role is None:
            continue
        pv = pipeline.preview(request, role=denied_role, project_root=tmp_path)
        assert pv.level == level
        assert pv.allowed is False, f"{denied_role} must be denied {level}"


# ---------------------------------------------------------------------------
# Destructive / admin security - both front-ends refuse an unauthorized role
# ---------------------------------------------------------------------------


def test_destructive_refused_for_unauthorized_role_on_both_front_ends(tmp_path: Path):
    project = seed_project(tmp_path)
    api = api_execute(
        project, request="delete all evidence", role="Automation Engineer",
        approve=True, approver="self",
    )
    mcp = mcp_run(
        project, request="delete all evidence", role="Automation Engineer",
        approve=True, approver="self",
    )
    assert api["blocked"] is True and api["executed"] is False
    assert mcp["blocked"] is True and mcp["executed"] is False
    # Blocked before the agent on both paths: nothing recorded.
    assert audit.read_entries(project) == []


def test_admin_refused_for_non_admin(tmp_path: Path):
    project = seed_project(tmp_path)
    body = api_execute(project, request="rotate the api key", role="Maintainer")
    assert body["level"] == "admin"
    assert body["blocked"] is True


def test_privileged_action_runs_for_maintainer_with_approval(tmp_path: Path):
    """A real privileged command (external-network /tc:explore) runs with approval."""
    project = seed_project(tmp_path)
    body = api_execute(
        project, request="explore the staging site", role="Maintainer",
        approve=True, approver="lead", user="bob",
    )
    assert body["level"] == "external-network"
    assert body["executed"] is True
    assert len(audit.read_entries(project)) == 1


def test_destructive_request_has_no_executable_workflow(tmp_path: Path):
    """A Maintainer is allowed `destructive`, but no /tc:* command deletes evidence,
    so the request maps to no executable workflow: it is not blocked, but nothing
    runs and nothing is audited (a privileged-classified, unrouted request never
    executes a no-op without a real plan)."""
    project = seed_project(tmp_path)
    body = api_execute(
        project, request="delete all evidence", role="Maintainer",
        approve=True, approver="lead",
    )
    assert body["level"] == "destructive"
    assert body["blocked"] is False
    assert body["executed"] is False
    assert audit.read_entries(project) == []


# ---------------------------------------------------------------------------
# No bypass
# ---------------------------------------------------------------------------


def test_client_cannot_escalate_by_supplying_a_level(tmp_path: Path):
    """A client-supplied `level` is ignored; the server classifies from the request."""
    project = seed_project(tmp_path)
    body = api_execute(
        project, request="delete all evidence", role="Viewer", level="read-only",
    )
    assert body["level"] == "destructive"
    assert body["blocked"] is True


def test_approval_without_approver_is_not_an_approval_api(tmp_path: Path):
    """approve=True with no approver must NOT execute a privileged action."""
    project = seed_project(tmp_path)
    body = api_execute(
        project, request="generate playwright tests for sign-in",
        role="Automation Engineer", approve=True,  # no approver
    )
    assert body["requires_approval"] is True
    assert body["executed"] is False
    assert audit.read_entries(project) == []


def test_approval_without_approver_is_not_an_approval_mcp(tmp_path: Path):
    project = seed_project(tmp_path)
    result = mcp_run(
        project, request="generate playwright tests for sign-in",
        role="Automation Engineer", approve=True,  # no approver
    )
    assert result["requires_approval"] is True
    assert result["executed"] is False
    assert audit.read_entries(project) == []
