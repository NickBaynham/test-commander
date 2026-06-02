"""Step 13.9 - Phase 13 sign-off pre-flight tests (project complete).

Lands red before the plan/CHANGELOG/status closing edits, green after. Covers
Phase 13's surface: the tc-continuous-quality skill (six commands), the
continuous/ autonomy package, the CI workflow, the four docs, the verifier cap
bump (>= 13, the FULL catalog PRESENT with UNEXPECTED=0), lessons coverage for
13.1-13.9, plan + CHANGELOG closing markers, the status-line flip, the
project-complete marker, and a pytest-count floor. The SKILL.md must parse as
strict YAML and carry no deferral wording anywhere under the tree.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLAN = REPO / "planning" / "plan.md"
CHANGELOG = REPO / "CHANGELOG.md"
README = REPO / "README.md"
VERIFY_SKILLS = REPO / "scripts" / "verify_skills.py"
PLUGIN = REPO / "plugins" / "test-commander"
TCQ = PLUGIN / "skills" / "tc-continuous-quality"
SCRIPTS = PLUGIN / "scripts"
CONTINUOUS = REPO / "continuous"
WORKFLOW = REPO / ".github" / "workflows" / "test-commander-continuous-quality.yml"
CUSTOMIZING = REPO / "docs" / "user-guide" / "customizing-for-your-project.md"
TESTS_DIR = REPO / "tests"

COMMANDS = ["watch-changes", "impact-analysis", "coverage-gap-analysis",
            "propose-tests", "create-test-pr", "continuous-quality-check"]
HELPERS = ["cq_support.py", "watch_changes.py", "impact_analysis.py",
           "coverage_gap_analysis.py", "propose_tests.py", "create_test_pr.py",
           "continuous_quality_check.py"]
DOCS = ["docs/continuous-quality-agent.md", "docs/autonomy-levels.md",
        "docs/governed-self-improvement.md", "docs/user-guide/continuous-quality.md"]
PHASE_TEST_FILES = (
    "test_phase_13_scaffolds.py", "test_cq_watch_impact.py", "test_cq_coverage_gap.py",
    "test_cq_propose_pr.py", "test_cq_check_gates.py", "test_cq_workflow.py",
    "test_phase_13_integration.py", "test_phase_13_signoff.py",
)
SUBSTEPS = ("13.1", "13.2", "13.3", "13.4", "13.5", "13.6", "13.7", "13.8", "13.9")


def test_all_phase_test_files_exist():
    for name in PHASE_TEST_FILES:
        assert (TESTS_DIR / name).is_file(), f"missing test file tests/{name}"


def test_continuous_package_exists():
    assert (CONTINUOUS / "__init__.py").is_file()
    assert (CONTINUOUS / "autonomy.py").is_file()


def test_command_helpers_exist():
    for name in HELPERS:
        assert (SCRIPTS / name).is_file(), f"missing scripts/{name}"


def test_command_pages_exist():
    for name in COMMANDS:
        assert (TCQ / "commands" / f"{name}.md").is_file(), f"missing commands/{name}.md"


def test_methodology_and_template_exist():
    assert (TCQ / "methodology" / "autonomy-modes.md").is_file()
    assert (TCQ / "methodology" / "impact-analysis.md").is_file()
    assert (TCQ / "templates" / "continuous-config.yaml").is_file()


def test_workflow_has_four_triggers_and_is_read_only():
    data = __import__("yaml").safe_load(WORKFLOW.read_text(encoding="utf-8"))
    on = data.get(True, data.get("on"))
    for trigger in ("pull_request", "push", "schedule", "workflow_dispatch"):
        assert trigger in on
    assert data.get("permissions", {}).get("contents") == "read"


def test_four_docs_exist():
    for rel in DOCS:
        assert (REPO / rel).is_file(), f"missing {rel}"


def test_verify_skills_catalog_has_tc_continuous_quality():
    assert re.search(r'"tc-continuous-quality":\s*13', VERIFY_SKILLS.read_text(encoding="utf-8"))


def test_verify_skills_cap_at_least_13_and_full_catalog():
    import verify_skills

    assert verify_skills.DEFAULT_PHASE_CAP >= 13
    # The whole catalog is in-schedule at the final phase: nothing UNEXPECTED.
    assert max(verify_skills.CATALOG.values()) <= verify_skills.DEFAULT_PHASE_CAP


def test_skill_md_strict_yaml_and_no_deferral_anywhere():
    import yaml

    text = (TCQ / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match, "tc-continuous-quality/SKILL.md missing frontmatter"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict) and data.get("name") == "tc-continuous-quality"
    markers = ("behavior arrives in", "arrives in step", "lands in step",
               "coming in phase", "not yet shipped", "scaffold spec")
    for md in TCQ.rglob("*.md"):
        low = md.read_text(encoding="utf-8").lower()
        for marker in markers:
            assert marker not in low, f"{md.name} carries deferral wording: {marker!r}"


def test_customizing_guide_records_phase_13():
    assert "Phase 13 continuous quality" in CUSTOMIZING.read_text(encoding="utf-8")


def test_lessons_cover_every_substep():
    text = PLAN.read_text(encoding="utf-8")
    for sub in SUBSTEPS:
        assert re.search(rf"- \*\*Step {re.escape(sub)} ", text), (
            f"plan.md Phase 13 Lessons missing an entry for Step {sub}"
        )


def test_changelog_phase_13_marked_complete():
    assert re.search(
        r"^### Phase 13 — Continuous Quality Agent Mode \(complete (\d{4}-\d{2}-\d{2})\)",
        CHANGELOG.read_text(encoding="utf-8"), flags=re.MULTILINE,
    ), "CHANGELOG must mark Phase 13 complete with a date"


def test_plan_completed_has_phase_13_entry():
    assert re.search(
        r"^### Phase 13 — Continuous Quality Agent Mode \((\d{4}-\d{2}-\d{2})\)",
        PLAN.read_text(encoding="utf-8"), flags=re.MULTILINE,
    ), "plan.md ## Completed must have a Phase 13 subsection with a date"


def test_plan_todo_phase_13_collapsed():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 13\s*$\n+(.*?)(?=^## Completed|\Z)",
        text, flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "could not locate the To Do Phase 13 block"
    body = match.group(1)
    assert not re.findall(r"^\s*-\s+\[ \]", body, flags=re.MULTILINE)
    assert re.search(r"Phase 13 complete \(\d{4}-\d{2}-\d{2}\)", body)


def test_status_line_marks_phase_13_complete():
    text = README.read_text(encoding="utf-8")
    pattern = r"Phase (\d+(?:\.\d+)?) complete \(\d{4}-\d{2}-\d{2}\)"
    completed = [float(m) for m in re.findall(pattern, text)]
    assert completed and max(completed) >= 13


def test_project_marked_complete():
    # The final phase: a project-complete marker exists somewhere durable.
    blob = (README.read_text(encoding="utf-8") + CHANGELOG.read_text(encoding="utf-8")
            + PLAN.read_text(encoding="utf-8")).lower()
    assert "phases 0–13" in blob or "phases 0-13" in blob or "project complete" in blob


def test_pytest_count_meets_floor():
    count = 0
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if "fixtures" in path.parts:
            continue
        count += len(re.findall(r"^def\s+test_\w+", path.read_text(encoding="utf-8"),
                                flags=re.MULTILINE))
    assert count >= 1100, f"expected pytest test-def count >= 1100 at Phase 13 close, got {count}"
