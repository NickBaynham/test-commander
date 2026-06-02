"""Step 10.5.5 - the command planner (displayable plan).

Produces an explicit, deterministic plan before execution: command, likely
reads, likely writes, permission level, target environment, expected artifacts,
and the approval-required flag.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime"))

from governance import planner  # noqa: E402


def test_plan_for_code_write_command():
    plan = planner.plan("/tc:automate")
    assert plan.command == "/tc:automate"
    assert plan.level == "code-write"
    assert any("tests/" in w for w in plan.writes)
    assert plan.requires_approval is True


def test_plan_for_safe_write_command():
    plan = planner.plan("/tc:review-requirements")
    assert plan.level == "safe-write"
    assert any("requirements/" in w for w in plan.writes)
    assert plan.requires_approval is False


def test_plan_for_external_network_command():
    plan = planner.plan("/tc:explore")
    assert plan.level == "external-network"
    assert plan.target_environment is not None
    assert plan.requires_approval is True


def test_read_only_plan_has_no_writes():
    plan = planner.plan("read-only")
    assert plan.level == "read-only"
    assert plan.writes == ()
    assert plan.requires_approval is False


def test_plan_is_deterministic():
    assert planner.plan("/tc:automate") == planner.plan("/tc:automate")


def test_plan_carries_reads_and_artifacts():
    plan = planner.plan("/tc:run")
    assert plan.level == "execute-tests"
    assert plan.reads and plan.expected_artifacts
    assert plan.requires_approval is True
