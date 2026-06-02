"""Step 13.8 - Phase 13 integration finalization.

The consolidated end-to-end smoke: simulate a PR with a code change and run the
continuous-quality check through the orchestrator. Asserts impact analysis
identifies the expected impacted features and proposes appropriate tests, that
the autonomy-mode boundaries hold (mode 0-2 open no PR; mode 3+ open a labeled
PR), and that PRs are clearly labeled. Pins the verifier state at Phase 13
(`DEFAULT_PHASE_CAP >= 13`, the full catalog PRESENT, UNEXPECTED=0).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runtime"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-continuous"

import continuous_quality_check  # noqa: E402
import verify_skills  # noqa: E402
from agent_adapters.mock_agent import MockAgentAdapter  # noqa: E402
from governance import audit  # noqa: E402

DIFF = FIXTURE / "pr-diff.txt"


def seed(tmp_path: Path, mode: int) -> Path:
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    shutil.copytree(SEEDED_WEB, ws)
    (ws / "policy").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "approvals").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "actions.jsonl").touch()
    (ws / "product-knowledge").mkdir(parents=True, exist_ok=True)
    (ws / "traceability").mkdir(parents=True, exist_ok=True)
    (ws / "continuous").mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE / "impact-map.yaml", ws / "product-knowledge" / "impact-map.yaml")
    shutil.copy(FIXTURE / "coverage.yaml", ws / "traceability" / "coverage.yaml")
    (ws / "continuous" / "config.yaml").write_text(
        f"schema: tc-continuous/v1\nautonomy_mode: {mode}\npr_label: test-commander/auto\n",
        encoding="utf-8",
    )
    return project


# ---------------------------------------------------------------------------
# Verifier state pinned at Phase 13 (full catalog)
# ---------------------------------------------------------------------------


def test_default_phase_cap_at_least_13():
    assert verify_skills.DEFAULT_PHASE_CAP >= 13


def test_full_catalog_present_at_13():
    assert verify_skills.CATALOG["tc-continuous-quality"] == 13
    # The cap covers every catalogued skill -> nothing is ahead-of-schedule.
    assert max(verify_skills.CATALOG.values()) <= verify_skills.DEFAULT_PHASE_CAP


# ---------------------------------------------------------------------------
# Simulated PR end to end
# ---------------------------------------------------------------------------


def test_simulated_pr_impact_and_proposals(tmp_path: Path):
    project = seed(tmp_path, mode=0)
    result = continuous_quality_check.check(
        project, diff_path=DIFF, adapter=MockAgentAdapter()
    )
    # Impact analysis identifies the expected impacted features...
    assert set(result["impact"]["features"]) == {"sign-in", "search"}
    # ...and proposes tests for the gap (search is impacted but not automated).
    assert result["proposals"] == ["search"]
    # Mode 0 (advisor): advice only, no PR, no audit.
    assert result["prs"] == []
    assert audit.read_entries(project) == []


def test_mode_boundaries_hold(tmp_path: Path):
    # Modes 0-2 cannot open a PR; modes 3-4 open a labeled PR.
    for mode in (0, 1, 2):
        project = seed(tmp_path / f"m{mode}", mode)
        result = continuous_quality_check.check(project, diff_path=DIFF, adapter=MockAgentAdapter())
        assert result["prs"] == [], f"mode {mode} must not open a PR"
        assert audit.read_entries(project) == []
    for mode in (3, 4):
        project = seed(tmp_path / f"m{mode}", mode)
        result = continuous_quality_check.check(project, diff_path=DIFF, adapter=MockAgentAdapter())
        opened = [pr for pr in result["prs"] if pr["opened"]]
        assert opened, f"mode {mode} must open a PR"
        assert len(audit.read_entries(project)) == 1


def test_opened_prs_are_clearly_labeled(tmp_path: Path):
    project = seed(tmp_path, mode=3)
    result = continuous_quality_check.check(project, diff_path=DIFF, adapter=MockAgentAdapter())
    opened = [pr for pr in result["prs"] if pr["opened"]]
    assert opened
    for pr in opened:
        assert pr["label"] == "test-commander/auto"
        assert pr["label"] in pr["title"]
