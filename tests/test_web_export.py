"""Step 10.6 - /tc:web-export.

Exports the console's current view (quality report + evidence + traceability +
the index data) as a shareable static bundle (data.json + index.html). Read-only
and deterministic; writes only under .web/export/, never a workspace artifact.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "apps" / "api"))
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
FIXTURE = REPO / "tests" / "fixtures" / "seeded-web"

import tcweb.exporter as exporter  # noqa: E402
import web_export  # noqa: E402


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    shutil.copytree(FIXTURE, project / ".test-commander")
    return project


def workspace_snapshot(project: Path) -> dict:
    ws = project / ".test-commander"
    return {
        p.relative_to(ws): p.read_bytes()
        for p in sorted(ws.rglob("*"))
        if p.is_file() and ".web" not in p.relative_to(ws).parts
    }


def test_export_produces_bundle(tmp_path: Path):
    project = seed_project(tmp_path)
    written = exporter.export(project)
    names = {p.name for p in written}
    assert {"data.json", "index.html"} <= names
    data_path = next(p for p in written if p.name == "data.json")
    data = json.loads(data_path.read_text(encoding="utf-8"))
    assert data["quality_facts"]["requirements"] == "3"
    assert len(data["requirements"]) == 3
    assert len(data["runs"]) == 1
    assert len(data["evidence"]) >= 1
    assert len(data["traceability"]) == 4


def test_export_html_renders_facts(tmp_path: Path):
    project = seed_project(tmp_path)
    written = exporter.export(project)
    html = next(p for p in written if p.name == "index.html").read_text(encoding="utf-8")
    assert "<html" in html.lower()
    assert "REQ-001" in html
    assert "RUN-20260601-093000" in html


def test_export_is_deterministic(tmp_path: Path):
    project = seed_project(tmp_path)
    first = {p.name: p.read_bytes() for p in exporter.export(project)}
    second = {p.name: p.read_bytes() for p in exporter.export(project)}
    assert first == second


def test_export_does_not_mutate_workspace(tmp_path: Path):
    project = seed_project(tmp_path)
    before = workspace_snapshot(project)
    exporter.export(project)
    assert workspace_snapshot(project) == before


def test_web_export_uninitialized_refused(tmp_path: Path):
    assert web_export.main([str(tmp_path / "nope")]) == 2


def test_web_export_builds_bundle(tmp_path: Path):
    project = seed_project(tmp_path)
    assert web_export.main([str(project)]) == 0
    assert (project / ".test-commander" / ".web" / "export" / "index.html").is_file()
