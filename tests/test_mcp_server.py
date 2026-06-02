"""Step 11.3 - MCP server + schema-first tool definitions.

The MCP server is a lightweight, schema-first registry. Every tool ships an
explicit JSON schema; a tool above read-only dispatches into the same
Phase-10.5 governance pipeline the console and Runtime API use. There is no
direct-execution backdoor.

A sample in-process client drives the server's `dispatch()` (the message handler
the stdio transport wraps): initialize -> tools/list -> tools/call, exactly as an
MCP client would over stdio.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime"))
sys.path.insert(0, str(REPO / "apps" / "mcp"))
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"
SEEDED_MCP = REPO / "tests" / "fixtures" / "seeded-mcp"

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


class SampleClient:
    """An in-process MCP client: sends protocol messages, reads responses."""

    def __init__(self, project_root: Path, adapter=None):
        self.project_root = project_root
        self.adapter = adapter or MockAgentAdapter()

    def send(self, method: str, params: dict | None = None) -> dict:
        return server.dispatch(
            {"method": method, "params": params or {}},
            project_root=self.project_root,
            adapter=self.adapter,
        )

    def list_tools(self) -> list[dict]:
        return self.send("tools/list")["tools"]

    def call(self, name: str, arguments: dict | None = None) -> dict:
        return self.send("tools/call", {"name": name, "arguments": arguments or {}})


# ---------------------------------------------------------------------------
# Schema-first catalog
# ---------------------------------------------------------------------------


def test_tools_are_schema_first():
    for tool in server.tools():
        assert tool["name"].startswith("tc_")
        assert isinstance(tool["description"], str) and tool["description"].strip()
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert "properties" in schema


def test_expected_tools_present():
    names = {t["name"] for t in server.tools()}
    assert {"tc_status", "tc_plan", "tc_run_command"} <= names


# ---------------------------------------------------------------------------
# Protocol round trip
# ---------------------------------------------------------------------------


def test_initialize_handshake(tmp_path: Path):
    c = SampleClient(seed_project(tmp_path))
    resp = c.send("initialize")
    assert resp["serverInfo"]["name"] == "test-commander"
    assert resp["capabilities"]["tools"] is not None


def test_tools_list_matches_registry(tmp_path: Path):
    c = SampleClient(seed_project(tmp_path))
    assert [t["name"] for t in c.list_tools()] == [t["name"] for t in server.tools()]


def test_unknown_tool_is_an_error(tmp_path: Path):
    c = SampleClient(seed_project(tmp_path))
    resp = c.call("tc_nonexistent")
    assert resp.get("isError") is True


def test_unknown_argument_is_rejected(tmp_path: Path):
    c = SampleClient(seed_project(tmp_path))
    resp = c.call("tc_plan", {"request": "what is the status", "bogus": 1})
    assert resp.get("isError") is True


# ---------------------------------------------------------------------------
# Tool behavior - read-only tools
# ---------------------------------------------------------------------------


def test_tc_status_advertises_levels(tmp_path: Path):
    c = SampleClient(seed_project(tmp_path))
    result = c.call("tc_status")["result"]
    assert len(result["permission_levels"]) == 7
    assert result["server"] == "test-commander"


def test_tc_plan_is_a_read_only_dry_run(tmp_path: Path):
    project = seed_project(tmp_path)
    c = SampleClient(project)
    result = c.call(
        "tc_plan", {"request": "generate playwright tests for sign-in", "role": "Admin"}
    )["result"]
    assert result["level"] == "code-write"
    assert result["command"] == "/tc:automate"
    # A dry run never executes and never audits.
    assert audit.read_entries(project) == []


# ---------------------------------------------------------------------------
# Tool gating - tc_run_command above read-only
# ---------------------------------------------------------------------------


def test_tc_run_command_blocks_denied(tmp_path: Path):
    project = seed_project(tmp_path)
    c = SampleClient(project)
    resp = c.call("tc_run_command", {"request": "delete all evidence", "role": "Viewer"})
    result = resp["result"]
    assert result["blocked"] is True
    assert result["executed"] is False
    assert audit.read_entries(project) == []


def test_tc_run_command_holds_without_approval(tmp_path: Path):
    project = seed_project(tmp_path)
    c = SampleClient(project)
    result = c.call(
        "tc_run_command",
        {"request": "generate playwright tests for sign-in", "role": "Automation Engineer"},
    )["result"]
    assert result["requires_approval"] is True
    assert result["executed"] is False
    assert audit.read_entries(project) == []


def test_tc_run_command_runs_with_approval(tmp_path: Path):
    project = seed_project(tmp_path)
    c = SampleClient(project)
    result = c.call(
        "tc_run_command",
        {
            "request": "generate playwright tests for sign-in",
            "role": "Automation Engineer",
            "approve": True,
            "approver": "maintainer",
        },
    )["result"]
    assert result["executed"] is True
    assert result["command"] == "/tc:automate"
    assert len(audit.read_entries(project)) == 1


# ---------------------------------------------------------------------------
# Seeded fixture round trip
# ---------------------------------------------------------------------------


def test_seeded_fixture_round_trips(tmp_path: Path):
    calls = yaml.safe_load((SEEDED_MCP / "tool-calls.yaml").read_text(encoding="utf-8"))
    for call in calls:
        project = seed_project(tmp_path / f"c{calls.index(call)}")
        c = SampleClient(project)
        result = c.call(call["tool"], call["arguments"])["result"]
        if call["tool"] == "tc_status":
            assert result["permission_levels"]
            continue
        assert result["level"] == call["expected_level"], call
        if call["tool"] == "tc_run_command":
            # Unsafe calls are refused before the agent; safe ones are not blocked.
            assert result["blocked"] is bool(call["unsafe"])
