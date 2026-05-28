"""Step 3.9.5 — Phase 3 sign-off pre-flight tests.

Lands red before 3.9.3's plan/CHANGELOG closing edits, green after. Mirrors
the Phase 2 sign-off shape (``tests/test_phase_2_signoff.py``) and covers
Phase 3's surface: scaffold + fixture, five command helpers plus the shared
synthesizer, six methodology docs, ten templates, customization-guide
schema parity for the ``tc-knowledge:`` block with three worked examples,
lessons-learned coverage for sub-steps 3.1-3.8, plan + CHANGELOG closing
markers, the verifier cap bump (``>=`` per the Phase-2 Step-2.8 lesson),
the workspace-layout addition of ``tests-coverage.md``, and a pytest-count
floor.
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
TCK = PLUGIN / "skills" / "tc-knowledge"
CUSTOMIZING = REPO / "docs" / "user-guide" / "customizing-for-your-project.md"
WALKTHROUGH = REPO / "docs" / "user-guide" / "building-project-knowledge.md"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-sample-project"
TESTS_DIR = REPO / "tests"
WORKSPACE_TEMPLATE = PLUGIN / "templates" / "workspace" / "product-knowledge"


# ---------------------------------------------------------------------------
# 1. All eight Phase 3 pytest files exist
# ---------------------------------------------------------------------------


PHASE_3_TEST_FILES = (
    "test_tc_knowledge_scaffold.py",
    "test_learn_from_docs.py",
    "test_learn_from_specs.py",
    "test_learn_from_code.py",
    "test_learn_from_api.py",
    "test_learn_from_tests.py",
    "test_phase_3_integration.py",
    "test_phase_3_signoff.py",
)


def test_all_phase_3_test_files_exist():
    for name in PHASE_3_TEST_FILES:
        assert (TESTS_DIR / name).is_file(), f"missing Phase 3 test file: tests/{name}"


# ---------------------------------------------------------------------------
# 2. All five helpers plus the shared synthesizer exist
# ---------------------------------------------------------------------------


PHASE_3_HELPERS = (
    "extract_knowledge_from_docs.py",
    "extract_knowledge_from_specs.py",
    "extract_knowledge_from_code.py",
    "extract_knowledge_from_api.py",
    "extract_knowledge_from_tests.py",
    "synthesize_system_model.py",
)


def test_all_phase_3_helpers_exist():
    for name in PHASE_3_HELPERS:
        assert (SCRIPTS / name).is_file(), f"missing helper: scripts/{name}"


# ---------------------------------------------------------------------------
# 3. All five Phase 3 command files exist
# ---------------------------------------------------------------------------


PHASE_3_COMMANDS = (
    "learn-from-docs.md",
    "learn-from-specs.md",
    "learn-from-code.md",
    "learn-from-api.md",
    "learn-from-tests.md",
)


def test_all_phase_3_command_files_exist():
    commands_dir = TCK / "commands"
    for name in PHASE_3_COMMANDS:
        assert (commands_dir / name).is_file(), (
            f"missing command page: tc-knowledge/commands/{name}"
        )


# ---------------------------------------------------------------------------
# 4. All six methodology files exist (umbrella + 5 per-source)
# ---------------------------------------------------------------------------


PHASE_3_METHODOLOGY = (
    "project-knowledge.md",
    "learning-from-documents.md",
    "learning-from-specs.md",
    "learning-from-code.md",
    "learning-from-api.md",
    "learning-from-tests.md",
)


def test_all_phase_3_methodology_files_exist():
    methodology_dir = TCK / "methodology"
    for name in PHASE_3_METHODOLOGY:
        assert (methodology_dir / name).is_file(), (
            f"missing methodology: tc-knowledge/methodology/{name}"
        )


# ---------------------------------------------------------------------------
# 5. All ten templates exist
# ---------------------------------------------------------------------------


PHASE_3_TEMPLATES = (
    "system-model-template.md",
    "documentation-model-template.md",
    "spec-derived-model-template.md",
    "code-derived-model-template.md",
    "api-model-template.md",
    "tests-coverage-template.md",
    "entities-template.md",
    "user-journeys-template.md",
    "business-rules-template.md",
    "assumptions-template.md",
)


def test_all_phase_3_templates_exist():
    templates_dir = TCK / "templates"
    for name in PHASE_3_TEMPLATES:
        assert (templates_dir / name).is_file(), (
            f"missing template: tc-knowledge/templates/{name}"
        )


# ---------------------------------------------------------------------------
# 6. Seeded sample-project fixture: five sub-trees + README
# ---------------------------------------------------------------------------


def test_seeded_sample_project_fixture_complete():
    assert FIXTURE.is_dir(), f"missing fixture: {FIXTURE.relative_to(REPO)}"
    assert (FIXTURE / "README.md").is_file(), "fixture README missing"
    for subtree in ("documents", "specs", "src", "recorded-api", "tests"):
        assert (FIXTURE / subtree).is_dir(), (
            f"fixture sub-tree missing: {subtree}/"
        )
    # Spot-check: the seeded openapi.yaml, responses.json, and at least one
    # Python source file are present.
    assert (FIXTURE / "specs" / "openapi.yaml").is_file()
    assert (FIXTURE / "recorded-api" / "responses.json").is_file()
    assert (FIXTURE / "src" / "app" / "__init__.py").is_file()
    assert (FIXTURE / "tests" / "test_auth.py").is_file()


# ---------------------------------------------------------------------------
# 7. verify_skills.py has CATALOG["tc-knowledge"] == 3 and
#    DEFAULT_PHASE_CAP >= 3 (per Phase-2 Step-2.8 lesson: >= not ==).
# ---------------------------------------------------------------------------


def test_verify_skills_catalog_has_tc_knowledge_at_phase_3():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r'"tc-knowledge"\s*:\s*([0-9]+(?:\.[0-9]+)?)\b', text)
    assert match, 'CATALOG["tc-knowledge"] not found in scripts/verify_skills.py'
    phase = float(match.group(1))
    assert phase == 3, f'expected CATALOG["tc-knowledge"] == 3, got {phase}'


def test_verify_skills_default_phase_cap_at_least_3():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r"DEFAULT_PHASE_CAP\s*:\s*float\s*=\s*([0-9]+(?:\.[0-9]+)?)\b", text)
    assert match, "DEFAULT_PHASE_CAP assignment not found"
    cap = float(match.group(1))
    assert cap >= 3, f"expected DEFAULT_PHASE_CAP >= 3, got {cap}"


# ---------------------------------------------------------------------------
# 8. tc-knowledge/SKILL.md describes all five commands + the shared
#    synthesizer and carries no deferral wording.
# ---------------------------------------------------------------------------


def test_tc_knowledge_skill_md_lists_all_five_commands():
    text = (TCK / "SKILL.md").read_text(encoding="utf-8")
    for cmd in (
        "/tc:learn-from-docs",
        "/tc:learn-from-specs",
        "/tc:learn-from-code",
        "/tc:learn-from-api",
        "/tc:learn-from-tests",
    ):
        assert cmd in text, f"tc-knowledge/SKILL.md missing reference to {cmd}"


def test_tc_knowledge_skill_md_describes_shared_synthesizer():
    text = (TCK / "SKILL.md").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "synthesize_system_model" in text or "synthesizer" in lowered, (
        "SKILL.md must describe the shared synthesizer"
    )


def test_tc_knowledge_skill_md_has_no_deferral_wording():
    text = (TCK / "SKILL.md").read_text(encoding="utf-8").lower()
    # Patterns that would indicate the SKILL.md still treats any Phase-3
    # command as not-yet-shipped.
    forbidden = (
        "behavior arrives in step 3.",
        "behavior arrives in phase 3",
        "coming in phase 3",
        "until phase 3 ships",
        "phase 3 starts next",
    )
    for marker in forbidden:
        assert marker not in text, (
            f"tc-knowledge/SKILL.md still carries deferral wording: {marker!r}"
        )


# ---------------------------------------------------------------------------
# 9. customizing-for-your-project.md has the tc-knowledge: schema block
#    with the four documented sub-blocks plus at least three worked
#    extension examples in distinct headings.
# ---------------------------------------------------------------------------


def test_customizing_guide_has_phase_3_schema():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    # Section heading
    assert "Phase 3 schema (`tc-knowledge`)" in text, (
        "customizing-for-your-project.md missing the Phase 3 schema section"
    )
    # YAML block with the four sub-blocks
    for key in ("tc-knowledge:", "documents:", "code:", "api:", "tests:"):
        assert key in text, f"customizing guide missing schema key: {key}"


def test_customizing_guide_has_three_worked_examples():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    # Each worked example lives under its own #### heading. The Phase-3
    # schema section uses headings like "#### Worked example - Python /
    # FastAPI app". Count them.
    matches = re.findall(
        r"^#{3,4}\s+Worked example\s*[—-]\s*.+$",
        text,
        flags=re.MULTILINE,
    )
    # Phase 2 ships three under the tc-requirements schema; Phase 3 ships
    # three more under tc-knowledge. After 3.7, total should be >= 6.
    assert len(matches) >= 6, (
        f"expected >= 6 worked-example headings (3 Phase-2 + 3 Phase-3), "
        f"got {len(matches)}: {matches}"
    )


def test_customizing_guide_has_phase_3_what_landed_subsection():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 3 — what landed" in text or "Phase 3 - what landed" in text, (
        "customizing guide missing the 'Phase 3 - what landed' subsection"
    )


# ---------------------------------------------------------------------------
# 10. Phase 3 — Lessons learned (running) has an entry for every sub-step
#     3.1 through 3.8.
# ---------------------------------------------------------------------------


def test_phase_3_lessons_learned_covers_every_substep():
    text = PLAN.read_text(encoding="utf-8")
    # The "Phase 3 — Lessons learned (running)" subsection lives inside the
    # Phase 3 section. Every sub-step entry uses the pattern "##### Step 3.N
    # — <title>". Scan for the eight expected entries.
    expected = {f"Step 3.{n}" for n in range(1, 9)}
    found = set(re.findall(r"^#####\s+(Step 3\.[1-8])\b", text, flags=re.MULTILINE))
    missing = expected - found
    assert not missing, (
        f"Phase 3 — Lessons learned subsection missing entries for: "
        f"{sorted(missing)}"
    )


# ---------------------------------------------------------------------------
# 11. CHANGELOG Phase 3 section marked complete with a date.
# ---------------------------------------------------------------------------


def test_changelog_phase_3_marked_complete():
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 3 — Project knowledge ingestion \(complete (\d{4}-\d{2}-\d{2})\)",
        text,
        flags=re.MULTILINE,
    )
    assert match, (
        "CHANGELOG must have a '### Phase 3 — Project knowledge ingestion "
        "(complete YYYY-MM-DD)' heading"
    )


# ---------------------------------------------------------------------------
# 12. plan.md Completed has a Phase 3 subsection with a date.
# ---------------------------------------------------------------------------


def test_plan_completed_has_phase_3_entry():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 3 — Project knowledge ingestion \((\d{4}-\d{2}-\d{2})\)",
        text,
        flags=re.MULTILINE,
    )
    assert match, (
        "plan.md ## Completed must have a '### Phase 3 — Project knowledge "
        "ingestion (YYYY-MM-DD)' subsection"
    )


# ---------------------------------------------------------------------------
# 13. plan.md To Do Phase 3 is the marker line (no unchecked items remain).
# ---------------------------------------------------------------------------


def test_plan_todo_phase_3_collapsed_to_marker():
    text = PLAN.read_text(encoding="utf-8")
    # Find the "### Phase 3" heading inside the ## To Do section.
    # The To Do section comes BEFORE the Completed section, so the FIRST
    # occurrence of "### Phase 3" (without the date suffix) is the To Do
    # marker line.
    match = re.search(
        r"^### Phase 3\s*$\n+(.*?)(?=^### Phase 4|^## Completed|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "could not locate the To Do Phase 3 block"
    body = match.group(1)
    # No unchecked items should remain.
    unchecked = re.findall(r"^\s*-\s+\[ \]", body, flags=re.MULTILINE)
    assert not unchecked, (
        f"To Do Phase 3 still has {len(unchecked)} unchecked items; expected "
        f"the marker line 'Phase 3 complete (YYYY-MM-DD) - see Completed'"
    )
    # The marker line must mention complete + a date.
    assert re.search(r"Phase 3 complete \(\d{4}-\d{2}-\d{2}\)", body), (
        "To Do Phase 3 must be a single marker line of the form "
        "'Phase 3 complete (YYYY-MM-DD) - see Completed'"
    )


# ---------------------------------------------------------------------------
# 14. plan.md Workspace Layout includes tests-coverage.md under
#     product-knowledge/.
# ---------------------------------------------------------------------------


def test_workspace_layout_includes_tests_coverage():
    text = PLAN.read_text(encoding="utf-8")
    # Locate the Workspace Layout fenced block.
    match = re.search(
        r"## Workspace Layout.*?```\n(.*?)```",
        text,
        flags=re.DOTALL,
    )
    assert match, "could not locate the Workspace Layout fenced block in plan.md"
    layout = match.group(1)
    assert "tests-coverage.md" in layout, (
        "plan.md Workspace Layout missing tests-coverage.md under product-knowledge/"
    )


# ---------------------------------------------------------------------------
# 15. Pytest count meets the Phase-3 floor (>= 200).
# ---------------------------------------------------------------------------


def test_pytest_count_meets_phase_3_floor():
    # Count test functions across every test_*.py under tests/ (excluding
    # the fixture sub-tree, which is gated by norecursedirs but defensively
    # excluded here too).
    test_root = TESTS_DIR
    count = 0
    for path in sorted(test_root.rglob("test_*.py")):
        if "fixtures" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        count += len(re.findall(r"^def\s+test_\w+", text, flags=re.MULTILINE))
    assert count >= 200, (
        f"expected pytest test count >= 200 at Phase 3 close, got {count}"
    )


# ---------------------------------------------------------------------------
# 16. Phase-3 walkthrough exists (sanity check on the dedicated doc step).
# ---------------------------------------------------------------------------


def test_phase_3_walkthrough_exists():
    assert WALKTHROUGH.is_file(), (
        "docs/user-guide/building-project-knowledge.md missing"
    )
    text = WALKTHROUGH.read_text(encoding="utf-8")
    for cmd in (
        "/tc:learn-from-docs",
        "/tc:learn-from-specs",
        "/tc:learn-from-code",
        "/tc:learn-from-api",
        "/tc:learn-from-tests",
    ):
        assert cmd in text, f"walkthrough missing reference to {cmd}"


# ---------------------------------------------------------------------------
# 17. Workspace template ships tests-coverage.md stub.
# ---------------------------------------------------------------------------


def test_workspace_template_has_tests_coverage_stub():
    stub = WORKSPACE_TEMPLATE / "tests-coverage.md"
    assert stub.is_file(), (
        "workspace template missing tests-coverage.md stub at "
        "plugins/test-commander/templates/workspace/product-knowledge/"
    )
