"""Step 10.8 - Phase 10 integration smoke (API layer).

The full docker-compose + Playwright e2e runs under `make web-e2e` (Node +
browsers, outside the hermetic suite). This in-process smoke is the enforced
gate: it drives the whole backend stack (index -> read routes -> SSE -> chat ->
export) against the seeded-web workspace via the FastAPI TestClient and asserts
the Step 10.8 contract: every page route serves data, SSE emits a change, the
chat is read-only + proposal-only, /tc:web-export produces a bundle, the write
boundary holds (only .web/ changes), and PHASE_OWNERSHIP is unaffected.
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

import tcweb.exporter as exporter  # noqa: E402
import tcweb.main as main  # noqa: E402
import web_export  # noqa: E402
import web_index_artifacts  # noqa: E402
import web_init  # noqa: E402
import web_start  # noqa: E402
import web_sync  # noqa: E402
import workspace_state  # noqa: E402

READ_ROUTES = (
    "/api/dashboard", "/api/requirements", "/api/runs", "/api/runs/results",
    "/api/journal", "/api/evidence", "/api/traceability", "/api/quality-report",
    "/api/sessions",
)


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    shutil.copytree(FIXTURE, project / ".test-commander")
    return project


def snapshot_outside_web(project: Path) -> dict:
    ws = project / ".test-commander"
    return {
        p.relative_to(ws): p.read_bytes()
        for p in sorted(ws.rglob("*"))
        if p.is_file() and ".web" not in p.relative_to(ws).parts
    }


def test_phase_ownership_unaffected_by_web_console():
    """The console writes only .web/ (derived); it owns no workspace signal."""
    assert "10" not in workspace_state.PHASE_OWNERSHIP


def test_full_phase_10_workflow(tmp_path: Path):
    project = seed_project(tmp_path)
    outside_before = snapshot_outside_web(project)

    # The five /tc:web-* commands.
    assert web_init.main([str(project)]) == 0
    assert web_index_artifacts.main([str(project)]) == 0
    assert web_sync.main([str(project)]) == 0
    assert web_export.main([str(project)]) == 0
    assert web_start.main([str(project)]) == 0  # dry run, no docker

    client = TestClient(main.create_app(project_root=project))

    # Every page route serves data.
    for route in READ_ROUTES:
        assert client.get(route).status_code == 200, route

    # SSE emits a connected/changed stream.
    with client.stream("GET", "/api/events?max_events=1") as resp:
        assert resp.headers["content-type"].startswith("text/event-stream")
        assert "event:" in "".join(resp.iter_text())

    # Chat is read-only + proposal-only.
    chat = client.post("/api/chat", json={"question": "run the tests now"}).json()
    assert chat["executed"] is False
    assert chat["proposal"] is not None

    # Export produces a bundle.
    written = exporter.export(project)
    assert {p.name for p in written} == {"data.json", "index.html"}

    # Write boundary: nothing outside .web/ changed across the whole workflow.
    assert snapshot_outside_web(project) == outside_before


def test_byte_stable_index_and_export(tmp_path: Path):
    project = seed_project(tmp_path)
    first_export = {p.name: p.read_bytes() for p in exporter.export(project)}
    second_export = {p.name: p.read_bytes() for p in exporter.export(project)}
    assert first_export == second_export
