"""Step 2.5 — /tc:requirements-coverage helper tests.

Test contract per planning/plan.md Step 2.5:
  - Uninitialized workspace refused.
  - Workspace with no `requirements-inventory.md` refused (the command
    requires the inventory artifact produced by /tc:review-requirements).
  - Workspace with only requirements (no downstream artifacts) reports
    every REQ as `not yet covered`.
  - Test-ideas file `<REQ-ID>.md` links the requirement.
  - Test-idea / feature naming a non-existent REQ-ID is flagged as orphan.
  - Idempotent re-run: coverage and traceability map byte-identical.
  - Traceability map at `traceability/requirements-map.md` updates with the
    same REQ-ID space as the inventory.
"""

import shutil
from pathlib import Path

import init_workspace
import pytest
import requirements_coverage
import review_requirements

REPO = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-flawed-requirements"
FIXTURE_REQUIREMENTS = FIXTURE_DIR / "requirements.md"


def _init_workspace(tmp_path: Path) -> Path:
    init_workspace.init_workspace(tmp_path)
    return tmp_path / ".test-commander"


def _seed_inventory(tmp_path: Path) -> Path:
    """Init the workspace, seed the fixture, run /tc:review-requirements."""
    workspace = _init_workspace(tmp_path)
    target = workspace / "documents" / "uploaded" / FIXTURE_REQUIREMENTS.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_REQUIREMENTS, target)
    review_requirements.review(tmp_path)
    return workspace


def test_uninitialized_workspace_refused(tmp_path):
    with pytest.raises(requirements_coverage.UninitializedWorkspaceError):
        requirements_coverage.coverage(tmp_path)


def test_missing_inventory_refused(tmp_path):
    _init_workspace(tmp_path)
    with pytest.raises(requirements_coverage.InventoryMissingError):
        requirements_coverage.coverage(tmp_path)


def test_no_downstream_all_uncovered(tmp_path):
    workspace = _seed_inventory(tmp_path)
    result = requirements_coverage.coverage(tmp_path)
    assert result.requirements_count == 17
    assert result.covered_count == 0
    assert result.unmapped_count == 17
    coverage_path = workspace / "requirements" / "requirements-coverage.md"
    coverage_text = coverage_path.read_text(encoding="utf-8")
    assert "not yet covered" in coverage_text.lower()
    # Every REQ-ID appears in the report
    for i in range(1, 18):
        assert f"REQ-{i:03d}" in coverage_text


def test_test_idea_links_requirement(tmp_path):
    workspace = _seed_inventory(tmp_path)
    test_ideas_dir = workspace / "test-ideas"
    test_ideas_dir.mkdir(parents=True, exist_ok=True)
    (test_ideas_dir / "REQ-001.md").write_text(
        "# Test ideas for REQ-001\n\n- Happy path test\n",
        encoding="utf-8",
    )
    result = requirements_coverage.coverage(tmp_path)
    coverage_by_req = {link.req_id: link for link in result.coverage_links}
    assert "REQ-001" in coverage_by_req
    assert coverage_by_req["REQ-001"].test_ideas, (
        "REQ-001 should be linked to test-ideas/REQ-001.md"
    )
    assert result.covered_count == 1
    assert result.unmapped_count == 16


def test_orphan_test_idea_flagged(tmp_path):
    workspace = _seed_inventory(tmp_path)
    test_ideas_dir = workspace / "test-ideas"
    test_ideas_dir.mkdir(parents=True, exist_ok=True)
    (test_ideas_dir / "REQ-999.md").write_text(
        "# Test ideas for REQ-999 (does not exist)\n",
        encoding="utf-8",
    )
    result = requirements_coverage.coverage(tmp_path)
    orphan_targets = {o.target for o in result.orphans}
    assert "REQ-999" in orphan_targets, (
        f"REQ-999 test idea should be orphan; got orphans: {sorted(orphan_targets)}"
    )


def test_bdd_feature_linking(tmp_path):
    workspace = _seed_inventory(tmp_path)
    features_dir = workspace / "bdd" / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    (features_dir / "sign-in.feature").write_text(
        "Feature: Sign in\n\n  # REQ-003\n  Scenario: Successful sign-in\n"
        "    Given a registered user\n    When they sign in\n    Then they land on the dashboard\n",
        encoding="utf-8",
    )
    result = requirements_coverage.coverage(tmp_path)
    coverage_by_req = {link.req_id: link for link in result.coverage_links}
    assert "REQ-003" in coverage_by_req
    assert coverage_by_req["REQ-003"].bdd_features, "REQ-003 should be linked to its BDD feature"


def test_idempotent_rerun(tmp_path):
    workspace = _seed_inventory(tmp_path)
    test_ideas_dir = workspace / "test-ideas"
    test_ideas_dir.mkdir(parents=True, exist_ok=True)
    (test_ideas_dir / "REQ-002.md").write_text("# REQ-002 ideas\n", encoding="utf-8")

    coverage_path = workspace / "requirements" / "requirements-coverage.md"
    trace_path = workspace / "traceability" / "requirements-map.md"

    requirements_coverage.coverage(tmp_path)
    cov_1 = coverage_path.read_bytes()
    trace_1 = trace_path.read_bytes()

    requirements_coverage.coverage(tmp_path)
    cov_2 = coverage_path.read_bytes()
    trace_2 = trace_path.read_bytes()

    assert cov_1 == cov_2, "requirements-coverage.md must be byte-identical on re-run"
    assert trace_1 == trace_2, "traceability/requirements-map.md must be byte-identical on re-run"


def test_traceability_map_uses_same_id_space(tmp_path):
    workspace = _seed_inventory(tmp_path)
    requirements_coverage.coverage(tmp_path)
    trace_text = (workspace / "traceability" / "requirements-map.md").read_text(encoding="utf-8")
    # Every parsed REQ-ID from the inventory must appear in the traceability map.
    for i in range(1, 18):
        assert f"REQ-{i:03d}" in trace_text, f"REQ-{i:03d} missing from traceability map"
