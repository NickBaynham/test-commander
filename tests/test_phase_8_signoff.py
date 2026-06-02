"""Step 8.10.5 - Phase 8 sign-off pre-flight tests.

Lands red before 8.10.3's plan/CHANGELOG closing edits, green after. Mirrors the
Phase 7 sign-off shape and covers Phase 8's surface: one skill (`tc-learning`,
six commands), six helpers, six command pages, six methodology files, three
templates, the seeded-learning fixture, the customization-guide "no new
extensible surface" record (Phase 8 ships no config schema), lessons-learned
coverage for 8.1-8.9, plan + CHANGELOG closing markers, the verifier cap bump
(`>=`), and a pytest-count floor. The SKILL.md must parse as strict YAML and
carry no deferral wording.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLAN = REPO / "planning" / "plan.md"
CHANGELOG = REPO / "CHANGELOG.md"
VERIFY_SKILLS = REPO / "scripts" / "verify_skills.py"
PLUGIN = REPO / "plugins" / "test-commander"
SCRIPTS = PLUGIN / "scripts"
TCL = PLUGIN / "skills" / "tc-learning"
CUSTOMIZING = REPO / "docs" / "user-guide" / "customizing-for-your-project.md"
WALKTHROUGH = REPO / "docs" / "user-guide" / "learning-loop.md"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-learning"
TESTS_DIR = REPO / "tests"

COMMANDS = [
    "/tc:learn",
    "/tc:learn-from-failures",
    "/tc:learn-from-exploration",
    "/tc:learn-from-feedback",
    "/tc:review-lessons",
    "/tc:promote-lessons",
]


# 1. All Phase 8 pytest files exist.

PHASE_8_TEST_FILES = (
    "test_phase_8_scaffolds.py",
    "test_capture_lesson.py",
    "test_learn_from_failures.py",
    "test_learn_from_exploration.py",
    "test_learn_from_feedback.py",
    "test_review_lessons.py",
    "test_promote_lessons.py",
    "test_phase_8_integration.py",
    "test_phase_8_signoff.py",
)


def test_all_phase_8_test_files_exist():
    for name in PHASE_8_TEST_FILES:
        assert (TESTS_DIR / name).is_file(), f"missing Phase 8 test file: tests/{name}"


# 2. All Phase 8 helpers exist.

PHASE_8_HELPERS = (
    "capture_lesson.py",
    "learn_from_failures.py",
    "learn_from_exploration.py",
    "learn_from_feedback.py",
    "review_lessons.py",
    "promote_lessons.py",
)


def test_all_phase_8_helpers_exist():
    for name in PHASE_8_HELPERS:
        assert (SCRIPTS / name).is_file(), f"missing Phase 8 helper: scripts/{name}"


def test_append_lessons_shared_engine_exists():
    text = (SCRIPTS / "capture_lesson.py").read_text(encoding="utf-8")
    assert re.search(r"^def append_lessons\(", text, flags=re.MULTILINE), (
        "capture_lesson.py must expose the shared append_lessons engine"
    )


# 3. All six command pages exist.


def test_all_phase_8_command_files_exist():
    for name in ("learn", "learn-from-failures", "learn-from-exploration",
                 "learn-from-feedback", "review-lessons", "promote-lessons"):
        assert (TCL / "commands" / f"{name}.md").is_file(), f"missing command page {name}.md"


# 4. All six methodology files exist.


def test_all_phase_8_methodology_files_exist():
    for name in ("learning-loop", "lesson-taxonomy", "improvement-governance",
                 "commander-doctrine", "anti-patterns", "heuristics"):
        assert (TCL / "methodology" / f"{name}.md").is_file(), f"missing methodology {name}.md"


# 5. All three templates exist.


def test_all_phase_8_templates_exist():
    for name in ("lesson-template", "improvement-proposal-template", "core-promotion-template"):
        assert (TCL / "templates" / f"{name}.md").is_file(), f"missing template {name}.md"


# 6. The seeded-learning fixture is complete.


def test_seeded_learning_fixture_complete():
    for name in ("README.md", "lessons-inbox.md", "analysis.md", "open-questions.md"):
        assert (FIXTURE / name).is_file(), f"seeded-learning fixture missing {name}"
    assert list(FIXTURE.glob("SESS-*.md")), "fixture missing an exploration note"


# 7. verify_skills catalog + cap (>=).


def test_verify_skills_catalog_has_tc_learning_at_phase_8():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    assert re.search(r'"tc-learning":\s*8', text), "CATALOG must map tc-learning -> 8"


def test_verify_skills_default_phase_cap_at_least_8():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r"DEFAULT_PHASE_CAP:\s*float\s*=\s*(\d+)", text)
    assert match and int(match.group(1)) >= 8, "DEFAULT_PHASE_CAP must be >= 8 at Phase 8 close"


# 8. SKILL.md lists all six commands, no deferral wording, strict YAML.


def test_skill_md_lists_all_six_commands():
    text = (TCL / "SKILL.md").read_text(encoding="utf-8")
    for cmd in COMMANDS:
        assert cmd in text, f"tc-learning/SKILL.md missing {cmd}"


def test_skill_md_has_no_deferral_wording():
    text = (TCL / "SKILL.md").read_text(encoding="utf-8").lower()
    for marker in ("behavior arrives in", "coming in phase", "not yet shipped",
                   "full behavior is documented in the per-command page once step"):
        assert marker not in text, f"tc-learning/SKILL.md carries deferral wording: {marker!r}"


def test_skill_md_frontmatter_parses_strict_yaml():
    import yaml

    text = (TCL / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match, "tc-learning/SKILL.md missing YAML frontmatter"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict) and data.get("name") == "tc-learning"
    assert isinstance(data.get("description"), str) and data["description"].strip()


# 9. Customization guide records "no new extensible surface" (not a schema block).


def test_customizing_guide_records_phase_8_no_new_surface():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 8 — what landed (no new extensible surface)" in text


# 10. Lessons-learned covers every sub-step 8.1-8.9.


def test_phase_8_lessons_learned_covers_every_substep():
    text = PLAN.read_text(encoding="utf-8")
    for substep in ("8.1", "8.2", "8.3", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9"):
        assert re.search(rf"- \*\*Step {re.escape(substep)} ", text), (
            f"plan.md Phase 8 Lessons learned missing an entry for Step {substep}"
        )


# 11. CHANGELOG Phase 8 marked complete with a date.


def test_changelog_phase_8_marked_complete():
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 8 — Continuous learning and self-improvement "
        r"\(complete (\d{4}-\d{2}-\d{2})\)",
        text, flags=re.MULTILINE,
    )
    assert match, "CHANGELOG must mark Phase 8 complete with a date"


# 12. plan.md Completed has a Phase 8 subsection with a date.


def test_plan_completed_has_phase_8_entry():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 8 — Continuous learning and self-improvement \((\d{4}-\d{2}-\d{2})\)",
        text, flags=re.MULTILINE,
    )
    assert match, "plan.md ## Completed must have a Phase 8 subsection with a date"


# 13. plan.md To Do Phase 8 collapsed to the marker line.


def test_plan_todo_phase_8_collapsed_to_marker():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 8\s*$\n+(.*?)(?=^### Phase 9|^## Completed|\Z)",
        text, flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "could not locate the To Do Phase 8 block"
    body = match.group(1)
    unchecked = re.findall(r"^\s*-\s+\[ \]", body, flags=re.MULTILINE)
    assert not unchecked, f"To Do Phase 8 still has {len(unchecked)} unchecked items"
    assert re.search(r"Phase 8 complete \(\d{4}-\d{2}-\d{2}\)", body), (
        "To Do Phase 8 must be a single marker line 'Phase 8 complete (YYYY-MM-DD) - see Completed'"
    )


# 14. Pytest count meets the Phase-8 floor (test-def count, not collected).


def test_pytest_count_meets_phase_8_floor():
    count = 0
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if "fixtures" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        count += len(re.findall(r"^def\s+test_\w+", text, flags=re.MULTILINE))
    assert count >= 720, f"expected pytest test-def count >= 720 at Phase 8 close, got {count}"


# 15. The Phase-8 walkthrough exists and references all six commands.


def test_phase_8_walkthrough_exists():
    assert WALKTHROUGH.is_file(), "docs/user-guide/learning-loop.md missing"
    text = WALKTHROUGH.read_text(encoding="utf-8")
    for cmd in COMMANDS:
        assert cmd in text, f"learning-loop.md missing reference to {cmd}"
