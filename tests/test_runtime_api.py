"""Step 11.2 - Runtime API expansion (through the Phase-10.5 pipeline).

The Runtime API is one of two front-ends to the governance pipeline. It adds, in
the `/api/runtime/` namespace:

- `GET /api/runtime/info`     - self-description (service + the seven levels).
- `POST /api/runtime/plan`    - a read-only dry run: the routed command, the
                                classified level, and whether the role is allowed,
                                with no execution and no audit entry.
- `POST /api/runtime/execute` - governed execution through the pipeline.

Every mutating route enters `governance.pipeline.handle_request`; a route above
read-only cannot execute without a plan and (where the level requires it) an
approval. The read class is the existing Phase-10 console routes (`/api/*`).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime"))
sys.path.insert(0, str(REPO / "apps" / "api"))
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"

import tcweb.main as main  # noqa: E402
from governance import audit  # noqa: E402


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    shutil.copytree(SEEDED_WEB, ws)
    (ws / "policy").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "approvals").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "actions.jsonl").touch()
    return project


def client_for(project: Path) -> TestClient:
    return TestClient(main.create_app(project_root=project))


# ---------------------------------------------------------------------------
# /api/runtime/info
# ---------------------------------------------------------------------------


def test_info_advertises_seven_levels(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    body = c.get("/api/runtime/info").json()
    assert body["service"] == "tc-runtime-api"
    assert len(body["permission_levels"]) == 7


# ---------------------------------------------------------------------------
# /api/runtime/plan  - read-only dry run
# ---------------------------------------------------------------------------


PLAN_CASES = [
    ("what is the current status", "read-only"),
    ("review these requirements", "safe-write"),
    ("generate playwright tests for sign-in", "code-write"),
    ("run the sign-in regression tests", "execute-tests"),
    ("delete all evidence", "destructive"),
]


def test_plan_classifies_each_level(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    for request, expected_level in PLAN_CASES:
        body = c.post("/api/runtime/plan", json={"request": request, "role": "Admin"}).json()
        assert body["level"] == expected_level, f"{request!r} -> {body['level']}"


def test_plan_reports_role_allowance(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    # A Viewer is allowed the read-only request but not the destructive one.
    ok = c.post(
        "/api/runtime/plan", json={"request": "what is the current status", "role": "Viewer"}
    ).json()
    assert ok["allowed"] is True
    denied = c.post(
        "/api/runtime/plan", json={"request": "delete all evidence", "role": "Viewer"}
    ).json()
    assert denied["level"] == "destructive"
    assert denied["allowed"] is False


def test_plan_never_executes(tmp_path: Path):
    project = seed_project(tmp_path)
    c = client_for(project)
    c.post("/api/runtime/plan", json={"request": "delete all evidence", "role": "Admin"})
    # A dry run writes nothing to the audit journal.
    assert audit.read_entries(project) == []


# ---------------------------------------------------------------------------
# /api/runtime/execute  - governed execution through the pipeline
# ---------------------------------------------------------------------------


def test_execute_read_only_does_not_execute(tmp_path: Path):
    project = seed_project(tmp_path)
    c = client_for(project)
    body = c.post(
        "/api/runtime/execute", json={"request": "what is the current status", "role": "Viewer"}
    ).json()
    assert body["level"] == "read-only"
    assert body["blocked"] is False
    assert body["executed"] is False
    assert audit.read_entries(project) == []


def test_execute_blocks_denied_request(tmp_path: Path):
    project = seed_project(tmp_path)
    c = client_for(project)
    body = c.post(
        "/api/runtime/execute", json={"request": "delete all evidence", "role": "Viewer"}
    ).json()
    assert body["blocked"] is True
    assert body["executed"] is False
    # Blocked before the agent: nothing recorded.
    assert audit.read_entries(project) == []


def test_execute_holds_privileged_without_approval(tmp_path: Path):
    project = seed_project(tmp_path)
    c = client_for(project)
    body = c.post(
        "/api/runtime/execute",
        json={"request": "generate playwright tests for sign-in", "role": "Automation Engineer"},
    ).json()
    assert body["blocked"] is False
    assert body["requires_approval"] is True
    assert body["executed"] is False
    # Held, not executed: no audit entry.
    assert audit.read_entries(project) == []


def test_execute_runs_with_approval(tmp_path: Path):
    project = seed_project(tmp_path)
    c = client_for(project)
    body = c.post(
        "/api/runtime/execute",
        json={
            "request": "generate playwright tests for sign-in",
            "role": "Automation Engineer",
            "approve": True,
            "approver": "maintainer",
            "user": "alice",
        },
    ).json()
    assert body["executed"] is True
    assert body["command"] == "/tc:automate"
    # Exactly one audit entry: execution went through governance.
    assert len(audit.read_entries(project)) == 1


# ---------------------------------------------------------------------------
# Read class - the existing console routes are read-only on the Runtime API
# ---------------------------------------------------------------------------


def test_read_route_is_read_only(tmp_path: Path):
    project = seed_project(tmp_path)
    c = client_for(project)
    resp = c.get("/api/requirements")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert audit.read_entries(project) == []
