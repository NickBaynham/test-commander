"""Step 2.4 — /tc:review-acceptance-criteria helper tests.

Test contract per planning/plan.md Step 2.4:
  - Uninitialized workspace refused.
  - Fresh workspace with no AC-bearing file: writes "no acceptance criteria
    found", exits 0.
  - Seeded fixture writes `requirements/acceptance-criteria-review.md`.
  - Every AC-rubric dimension produces >= 1 finding traced to the seeded
    AC-NNN-NN tagged with that dimension.
  - AC that references a non-existent story ID is flagged as orphan.
  - AC whose story ID resolves to a parsed user story is NOT flagged orphan.
  - Idempotent re-run: review byte-identical.
"""

import shutil
from pathlib import Path

import init_workspace
import pytest
import review_acceptance_criteria

REPO = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-flawed-requirements"
FIXTURE_ACS = FIXTURE_DIR / "acceptance-criteria.md"
FIXTURE_STORIES = FIXTURE_DIR / "user-stories.md"

DIMENSION_TO_AC = {
    "ac-missing-edge-cases": "AC-001-01",
    "ac-missing-negative-cases": "AC-001-02",
    "ac-untestable-predicate": "AC-002-01",
    "ac-ambiguous-data-rule": "AC-003-01",
    "ac-missing-role-context": "AC-004-01",
}


def _init_workspace(tmp_path: Path) -> Path:
    init_workspace.init_workspace(tmp_path)
    return tmp_path / ".test-commander"


def _seed_acs_and_stories(workspace: Path) -> None:
    uploaded = workspace / "documents" / "uploaded"
    uploaded.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_ACS, uploaded / "acceptance-criteria.md")
    shutil.copy(FIXTURE_STORIES, uploaded / "user-stories.md")


def test_uninitialized_workspace_refused(tmp_path):
    with pytest.raises(review_acceptance_criteria.UninitializedWorkspaceError):
        review_acceptance_criteria.review(tmp_path)


def test_no_acs_writes_empty_review(tmp_path):
    workspace = _init_workspace(tmp_path)
    result = review_acceptance_criteria.review(tmp_path)
    assert result.ac_count == 0
    review_path = workspace / "requirements" / "acceptance-criteria-review.md"
    assert "no acceptance criteria found" in review_path.read_text(encoding="utf-8").lower()


def test_seeded_fixture_writes_review_artifact(tmp_path):
    workspace = _init_workspace(tmp_path)
    _seed_acs_and_stories(workspace)
    result = review_acceptance_criteria.review(tmp_path)
    assert (workspace / "requirements" / "acceptance-criteria-review.md").is_file()
    assert result.ac_count == 5


def test_every_ac_rubric_dimension_produces_finding(tmp_path):
    workspace = _init_workspace(tmp_path)
    _seed_acs_and_stories(workspace)
    result = review_acceptance_criteria.review(tmp_path)
    findings_by_dim: dict[str, set[str]] = {}
    for f in result.findings:
        findings_by_dim.setdefault(f.dimension, set()).add(f.ac_id)
    missing = []
    for dim, expected_ac in DIMENSION_TO_AC.items():
        seen = findings_by_dim.get(dim, set())
        if expected_ac not in seen:
            missing.append(f"{dim} (expected {expected_ac}, got {sorted(seen)})")
    assert not missing, "missing AC-rubric findings: " + "; ".join(missing)


def test_orphan_ac_flagged_when_story_missing(tmp_path):
    workspace = _init_workspace(tmp_path)
    uploaded = workspace / "documents" / "uploaded"
    uploaded.mkdir(parents=True, exist_ok=True)
    (uploaded / "orphan.md").write_text(
        "AC-999-01: Given X, When Y, Then Z.\n", encoding="utf-8"
    )
    result = review_acceptance_criteria.review(tmp_path)
    orphan_ids = {f.ac_id for f in result.findings if f.dimension == "orphan"}
    assert "AC-999-01" in orphan_ids, (
        f"AC-999-01 should be orphan (no US-999 in scope), got orphans: {sorted(orphan_ids)}"
    )


def test_ac_with_existing_story_not_flagged_orphan(tmp_path):
    workspace = _init_workspace(tmp_path)
    uploaded = workspace / "documents" / "uploaded"
    uploaded.mkdir(parents=True, exist_ok=True)
    (uploaded / "stories.md").write_text(
        "US-700: As a user, I want to export reports, So that I can share results.\n",
        encoding="utf-8",
    )
    (uploaded / "acs.md").write_text(
        "AC-700-01: Given a user, When they click 'Export', Then a CSV is downloaded.\n",
        encoding="utf-8",
    )
    result = review_acceptance_criteria.review(tmp_path)
    orphan_ids = {f.ac_id for f in result.findings if f.dimension == "orphan"}
    assert "AC-700-01" not in orphan_ids, (
        "AC-700-01 has a parent (US-700) and should not be orphan"
    )


def test_idempotent_rerun(tmp_path):
    workspace = _init_workspace(tmp_path)
    _seed_acs_and_stories(workspace)
    review_path = workspace / "requirements" / "acceptance-criteria-review.md"

    review_acceptance_criteria.review(tmp_path)
    review_1 = review_path.read_bytes()

    review_acceptance_criteria.review(tmp_path)
    review_2 = review_path.read_bytes()

    assert review_1 == review_2, "acceptance-criteria-review.md must be byte-identical on re-run"
