"""Step 2.6 — /tc:requirements-to-tests helper tests.

Test contract per planning/plan.md Step 2.6:
  - Uninitialized workspace refused.
  - Workspace with no requirements-review.md (or only the template stub) refused.
  - Seeded fixture (after /tc:review-requirements has run) generates one
    test-idea file per parsed requirement under test-ideas/<REQ-ID>.md.
  - Each emitted file has the Phase-4-compatible YAML frontmatter schema.
  - User edits to existing test-idea files are preserved on re-run.
  - Idempotent re-run does not duplicate files.
  - Traceability map at traceability/requirements-map.md is refreshed to
    include each new test-idea file path.
  - AC review presence adds an explicit AC-findings section to the seed.
"""

import shutil
from pathlib import Path

import init_workspace
import pytest
import requirements_to_tests
import review_acceptance_criteria
import review_requirements

REPO = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-flawed-requirements"
FIXTURE_REQUIREMENTS = FIXTURE_DIR / "requirements.md"
FIXTURE_ACS = FIXTURE_DIR / "acceptance-criteria.md"
FIXTURE_STORIES = FIXTURE_DIR / "user-stories.md"


def _init_workspace(tmp_path: Path) -> Path:
    init_workspace.init_workspace(tmp_path)
    return tmp_path / ".test-commander"


def _seed_review(tmp_path: Path) -> Path:
    workspace = _init_workspace(tmp_path)
    target = workspace / "documents" / "uploaded" / FIXTURE_REQUIREMENTS.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_REQUIREMENTS, target)
    review_requirements.review(tmp_path)
    return workspace


def _seed_review_and_acs(tmp_path: Path) -> Path:
    workspace = _seed_review(tmp_path)
    uploaded = workspace / "documents" / "uploaded"
    shutil.copy(FIXTURE_ACS, uploaded / FIXTURE_ACS.name)
    shutil.copy(FIXTURE_STORIES, uploaded / FIXTURE_STORIES.name)
    review_acceptance_criteria.review(tmp_path)
    return workspace


def test_uninitialized_workspace_refused(tmp_path):
    with pytest.raises(requirements_to_tests.UninitializedWorkspaceError):
        requirements_to_tests.to_tests(tmp_path)


def test_missing_review_refused(tmp_path):
    _init_workspace(tmp_path)
    with pytest.raises(requirements_to_tests.ReviewMissingError):
        requirements_to_tests.to_tests(tmp_path)


def test_generates_one_file_per_requirement(tmp_path):
    workspace = _seed_review(tmp_path)
    result = requirements_to_tests.to_tests(tmp_path)
    assert result.requirements_count == 17
    assert result.created_count == 17
    test_ideas = workspace / "test-ideas"
    md_files = sorted(test_ideas.glob("REQ-*.md"))
    assert len(md_files) == 17, f"expected 17 REQ-*.md files, got {len(md_files)}"
    for i in range(1, 18):
        path = test_ideas / f"REQ-{i:03d}.md"
        assert path.is_file(), f"missing test-idea seed for REQ-{i:03d}"


def test_schema_header_shape(tmp_path):
    workspace = _seed_review(tmp_path)
    requirements_to_tests.to_tests(tmp_path)
    seed = (workspace / "test-ideas" / "REQ-001.md").read_text(encoding="utf-8")
    # YAML frontmatter present and well-formed
    assert seed.startswith("---\n"), "test-idea seed must begin with --- frontmatter"
    end = seed.find("\n---\n", 4)
    assert end > 0, "frontmatter must end with ---"
    fm = seed[4:end]
    # Required Phase-4-contract keys
    for key in (
        "schema:", "requirement_id:", "requirement_title:",
        "source:", "status:", "phase_2_findings:", "candidates:",
    ):
        assert key in fm, f"frontmatter missing required key: {key}"
    # Schema version stamp must be present
    assert "schema: tc-test-idea/v1" in fm
    assert "requirement_id: REQ-001" in fm
    assert "status: seed" in fm
    # Candidates section: at least happy / edge / negative
    assert "happy" in fm.lower()
    assert "edge" in fm.lower()
    assert "negative" in fm.lower()


def test_user_edits_preserved_on_rerun(tmp_path):
    workspace = _seed_review(tmp_path)
    requirements_to_tests.to_tests(tmp_path)
    seed_path = workspace / "test-ideas" / "REQ-001.md"
    # Simulate a user (or Phase 4) appending content
    with seed_path.open("a", encoding="utf-8") as fh:
        fh.write("\n## User-added content\n\nManual notes from a tester.\n")
    snapshot = seed_path.read_text(encoding="utf-8")
    # Re-run: existing files must not be overwritten
    result = requirements_to_tests.to_tests(tmp_path)
    assert seed_path.read_text(encoding="utf-8") == snapshot
    assert result.skipped_count == 17, "every existing file should be skipped on re-run"
    assert result.created_count == 0


def test_idempotent_file_count(tmp_path):
    workspace = _seed_review(tmp_path)
    requirements_to_tests.to_tests(tmp_path)
    md_before = sorted((workspace / "test-ideas").glob("REQ-*.md"))
    requirements_to_tests.to_tests(tmp_path)
    md_after = sorted((workspace / "test-ideas").glob("REQ-*.md"))
    assert [p.name for p in md_before] == [p.name for p in md_after]


def test_traceability_map_updated(tmp_path):
    workspace = _seed_review(tmp_path)
    requirements_to_tests.to_tests(tmp_path)
    trace_text = (workspace / "traceability" / "requirements-map.md").read_text(
        encoding="utf-8"
    )
    # Every REQ row should now link to its test-ideas/<REQ-ID>.md seed
    for i in range(1, 18):
        rid = f"REQ-{i:03d}"
        assert rid in trace_text, f"{rid} missing from traceability map"
        assert f"test-ideas/{rid}.md" in trace_text, (
            f"{rid} traceability row missing test-ideas/{rid}.md link"
        )


def test_ac_review_present_adds_ac_findings_section(tmp_path):
    workspace = _seed_review_and_acs(tmp_path)
    requirements_to_tests.to_tests(tmp_path)
    seed = (workspace / "test-ideas" / "REQ-001.md").read_text(encoding="utf-8")
    # When AC review is present, the seed flags it explicitly
    assert "acceptance-criteria-review.md" in seed, (
        "test-idea seed should reference the AC review when it exists"
    )


def test_no_ac_review_does_not_add_ac_findings_section(tmp_path):
    workspace = _seed_review(tmp_path)
    requirements_to_tests.to_tests(tmp_path)
    seed = (workspace / "test-ideas" / "REQ-001.md").read_text(encoding="utf-8")
    assert "acceptance-criteria-review.md" not in seed, (
        "without AC review, test-idea seed should not reference it"
    )
