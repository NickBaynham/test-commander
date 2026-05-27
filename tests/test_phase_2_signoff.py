"""Step 2.9.5 — Phase 2 sign-off pre-flight tests.

Lands red before 2.9.3's plan/CHANGELOG closing edits, green after. Mirrors
the Phase 1 sign-off shape (tests/test_phase_1_signoff.py) but covers
Phase 2's surface: scaffold + fixture, five command helpers, three
methodology docs, four templates, customization-guide schema parity,
lessons-learned coverage, plan + CHANGELOG closing markers, and the
verifier cap bump.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLAN = REPO / "planning" / "plan.md"
CHANGELOG = REPO / "CHANGELOG.md"
VERIFY_SKILLS = REPO / "scripts" / "verify_skills.py"
PLUGIN = REPO / "plugins" / "test-commander"
TCR = PLUGIN / "skills" / "tc-requirements"
CUSTOMIZING = REPO / "docs" / "user-guide" / "customizing-for-your-project.md"
TESTS_DIR = REPO / "tests"


# --- All eight Phase 2 pytest files exist ---

PHASE_2_TEST_FILES = (
    "test_tc_requirements_scaffold.py",
    "test_review_requirements.py",
    "test_review_user_stories.py",
    "test_review_acceptance_criteria.py",
    "test_requirements_coverage.py",
    "test_requirements_to_tests.py",
    "test_phase_2_integration.py",
    "test_phase_2_signoff.py",
)


def test_all_phase_2_test_files_exist():
    for name in PHASE_2_TEST_FILES:
        path = TESTS_DIR / name
        assert path.is_file(), f"missing Phase 2 test file: tests/{name}"


# --- All five helpers exist ---

PHASE_2_HELPERS = (
    "review_requirements.py",
    "review_user_stories.py",
    "review_acceptance_criteria.py",
    "requirements_coverage.py",
    "requirements_to_tests.py",
)


def test_all_phase_2_helpers_exist():
    scripts = PLUGIN / "scripts"
    for name in PHASE_2_HELPERS:
        assert (scripts / name).is_file(), f"missing helper: scripts/{name}"


# --- All five command files exist ---

PHASE_2_COMMAND_PAGES = (
    "review-requirements.md",
    "review-user-stories.md",
    "review-acceptance-criteria.md",
    "requirements-coverage.md",
    "requirements-to-tests.md",
)


def test_all_phase_2_command_pages_exist():
    commands = TCR / "commands"
    for name in PHASE_2_COMMAND_PAGES:
        assert (commands / name).is_file(), f"missing command page: commands/{name}"


# --- All three methodology files exist ---

PHASE_2_METHODOLOGY_DOCS = (
    "requirements-quality-review.md",
    "user-story-readiness.md",
    "acceptance-criteria-quality.md",
)


def test_all_phase_2_methodology_docs_exist():
    methodology = TCR / "methodology"
    for name in PHASE_2_METHODOLOGY_DOCS:
        assert (methodology / name).is_file(), f"missing methodology doc: methodology/{name}"


# --- All four templates exist ---

PHASE_2_TEMPLATES = (
    "requirements-review-template.md",
    "user-story-review-template.md",
    "acceptance-criteria-review-template.md",
    "requirements-coverage-template.md",
)


def test_all_phase_2_templates_exist():
    templates = TCR / "templates"
    for name in PHASE_2_TEMPLATES:
        assert (templates / name).is_file(), f"missing template: templates/{name}"


# --- Seeded-flawed-requirements fixture intact ---

def test_seeded_fixture_intact():
    fixture = REPO / "tests" / "fixtures" / "seeded-flawed-requirements"
    for name in ("requirements.md", "user-stories.md", "acceptance-criteria.md", "README.md"):
        assert (fixture / name).is_file(), f"missing fixture file: {name}"


# --- verify_skills cap and catalog reflect Phase 2 close ---

def test_verify_skills_catalog_tc_requirements_is_phase_2():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    assert re.search(r'"tc-requirements":\s*2\b', text), (
        'expected CATALOG["tc-requirements"] == 2 in scripts/verify_skills.py'
    )


def test_verify_skills_default_phase_cap_at_least_2():
    # Phase 2 close bumped DEFAULT_PHASE_CAP from 1 to 2. Future phases bump
    # it further; the assertion is monotonically non-decreasing (per the
    # Step 2.8 lesson on prior-phase sign-off coupling).
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r"DEFAULT_PHASE_CAP:\s*float\s*=\s*([0-9]+(?:\.[0-9]+)?)\b", text)
    assert match, "DEFAULT_PHASE_CAP assignment not found in scripts/verify_skills.py"
    cap = float(match.group(1))
    assert cap >= 2, (
        f"expected DEFAULT_PHASE_CAP >= 2 in scripts/verify_skills.py, got {cap}"
    )


# --- tc-requirements/SKILL.md describes every shipped command with no deferral wording ---

def test_tc_requirements_skill_md_describes_all_five_commands():
    text = (TCR / "SKILL.md").read_text(encoding="utf-8")
    for cmd in (
        "/tc:review-requirements",
        "/tc:review-user-stories",
        "/tc:review-acceptance-criteria",
        "/tc:requirements-coverage",
        "/tc:requirements-to-tests",
    ):
        assert cmd in text, f"SKILL.md missing reference to {cmd}"


def test_tc_requirements_skill_md_has_no_deferral_wording():
    text = (TCR / "SKILL.md").read_text(encoding="utf-8")
    forbidden_patterns = (
        r"behavior arrives in",
        r"coming in phase",
        r"until then.*placeholder",
        r"arrives in phase \d",
    )
    for pat in forbidden_patterns:
        match = re.search(pat, text, flags=re.IGNORECASE)
        assert match is None, (
            f"SKILL.md still contains deferral wording matching /{pat}/: "
            f"{text[max(0, match.start()-30):match.end()+30]!r}"
        )


# --- CHANGELOG Phase 2 closing entry ---

def test_changelog_phase_2_marked_complete():
    text = CHANGELOG.read_text(encoding="utf-8")
    pattern = re.compile(
        r"Phase 2 — Requirements and user story intelligence \(complete\s+\d{4}-\d{2}-\d{2}\)"
    )
    assert pattern.search(text), (
        "CHANGELOG.md: Phase 2 heading must be marked complete with a date "
        "(e.g. 'Phase 2 — Requirements and user story intelligence (complete 2026-05-27)')"
    )


# --- plan.md Completed has Phase 2 entry ---

def test_plan_completed_has_phase_2_entry():
    text = PLAN.read_text(encoding="utf-8")
    pattern = re.compile(
        r"### Phase 2 — Requirements and user story intelligence \(\d{4}-\d{2}-\d{2}\)"
    )
    assert pattern.search(text), (
        "planning/plan.md ## Completed must have a Phase 2 entry with a date "
        "(e.g. '### Phase 2 — Requirements and user story intelligence (2026-05-27)')"
    )


# --- plan.md To Do Phase 2 collapsed to marker line ---

def test_plan_todo_phase_2_collapsed_to_marker():
    text = PLAN.read_text(encoding="utf-8")
    # Find the Phase 2 To Do section header and grab everything until the next ### header
    match = re.search(
        r"### Phase 2\n(.*?)\n###\s",
        text,
        re.DOTALL,
    )
    assert match, "planning/plan.md must contain a '### Phase 2' To Do section"
    body = match.group(1).strip()
    # The body should be a single line "Phase 2 complete (YYYY-MM-DD) — see Completed"
    assert re.match(
        r"Phase 2 complete \(\d{4}-\d{2}-\d{2}\) — see Completed\.?$", body
    ), (
        "Phase 2 To Do section must be collapsed to the marker line, "
        f"got:\n{body!r}"
    )


# --- Customization guide reflects shipped tc-requirements schema ---

def test_customization_guide_carries_tc_requirements_schema():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "tc-requirements:" in text, (
        "customizing-for-your-project.md must contain a `tc-requirements:` YAML block"
    )
    for key in ("data-rules:", "risk:", "roles-permissions:"):
        assert key in text, (
            f"customizing-for-your-project.md must document the {key} schema key"
        )


def test_customization_guide_has_three_worked_examples():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    # Three domain-diverse worked examples should be sub-headings under Hook 1
    example_count = len(re.findall(r"###\s+Worked example", text))
    assert example_count >= 3, (
        f"customizing-for-your-project.md must carry at least three worked "
        f"extension examples, found {example_count}"
    )


# --- Lessons-learned coverage per Sub-step Lesson Capture Convention ---

def test_phase_2_lessons_learned_has_entry_per_sub_step():
    text = PLAN.read_text(encoding="utf-8")
    for step in ("Step 2.1", "Step 2.2", "Step 2.3", "Step 2.4",
                 "Step 2.5", "Step 2.6", "Step 2.7", "Step 2.8"):
        pattern = re.compile(rf"#####\s+{re.escape(step)}\s+—")
        assert pattern.search(text), (
            f"planning/plan.md Phase 2 Lessons learned subsection must have "
            f"an entry for {step}"
        )


# --- Total pytest count meets minimum ---

def test_total_pytest_count_at_least_140():
    """Sanity floor per the plan. Phase 2 finished at 155+; the assertion
    guards against accidental test deletions or regressions during sign-off.
    """
    import subprocess
    proc = subprocess.run(
        ["pdm", "run", "pytest", "--collect-only", "-q"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=60,
    )
    last_line = proc.stdout.strip().split("\n")[-1]
    match = re.search(r"(\d+)\s+tests?\s+collected", last_line)
    assert match, f"could not parse pytest collection summary: {last_line!r}"
    count = int(match.group(1))
    assert count >= 140, (
        f"expected at least 140 tests in the suite at Phase 2 close, got {count}"
    )
