"""Step 13.5 - /tc:continuous-quality-check + the five autonomy-mode gates.

The orchestrator runs watch -> impact -> coverage-gap -> propose (read-only
analysis), then opens labeled PRs for the gaps only when the configured autonomy
mode allows it. The five mode gates map to the Phase-10.5 auto-approval levels:
each mode auto-approves exactly its levels and no more; mode 0 cannot open PRs;
nothing above the configured mode executes without explicit human approval.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "runtime"))
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
SEEDED_WEB = REPO / "tests" / "fixtures" / "seeded-web"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-continuous"

import continuous_quality_check  # noqa: E402
from agent_adapters.mock_agent import MockAgentAdapter  # noqa: E402
from governance import audit  # noqa: E402

from continuous.autonomy import auto_approves, can_open_pr  # noqa: E402

LEVELS = ("read-only", "safe-write", "code-write", "execute-tests",
          "external-network", "destructive", "admin")

# The cumulative auto-approval set per mode (read-only is always allowed).
EXPECTED = {
    0: set(),
    1: {"safe-write"},
    2: {"safe-write", "execute-tests"},
    3: {"safe-write", "execute-tests", "code-write"},
    4: {"safe-write", "execute-tests", "code-write", "external-network"},
}


def seed(tmp_path: Path, mode: int, *, governed: bool) -> Path:
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    if governed:
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
# The five autonomy-mode gates (the auto-approval matrix)
# ---------------------------------------------------------------------------


def test_each_mode_auto_approves_exactly_its_levels():
    for mode, expected in EXPECTED.items():
        approved = {lvl for lvl in LEVELS if lvl != "read-only" and auto_approves(mode, lvl)}
        assert approved == expected, f"mode {mode}: {approved} != {expected}"


def test_read_only_is_always_allowed():
    for mode in EXPECTED:
        assert auto_approves(mode, "read-only")


def test_destructive_and_admin_never_auto_approve():
    for mode in EXPECTED:
        assert not auto_approves(mode, "destructive")
        assert not auto_approves(mode, "admin")


def test_only_modes_3_and_4_can_open_prs():
    assert [m for m in EXPECTED if can_open_pr(m)] == [3, 4]


# ---------------------------------------------------------------------------
# /tc:continuous-quality-check orchestrator
# ---------------------------------------------------------------------------


def test_check_runs_full_analysis(tmp_path: Path):
    project = seed(tmp_path, mode=0, governed=False)
    result = continuous_quality_check.check(project, diff_path=FIXTURE / "pr-diff.txt")
    assert set(result["impact"]["features"]) == {"sign-in", "search"}
    assert {g["feature"] for g in result["gaps"]["gaps"]} == {"search"}
    assert "search" in result["proposals"]


def test_mode_0_opens_no_pr_and_writes_no_audit(tmp_path: Path):
    project = seed(tmp_path, mode=0, governed=True)
    result = continuous_quality_check.check(
        project, diff_path=FIXTURE / "pr-diff.txt", adapter=MockAgentAdapter()
    )
    assert result["prs"] == []
    assert audit.read_entries(project) == []


def test_mode_3_opens_a_labeled_pr_for_the_gap(tmp_path: Path):
    project = seed(tmp_path, mode=3, governed=True)
    result = continuous_quality_check.check(
        project, diff_path=FIXTURE / "pr-diff.txt", adapter=MockAgentAdapter()
    )
    opened = [pr for pr in result["prs"] if pr["opened"]]
    assert opened and opened[0]["feature"] == "search"
    assert opened[0]["label"] == "test-commander/auto"
    # The gated execution went through the pipeline: one audit entry.
    assert len(audit.read_entries(project)) == 1


def test_check_refuses_uninitialized(tmp_path: Path):
    assert continuous_quality_check.main(
        [str(tmp_path / "nope"), "--diff", str(FIXTURE / "pr-diff.txt")]
    ) == 2
