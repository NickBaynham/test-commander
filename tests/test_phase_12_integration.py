"""Step 12.6 - Phase 12 integration finalization.

The consolidated end-to-end smoke for the sandbox: the full command lifecycle
through a mocked provider (a CI dry run asserting build -> publish -> teardown
sequencing), the safety-guard refusals, and the governance-in-sandbox assertion.
Also pins the verifier state at Phase 12 (`DEFAULT_PHASE_CAP >= 12`, so
`tc-sandbox` is PRESENT, not UNEXPECTED).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runtime"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-sandbox"

import sandbox_export  # noqa: E402
import sandbox_init  # noqa: E402
import sandbox_launch  # noqa: E402
import sandbox_status  # noqa: E402
import sandbox_stop  # noqa: E402
import sandbox_sync  # noqa: E402
import verify_skills  # noqa: E402
from agent_adapters.mock_agent import MockAgentAdapter  # noqa: E402
from governance import audit  # noqa: E402

from sandbox.governance import run_in_sandbox  # noqa: E402
from sandbox.providers.mock import MockSandboxProvider  # noqa: E402
from sandbox.safety import check_target  # noqa: E402

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
# Verifier state pinned at Phase 12
# ---------------------------------------------------------------------------


def test_default_phase_cap_at_least_12():
    assert verify_skills.DEFAULT_PHASE_CAP >= 12


def test_tc_sandbox_in_catalog_at_12():
    assert verify_skills.CATALOG["tc-sandbox"] == 12


# ---------------------------------------------------------------------------
# Full lifecycle through a mocked provider (CI dry run: build -> publish -> teardown)
# ---------------------------------------------------------------------------


def test_sandbox_lifecycle_end_to_end(tmp_path: Path):
    project = seed_project(tmp_path)
    mock = MockSandboxProvider()

    sandbox_init.init(project)
    assert sandbox_status.status(project)["status"] == "none"

    # Build (launch).
    assert sandbox_launch.launch(project, provider=mock)["status"] == "running"
    assert sandbox_status.status(project)["status"] == "running"

    # Sync.
    assert sandbox_sync.sync(project, provider=mock)["status"] == "running"

    # Publish (export).
    bundle_path = sandbox_export.export(project)
    bundle = yaml.safe_load(bundle_path.read_text(encoding="utf-8"))
    assert "web" in bundle["endpoints"] and bundle["status"] == "running"

    # Teardown (stop).
    assert sandbox_stop.stop(project, provider=mock)["status"] == "stopped"
    assert sandbox_status.status(project)["status"] == "stopped"

    # The provider saw the lifecycle in order (build -> sync -> teardown).
    assert mock.calls == ["launch", "sync", "teardown"]


def test_stop_is_idempotent_end_to_end(tmp_path: Path):
    project = seed_project(tmp_path)
    sandbox_init.init(project)
    mock = MockSandboxProvider()
    sandbox_launch.launch(project, provider=mock)
    sandbox_stop.stop(project, provider=mock)
    sandbox_stop.stop(project, provider=mock)
    assert mock.calls.count("teardown") == 1


# ---------------------------------------------------------------------------
# Safety guards + governance in the sandbox
# ---------------------------------------------------------------------------


def test_safety_guards_refuse_unsafe_targets():
    targets = yaml.safe_load((FIXTURE / "targets.yaml").read_text(encoding="utf-8"))
    for t in targets:
        assert check_target(t["url"], CONFIG).allowed is not bool(t["unsafe"]), t


def test_governance_travels_with_the_sandbox(tmp_path: Path):
    project = seed_project(tmp_path)
    # Blocked: a Viewer cannot run a destructive action in the sandbox.
    assert run_in_sandbox(
        "delete all evidence", role="Viewer", project_root=project, adapter=MockAgentAdapter()
    ).blocked is True
    # Executed: an approved in-scope code-write runs and is audited.
    res = run_in_sandbox(
        "generate playwright tests for sign-in", role="Automation Engineer",
        project_root=project, adapter=MockAgentAdapter(), approve=True, approver="lead",
    )
    assert res.executed is True
    assert len(audit.read_entries(project)) == 1
