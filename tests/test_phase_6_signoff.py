"""Step 6.9.5 - Phase 6 sign-off pre-flight tests.

Lands red before 6.9.3's plan/CHANGELOG closing edits, green after. Mirrors the
Phase 5 sign-off shape (`tests/test_phase_5_signoff.py`) and covers Phase 6's
surface: four skills (`tc-build-framework`, `tc-automation-plan`, `tc-automate`,
`tc-test-data`), five command helpers plus `ensure_framework`, the
seeded-automation fixture, the methodology + templates (including the four `.ts`
object templates), the customization-guide `tc-automate` schema with three
project-shape worked examples, lessons-learned coverage for sub-steps 6.1-6.8,
plan + CHANGELOG closing markers, the verifier cap bump (`>=` per the Phase-2
Step-2.8 lesson) with all four catalog entries, and a pytest-count floor. All
four SKILL.md files must parse as strict YAML and carry no deferral wording.
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
SKILLS = PLUGIN / "skills"
TCBF = SKILLS / "tc-build-framework"
TCAP = SKILLS / "tc-automation-plan"
TCAU = SKILLS / "tc-automate"
TCTD = SKILLS / "tc-test-data"
CUSTOMIZING = REPO / "docs" / "user-guide" / "customizing-for-your-project.md"
WALKTHROUGH = REPO / "docs" / "user-guide" / "automation.md"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-automation"
TESTS_DIR = REPO / "tests"

PHASE_6_SKILLS = {
    "tc-build-framework": TCBF,
    "tc-automation-plan": TCAP,
    "tc-automate": TCAU,
    "tc-test-data": TCTD,
}


# 1. All Phase 6 pytest files exist.

PHASE_6_TEST_FILES = (
    "test_phase_6_scaffolds.py",
    "test_build_framework.py",
    "test_automation_plan.py",
    "test_automate.py",
    "test_review_automation.py",
    "test_generate_test_data.py",
    "test_phase_6_integration.py",
    "test_phase_6_signoff.py",
)


def test_all_phase_6_test_files_exist():
    for name in PHASE_6_TEST_FILES:
        assert (TESTS_DIR / name).is_file(), f"missing Phase 6 test file: tests/{name}"


# 2. All Phase 6 helpers exist + ensure_framework is the lazy-init entry point.

PHASE_6_HELPERS = (
    "build_framework.py",
    "automation_plan.py",
    "automate.py",
    "review_automation.py",
    "generate_test_data.py",
)


def test_all_phase_6_helpers_exist():
    for name in PHASE_6_HELPERS:
        assert (SCRIPTS / name).is_file(), f"missing Phase 6 helper: scripts/{name}"


def test_ensure_framework_entry_point_exists():
    text = (SCRIPTS / "build_framework.py").read_text(encoding="utf-8")
    assert re.search(r"^def ensure_framework\(", text, flags=re.MULTILINE), (
        "build_framework.py must expose ensure_framework (the lazy-init entry point)"
    )


# 3. All Phase 6 command pages exist.


def test_all_phase_6_command_files_exist():
    assert (TCBF / "commands" / "build-framework.md").is_file()
    assert (TCAP / "commands" / "automation-plan.md").is_file()
    assert (TCAU / "commands" / "automate.md").is_file()
    assert (TCAU / "commands" / "review-automation.md").is_file()
    assert (TCTD / "commands" / "generate-test-data.md").is_file()


# 4. All methodology files exist.


def test_all_phase_6_methodology_files_exist():
    assert (TCBF / "methodology" / "playwright-standards.md").is_file()
    assert (TCBF / "methodology" / "locator-strategy.md").is_file()
    assert (TCAP / "methodology" / "automation-suitability.md").is_file()
    assert (TCAU / "methodology" / "automation-generation.md").is_file()
    assert (TCAU / "methodology" / "automation-review.md").is_file()
    assert (TCTD / "methodology" / "test-data-strategy.md").is_file()


# 5. All templates exist (the four .ts object templates + others).


def test_all_phase_6_templates_exist():
    for name in (
        "page-object-template.ts",
        "component-object-template.ts",
        "playwright-spec-template.ts",
        "fixture-template.ts",
    ):
        assert (TCBF / "templates" / name).is_file(), f"missing template {name}"
    assert (TCAP / "templates" / "automation-plan-template.md").is_file()
    assert (TCAU / "templates" / "automation-review-template.md").is_file()
    assert (TCTD / "templates" / "test-data-template.json").is_file()


# 6. The seeded-automation fixture is complete.


def test_seeded_automation_fixture_complete():
    for name in ("README.md", "sign-in.feature", "flawed.spec.ts"):
        assert (FIXTURE / name).is_file(), f"seeded-automation fixture missing {name}"


# 7. verify_skills catalog + cap (>= per the Phase-2 Step-2.8 lesson).


def test_verify_skills_catalog_has_all_four_phase_6_skills():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    for skill in PHASE_6_SKILLS:
        assert re.search(rf'"{re.escape(skill)}":\s*6', text), f"CATALOG must map {skill} -> 6"


def test_verify_skills_default_phase_cap_at_least_6():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r"DEFAULT_PHASE_CAP:\s*float\s*=\s*(\d+)", text)
    assert match, "could not find DEFAULT_PHASE_CAP"
    assert int(match.group(1)) >= 6, (
        f"DEFAULT_PHASE_CAP must be >= 6 at Phase 6 close, got {match.group(1)}"
    )


# 8. Each SKILL.md lists its shipped commands.


def test_phase_6_skill_md_lists_commands():
    expected = {
        "tc-build-framework": ["/tc:build-framework"],
        "tc-automation-plan": ["/tc:automation-plan"],
        "tc-automate": ["/tc:automate", "/tc:review-automation"],
        "tc-test-data": ["/tc:generate-test-data"],
    }
    for skill, path in PHASE_6_SKILLS.items():
        text = (path / "SKILL.md").read_text(encoding="utf-8")
        for cmd in expected[skill]:
            assert cmd in text, f"{skill}/SKILL.md missing {cmd}"


# 9. No SKILL.md carries deferral wording.


def test_phase_6_skill_md_has_no_deferral_wording():
    for skill, path in PHASE_6_SKILLS.items():
        text = (path / "SKILL.md").read_text(encoding="utf-8").lower()
        for marker in (
            "behavior arrives in",
            "coming in phase",
            "ships in step 6",
            "behavior ships in step",
            "not yet shipped",
            "full behavior is documented in the per-command page once step",
        ):
            assert marker not in text, (
                f"{skill}/SKILL.md still carries deferral wording: {marker!r}"
            )


# 10. All four SKILL.md frontmatter parse as strict YAML.


def test_phase_6_skill_md_frontmatter_parses_strict_yaml():
    import yaml

    for skill, path in PHASE_6_SKILLS.items():
        text = (path / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
        assert match, f"{skill}/SKILL.md missing YAML frontmatter"
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError as exc:
            raise AssertionError(
                f"{skill}/SKILL.md frontmatter failed strict YAML parse: {exc}"
            ) from exc
        assert isinstance(data, dict)
        assert data.get("name") == skill
        assert isinstance(data.get("description"), str) and data["description"].strip()


# 11. Customization guide carries the Phase 6 schema with three project shapes.


def test_customizing_guide_has_phase_6_schema():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 6 schema (`tc-automate`)" in text
    assert "tc-automate.suitability.weights" in text or "suitability" in text


def test_customizing_guide_has_phase_6_what_landed():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 6 — what landed" in text


def test_customizing_guide_phase_6_has_three_project_shapes():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    after = text.split("Phase 6 schema (`tc-automate`)", 1)
    assert len(after) == 2, "missing the Phase 6 schema section"
    body = after[1].split("## Hook 2", 1)[0]
    weights_blocks = body.count("suitability:")
    assert weights_blocks >= 3, (
        f"Phase 6 customization needs >= 3 project-shape weight examples, got {weights_blocks}"
    )


# 12. Lessons-learned covers every sub-step 6.1-6.8.


def test_phase_6_lessons_learned_covers_every_substep():
    text = PLAN.read_text(encoding="utf-8")
    for substep in ("6.1", "6.2", "6.3", "6.4", "6.5", "6.6", "6.7", "6.8"):
        assert re.search(rf"- \*\*Step {re.escape(substep)} ", text), (
            f"plan.md Phase 6 Lessons learned missing an entry for Step {substep}"
        )


# 13. CHANGELOG Phase 6 marked complete with a date.


def test_changelog_phase_6_marked_complete():
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 6 — Playwright framework and strategic automation "
        r"\(complete (\d{4}-\d{2}-\d{2})\)",
        text,
        flags=re.MULTILINE,
    )
    assert match, (
        "CHANGELOG must have a '### Phase 6 — Playwright framework and strategic "
        "automation (complete YYYY-MM-DD)' heading"
    )


# 14. plan.md Completed has a Phase 6 subsection with a date.


def test_plan_completed_has_phase_6_entry():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 6 — Playwright framework and strategic automation "
        r"\((\d{4}-\d{2}-\d{2})\)",
        text,
        flags=re.MULTILINE,
    )
    assert match, (
        "plan.md ## Completed must have a '### Phase 6 — Playwright framework and "
        "strategic automation (YYYY-MM-DD)' subsection"
    )


# 15. plan.md To Do Phase 6 collapsed to the marker line.


def test_plan_todo_phase_6_collapsed_to_marker():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 6\s*$\n+(.*?)(?=^### Phase 7|^## Completed|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "could not locate the To Do Phase 6 block"
    body = match.group(1)
    unchecked = re.findall(r"^\s*-\s+\[ \]", body, flags=re.MULTILINE)
    assert not unchecked, (
        f"To Do Phase 6 still has {len(unchecked)} unchecked items; expected "
        f"the marker line 'Phase 6 complete (YYYY-MM-DD) - see Completed'"
    )
    assert re.search(r"Phase 6 complete \(\d{4}-\d{2}-\d{2}\)", body), (
        "To Do Phase 6 must be a single marker line of the form "
        "'Phase 6 complete (YYYY-MM-DD) - see Completed'"
    )


# 16. Pytest count meets the Phase-6 floor.


def test_pytest_count_meets_phase_6_floor():
    count = 0
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if "fixtures" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        count += len(re.findall(r"^def\s+test_\w+", text, flags=re.MULTILINE))
    assert count >= 590, f"expected pytest test count >= 590 at Phase 6 close, got {count}"


# 17. Phase-6 walkthrough exists and references all five commands.


def test_phase_6_walkthrough_exists():
    assert WALKTHROUGH.is_file(), "docs/user-guide/automation.md missing"
    text = WALKTHROUGH.read_text(encoding="utf-8")
    for cmd in (
        "/tc:build-framework",
        "/tc:automation-plan",
        "/tc:automate",
        "/tc:review-automation",
        "/tc:generate-test-data",
    ):
        assert cmd in text, f"walkthrough missing reference to {cmd}"


# 18. The umbrella methodology files carry no Phase-6 deferral wording.


def test_umbrella_methodology_has_no_phase_6_deferral_wording():
    for path in (
        TCAU / "methodology" / "automation-generation.md",
        TCAU / "methodology" / "automation-review.md",
    ):
        text = path.read_text(encoding="utf-8").lower()
        for marker in ("ships generation only", "step 6.5 adds", "wired in step 6.5"):
            assert marker not in text, (
                f"{path.name} still carries deferral wording: {marker!r}"
            )
