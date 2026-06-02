"""Step 10.3 - read-only APIs + SSE event stream + /tc:web-sync.

Read routes serve each page's data from the index; the SSE stream emits an event
on a workspace change; proposal generation returns a card and never executes.
Every route is read-only: hitting them all leaves the workspace byte-identical.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "apps" / "api"))
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
FIXTURE = REPO / "tests" / "fixtures" / "seeded-web"

import tcweb.config as config  # noqa: E402
import tcweb.main as main  # noqa: E402
import tcweb.proposals as proposals  # noqa: E402
import tcweb.sse as sse  # noqa: E402
import web_sync  # noqa: E402


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    shutil.copytree(FIXTURE, project / ".test-commander")
    return project


def client_for(project: Path) -> TestClient:
    return TestClient(main.create_app(project_root=project))


def workspace_snapshot(project: Path) -> dict:
    ws = project / ".test-commander"
    return {
        p.relative_to(ws): p.read_bytes()
        for p in sorted(ws.rglob("*"))
        if p.is_file() and ".web" not in p.relative_to(ws).parts
    }


# ---------------------------------------------------------------------------
# Read routes
# ---------------------------------------------------------------------------


def test_requirements_route(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    data = c.get("/api/requirements").json()
    assert len(data) == 3
    assert {row["req_id"] for row in data} == {"REQ-001", "REQ-002", "REQ-003"}


def test_runs_route(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    data = c.get("/api/runs").json()
    assert len(data) == 1
    assert data[0]["run_id"] == "RUN-20260601-093000"
    assert (data[0]["passed"], data[0]["failed"], data[0]["flaky"]) == (1, 1, 1)


def test_dashboard_route(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    data = c.get("/api/dashboard").json()
    assert data["requirements"] == 3
    assert data["latest_run"]["run_id"] == "RUN-20260601-093000"
    assert "source" in data, "the dashboard must cite the artifacts it rendered"


def test_journal_route(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    data = c.get("/api/journal").json()
    assert len(data) >= 2
    assert all("title" in e for e in data)


def test_evidence_route(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    data = c.get("/api/evidence").json()
    assert len(data) >= 1
    assert data[0]["artifact"].startswith("evidence/")


def test_quality_report_route(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    data = c.get("/api/quality-report").json()
    assert data["facts"]["requirements"] == "3"


def test_sessions_route_empty_is_ok(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    assert c.get("/api/sessions").json() == []


# ---------------------------------------------------------------------------
# SSE
# ---------------------------------------------------------------------------


def test_sse_emits_change_on_journal_append(tmp_path: Path):
    project = seed_project(tmp_path)
    ws = project / ".test-commander"
    state = sse.snapshot_state(ws)
    changed, _new = sse.detect_change(state, ws)
    assert changed is False, "no change yet"
    (ws / "journal" / "2026-06-01.md").write_text(
        (ws / "journal" / "2026-06-01.md").read_text(encoding="utf-8") + "\n## 10:00:00 — note\n",
        encoding="utf-8",
    )
    changed, _new = sse.detect_change(state, ws)
    assert changed is True, "a journal append must register as a workspace change"


def test_sse_endpoint_streams_event_stream(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    with c.stream("GET", "/api/events?max_events=1") as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = "".join(resp.iter_text())
    assert "event:" in body


# ---------------------------------------------------------------------------
# Proposal generation (read-only)
# ---------------------------------------------------------------------------


def test_proposal_returns_card_never_executes(tmp_path: Path):
    c = client_for(seed_project(tmp_path))
    before = workspace_snapshot(tmp_path / "proj")
    resp = c.post("/api/proposals", json={"intent": "generate BDD for sign-in"}).json()
    assert resp["kind"] == "proposal"
    assert resp["command"].startswith("/tc:")
    assert "execute" not in resp or resp.get("executed") is False
    assert workspace_snapshot(tmp_path / "proj") == before, "a proposal must not mutate anything"


def test_propose_maps_intents():
    assert proposals.propose("please generate bdd").command == "/tc:generate-bdd"
    assert proposals.propose("what should we automate?").command == "/tc:automation-plan"
    assert proposals.propose("anything else").kind == "proposal"


# ---------------------------------------------------------------------------
# Read-only boundary
# ---------------------------------------------------------------------------


def test_all_read_routes_leave_workspace_unchanged(tmp_path: Path):
    project = seed_project(tmp_path)
    c = client_for(project)
    before = workspace_snapshot(project)
    for route in ("/api/dashboard", "/api/requirements", "/api/runs", "/api/journal",
                  "/api/evidence", "/api/quality-report", "/api/sessions"):
        assert c.get(route).status_code == 200
    assert workspace_snapshot(project) == before


# ---------------------------------------------------------------------------
# /tc:web-sync
# ---------------------------------------------------------------------------


def test_web_sync_uninitialized_refused(tmp_path: Path):
    assert web_sync.main([str(tmp_path / "nope")]) == 2


def test_web_sync_reconciles_index(tmp_path: Path):
    project = seed_project(tmp_path)
    assert web_sync.main([str(project)]) == 0
    assert config.index_db_path(project).is_file()
