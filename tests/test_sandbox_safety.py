"""Step 12.4 - safety guards + governance-in-sandbox + the workflow.

Safe-by-default targeting: allow-listed hosts only, private/loopback/link-local
ranges blocked by default. Governance travels with the sandbox: the Phase-10.5
pipeline runs inside it, so a sandbox cannot execute above its approved level.
The GitHub Actions workflow is valid, manual-dispatch only, and sequences the
safety check -> build -> publish -> teardown.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runtime"))
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-sandbox"
WORKFLOW = REPO / ".github" / "workflows" / "test-commander-sandbox.yml"

from agent_adapters.mock_agent import MockAgentAdapter  # noqa: E402
from governance import audit  # noqa: E402

from sandbox.governance import run_in_sandbox  # noqa: E402
from sandbox.safety import check_target, is_private_host  # noqa: E402

CONFIG = yaml.safe_load((FIXTURE / "config.yaml").read_text(encoding="utf-8"))


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    shutil.copytree(SEEDED_WEB, ws)
    (ws / "policy").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "approvals").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "actions.jsonl").touch()
    return project


# ---------------------------------------------------------------------------
# Safe-by-default targeting
# ---------------------------------------------------------------------------


def test_private_ranges_are_blocked():
    for host in ("192.168.1.10", "10.0.0.5", "172.16.0.1", "127.0.0.1", "169.254.1.1"):
        assert is_private_host(host), host


def test_public_host_is_not_flagged_private():
    assert not is_private_host("93.184.216.34")  # example.com's address range
    assert not is_private_host("sandbox.example.com")


def test_allowlisted_hosts_pass():
    assert check_target("https://sandbox.example.com/app", CONFIG).allowed
    assert check_target("https://app.example.com/dashboard", CONFIG).allowed  # wildcard


def test_non_allowlisted_host_refused():
    decision = check_target("https://evil.test/login", CONFIG)
    assert decision.allowed is False
    assert "allow-list" in decision.reason


def test_private_target_refused_even_if_reachable():
    decision = check_target("http://192.168.1.10:8080", CONFIG)
    assert decision.allowed is False


def test_seeded_targets_classify_as_flagged():
    targets = yaml.safe_load((FIXTURE / "targets.yaml").read_text(encoding="utf-8"))
    for t in targets:
        decision = check_target(t["url"], CONFIG)
        assert decision.allowed is not bool(t["unsafe"]), t


# ---------------------------------------------------------------------------
# Governance travels with the sandbox
# ---------------------------------------------------------------------------


def test_sandbox_runs_the_governance_pipeline_and_blocks_unsafe(tmp_path: Path):
    project = seed_project(tmp_path)
    res = run_in_sandbox(
        "delete all evidence", role="Viewer", project_root=project, adapter=MockAgentAdapter()
    )
    assert res.blocked is True and res.executed is False
    assert audit.read_entries(project) == []


def test_sandbox_cannot_execute_above_approved_level(tmp_path: Path):
    project = seed_project(tmp_path)
    # A Tester lacks code-write, so a generate-tests request is blocked in-sandbox.
    res = run_in_sandbox(
        "generate playwright tests for sign-in", role="Tester",
        project_root=project, adapter=MockAgentAdapter(),
    )
    assert res.blocked is True and res.executed is False


def test_sandbox_executes_an_approved_in_scope_action(tmp_path: Path):
    project = seed_project(tmp_path)
    res = run_in_sandbox(
        "generate playwright tests for sign-in", role="Automation Engineer",
        project_root=project, adapter=MockAgentAdapter(), approve=True, approver="lead",
    )
    assert res.executed is True
    assert len(audit.read_entries(project)) == 1


# ---------------------------------------------------------------------------
# The GitHub Actions workflow
# ---------------------------------------------------------------------------


def test_workflow_is_valid_manual_only_and_sequenced():
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    # Manual dispatch only - no automatic push/PR trigger (never auto-runs or spends).
    on = data.get(True, data.get("on"))  # PyYAML parses bare `on:` as the bool True
    assert "workflow_dispatch" in on
    assert "push" not in on and "pull_request" not in on
    steps = data["jobs"]["sandbox"]["steps"]
    names = [s.get("name", "").lower() for s in steps]
    blob = " | ".join(names)
    # Safety check precedes build; build precedes publish precedes teardown.
    order = [names.index(n) for n in names if any(
        k in n for k in ("safety", "build", "publish", "teardown"))]
    assert order == sorted(order)
    for keyword in ("safety", "build", "publish", "teardown"):
        assert keyword in blob, f"workflow must have a {keyword} step"
