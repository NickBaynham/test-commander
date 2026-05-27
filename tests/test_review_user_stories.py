"""Step 2.3 — /tc:review-user-stories helper tests.

Test contract per planning/plan.md Step 2.3:
  - Uninitialized workspace refused.
  - Fresh workspace with no US-bearing file: writes "no user stories found",
    exits 0.
  - Seeded fixture (only user-stories.md copied) writes
    `requirements/user-story-review.md`.
  - Every INVEST letter produces >= 1 finding traced to the seeded US-NNN tagged
    with that letter (US-001 invest-independent, US-002 invest-negotiable,
    US-003 invest-valuable, US-004 invest-estimable, US-005 invest-small,
    US-006 invest-testable).
  - All 6 fixture stories flag `needs-acceptance-criteria` (none cite AC-NNN).
  - Role-action-benefit shape violation is flagged for a synthetic
    malformed story (no "As a" prefix).
  - Idempotent re-run: review byte-identical.
  - Stories with AC pointers (`AC-\\d+`) do NOT flag `needs-acceptance-criteria`.
"""

import shutil
from pathlib import Path

import init_workspace
import pytest
import review_user_stories

REPO = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-flawed-requirements"
FIXTURE_USER_STORIES = FIXTURE_DIR / "user-stories.md"

INVEST_TO_US = {
    "invest-independent": "US-001",
    "invest-negotiable": "US-002",
    "invest-valuable": "US-003",
    "invest-estimable": "US-004",
    "invest-small": "US-005",
    "invest-testable": "US-006",
}


def _init_workspace(tmp_path: Path) -> Path:
    init_workspace.init_workspace(tmp_path)
    return tmp_path / ".test-commander"


def _seed_user_stories(workspace: Path, source: Path = FIXTURE_USER_STORIES) -> Path:
    target = workspace / "documents" / "uploaded" / source.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(source, target)
    return target


def test_uninitialized_workspace_refused(tmp_path):
    with pytest.raises(review_user_stories.UninitializedWorkspaceError):
        review_user_stories.review(tmp_path)


def test_no_user_stories_writes_empty_review(tmp_path):
    workspace = _init_workspace(tmp_path)
    result = review_user_stories.review(tmp_path)
    assert result.story_count == 0
    review_path = workspace / "requirements" / "user-story-review.md"
    assert "no user stories found" in review_path.read_text(encoding="utf-8").lower()


def test_seeded_fixture_writes_review_artifact(tmp_path):
    workspace = _init_workspace(tmp_path)
    _seed_user_stories(workspace)
    result = review_user_stories.review(tmp_path)
    assert (workspace / "requirements" / "user-story-review.md").is_file()
    assert result.story_count == 6


def test_every_invest_letter_produces_finding(tmp_path):
    workspace = _init_workspace(tmp_path)
    _seed_user_stories(workspace)
    result = review_user_stories.review(tmp_path)
    findings_by_dim: dict[str, set[str]] = {}
    for f in result.findings:
        findings_by_dim.setdefault(f.dimension, set()).add(f.story_id)
    missing = []
    for dim, expected_us in INVEST_TO_US.items():
        seen = findings_by_dim.get(dim, set())
        if expected_us not in seen:
            missing.append(f"{dim} (expected {expected_us}, got {sorted(seen)})")
    assert not missing, "missing INVEST findings: " + "; ".join(missing)


def test_all_fixture_stories_flag_needs_acceptance_criteria(tmp_path):
    workspace = _init_workspace(tmp_path)
    _seed_user_stories(workspace)
    result = review_user_stories.review(tmp_path)
    needs_ac = {f.story_id for f in result.findings if f.dimension == "needs-acceptance-criteria"}
    expected = {f"US-{i:03d}" for i in range(1, 7)}
    assert expected.issubset(needs_ac), (
        f"every fixture story should flag needs-acceptance-criteria; missing: {expected - needs_ac}"
    )


def test_story_with_ac_pointer_does_not_flag_needs_acceptance_criteria(tmp_path):
    workspace = _init_workspace(tmp_path)
    uploaded = workspace / "documents" / "uploaded"
    uploaded.mkdir(parents=True, exist_ok=True)
    (uploaded / "custom.md").write_text(
        "US-200: As a user, I want to export reports, So that I can share results. AC-001.\n",
        encoding="utf-8",
    )
    result = review_user_stories.review(tmp_path)
    needs_ac = {f.story_id for f in result.findings if f.dimension == "needs-acceptance-criteria"}
    assert "US-200" not in needs_ac, (
        "story with AC pointer should not flag needs-acceptance-criteria"
    )


def test_role_action_benefit_shape_violation_is_flagged(tmp_path):
    workspace = _init_workspace(tmp_path)
    uploaded = workspace / "documents" / "uploaded"
    uploaded.mkdir(parents=True, exist_ok=True)
    (uploaded / "custom.md").write_text(
        "US-300: Make the system faster and better.\n",
        encoding="utf-8",
    )
    result = review_user_stories.review(tmp_path)
    shape_findings = {
        f.story_id for f in result.findings if f.dimension == "role-action-benefit"
    }
    assert "US-300" in shape_findings, (
        "story without As-a/I-want/So-that shape should flag role-action-benefit"
    )


def test_seeded_stories_pass_role_action_benefit_check(tmp_path):
    workspace = _init_workspace(tmp_path)
    _seed_user_stories(workspace)
    result = review_user_stories.review(tmp_path)
    shape_findings = {
        f.story_id for f in result.findings if f.dimension == "role-action-benefit"
    }
    assert not shape_findings, (
        f"seeded stories all use the role-action-benefit shape; "
        f"unexpected shape findings: {sorted(shape_findings)}"
    )


def test_idempotent_rerun(tmp_path):
    workspace = _init_workspace(tmp_path)
    _seed_user_stories(workspace)
    review_path = workspace / "requirements" / "user-story-review.md"

    review_user_stories.review(tmp_path)
    review_1 = review_path.read_bytes()

    review_user_stories.review(tmp_path)
    review_2 = review_path.read_bytes()

    assert review_1 == review_2, "user-story-review.md must be byte-identical on re-run"
