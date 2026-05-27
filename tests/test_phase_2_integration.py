"""Step 2.8 — Phase 2 integration smoke.

Drives all five Phase 2 helpers in sequence against a fresh tmp consuming
project seeded with the deliberately-generic fixture. Complements the
per-command unit tests in 2.2-2.6 by exercising the full

    init -> customize -> next (R3) -> upload -> review-requirements ->
    review-user-stories -> review-acceptance-criteria ->
    requirements-coverage -> requirements-to-tests -> next (post-Phase-2)

workflow end to end, with assertions at every transition that the
expected artifact landed and the next step's preconditions are met.
"""

import shutil
from pathlib import Path

import init_workspace
import next_step
import requirements_coverage
import requirements_to_tests
import review_acceptance_criteria
import review_requirements
import review_user_stories
import workspace_state

REPO = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-flawed-requirements"
FIXTURE_REQUIREMENTS = FIXTURE_DIR / "requirements.md"
FIXTURE_USER_STORIES = FIXTURE_DIR / "user-stories.md"
FIXTURE_ACS = FIXTURE_DIR / "acceptance-criteria.md"


def test_full_phase_2_workflow(tmp_path):
    project = tmp_path / "my-project"
    project.mkdir()

    # --- 1. /tc:init ---
    init_workspace.init_workspace(project)
    workspace = project / ".test-commander"
    assert workspace.is_dir()

    # --- 2. Customize Phase 1 metadata (so /tc:next advances past R2) ---
    (workspace / "project.md").write_text(
        "# my-project\n\nIntegration smoke for Phase 2.\n", encoding="utf-8"
    )

    # --- 3. /tc:next on fresh+customized workspace -> R3 /tc:review-requirements ---
    rec = next_step.next_step_for(project)
    assert rec is not None, "expected a recommendation after Phase 1 customization"
    assert rec.command == "/tc:review-requirements", (
        f"expected R3 /tc:review-requirements, got {rec.command} (priority {rec.priority})"
    )
    assert rec.phase == "2"

    # --- 4. Upload the seeded fixture into documents/uploaded/ ---
    uploaded = workspace / "documents" / "uploaded"
    uploaded.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_REQUIREMENTS, uploaded / FIXTURE_REQUIREMENTS.name)
    shutil.copy(FIXTURE_USER_STORIES, uploaded / FIXTURE_USER_STORIES.name)
    shutil.copy(FIXTURE_ACS, uploaded / FIXTURE_ACS.name)

    # --- 5. /tc:review-requirements ---
    rr_result = review_requirements.review(project)
    assert rr_result.requirements_count == 17
    assert (workspace / "requirements" / "requirements-review.md").is_file()
    assert (workspace / "requirements" / "requirements-inventory.md").is_file()
    assert (workspace / "requirements" / "open-questions.md").is_file()
    # All 16 partition-table dimensions fire on the seeded fixture
    dimensions_seen = {f.dimension for f in rr_result.findings}
    expected_dimensions = {
        "clarity", "testability", "completeness", "consistency", "atomicity",
        "measurability", "ac-quality", "edge-cases", "negative-cases",
        "data-rules", "roles-permissions", "nfrs", "dependencies",
        "ambiguity", "risk", "automation-suitability",
    }
    missing = expected_dimensions - dimensions_seen
    assert not missing, f"review_requirements missed dimensions: {missing}"

    # --- 6. /tc:review-user-stories ---
    us_result = review_user_stories.review(project)
    assert us_result.story_count == 6
    assert (workspace / "requirements" / "user-story-review.md").is_file()
    invest_letters = {f.dimension for f in us_result.findings if f.dimension.startswith("invest-")}
    expected_invest = {
        "invest-independent", "invest-negotiable", "invest-valuable",
        "invest-estimable", "invest-small", "invest-testable",
    }
    missing_invest = expected_invest - invest_letters
    assert not missing_invest, f"review_user_stories missed INVEST letters: {missing_invest}"

    # --- 7. /tc:review-acceptance-criteria ---
    ac_result = review_acceptance_criteria.review(project)
    assert ac_result.ac_count == 5
    assert (workspace / "requirements" / "acceptance-criteria-review.md").is_file()
    ac_dimensions = {f.dimension for f in ac_result.findings}
    expected_ac = {
        "ac-missing-edge-cases", "ac-missing-negative-cases",
        "ac-untestable-predicate", "ac-ambiguous-data-rule",
        "ac-missing-role-context",
    }
    missing_ac = expected_ac - ac_dimensions
    assert not missing_ac, f"review_acceptance_criteria missed dimensions: {missing_ac}"

    # --- 8. /tc:requirements-coverage (pre-seed; everything uncovered) ---
    cov1 = requirements_coverage.coverage(project)
    assert cov1.requirements_count == 17
    assert cov1.covered_count == 0
    assert cov1.unmapped_count == 17
    assert (workspace / "requirements" / "requirements-coverage.md").is_file()
    assert (workspace / "traceability" / "requirements-map.md").is_file()

    # --- 9. /tc:requirements-to-tests (seeds + refreshes the traceability map) ---
    seed_result = requirements_to_tests.to_tests(project)
    assert seed_result.requirements_count == 17
    assert seed_result.created_count == 17
    assert seed_result.skipped_count == 0
    assert seed_result.ac_review_present is True
    test_ideas = workspace / "test-ideas"
    for i in range(1, 18):
        assert (test_ideas / f"REQ-{i:03d}.md").is_file()

    # Re-run is a no-op for seeds (skip-not-overwrite)
    rerun = requirements_to_tests.to_tests(project)
    assert rerun.created_count == 0
    assert rerun.skipped_count == 17

    # --- 10. /tc:requirements-coverage after seeding (now every REQ is covered) ---
    cov2 = requirements_coverage.coverage(project)
    assert cov2.covered_count == 17, (
        f"after seeding, every REQ should be covered; got covered={cov2.covered_count}"
    )
    assert cov2.unmapped_count == 0
    trace_text = (workspace / "traceability" / "requirements-map.md").read_text(encoding="utf-8")
    for i in range(1, 18):
        rid = f"REQ-{i:03d}"
        assert f"test-ideas/{rid}.md" in trace_text, (
            f"traceability map missing test-ideas/{rid}.md link"
        )

    # --- 11. /tc:next advances past Phase 2 ---
    rec_after = next_step.next_step_for(project)
    assert rec_after is not None, "expected a recommendation after Phase 2 chain"
    assert rec_after.command != "/tc:review-requirements", (
        f"/tc:next should advance past Phase 2; still recommends {rec_after.command}"
    )

    # --- 12. Phase status reflects Phase 2 (and downstream) progress ---
    snap = workspace_state.snapshot(project)
    assert snap.phase_status["2"] == "in_progress", (
        "Phase 2 must be in_progress after the review chain"
    )

    # --- 13. Re-running the overwrite-mode helpers is byte-deterministic ---
    review_path = workspace / "requirements" / "requirements-review.md"
    coverage_path = workspace / "requirements" / "requirements-coverage.md"
    before_review = review_path.read_bytes()
    before_coverage = coverage_path.read_bytes()
    review_requirements.review(project)
    requirements_coverage.coverage(project)
    assert review_path.read_bytes() == before_review, (
        "requirements-review.md must be byte-identical on re-run"
    )
    assert coverage_path.read_bytes() == before_coverage, (
        "requirements-coverage.md must be byte-identical on re-run"
    )
