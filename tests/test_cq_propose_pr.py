"""Step 13.4 - /tc:propose-tests + /tc:create-test-pr.

/tc:propose-tests proposes new BDD/automation for the coverage gaps (reusing the
Phase-5/6 generators as proposals). /tc:create-test-pr opens a clearly-labeled
pull request through the Phase-10.5 pipeline, gated by the configured autonomy
mode: a below-threshold mode (0-2) cannot open a PR; mode 3+ opens a labeled PR
(auto-approving the code-write through the pipeline, recorded in the audit log).
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

import create_test_pr  # noqa: E402
import propose_tests  # noqa: E402
from agent_adapters.mock_agent import MockAgentAdapter  # noqa: E402
from governance import audit  # noqa: E402

from continuous.autonomy import auto_approves, can_open_pr  # noqa: E402


def seed_basic(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    (project / ".test-commander" / "continuous").mkdir(parents=True)
    return project


def seed_governed(tmp_path: Path, mode: int) -> Path:
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    shutil.copytree(SEEDED_WEB, ws)
    (ws / "policy").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "approvals").mkdir(parents=True, exist_ok=True)
    (ws / "audit" / "actions.jsonl").touch()
    (ws / "continuous").mkdir(parents=True, exist_ok=True)
    (ws / "continuous" / "config.yaml").write_text(
        f"schema: tc-continuous/v1\nautonomy_mode: {mode}\npr_label: test-commander/auto\n",
        encoding="utf-8",
    )
    return project


# ---------------------------------------------------------------------------
# Autonomy gate primitives
# ---------------------------------------------------------------------------


def test_only_modes_3_and_4_can_open_prs():
    assert not can_open_pr(0) and not can_open_pr(1) and not can_open_pr(2)
    assert can_open_pr(3) and can_open_pr(4)


def test_destructive_and_admin_never_auto_approve():
    for mode in range(5):
        assert not auto_approves(mode, "destructive")
        assert not auto_approves(mode, "admin")


# ---------------------------------------------------------------------------
# /tc:propose-tests
# ---------------------------------------------------------------------------


def test_propose_writes_a_proposal_per_gap(tmp_path: Path):
    project = seed_basic(tmp_path)
    result = propose_tests.propose(project, gaps=["search"])
    assert "search" in result["proposals"]
    assert (project / ".test-commander" / "continuous" / "proposals" / "search.md").is_file()


def test_propose_reads_gaps_from_coverage_gaps_json(tmp_path: Path):
    project = seed_basic(tmp_path)
    import json

    (project / ".test-commander" / "continuous" / "coverage-gaps.json").write_text(
        json.dumps({"gaps": [{"feature": "search", "reason": "not automated"}], "covered": []}),
        encoding="utf-8",
    )
    result = propose_tests.propose(project)
    assert result["proposals"] == ["search"]


def test_propose_refuses_uninitialized(tmp_path: Path):
    assert propose_tests.main([str(tmp_path / "nope")]) == 2


# ---------------------------------------------------------------------------
# /tc:create-test-pr - gated by mode
# ---------------------------------------------------------------------------


def test_create_pr_blocked_for_mode_0(tmp_path: Path):
    project = seed_governed(tmp_path, mode=0)
    result = create_test_pr.create_pr(project, gap_feature="sign-in", adapter=MockAgentAdapter())
    assert result["opened"] is False
    assert "cannot open" in result["reason"].lower()
    assert audit.read_entries(project) == []


def test_create_pr_blocked_for_mode_2(tmp_path: Path):
    project = seed_governed(tmp_path, mode=2)
    result = create_test_pr.create_pr(project, gap_feature="sign-in", adapter=MockAgentAdapter())
    assert result["opened"] is False
    assert audit.read_entries(project) == []


def test_create_pr_opens_labeled_pr_at_mode_3(tmp_path: Path):
    project = seed_governed(tmp_path, mode=3)
    result = create_test_pr.create_pr(project, gap_feature="sign-in", adapter=MockAgentAdapter())
    assert result["opened"] is True
    assert result["label"] == "test-commander/auto"
    assert "test-commander/auto" in result["title"]
    # The PR was opened through the pipeline: one audit entry.
    assert len(audit.read_entries(project)) == 1


def test_create_pr_persists_the_bundle(tmp_path: Path):
    project = seed_governed(tmp_path, mode=4)
    create_test_pr.create_pr(project, gap_feature="sign-in", adapter=MockAgentAdapter())
    assert (project / ".test-commander" / "continuous" / "pr.json").is_file()


def test_create_pr_refuses_uninitialized(tmp_path: Path):
    assert create_test_pr.main([str(tmp_path / "nope"), "--feature", "sign-in"]) == 2
