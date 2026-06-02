"""Step 11.1 - Phase 11 runtime API + MCP server scaffold.

Asserts the `tc-mcp` skill, the `apps/mcp/` server package (health check + tool
registry placeholder), the expanded Runtime API skeleton (`/api/runtime/info`),
and the seeded-mcp fixture. The Runtime API routes land in 11.2, the MCP tools
in 11.3, and the per-level permission gates in 11.4; this is the scaffold those
sub-steps build toward.

The MCP server is a lightweight, schema-first tool registry (no heavy SDK
dependency): every tool dispatches into the same Phase-10.5 governance pipeline
the console uses. There is no direct-execution backdoor.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "apps" / "mcp"))
sys.path.insert(0, str(REPO / "apps" / "api"))

SKILLS_ROOT = REPO / "plugins" / "test-commander" / "skills"
TCM = SKILLS_ROOT / "tc-mcp"
MCP_APP = REPO / "apps" / "mcp"
API_APP = REPO / "apps" / "api"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-mcp"
VERIFY_SKILLS = REPO / "scripts" / "verify_skills.py"

SUBDIRS = ["methodology", "templates"]
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    match = FRONTMATTER_RE.match(text)
    assert match, "expected a YAML frontmatter block delimited by ---"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict), "frontmatter must parse to a mapping"
    return data


# ---------------------------------------------------------------------------
# tc-mcp skill
# ---------------------------------------------------------------------------


def test_skill_directory_exists():
    assert TCM.is_dir(), "expected skills/tc-mcp/"


def test_skill_md_frontmatter_parses_strict_yaml():
    data = parse_frontmatter((TCM / "SKILL.md").read_text(encoding="utf-8"))
    assert data.get("name") == "tc-mcp"
    assert isinstance(data.get("description"), str) and data["description"].strip()


def test_skill_md_body_references_tools_and_the_pipeline():
    text = (TCM / "SKILL.md").read_text(encoding="utf-8").lower()
    for token in ("tool", "pipeline", "permission", "schema"):
        assert token in text, f"tc-mcp/SKILL.md must reference {token}"


def test_skill_subdirectories_exist():
    for sub in SUBDIRS:
        assert (TCM / sub).is_dir(), f"expected skills/tc-mcp/{sub}/"


# ---------------------------------------------------------------------------
# apps/mcp server package
# ---------------------------------------------------------------------------


def test_mcp_package_exists():
    assert (MCP_APP / "tcmcp" / "__init__.py").is_file()
    assert (MCP_APP / "tcmcp" / "server.py").is_file()
    assert (MCP_APP / "Dockerfile").is_file()


def test_mcp_server_health_check():
    from tcmcp import server

    health = server.health()
    assert health["status"] == "ok"
    assert health["server"] == "test-commander"


def test_mcp_server_tool_registry_is_callable():
    from tcmcp import server

    # The registry exists and returns a list (populated with schema-first tools
    # in 11.3); the scaffold returns an empty list, never raises.
    assert isinstance(server.tools(), list)


# ---------------------------------------------------------------------------
# Expanded Runtime API skeleton
# ---------------------------------------------------------------------------


def test_runtime_api_info_route():
    import tcweb.main as main

    client = TestClient(main.create_app(project_root=REPO))
    resp = client.get("/api/runtime/info")
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "tc-runtime-api"
    # The seven permission levels are advertised so a client can self-describe.
    assert body["permission_levels"] == [
        "read-only", "safe-write", "code-write", "execute-tests",
        "external-network", "destructive", "admin",
    ]


# ---------------------------------------------------------------------------
# seeded-mcp fixture
# ---------------------------------------------------------------------------


def test_seeded_mcp_fixture():
    assert (FIXTURE / "README.md").is_file()
    calls = yaml.safe_load((FIXTURE / "tool-calls.yaml").read_text(encoding="utf-8"))
    assert isinstance(calls, list) and calls, "fixture must carry sample tool calls"
    assert any(c.get("unsafe") for c in calls), "fixture must carry an unsafe tool call"


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


def test_verify_skills_catalog_has_tc_mcp_at_phase_11():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    assert re.search(r'"tc-mcp":\s*11', text), "CATALOG must map tc-mcp -> 11"
