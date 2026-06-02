"""Step 9.9 - Phase 9 sign-off pre-flight tests.

Lands red before the plan/CHANGELOG closing edits, green after. Mirrors the
Phase 8 sign-off shape and covers Phase 9's surface: one skill (`tc-visualize`,
eleven commands), three helpers, eleven command pages, three methodology files,
ten templates, the seeded-visuals fixture, the customization-guide "no new
extensible surface" record, lessons-learned coverage for 9.1-9.9, plan +
CHANGELOG closing markers, the verifier cap bump (`>=`), and a pytest-count
floor. The SKILL.md must parse as strict YAML and carry no deferral wording.
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
TCV = PLUGIN / "skills" / "tc-visualize"
CUSTOMIZING = REPO / "docs" / "user-guide" / "customizing-for-your-project.md"
WALKTHROUGH = REPO / "docs" / "user-guide" / "visuals.md"
TESTS_DIR = REPO / "tests"

COMMANDS = [
    "/tc:visualize",
    "/tc:diagram-flow",
    "/tc:diagram-sequence",
    "/tc:diagram-state",
    "/tc:diagram-architecture",
    "/tc:diagram-risk",
    "/tc:diagram-coverage",
    "/tc:diagram-traceability",
    "/tc:diagram-test-strategy",
    "/tc:generate-infographic",
    "/tc:render-visuals",
]

COMMAND_PAGES = [
    "visualize", "diagram-flow", "diagram-sequence", "diagram-state",
    "diagram-architecture", "diagram-risk", "diagram-coverage",
    "diagram-traceability", "diagram-test-strategy", "generate-infographic",
    "render-visuals",
]

TEMPLATES = [
    "flow-diagram-template", "sequence-diagram-template", "state-diagram-template",
    "architecture-diagram-template", "risk-diagram-template", "coverage-diagram-template",
    "traceability-diagram-template", "test-strategy-diagram-template",
    "infographic-brief-template", "infographic-spec-template",
]

METHODOLOGY = ["visual-documentation", "diagram-standards", "infographic-standards"]
HELPERS = ["visualize.py", "generate_infographic.py", "render_visuals.py"]

PHASE_9_TEST_FILES = (
    "test_phase_9_scaffolds.py",
    "test_visualize.py",
    "test_diagrams_structural.py",
    "test_diagrams_quality.py",
    "test_generate_infographic.py",
    "test_render_visuals.py",
    "test_phase_9_integration.py",
    "test_phase_9_signoff.py",
)


def test_all_phase_9_test_files_exist():
    for name in PHASE_9_TEST_FILES:
        assert (TESTS_DIR / name).is_file(), f"missing Phase 9 test file: tests/{name}"


def test_all_phase_9_helpers_exist():
    for name in HELPERS:
        assert (SCRIPTS / name).is_file(), f"missing Phase 9 helper: scripts/{name}"


def test_shared_render_engine_exists():
    text = (SCRIPTS / "visualize.py").read_text(encoding="utf-8")
    assert re.search(r"^def render_diagram\(", text, flags=re.MULTILINE), (
        "visualize.py must expose the shared render_diagram engine"
    )


def test_all_phase_9_command_pages_exist():
    for name in COMMAND_PAGES:
        assert (TCV / "commands" / f"{name}.md").is_file(), f"missing command page {name}.md"


def test_all_phase_9_methodology_files_exist():
    for name in METHODOLOGY:
        assert (TCV / "methodology" / f"{name}.md").is_file(), f"missing methodology {name}.md"


def test_all_phase_9_templates_exist():
    for name in TEMPLATES:
        assert (TCV / "templates" / f"{name}.md").is_file(), f"missing template {name}.md"


def test_seeded_visuals_fixture_complete():
    fixture = REPO / "tests" / "fixtures" / "seeded-visuals"
    for rel in (
        "README.md",
        "traceability/test-map.md",
        "traceability/requirements-map.md",
        "requirements/requirements-inventory.md",
        "risk-register/risk-register.md",
        "quality-report/current-quality-report.md",
        "product-knowledge/system-model.md",
        "product-knowledge/user-journeys.md",
        "automation-plan/sign-in.md",
    ):
        assert (fixture / rel).is_file(), f"seeded-visuals fixture missing {rel}"


def test_verify_skills_catalog_has_tc_visualize_at_phase_9():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    assert re.search(r'"tc-visualize":\s*9', text), "CATALOG must map tc-visualize -> 9"


def test_verify_skills_default_phase_cap_at_least_9():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r"DEFAULT_PHASE_CAP:\s*float\s*=\s*(\d+)", text)
    assert match and int(match.group(1)) >= 9, "DEFAULT_PHASE_CAP must be >= 9 at Phase 9 close"


def test_skill_md_lists_all_eleven_commands():
    text = (TCV / "SKILL.md").read_text(encoding="utf-8")
    for cmd in COMMANDS:
        assert cmd in text, f"tc-visualize/SKILL.md missing {cmd}"


def test_skill_md_has_no_deferral_wording():
    text = (TCV / "SKILL.md").read_text(encoding="utf-8").lower()
    for marker in ("behavior arrives in", "coming in phase", "not yet shipped",
                   "once that step ships"):
        assert marker not in text, f"tc-visualize/SKILL.md carries deferral wording: {marker!r}"


def test_skill_md_frontmatter_parses_strict_yaml():
    import yaml

    text = (TCV / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match, "tc-visualize/SKILL.md missing YAML frontmatter"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict) and data.get("name") == "tc-visualize"
    assert isinstance(data.get("description"), str) and data["description"].strip()


def test_customizing_guide_records_phase_9_no_new_surface():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 9 — what landed (no new extensible surface)" in text


def test_phase_9_lessons_learned_covers_every_substep():
    text = PLAN.read_text(encoding="utf-8")
    for substep in ("9.1", "9.2", "9.3", "9.4", "9.5", "9.6", "9.7", "9.8", "9.9"):
        assert re.search(rf"- \*\*Step {re.escape(substep)} ", text), (
            f"plan.md Phase 9 Lessons learned missing an entry for Step {substep}"
        )


def test_changelog_phase_9_marked_complete():
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 9 — Visual documentation and infographics "
        r"\(complete (\d{4}-\d{2}-\d{2})\)",
        text, flags=re.MULTILINE,
    )
    assert match, "CHANGELOG must mark Phase 9 complete with a date"


def test_plan_completed_has_phase_9_entry():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 9 — Visual documentation and infographics \((\d{4}-\d{2}-\d{2})\)",
        text, flags=re.MULTILINE,
    )
    assert match, "plan.md ## Completed must have a Phase 9 subsection with a date"


def test_plan_todo_phase_9_collapsed_to_marker():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 9\s*$\n+(.*?)(?=^### Phase 10|^## Completed|\Z)",
        text, flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "could not locate the To Do Phase 9 block"
    body = match.group(1)
    unchecked = re.findall(r"^\s*-\s+\[ \]", body, flags=re.MULTILINE)
    assert not unchecked, f"To Do Phase 9 still has {len(unchecked)} unchecked items"
    assert re.search(r"Phase 9 complete \(\d{4}-\d{2}-\d{2}\)", body), (
        "To Do Phase 9 must be a single marker line 'Phase 9 complete (YYYY-MM-DD) - see Completed'"
    )


def test_pytest_count_meets_phase_9_floor():
    count = 0
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if "fixtures" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        count += len(re.findall(r"^def\s+test_\w+", text, flags=re.MULTILINE))
    assert count >= 790, f"expected pytest test-def count >= 790 at Phase 9 close, got {count}"


def test_phase_9_walkthrough_exists():
    assert WALKTHROUGH.is_file(), "docs/user-guide/visuals.md missing"
    text = WALKTHROUGH.read_text(encoding="utf-8")
    for cmd in ("/tc:visualize", "/tc:generate-infographic", "/tc:render-visuals"):
        assert cmd in text, f"visuals.md missing reference to {cmd}"
