"""Step 10.1 - Phase 10 web console scaffold.

Asserts the `tc-web` skill, the apps/web (Next.js) + apps/api (FastAPI) + runtime
trees, the `make run` docker-compose target, the FastAPI health route, and the
seeded-web fixture. Phase 10 is the first runtime phase: the backend ships under
apps/api and is exercised by the existing pytest gate via the apps/api pythonpath
entry; the frontend manages its own deps under apps/web.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO / "plugins" / "test-commander" / "skills"
TCW = SKILLS_ROOT / "tc-web"
APPS = REPO / "apps"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-web"

COMMANDS = [
    "/tc:web-init",
    "/tc:web-start",
    "/tc:web-sync",
    "/tc:web-index-artifacts",
    "/tc:web-export",
]
SUBDIRS = ["commands", "methodology", "templates"]
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    match = FRONTMATTER_RE.match(text)
    assert match, "expected a YAML frontmatter block delimited by ---"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict), "frontmatter must parse to a mapping"
    return data


# ---------------------------------------------------------------------------
# tc-web skill scaffold
# ---------------------------------------------------------------------------


def test_skill_directory_exists():
    assert TCW.is_dir(), "expected skills/tc-web/"


def test_skill_md_frontmatter_parses_strict_yaml():
    data = parse_frontmatter((TCW / "SKILL.md").read_text(encoding="utf-8"))
    assert data.get("name") == "tc-web"
    desc = data.get("description")
    assert isinstance(desc, str) and desc.strip()


def test_skill_md_body_references_all_five_commands():
    text = (TCW / "SKILL.md").read_text(encoding="utf-8")
    for cmd in COMMANDS:
        assert cmd in text, f"tc-web/SKILL.md body must reference {cmd}"


def test_skill_subdirectories_exist():
    for sub in SUBDIRS:
        assert (TCW / sub).is_dir(), f"expected skills/tc-web/{sub}/"


# ---------------------------------------------------------------------------
# apps/web (Next.js) + apps/api (FastAPI) + runtime trees
# ---------------------------------------------------------------------------


def test_backend_tree_exists():
    assert (APPS / "api" / "tcweb" / "__init__.py").is_file()
    assert (APPS / "api" / "tcweb" / "main.py").is_file()


def test_frontend_tree_exists():
    assert (APPS / "web" / "package.json").is_file()
    pkg = (APPS / "web" / "package.json").read_text(encoding="utf-8")
    assert '"next"' in pkg, "apps/web must depend on Next.js"
    assert (APPS / "web" / "app").is_dir(), "expected the Next.js app/ router dir"


def test_runtime_tree_exists():
    assert (REPO / "runtime").is_dir(), "expected runtime/"


# ---------------------------------------------------------------------------
# make run + docker compose
# ---------------------------------------------------------------------------


def test_make_run_target_present():
    body = (REPO / "Makefile").read_text(encoding="utf-8")
    assert re.search(r"^run:", body, flags=re.MULTILINE)
    assert "docker compose" in body, "make run must bring the stack up via docker compose"


def test_docker_compose_declares_api_and_web():
    compose = (REPO / "docker-compose.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(compose)
    services = data.get("services") or {}
    assert "api" in services, "compose must declare the api service"
    assert "web" in services, "compose must declare the web service"


# ---------------------------------------------------------------------------
# FastAPI health route
# ---------------------------------------------------------------------------


def test_health_route_returns_ok():
    import tcweb.main as main
    from fastapi.testclient import TestClient

    client = TestClient(main.create_app())
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


# ---------------------------------------------------------------------------
# seeded-web fixture
# ---------------------------------------------------------------------------


def test_seeded_web_fixture_exists():
    assert FIXTURE.is_dir(), "expected tests/fixtures/seeded-web/"
    for rel in (
        "project.md",
        "requirements/requirements-inventory.md",
        "quality-report/current-quality-report.md",
        "traceability/test-map.md",
    ):
        assert (FIXTURE / rel).is_file(), f"seeded-web fixture missing {rel}"
    assert list((FIXTURE / "journal").glob("*.md")), "fixture must carry a journal day file"
    assert list((FIXTURE / "runs").glob("RUN-*")), "fixture must carry a run dir"
