"""Step 1.8 — Phase 1 sign-off tests.

Asserts that Phase 1 is actually closed in the planning/CHANGELOG record,
that every Phase 1 artifact is on disk, and that the verifier reflects the
phase bump. Mirrors `test_phase_0_signoff.py`; lands red until 1.8.3's
plan/CHANGELOG edits are applied.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHANGELOG = REPO / "CHANGELOG.md"
PLAN = REPO / "planning" / "plan.md"
TESTS_DIR = REPO / "tests"
PLUGIN = REPO / "plugins" / "test-commander"
TC_CORE = PLUGIN / "skills" / "tc-core"
VERIFY_SKILLS = REPO / "scripts" / "verify_skills.py"

PHASE_1_TEST_FILES = [
    "test_workspace_template.py",
    "test_init_workspace.py",
    "test_workspace_state.py",
    "test_journal.py",
    "test_next_step.py",
    "test_phase_1_integration.py",
    "test_phase_1_signoff.py",
]

PHASE_1_HELPERS = [
    "init_workspace.py",
    "workspace_state.py",
    "journal.py",
    "next_step.py",
]

PHASE_1_COMMAND_FILES = ["init.md", "status.md", "journal.md", "next.md"]


def _find_heading(text: str, heading: str) -> int:
    pattern = re.compile(rf"^{re.escape(heading)}$", re.MULTILINE)
    match = pattern.search(text)
    return match.start() if match else -1


# --- Phase 1 artifacts on disk ---

def test_all_phase_1_test_files_exist():
    for name in PHASE_1_TEST_FILES:
        assert (TESTS_DIR / name).exists(), f"missing tests/{name}"


def test_all_phase_1_helpers_exist():
    scripts_dir = PLUGIN / "scripts"
    for name in PHASE_1_HELPERS:
        assert (scripts_dir / name).exists(), f"missing {scripts_dir.relative_to(REPO)}/{name}"


def test_all_phase_1_command_files_exist():
    commands_dir = TC_CORE / "commands"
    for name in PHASE_1_COMMAND_FILES:
        assert (commands_dir / name).exists(), f"missing {commands_dir.relative_to(REPO)}/{name}"


def test_next_step_methodology_doc_exists():
    path = TC_CORE / "methodology" / "next-step-inference.md"
    assert path.exists(), f"missing {path.relative_to(REPO)}"


def test_bundled_template_at_d18_location():
    path = PLUGIN / "templates" / "workspace"
    assert path.is_dir(), f"missing {path.relative_to(REPO)}"


def test_tc_core_skill_md_describes_shipped_phase_1_commands():
    """Per the SKILL.md-surfaces-shipped-behavior convention, tc-core's SKILL.md
    must describe every shipped Phase 1 command and must not carry deferral
    wording for them. Otherwise Claude reads the SKILL.md and routes the user
    away from the implementation."""
    path = TC_CORE / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    for command in ("/tc:init", "/tc:status", "/tc:journal", "/tc:next"):
        assert command in text, f"tc-core/SKILL.md does not describe {command}"
    forbidden_phrases = (
        "Behavior arrives in Phase 1",
        "Coming in Phase 1",
        "No commands are implemented yet",
    )
    for phrase in forbidden_phrases:
        assert phrase not in text, (
            f"tc-core/SKILL.md still carries stale deferral wording: {phrase!r}"
        )
    # Must reference at least one of the bundled helpers so Claude knows to
    # invoke implementation rather than reinvent it.
    helpers_mentioned = [
        h for h in ("init_workspace.py", "workspace_state.py", "journal.py", "next_step.py")
        if h in text
    ]
    assert len(helpers_mentioned) == 4, (
        f"tc-core/SKILL.md should reference all four bundled helpers; "
        f"found: {helpers_mentioned}"
    )


# --- verify_skills phase-cap bump ---

def test_verify_skills_catalog_tc_core_is_phase_1():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    assert re.search(r'"tc-core":\s*1\b', text), (
        'expected CATALOG["tc-core"] == 1 in scripts/verify_skills.py'
    )


def test_verify_skills_default_phase_cap_at_least_1():
    # Phase 1 close bumped DEFAULT_PHASE_CAP from 0 to 1. Subsequent phases
    # bump it further (Phase 2 -> 2, etc.). This assertion guards the
    # "Phase 1 closed properly" invariant; later phases may raise the cap.
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r"DEFAULT_PHASE_CAP:\s*float\s*=\s*([0-9]+(?:\.[0-9]+)?)\b", text)
    assert match, "DEFAULT_PHASE_CAP assignment not found in scripts/verify_skills.py"
    cap = float(match.group(1))
    assert cap >= 1, (
        f"expected DEFAULT_PHASE_CAP >= 1 in scripts/verify_skills.py, got {cap}"
    )


# --- CHANGELOG + plan markers ---

def test_changelog_phase_1_marked_complete():
    text = CHANGELOG.read_text(encoding="utf-8")
    pattern = re.compile(
        r"Phase 1 — Workspace and artifact model \(complete\s+\d{4}-\d{2}-\d{2}\)"
    )
    assert pattern.search(text), (
        "CHANGELOG.md: Phase 1 heading must be marked complete with a date "
        "(e.g. 'Phase 1 — Workspace and artifact model (complete 2026-05-26)')"
    )


def test_plan_completed_has_phase_1_entry():
    text = PLAN.read_text(encoding="utf-8")
    completed_idx = _find_heading(text, "## Completed")
    assert completed_idx >= 0, "plan.md missing ## Completed section"
    completed_section = text[completed_idx:]
    pattern = re.compile(r"###\s+Phase 1\b[^\n]*\d{4}-\d{2}-\d{2}")
    assert pattern.search(completed_section), (
        "plan.md ## Completed missing 'Phase 1' subsection with a date"
    )


def test_plan_to_do_phase_1_collapsed_to_marker():
    text = PLAN.read_text(encoding="utf-8")
    todo_idx = _find_heading(text, "## To Do")
    completed_idx = _find_heading(text, "## Completed")
    assert 0 <= todo_idx < completed_idx, "plan.md To Do/Completed sections malformed"
    todo_section = text[todo_idx:completed_idx]
    match = re.search(
        r"### Phase 1\b.*?(?=^### Phase|\Z)", todo_section, re.DOTALL | re.MULTILINE
    )
    assert match, "plan.md To Do missing Phase 1 subsection"
    body = match.group(0)
    unchecked = re.findall(r"^\s*-\s*\[\s*\]", body, re.MULTILINE)
    assert not unchecked, (
        f"plan.md To Do Phase 1 still has {len(unchecked)} unchecked items; "
        "they should be moved to Completed"
    )
    assert "complete" in body.lower() or "see Completed" in body, (
        "plan.md To Do Phase 1 should reference completion"
    )


# --- suite minimum size ---

def test_pytest_suite_has_minimum_count():
    count = 0
    for f in sorted(TESTS_DIR.glob("test_*.py")):
        text = f.read_text(encoding="utf-8")
        count += len(re.findall(r"^def test_\w+", text, re.MULTILINE))
    assert count >= 84, f"expected >= 84 tests in suite, got {count}"
