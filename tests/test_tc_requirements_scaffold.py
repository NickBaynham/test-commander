"""Step 2.1 — tc-requirements skill scaffold and seeded-flawed-requirements fixture.

Asserts the skill directory, SKILL.md frontmatter and body, the empty
methodology/ and templates/ directories (to be filled by 2.2-2.6), and the
seeded-flawed-requirements fixture covering every rubric dimension named in
the Phase 2 plan plus every INVEST letter and every AC-rubric dimension.

The fixture uses inline HTML comments of the form

    <!-- defect: <dimension> -->

to mark defects. The scaffold test parses these comments to verify rubric
coverage. Adding a new rubric dimension means adding a seeded defect — the
fixture is the contract.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "plugins" / "test-commander" / "skills" / "tc-requirements"
SKILL_MD = SKILL_DIR / "SKILL.md"
METHODOLOGY_DIR = SKILL_DIR / "methodology"
TEMPLATES_DIR = SKILL_DIR / "templates"
FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-flawed-requirements"
FIXTURE_REQUIREMENTS = FIXTURE_DIR / "requirements.md"
FIXTURE_USER_STORIES = FIXTURE_DIR / "user-stories.md"
FIXTURE_ACCEPTANCE = FIXTURE_DIR / "acceptance-criteria.md"
FIXTURE_README = FIXTURE_DIR / "README.md"

COMMANDS = [
    "/tc:review-requirements",
    "/tc:review-user-stories",
    "/tc:review-acceptance-criteria",
    "/tc:requirements-coverage",
    "/tc:requirements-to-tests",
]

TOP_LEVEL_RUBRIC = [
    "clarity",
    "testability",
    "completeness",
    "consistency",
    "atomicity",
    "measurability",
    "ac-quality",
    "edge-cases",
    "negative-cases",
    "data-rules",
    "roles-permissions",
    "nfrs",
    "dependencies",
    "ambiguity",
    "risk",
    "automation-suitability",
]

INVEST_LETTERS = [
    "invest-independent",
    "invest-negotiable",
    "invest-valuable",
    "invest-estimable",
    "invest-small",
    "invest-testable",
]

AC_RUBRIC = [
    "ac-missing-edge-cases",
    "ac-missing-negative-cases",
    "ac-untestable-predicate",
    "ac-ambiguous-data-rule",
    "ac-missing-role-context",
]

DEFECT_RE = re.compile(r"<!--\s*defect:\s*([a-z][a-z0-9-]*)\s*-->")


def parse_defect_tags(path: Path) -> set[str]:
    return set(DEFECT_RE.findall(path.read_text(encoding="utf-8")))


def test_skill_directory_exists():
    assert SKILL_DIR.is_dir(), f"expected {SKILL_DIR.relative_to(REPO)}"


def test_skill_md_exists():
    assert SKILL_MD.is_file(), f"expected {SKILL_MD.relative_to(REPO)}"


def test_skill_md_has_valid_frontmatter():
    text = SKILL_MD.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md must begin with a YAML frontmatter block delimited by ---"
    fm = match.group(1)
    name_match = re.search(r"^name:\s*(\S+)\s*$", fm, re.MULTILINE)
    desc_match = re.search(r"^description:\s*(.+?)\s*$", fm, re.MULTILINE)
    assert name_match, "frontmatter missing name"
    assert desc_match, "frontmatter missing description"
    assert name_match.group(1) == "tc-requirements", (
        f"expected name: tc-requirements, got {name_match.group(1)}"
    )
    assert re.fullmatch(r"[a-z][a-z0-9-]*", name_match.group(1)), "name must be kebab-case"
    assert desc_match.group(1).strip(), "description must be non-empty"


def test_skill_md_body_references_all_five_commands():
    text = SKILL_MD.read_text(encoding="utf-8")
    for cmd in COMMANDS:
        assert cmd in text, f"SKILL.md body must reference {cmd}"


def test_methodology_directory_exists():
    assert METHODOLOGY_DIR.is_dir(), (
        f"expected {METHODOLOGY_DIR.relative_to(REPO)} (filled in by 2.2-2.4)"
    )


def test_templates_directory_exists():
    assert TEMPLATES_DIR.is_dir(), (
        f"expected {TEMPLATES_DIR.relative_to(REPO)} (filled in by 2.2-2.5)"
    )


def test_fixture_directory_exists():
    assert FIXTURE_DIR.is_dir(), f"expected {FIXTURE_DIR.relative_to(REPO)}"


def test_fixture_files_present():
    for path in (FIXTURE_REQUIREMENTS, FIXTURE_USER_STORIES, FIXTURE_ACCEPTANCE, FIXTURE_README):
        assert path.is_file(), f"missing fixture file: {path.relative_to(REPO)}"


def test_fixture_readme_describes_defect_convention():
    text = FIXTURE_README.read_text(encoding="utf-8")
    assert "<!-- defect:" in text, (
        "fixture README must document the inline defect-comment convention"
    )


def test_top_level_rubric_dimensions_all_seeded():
    aggregate: set[str] = set()
    for path in (FIXTURE_REQUIREMENTS, FIXTURE_USER_STORIES, FIXTURE_ACCEPTANCE):
        aggregate |= parse_defect_tags(path)
    missing = [dim for dim in TOP_LEVEL_RUBRIC if dim not in aggregate]
    assert not missing, (
        f"fixture missing seeded defects for top-level rubric dimensions: {missing}"
    )


def test_invest_letters_all_seeded_in_user_stories():
    tags = parse_defect_tags(FIXTURE_USER_STORIES)
    missing = [letter for letter in INVEST_LETTERS if letter not in tags]
    assert not missing, (
        f"fixture user-stories.md missing seeded defects for INVEST letters: {missing}"
    )


def test_ac_rubric_dimensions_all_seeded_in_acceptance_criteria():
    tags = parse_defect_tags(FIXTURE_ACCEPTANCE)
    missing = [dim for dim in AC_RUBRIC if dim not in tags]
    assert not missing, (
        f"fixture acceptance-criteria.md missing seeded defects for AC-rubric dimensions: {missing}"
    )


def test_fixture_requirements_has_realistic_body():
    text = FIXTURE_REQUIREMENTS.read_text(encoding="utf-8")
    assert text.strip(), "requirements.md must not be empty"
    assert "REQ-" in text, "requirements.md must use REQ-NNN identifiers"


def test_fixture_user_stories_uses_role_action_benefit_shape():
    text = FIXTURE_USER_STORIES.read_text(encoding="utf-8")
    assert "As a" in text, "user-stories.md must use 'As a ... I want ... So that ...' shape"


def test_fixture_acceptance_criteria_uses_given_when_then():
    text = FIXTURE_ACCEPTANCE.read_text(encoding="utf-8")
    lowered = text.lower()
    for keyword in ("given", "when", "then"):
        assert keyword in lowered, (
            f"acceptance-criteria.md must use Given/When/Then ({keyword!r} missing)"
        )
