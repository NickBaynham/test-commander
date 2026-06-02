"""Step 10.4 - the MVP pages + /tc:web-init + /tc:web-start.

The Next.js frontend is Node-managed; its vitest/Playwright lanes run under
`make run`/docker (Step 10.8). Here a structural test asserts the page tree, the
per-page API wiring, the nav, and the SSE live-update component, plus the two
plugin helpers. This keeps the frontend covered by the existing pytest gate
without booting Node.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "apps" / "api"))
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
WEB = REPO / "apps" / "web"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-web"

import tcweb.config as config  # noqa: E402
import web_init  # noqa: E402
import web_start  # noqa: E402


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    shutil.copytree(FIXTURE, project / ".test-commander")
    return project


# ---------------------------------------------------------------------------
# Pages + API wiring
# ---------------------------------------------------------------------------

# (route dir, the API path the page reads)
PAGES = {
    "": "/api/dashboard",
    "quality-report": "/api/quality-report",
    "journal": "/api/journal",
    "sessions": "/api/sessions",
    "requirements": "/api/requirements",
    "runs": "/api/runs",
    "evidence": "/api/evidence",
    "settings": None,  # static config page, no fetch required
}


def _page_path(route: str) -> Path:
    return WEB / "app" / route / "page.tsx" if route else WEB / "app" / "page.tsx"


def test_every_mvp_page_exists():
    for route in PAGES:
        assert _page_path(route).is_file(), f"missing page app/{route}/page.tsx"


def test_each_page_reads_its_api():
    for route, api in PAGES.items():
        if api is None:
            continue
        text = _page_path(route).read_text(encoding="utf-8")
        assert api in text, f"app/{route}/page.tsx must read {api}"


def test_nav_links_every_page():
    nav = (WEB / "components" / "Nav.tsx").read_text(encoding="utf-8")
    for route in ("quality-report", "journal", "sessions", "requirements", "runs", "evidence",
                  "settings"):
        assert f"/{route}" in nav, f"Nav must link /{route}"


def test_sse_live_update_component_uses_event_source():
    live = (WEB / "components" / "LiveBadge.tsx").read_text(encoding="utf-8")
    assert "EventSource" in live, "the live-update component must subscribe to SSE"
    assert "/api/events" in live


def test_dashboard_shows_live_badge():
    page = _page_path("").read_text(encoding="utf-8")
    assert "LiveBadge" in page, "the dashboard must surface the SSE live badge"


# ---------------------------------------------------------------------------
# /tc:web-init
# ---------------------------------------------------------------------------


def test_web_init_uninitialized_refused(tmp_path: Path):
    assert web_init.main([str(tmp_path / "nope")]) == 2


def test_web_init_writes_console_config_idempotently(tmp_path: Path):
    project = seed_project(tmp_path)
    assert web_init.main([str(project)]) == 0
    cfg = config.workspace_dir(project) / ".web" / "console.json"
    assert cfg.is_file()
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert "api_base" in data and "web_port" in data
    first = cfg.read_bytes()
    assert web_init.main([str(project)]) == 0  # idempotent
    assert cfg.read_bytes() == first


# ---------------------------------------------------------------------------
# /tc:web-start
# ---------------------------------------------------------------------------


def test_web_start_prints_command_without_executing(tmp_path: Path, capsys):
    project = seed_project(tmp_path)
    rc = web_start.main([str(project)])  # no --up: prints the command, does not run docker
    assert rc == 0
    out = capsys.readouterr().out
    assert "docker compose up" in out


def test_web_start_refuses_real_up_under_pytest(tmp_path: Path):
    import pytest

    project = seed_project(tmp_path)
    with pytest.raises(web_start.ComposeRefusedError):
        web_start.main([str(project), "--up"])
