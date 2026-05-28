"""Step 4.8.5 - Phase 4 sign-off pre-flight tests.

Lands red before 4.8.3's plan/CHANGELOG closing edits, green after.
Mirrors the Phase 3 sign-off shape (`tests/test_phase_3_signoff.py`) and
covers Phase 4's surface: scaffold + fixture, four command helpers, three
methodology docs plus the umbrella, seven templates, customization-guide
schema parity for the `tc-explore:` block with three worked examples
spanning materially-different project shapes, lessons-learned coverage
for sub-steps 4.1-4.7, plan + CHANGELOG closing markers, the verifier
cap bump (`>=` per the Phase-2 Step-2.8 lesson), and a pytest-count
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
TCE = PLUGIN / "skills" / "tc-explore"
CUSTOMIZING = REPO / "docs" / "user-guide" / "customizing-for-your-project.md"
WALKTHROUGH = REPO / "docs" / "user-guide" / "exploring-an-app.md"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-exploration-session"
TESTS_DIR = REPO / "tests"


# ---------------------------------------------------------------------------
# 1. All seven Phase 4 pytest files exist
# ---------------------------------------------------------------------------


PHASE_4_TEST_FILES = (
    "test_tc_explore_scaffold.py",
    "test_create_charter.py",
    "test_explore.py",
    "test_session_summary.py",
    "test_enrich_test_ideas.py",
    "test_phase_4_integration.py",
    "test_phase_4_signoff.py",
)


def test_all_phase_4_test_files_exist():
    for name in PHASE_4_TEST_FILES:
        assert (TESTS_DIR / name).is_file(), f"missing Phase 4 test file: tests/{name}"


# ---------------------------------------------------------------------------
# 2. All four Phase 4 helpers exist
# ---------------------------------------------------------------------------


PHASE_4_HELPERS = (
    "create_charter.py",
    "explore.py",
    "session_summary.py",
    "enrich_test_ideas.py",
)


def test_all_phase_4_helpers_exist():
    for name in PHASE_4_HELPERS:
        assert (SCRIPTS / name).is_file(), f"missing helper: scripts/{name}"


# ---------------------------------------------------------------------------
# 3. All four Phase 4 command files exist
# ---------------------------------------------------------------------------


PHASE_4_COMMANDS = (
    "create-charter.md",
    "explore.md",
    "session-summary.md",
    "test-ideas.md",
)


def test_all_phase_4_command_files_exist():
    commands_dir = TCE / "commands"
    for name in PHASE_4_COMMANDS:
        assert (commands_dir / name).is_file(), (
            f"missing command page: tc-explore/commands/{name}"
        )


# ---------------------------------------------------------------------------
# 4. All four methodology files exist (umbrella + three per-command)
# ---------------------------------------------------------------------------


PHASE_4_METHODOLOGY = (
    "exploratory-testing.md",
    "charter-based-exploration.md",
    "session-based-test-management.md",
    "test-idea-model.md",
)


def test_all_phase_4_methodology_files_exist():
    methodology_dir = TCE / "methodology"
    for name in PHASE_4_METHODOLOGY:
        assert (methodology_dir / name).is_file(), (
            f"missing methodology: tc-explore/methodology/{name}"
        )


# ---------------------------------------------------------------------------
# 5. All seven templates exist
# ---------------------------------------------------------------------------


PHASE_4_TEMPLATES = (
    "charter-template.md",
    "target-app-template.md",
    "exploration-note-template.md",
    "anomaly-record-template.md",
    "exploration-review-template.md",
    "session-summary-template.md",
    "test-idea-enrichment-template.md",
)


def test_all_phase_4_templates_exist():
    templates_dir = TCE / "templates"
    for name in PHASE_4_TEMPLATES:
        assert (templates_dir / name).is_file(), (
            f"missing template: tc-explore/templates/{name}"
        )


# ---------------------------------------------------------------------------
# 6. Seeded exploration-session fixture: four required files
# ---------------------------------------------------------------------------


def test_seeded_exploration_session_fixture_complete():
    assert FIXTURE.is_dir(), f"missing fixture: {FIXTURE.relative_to(REPO)}"
    for name in ("README.md", "charter.md", "recorded-session.json", "target-app.md"):
        assert (FIXTURE / name).is_file(), (
            f"fixture file missing: {FIXTURE.relative_to(REPO)}/{name}"
        )


# ---------------------------------------------------------------------------
# 7. verify_skills.py has CATALOG["tc-explore"] == 4 and
#    DEFAULT_PHASE_CAP >= 4 (per Phase-2 Step-2.8 lesson: >= not ==).
# ---------------------------------------------------------------------------


def test_verify_skills_catalog_has_tc_explore_at_phase_4():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r'"tc-explore"\s*:\s*([0-9]+(?:\.[0-9]+)?)\b', text)
    assert match, 'CATALOG["tc-explore"] not found in scripts/verify_skills.py'
    phase = float(match.group(1))
    assert phase == 4, f'expected CATALOG["tc-explore"] == 4, got {phase}'


def test_verify_skills_default_phase_cap_at_least_4():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(
        r"DEFAULT_PHASE_CAP\s*:\s*float\s*=\s*([0-9]+(?:\.[0-9]+)?)\b", text
    )
    assert match, "DEFAULT_PHASE_CAP assignment not found"
    cap = float(match.group(1))
    assert cap >= 4, f"expected DEFAULT_PHASE_CAP >= 4, got {cap}"


# ---------------------------------------------------------------------------
# 8. tc-explore/SKILL.md describes all four commands plus the internal
#    review sub-mode and carries no deferral wording.
# ---------------------------------------------------------------------------


def test_tc_explore_skill_md_lists_all_four_commands():
    text = (TCE / "SKILL.md").read_text(encoding="utf-8")
    for cmd in (
        "/tc:create-charter",
        "/tc:explore",
        "/tc:session-summary",
        "/tc:test-ideas",
    ):
        assert cmd in text, f"tc-explore/SKILL.md missing reference to {cmd}"


def test_tc_explore_skill_md_describes_review_sub_mode():
    text = (TCE / "SKILL.md").read_text(encoding="utf-8").lower()
    assert "exploration-review" in text or "review sub-mode" in text, (
        "SKILL.md must describe the internal exploration-review sub-mode"
    )


def test_tc_explore_skill_md_has_no_deferral_wording():
    text = (TCE / "SKILL.md").read_text(encoding="utf-8").lower()
    forbidden = (
        "behavior arrives in step 4.",
        "behavior arrives in phase 4",
        "coming in phase 4",
        "until phase 4 ships",
        "when phase 4 ships",
    )
    for marker in forbidden:
        assert marker not in text, (
            f"tc-explore/SKILL.md still carries deferral wording: {marker!r}"
        )


# ---------------------------------------------------------------------------
# 9. customizing-for-your-project.md has the tc-explore: schema block
#    with the three documented sub-blocks plus at least three worked
#    extension examples in distinct headings.
# ---------------------------------------------------------------------------


def test_customizing_guide_has_phase_4_schema():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 4 schema (`tc-explore`)" in text, (
        "customizing-for-your-project.md missing the Phase 4 schema section"
    )
    for key in ("tc-explore:", "charters:", "exploration:", "review:"):
        assert key in text, f"customizing guide missing schema key: {key}"


def test_customizing_guide_has_six_or_more_worked_examples():
    """Phase 2 ships 3 worked examples; Phase 3 ships 3; Phase 4 ships 3.
    After 4.6 the customizing guide should carry >= 9 worked-example
    headings (the >= form per the Phase 2 Step 2.8 monotonic-non-decreasing
    discipline)."""
    text = CUSTOMIZING.read_text(encoding="utf-8")
    matches = re.findall(
        r"^#{3,4}\s+Worked example\s*[—-]\s*.+$",
        text,
        flags=re.MULTILINE,
    )
    assert len(matches) >= 9, (
        f"expected >= 9 worked-example headings (3 Phase-2 + 3 Phase-3 + "
        f"3 Phase-4), got {len(matches)}: {matches}"
    )


def test_customizing_guide_has_phase_4_what_landed_subsection():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 4 — what landed" in text or "Phase 4 - what landed" in text, (
        "customizing guide missing the 'Phase 4 - what landed' subsection"
    )


# ---------------------------------------------------------------------------
# 10. Phase 4 — Lessons learned (running) has an entry for every sub-step
#     4.1 through 4.7.
# ---------------------------------------------------------------------------


def test_phase_4_lessons_learned_covers_every_substep():
    text = PLAN.read_text(encoding="utf-8")
    expected = {f"Step 4.{n}" for n in range(1, 8)}
    found = set(re.findall(r"^#####\s+(Step 4\.[1-7])\b", text, flags=re.MULTILINE))
    missing = expected - found
    assert not missing, (
        f"Phase 4 — Lessons learned subsection missing entries for: "
        f"{sorted(missing)}"
    )


# ---------------------------------------------------------------------------
# 11. CHANGELOG Phase 4 section marked complete with a date.
# ---------------------------------------------------------------------------


def test_changelog_phase_4_marked_complete():
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 4 — Exploratory testing.+? \(complete (\d{4}-\d{2}-\d{2})\)",
        text,
        flags=re.MULTILINE,
    )
    assert match, (
        "CHANGELOG must have a '### Phase 4 — Exploratory testing ... "
        "(complete YYYY-MM-DD)' heading"
    )


# ---------------------------------------------------------------------------
# 12. plan.md Completed has a Phase 4 subsection with a date.
# ---------------------------------------------------------------------------


def test_plan_completed_has_phase_4_entry():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 4 — Exploratory testing.+? \((\d{4}-\d{2}-\d{2})\)",
        text,
        flags=re.MULTILINE,
    )
    assert match, (
        "plan.md ## Completed must have a '### Phase 4 — Exploratory testing "
        "... (YYYY-MM-DD)' subsection"
    )


# ---------------------------------------------------------------------------
# 13. plan.md To Do Phase 4 is the marker line (no unchecked items remain).
# ---------------------------------------------------------------------------


def test_plan_todo_phase_4_collapsed_to_marker():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 4\s*$\n+(.*?)(?=^### Phase 5|^## Completed|\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "could not locate the To Do Phase 4 block"
    body = match.group(1)
    unchecked = re.findall(r"^\s*-\s+\[ \]", body, flags=re.MULTILINE)
    assert not unchecked, (
        f"To Do Phase 4 still has {len(unchecked)} unchecked items; expected "
        f"the marker line 'Phase 4 complete (YYYY-MM-DD) - see Completed'"
    )
    assert re.search(r"Phase 4 complete \(\d{4}-\d{2}-\d{2}\)", body), (
        "To Do Phase 4 must be a single marker line of the form "
        "'Phase 4 complete (YYYY-MM-DD) - see Completed'"
    )


# ---------------------------------------------------------------------------
# 14. Pytest count meets the Phase-4 floor (>= 400, per the Phase 2/3
#     monotonic-non-decreasing discipline).
# ---------------------------------------------------------------------------


def test_pytest_count_meets_phase_4_floor():
    count = 0
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if "fixtures" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        count += len(re.findall(r"^def\s+test_\w+", text, flags=re.MULTILINE))
    assert count >= 400, (
        f"expected pytest test count >= 400 at Phase 4 close, got {count}"
    )


# ---------------------------------------------------------------------------
# 15. Phase-4 walkthrough exists (sanity check on the dedicated doc step).
# ---------------------------------------------------------------------------


def test_phase_4_walkthrough_exists():
    assert WALKTHROUGH.is_file(), (
        "docs/user-guide/exploring-an-app.md missing"
    )
    text = WALKTHROUGH.read_text(encoding="utf-8")
    for cmd in (
        "/tc:create-charter",
        "/tc:explore",
        "/tc:session-summary",
        "/tc:test-ideas",
    ):
        assert cmd in text, f"walkthrough missing reference to {cmd}"


# ---------------------------------------------------------------------------
# 16. The umbrella methodology workflow diagram lists all four commands
#     as shipped (no "behavior arrives in" deferral wording).
# ---------------------------------------------------------------------------


def test_umbrella_methodology_has_no_phase_4_deferral_wording():
    text = (TCE / "methodology" / "exploratory-testing.md").read_text(encoding="utf-8")
    for marker in (
        "behavior arrives in 4.",
        "behavior arrives in phase 4",
        "when phase 4 ships",
    ):
        assert marker.lower() not in text.lower(), (
            f"exploratory-testing.md still carries deferral wording: {marker!r}"
        )


# ---------------------------------------------------------------------------
# 17. tc-explore/SKILL.md frontmatter parses as strict YAML (mirrors the
#     `claude plugin validate` discipline that Step 4.8.1's cold-user
#     walkthrough surfaced).
# ---------------------------------------------------------------------------


def test_tc_explore_skill_md_frontmatter_parses_strict_yaml():
    import yaml

    text = (TCE / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match, "tc-explore/SKILL.md missing YAML frontmatter"
    fm_body = match.group(1)
    try:
        data = yaml.safe_load(fm_body)
    except yaml.YAMLError as exc:
        raise AssertionError(
            f"tc-explore/SKILL.md frontmatter failed strict YAML parse: {exc}"
        ) from exc
    assert isinstance(data, dict), "frontmatter must parse as a mapping"
    assert data.get("name") == "tc-explore", (
        f"frontmatter name field expected 'tc-explore', got {data.get('name')!r}"
    )
    assert isinstance(data.get("description"), str) and data["description"].strip(), (
        "frontmatter description field must be a non-empty string"
    )
