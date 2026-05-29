"""Step 5.7.5 - Phase 5 sign-off pre-flight tests.

Lands red before 5.7.3's plan/CHANGELOG closing edits, green after. Mirrors
the Phase 4 sign-off shape (`tests/test_phase_4_signoff.py`) and covers Phase
5's surface: two skills (`tc-bdd`, `tc-traceability`), three command helpers
plus the shared `traceability_render.py`, the seeded-bdd fixture, the umbrella
+ per-command methodology and templates, customization-guide schema parity for
the `tc-bdd:` block with three project-shape worked examples, lessons-learned
coverage for sub-steps 5.1-5.6, plan + CHANGELOG closing markers, the verifier
cap bump (`>=` per the Phase-2 Step-2.8 lesson) with both catalog entries, and
a pytest-count floor. Both new SKILL.md files must parse as strict YAML and
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
TCB = PLUGIN / "skills" / "tc-bdd"
TCT = PLUGIN / "skills" / "tc-traceability"
CUSTOMIZING = REPO / "docs" / "user-guide" / "customizing-for-your-project.md"
WALKTHROUGH = REPO / "docs" / "user-guide" / "generating-bdd.md"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-bdd"
TESTS_DIR = REPO / "tests"


# 1. All Phase 5 pytest files exist.

PHASE_5_TEST_FILES = (
    "test_tc_bdd_scaffold.py",
    "test_tc_traceability_scaffold.py",
    "test_generate_bdd.py",
    "test_review_bdd.py",
    "test_traceability_map.py",
    "test_phase_5_integration.py",
    "test_phase_5_signoff.py",
)


def test_all_phase_5_test_files_exist():
    for name in PHASE_5_TEST_FILES:
        assert (TESTS_DIR / name).is_file(), f"missing Phase 5 test file: tests/{name}"


# 2. All Phase 5 helpers exist (three commands + shared renderer).

PHASE_5_HELPERS = (
    "generate_bdd.py",
    "review_bdd.py",
    "traceability_map.py",
    "traceability_render.py",
)


def test_all_phase_5_helpers_exist():
    for name in PHASE_5_HELPERS:
        assert (SCRIPTS / name).is_file(), f"missing Phase 5 helper: scripts/{name}"


# 3. All Phase 5 command pages exist.


def test_all_phase_5_command_files_exist():
    assert (TCB / "commands" / "generate-bdd.md").is_file()
    assert (TCB / "commands" / "review-bdd.md").is_file()
    assert (TCT / "commands" / "traceability-map.md").is_file()


# 4. All methodology files exist.


def test_all_phase_5_methodology_files_exist():
    assert (TCB / "methodology" / "bdd-generation.md").is_file()
    assert (TCB / "methodology" / "bdd-quality-review.md").is_file()
    assert (TCT / "methodology" / "traceability.md").is_file()


# 5. All templates exist.


def test_all_phase_5_templates_exist():
    assert (TCB / "templates" / "feature-template.feature").is_file()
    assert (TCB / "templates" / "bdd-summary-template.md").is_file()
    assert (TCB / "templates" / "bdd-review-template.md").is_file()
    assert (TCT / "templates" / "traceability-map-template.md").is_file()


# 6. The seeded-bdd fixture is complete.


def test_seeded_bdd_fixture_complete():
    for name in ("README.md", "REQ-001.md", "SESS-20260115-001.md", "flawed.feature"):
        assert (FIXTURE / name).is_file(), f"seeded-bdd fixture missing {name}"


# 7. verify_skills catalog + cap (>= per the Phase-2 Step-2.8 lesson).


def test_verify_skills_catalog_has_both_phase_5_skills():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    assert re.search(r'"tc-bdd":\s*5', text), "CATALOG must map tc-bdd -> 5"
    assert re.search(r'"tc-traceability":\s*5', text), "CATALOG must map tc-traceability -> 5"


def test_verify_skills_default_phase_cap_at_least_5():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r"DEFAULT_PHASE_CAP:\s*float\s*=\s*(\d+)", text)
    assert match, "could not find DEFAULT_PHASE_CAP"
    assert int(match.group(1)) >= 5, (
        f"DEFAULT_PHASE_CAP must be >= 5 at Phase 5 close, got {match.group(1)}"
    )


# 8. Both SKILL.md files list their shipped commands.


def test_tc_bdd_skill_md_lists_both_commands():
    text = (TCB / "SKILL.md").read_text(encoding="utf-8")
    for cmd in ("/tc:generate-bdd", "/tc:review-bdd"):
        assert cmd in text, f"tc-bdd/SKILL.md missing {cmd}"


def test_tc_traceability_skill_md_lists_command():
    text = (TCT / "SKILL.md").read_text(encoding="utf-8")
    assert "/tc:traceability-map" in text


# 9. Neither SKILL.md carries deferral wording.


def test_phase_5_skill_md_has_no_deferral_wording():
    for skill in (TCB, TCT):
        text = (skill / "SKILL.md").read_text(encoding="utf-8").lower()
        for marker in (
            "behavior arrives in",
            "coming in phase",
            "when phase 5 ships",
            "ships in step 5",
            "behavior ships in step",
        ):
            assert marker not in text, (
                f"{skill.name}/SKILL.md still carries deferral wording: {marker!r}"
            )


# 10. Both SKILL.md frontmatter parse as strict YAML (the claude plugin
#     validate discipline; baked into 5.1's scaffold tests too).


def test_phase_5_skill_md_frontmatter_parses_strict_yaml():
    import yaml

    for skill, name in ((TCB, "tc-bdd"), (TCT, "tc-traceability")):
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
        assert match, f"{name}/SKILL.md missing YAML frontmatter"
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            raise AssertionError(
                f"{name}/SKILL.md frontmatter failed strict YAML parse: {exc}"
            ) from exc
        assert isinstance(data, dict)
        assert data.get("name") == name
        assert isinstance(data.get("description"), str) and data["description"].strip()


# 11. Customization guide carries the Phase 5 schema with three project shapes.


def test_customizing_guide_has_phase_5_schema():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 5 schema (`tc-bdd`)" in text
    assert "tc-bdd.tags.extra-classes" in text or "extra-classes" in text
    assert "rubric-extensions" in text


def test_customizing_guide_has_phase_5_what_landed():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 5 — what landed" in text


def test_customizing_guide_phase_5_has_three_project_shapes():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    section = text.split("Worked examples by project shape", 1)
    assert len(section) == 2, "missing 'Worked examples by project shape' subsection"
    body = section[1].split("## Hook 2", 1)[0]
    for shape in ("Web app", "API-only project", "Mobile app"):
        assert shape in body, f"Phase 5 worked examples missing the {shape!r} shape"


# 12. Lessons-learned covers every sub-step 5.1-5.6.


def test_phase_5_lessons_learned_covers_every_substep():
    text = PLAN.read_text(encoding="utf-8")
    for substep in ("5.1", "5.2", "5.3", "5.4", "5.5", "5.6"):
        assert re.search(rf"^##### Step {re.escape(substep)} ", text, flags=re.MULTILINE), (
            f"plan.md Phase 5 Lessons learned missing an entry for Step {substep}"
        )


# 13. CHANGELOG Phase 5 marked complete with a date.


def test_changelog_phase_5_marked_complete():
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 5 — BDD generation and traceability \(complete (\d{4}-\d{2}-\d{2})\)",
        text,
        flags=re.MULTILINE,
    )
    assert match, (
        "CHANGELOG must have a '### Phase 5 — BDD generation and traceability "
        "(complete YYYY-MM-DD)' heading"
    )


# 14. plan.md Completed has a Phase 5 subsection with a date.


def test_plan_completed_has_phase_5_entry():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 5 — BDD generation and traceability \((\d{4}-\d{2}-\d{2})\)",
        text,
        flags=re.MULTILINE,
    )
    assert match, (
        "plan.md ## Completed must have a '### Phase 5 — BDD generation and "
        "traceability (YYYY-MM-DD)' subsection"
    )


# 15. plan.md To Do Phase 5 collapsed to the marker line.


def test_plan_todo_phase_5_collapsed_to_marker():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 5\s*$\n+(.*?)(?=^### Phase 6|^## Completed|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "could not locate the To Do Phase 5 block"
    body = match.group(1)
    unchecked = re.findall(r"^\s*-\s+\[ \]", body, flags=re.MULTILINE)
    assert not unchecked, (
        f"To Do Phase 5 still has {len(unchecked)} unchecked items; expected "
        f"the marker line 'Phase 5 complete (YYYY-MM-DD) - see Completed'"
    )
    assert re.search(r"Phase 5 complete \(\d{4}-\d{2}-\d{2}\)", body), (
        "To Do Phase 5 must be a single marker line of the form "
        "'Phase 5 complete (YYYY-MM-DD) - see Completed'"
    )


# 16. Pytest count meets the Phase-5 floor.


def test_pytest_count_meets_phase_5_floor():
    count = 0
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if "fixtures" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        count += len(re.findall(r"^def\s+test_\w+", text, flags=re.MULTILINE))
    assert count >= 460, f"expected pytest test count >= 460 at Phase 5 close, got {count}"


# 17. Phase-5 walkthrough exists and references all three commands.


def test_phase_5_walkthrough_exists():
    assert WALKTHROUGH.is_file(), "docs/user-guide/generating-bdd.md missing"
    text = WALKTHROUGH.read_text(encoding="utf-8")
    for cmd in ("/tc:generate-bdd", "/tc:review-bdd", "/tc:traceability-map"):
        assert cmd in text, f"walkthrough missing reference to {cmd}"


# 18. The umbrella bdd-generation.md carries no Phase-5 deferral wording.


def test_umbrella_methodology_has_no_phase_5_deferral_wording():
    text = (TCB / "methodology" / "bdd-generation.md").read_text(encoding="utf-8").lower()
    for marker in ("behavior arrives in 5.", "when phase 5 ships", "ships in step 5"):
        assert marker not in text, (
            f"bdd-generation.md still carries deferral wording: {marker!r}"
        )
