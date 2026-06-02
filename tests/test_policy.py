"""Step 10.5.3 - the permission policy engine (7 levels, role-aware).

Classifies every request into one of the seven levels and resolves it against
the role's allowed levels (default deny). Unknown actions default to read-only.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime"))
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"

from governance import policy  # noqa: E402


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    shutil.copytree(SEEDED_WEB, project / ".test-commander")
    return project


def test_seven_levels_defined():
    assert policy.LEVELS == (
        "read-only", "safe-write", "code-write", "execute-tests",
        "external-network", "destructive", "admin",
    )


def test_classify_maps_requests_to_levels():
    assert policy.classify("show me the quality report") == "read-only"
    assert policy.classify("review these requirements") == "safe-write"
    assert policy.classify("generate playwright tests for sign-in") == "code-write"
    assert policy.classify("run the sign-in regression tests") == "execute-tests"
    assert policy.classify("explore the staging site") == "external-network"
    assert policy.classify("delete all evidence") == "destructive"
    assert policy.classify("manage the provider credentials") == "admin"


def test_unknown_action_defaults_read_only():
    assert policy.classify("hmm what about the weather") == "read-only"


def test_roles_default_deny():
    assert policy.allows("Viewer", "read-only") is True
    assert policy.allows("Viewer", "destructive") is False
    assert policy.allows("Automation Engineer", "code-write") is True
    assert policy.allows("Automation Engineer", "admin") is False
    assert policy.allows("Admin", "admin") is True
    # Unknown role -> default deny.
    assert policy.allows("Stranger", "read-only") is False


def test_decide_blocks_unsafe_for_viewer(tmp_path: Path):
    project = seed_project(tmp_path)
    decision = policy.decide("delete all evidence", "Viewer", project)
    assert decision.level == "destructive"
    assert decision.allowed is False


def test_decide_allows_safe_write_for_tester(tmp_path: Path):
    project = seed_project(tmp_path)
    decision = policy.decide("review these requirements", "Tester", project)
    assert decision.level == "safe-write"
    assert decision.allowed is True


def test_permissions_yaml_override(tmp_path: Path):
    project = seed_project(tmp_path)
    (project / ".test-commander" / "policy").mkdir(parents=True, exist_ok=True)
    (project / ".test-commander" / "policy" / "permissions.yaml").write_text(
        "Viewer:\n  - read-only\n  - destructive\n", encoding="utf-8"
    )
    # The override grants Viewer destructive in this deployment.
    assert policy.allows("Viewer", "destructive", project) is True
