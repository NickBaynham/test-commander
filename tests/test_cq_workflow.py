"""Step 13.6 - the continuous-quality CI workflow.

The workflow triggers on pull_request / push / schedule / workflow_dispatch and
wires the continuous-quality check into CI: the read-only analysis runs
automatically, and any generated change arrives only as a gated, labeled PR (the
workflow's token is read-only). A simulated PR runs the check at the configured
mode (mode 0 -> advice only, no PR).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runtime"))
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
FIXTURE = REPO / "tests" / "fixtures" / "seeded-continuous"
WORKFLOW = REPO / ".github" / "workflows" / "test-commander-continuous-quality.yml"

import continuous_quality_check  # noqa: E402


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Workflow shape
# ---------------------------------------------------------------------------


def test_workflow_has_the_four_triggers():
    data = _workflow()
    on = data.get(True, data.get("on"))
    for trigger in ("pull_request", "push", "schedule", "workflow_dispatch"):
        assert trigger in on, f"workflow must trigger on {trigger}"


def test_workflow_is_read_only_by_default():
    # Read-only token: generated changes arrive as gated PRs, never a direct push.
    assert _workflow().get("permissions", {}).get("contents") == "read"


def test_workflow_runs_the_continuous_quality_check():
    steps = _workflow()["jobs"]["continuous-quality"]["steps"]
    blob = "\n".join(s.get("run", "") for s in steps)
    assert "continuous_quality_check.py" in blob, "the workflow must run the check helper"


def test_workflow_skips_cleanly_without_a_workspace():
    # The plugin repo has no consuming .test-commander; the check step must guard
    # on the workspace so CI stays green where there is nothing to analyze.
    steps = _workflow()["jobs"]["continuous-quality"]["steps"]
    blob = "\n".join(s.get("run", "") for s in steps)
    assert ".test-commander" in blob


# ---------------------------------------------------------------------------
# Simulated PR runs the check at the configured mode
# ---------------------------------------------------------------------------


def test_simulated_pr_runs_the_check_at_mode_0(tmp_path: Path):
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    (ws / "product-knowledge").mkdir(parents=True)
    (ws / "traceability").mkdir(parents=True)
    (ws / "continuous").mkdir(parents=True)
    shutil.copy(FIXTURE / "impact-map.yaml", ws / "product-knowledge" / "impact-map.yaml")
    shutil.copy(FIXTURE / "coverage.yaml", ws / "traceability" / "coverage.yaml")
    (ws / "continuous" / "config.yaml").write_text(
        "schema: tc-continuous/v1\nautonomy_mode: 0\npr_label: test-commander/auto\n",
        encoding="utf-8",
    )
    result = continuous_quality_check.check(project, diff_path=FIXTURE / "pr-diff.txt")
    assert result["mode"] == "read-only-advisor"
    assert "search" in result["proposals"]
    assert result["prs"] == []  # mode 0: advice only, no PR opened from CI
