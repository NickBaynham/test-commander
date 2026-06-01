"""Step 7.9.5 - Phase 7 sign-off pre-flight tests.

Lands red before 7.9.3's plan/CHANGELOG closing edits, green after. Mirrors the
Phase 6 sign-off shape (`tests/test_phase_6_signoff.py`) and covers Phase 7's
surface: three skills (`tc-run`, `tc-quality-report`, `tc-evidence` — the last
a command-less internal indexer), five helpers (`run_tests`, `index_evidence`,
`analyze_results`, `build_report`, `quality_gate`), the four command pages
(tc-evidence has none), the methodology + templates, the seeded-results
fixture, the customization-guide `tc-quality-report` gate schema with three
project-shape worked examples, lessons-learned coverage for sub-steps 7.1-7.8,
plan + CHANGELOG closing markers, the verifier cap bump (`>=` per the Phase-2
Step-2.8 lesson) with all three catalog entries, and a pytest-count floor. All
three SKILL.md files must parse as strict YAML and carry no deferral wording.
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
TCRUN = SKILLS / "tc-run"
TCQR = SKILLS / "tc-quality-report"
TCEV = SKILLS / "tc-evidence"
CUSTOMIZING = REPO / "docs" / "user-guide" / "customizing-for-your-project.md"
RUNNING = REPO / "docs" / "user-guide" / "running-tests.md"
QUALITY = REPO / "docs" / "user-guide" / "quality-report.md"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-results"
TESTS_DIR = REPO / "tests"

PHASE_7_SKILLS = {"tc-run": TCRUN, "tc-quality-report": TCQR, "tc-evidence": TCEV}


# 1. All Phase 7 pytest files exist.

PHASE_7_TEST_FILES = (
    "test_phase_7_scaffolds.py",
    "test_run_tests.py",
    "test_index_evidence.py",
    "test_analyze_results.py",
    "test_build_report.py",
    "test_quality_gate.py",
    "test_phase_7_integration.py",
    "test_phase_7_signoff.py",
)


def test_all_phase_7_test_files_exist():
    for name in PHASE_7_TEST_FILES:
        assert (TESTS_DIR / name).is_file(), f"missing Phase 7 test file: tests/{name}"


# 2. All Phase 7 helpers exist.

PHASE_7_HELPERS = (
    "run_tests.py",
    "index_evidence.py",
    "analyze_results.py",
    "build_report.py",
    "quality_gate.py",
)


def test_all_phase_7_helpers_exist():
    for name in PHASE_7_HELPERS:
        assert (SCRIPTS / name).is_file(), f"missing Phase 7 helper: scripts/{name}"


def test_index_run_evidence_entry_point_exists():
    text = (SCRIPTS / "index_evidence.py").read_text(encoding="utf-8")
    assert re.search(r"^def index_run_evidence\(", text, flags=re.MULTILINE), (
        "index_evidence.py must expose index_run_evidence (the auto-run entry point)"
    )


# 3. All Phase 7 command pages exist (tc-evidence is command-less).


def test_all_phase_7_command_files_exist():
    assert (TCRUN / "commands" / "run.md").is_file()
    assert (TCRUN / "commands" / "analyze-results.md").is_file()
    assert (TCQR / "commands" / "report.md").is_file()
    assert (TCQR / "commands" / "quality-gate.md").is_file()


def test_tc_evidence_has_no_command_page():
    cmds = [p for p in (TCEV / "commands").glob("*.md")]
    assert cmds == [], f"tc-evidence is command-less; found command pages: {cmds}"


# 4. All methodology files exist.


def test_all_phase_7_methodology_files_exist():
    assert (TCRUN / "methodology" / "test-execution.md").is_file()
    assert (TCRUN / "methodology" / "failure-triage.md").is_file()
    assert (TCEV / "methodology" / "evidence-management.md").is_file()
    assert (TCQR / "methodology" / "quality-reporting.md").is_file()
    assert (TCQR / "methodology" / "quality-gates.md").is_file()


# 5. All templates exist.


def test_all_phase_7_templates_exist():
    assert (TCRUN / "templates" / "test-run-summary-template.md").is_file()
    assert (TCRUN / "templates" / "analysis-template.md").is_file()
    assert (TCEV / "templates" / "evidence-summary-template.md").is_file()
    assert (TCQR / "templates" / "quality-report-template.md").is_file()
    assert (TCQR / "templates" / "quality-gate-template.md").is_file()


# 6. The seeded-results fixture is complete.


def test_seeded_results_fixture_complete():
    for name in ("README.md", "results.json", "automation-map.md", "sign-in.spec.ts"):
        assert (FIXTURE / name).is_file(), f"seeded-results fixture missing {name}"
    assert (FIXTURE / "evidence" / "screenshots").is_dir()
    assert list((FIXTURE / "evidence" / "videos").glob("*")), "no video stub"
    assert list((FIXTURE / "evidence" / "traces").glob("*")), "no trace stub"


# 7. verify_skills catalog + cap (>= per the Phase-2 Step-2.8 lesson).


def test_verify_skills_catalog_has_all_three_phase_7_skills():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    for skill in PHASE_7_SKILLS:
        assert re.search(rf'"{re.escape(skill)}":\s*7', text), f"CATALOG must map {skill} -> 7"


def test_verify_skills_default_phase_cap_at_least_7():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r"DEFAULT_PHASE_CAP:\s*float\s*=\s*(\d+)", text)
    assert match, "could not find DEFAULT_PHASE_CAP"
    assert int(match.group(1)) >= 7, (
        f"DEFAULT_PHASE_CAP must be >= 7 at Phase 7 close, got {match.group(1)}"
    )


# 8. Each SKILL.md lists its shipped commands; tc-evidence documents the indexer.


def test_phase_7_skill_md_lists_commands():
    expected = {
        "tc-run": ["/tc:run", "/tc:analyze-results"],
        "tc-quality-report": ["/tc:report", "/tc:quality-gate"],
    }
    for skill, cmds in expected.items():
        text = (PHASE_7_SKILLS[skill] / "SKILL.md").read_text(encoding="utf-8")
        for cmd in cmds:
            assert cmd in text, f"{skill}/SKILL.md missing {cmd}"


def test_tc_evidence_skill_md_documents_internal_indexer():
    text = (TCEV / "SKILL.md").read_text(encoding="utf-8").lower()
    assert "indexer" in text and "internal" in text and "tc-run" in text


# 9. No SKILL.md carries deferral wording.


def test_phase_7_skill_md_has_no_deferral_wording():
    for skill, path in PHASE_7_SKILLS.items():
        text = (path / "SKILL.md").read_text(encoding="utf-8").lower()
        for marker in (
            "behavior arrives in",
            "coming in phase",
            "behavior arrives in step 7",
            "not yet shipped",
            "full behavior is documented in the per-command page once step",
        ):
            assert marker not in text, (
                f"{skill}/SKILL.md still carries deferral wording: {marker!r}"
            )


# 10. All three SKILL.md frontmatter parse as strict YAML.


def test_phase_7_skill_md_frontmatter_parses_strict_yaml():
    import yaml

    for skill, path in PHASE_7_SKILLS.items():
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


# 11. Customization guide carries the Phase 7 schema with three project shapes.


def test_customizing_guide_has_phase_7_schema():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 7 schema (`tc-quality-report`)" in text
    assert "tc-quality-report.gate.thresholds" in text


def test_customizing_guide_has_phase_7_what_landed():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 7 — what landed" in text


def test_customizing_guide_phase_7_has_three_project_shapes():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    after = text.split("Phase 7 schema (`tc-quality-report`)", 1)
    assert len(after) == 2, "missing the Phase 7 schema section"
    body = after[1].split("## Hook 2", 1)[0]
    threshold_blocks = body.count("thresholds:")
    assert threshold_blocks >= 3, (
        f"Phase 7 customization needs >= 3 project-shape threshold examples, "
        f"got {threshold_blocks}"
    )


# 12. Lessons-learned covers every sub-step 7.1-7.8.


def test_phase_7_lessons_learned_covers_every_substep():
    text = PLAN.read_text(encoding="utf-8")
    for substep in ("7.1", "7.2", "7.3", "7.4", "7.5", "7.6", "7.7", "7.8"):
        assert re.search(rf"- \*\*Step {re.escape(substep)} ", text), (
            f"plan.md Phase 7 Lessons learned missing an entry for Step {substep}"
        )


# 13. CHANGELOG Phase 7 marked complete with a date.


def test_changelog_phase_7_marked_complete():
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 7 — Execution, evidence, and quality report "
        r"\(complete (\d{4}-\d{2}-\d{2})\)",
        text,
        flags=re.MULTILINE,
    )
    assert match, (
        "CHANGELOG must have a '### Phase 7 — Execution, evidence, and quality "
        "report (complete YYYY-MM-DD)' heading"
    )


# 14. plan.md Completed has a Phase 7 subsection with a date.


def test_plan_completed_has_phase_7_entry():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 7 — Execution, evidence, and quality report "
        r"\((\d{4}-\d{2}-\d{2})\)",
        text,
        flags=re.MULTILINE,
    )
    assert match, (
        "plan.md ## Completed must have a '### Phase 7 — Execution, evidence, and "
        "quality report (YYYY-MM-DD)' subsection"
    )


# 15. plan.md To Do Phase 7 collapsed to the marker line.


def test_plan_todo_phase_7_collapsed_to_marker():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 7\s*$\n+(.*?)(?=^### Phase 8|^## Completed|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "could not locate the To Do Phase 7 block"
    body = match.group(1)
    unchecked = re.findall(r"^\s*-\s+\[ \]", body, flags=re.MULTILINE)
    assert not unchecked, (
        f"To Do Phase 7 still has {len(unchecked)} unchecked items; expected "
        f"the marker line 'Phase 7 complete (YYYY-MM-DD) - see Completed'"
    )
    assert re.search(r"Phase 7 complete \(\d{4}-\d{2}-\d{2}\)", body), (
        "To Do Phase 7 must be a single marker line of the form "
        "'Phase 7 complete (YYYY-MM-DD) - see Completed'"
    )


# 16. Pytest count meets the Phase-7 floor.


def test_pytest_count_meets_phase_7_floor():
    count = 0
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if "fixtures" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        count += len(re.findall(r"^def\s+test_\w+", text, flags=re.MULTILINE))
    # Counts test-function `def`s (not pytest-collected count, which is higher
    # because of parametrized suites) — the same method the Phase-6 sign-off
    # used. The plan's "700" was a collected-count estimate; the def count at
    # Phase 7 close is ~682.
    assert count >= 680, f"expected pytest test-def count >= 680 at Phase 7 close, got {count}"


# 17. The Phase-7 walkthroughs exist and reference all four commands.


def test_phase_7_walkthroughs_exist():
    assert RUNNING.is_file(), "docs/user-guide/running-tests.md missing"
    assert QUALITY.is_file(), "docs/user-guide/quality-report.md missing"
    text = RUNNING.read_text(encoding="utf-8")
    for cmd in ("/tc:run", "/tc:analyze-results", "/tc:report", "/tc:quality-gate"):
        assert cmd in text, f"running-tests.md missing reference to {cmd}"
