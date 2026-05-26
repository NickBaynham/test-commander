"""Step 0.9 — Phase 0 sign-off tests.

Asserts that Phase 0 is actually closed in the planning/CHANGELOG record and
that the expected suite of tests is in place. These tests should be red until
0.9.3 (plan and CHANGELOG updates) is applied.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHANGELOG = REPO / "CHANGELOG.md"
PLAN = REPO / "planning" / "plan.md"
TESTS_DIR = REPO / "tests"

PHASE_0_TEST_FILES = [
    "test_placeholder.py",
    "test_plugin_scaffold.py",
    "test_verify_skills.py",
    "test_make_install.py",
    "test_skill_evaluation.py",
]


def test_all_phase_0_test_files_exist():
    for name in PHASE_0_TEST_FILES:
        assert (TESTS_DIR / name).exists(), f"missing tests/{name}"


def test_changelog_phase_0_marked_complete():
    text = CHANGELOG.read_text(encoding="utf-8")
    pattern = re.compile(
        r"Phase 0 — Repository foundation \(complete\s+\d{4}-\d{2}-\d{2}\)"
    )
    assert pattern.search(text), (
        "CHANGELOG.md: Phase 0 heading must be marked complete with a date "
        "(e.g. 'Phase 0 — Repository foundation (complete 2026-05-26)')"
    )


def _find_heading(text: str, heading: str) -> int:
    """Return the byte offset of a top-level Markdown heading, anchored to a line start."""
    pattern = re.compile(rf"^{re.escape(heading)}$", re.MULTILINE)
    match = pattern.search(text)
    return match.start() if match else -1


def test_plan_completed_has_phase_0_entry():
    text = PLAN.read_text(encoding="utf-8")
    completed_idx = _find_heading(text, "## Completed")
    assert completed_idx >= 0, "plan.md missing ## Completed section"
    completed_section = text[completed_idx:]
    pattern = re.compile(r"###\s+Phase 0\b[^\n]*\d{4}-\d{2}-\d{2}")
    assert pattern.search(completed_section), (
        "plan.md ## Completed missing 'Phase 0' subsection with a date"
    )


def test_plan_to_do_phase_0_collapsed_to_marker():
    text = PLAN.read_text(encoding="utf-8")
    todo_idx = _find_heading(text, "## To Do")
    completed_idx = _find_heading(text, "## Completed")
    assert 0 <= todo_idx < completed_idx, "plan.md To Do/Completed sections malformed"
    todo_section = text[todo_idx:completed_idx]
    match = re.search(r"### Phase 0\b.*?(?=^### Phase|\Z)", todo_section, re.DOTALL | re.MULTILINE)
    assert match, "plan.md To Do missing Phase 0 subsection"
    body = match.group(0)
    unchecked = re.findall(r"^\s*-\s*\[\s*\]", body, re.MULTILINE)
    assert not unchecked, (
        f"plan.md To Do Phase 0 still has {len(unchecked)} unchecked items; "
        "they should be moved to Completed"
    )
    assert "complete" in body.lower() or "see Completed" in body, (
        "plan.md To Do Phase 0 should reference completion"
    )


def test_pytest_suite_has_minimum_count():
    count = 0
    for f in sorted(TESTS_DIR.glob("test_*.py")):
        text = f.read_text(encoding="utf-8")
        count += len(re.findall(r"^def test_\w+", text, re.MULTILINE))
    assert count >= 41, f"expected >= 41 tests in suite, got {count}"
