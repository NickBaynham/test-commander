"""Step 5.1 - tc-bdd skill scaffold and seeded-bdd fixture.

Asserts the tc-bdd skill directory, SKILL.md frontmatter (parsed under
strict PyYAML, per the Phase 4 Step 4.8 lesson) and body, the empty
commands/ methodology/ templates/ directories (filled by 5.2-5.3), and
the shared seeded-bdd fixture: an enriched test-idea seed and a session
summary (the generator inputs) plus a flawed.feature carrying one
deliberate defect per universal BDD-review category.

The fixture uses the universal marker token ``knowledge: <category>``
embedded in each file's native comment syntax (Markdown HTML comments;
Gherkin ``#`` comments), the same convention established in Phase 3
Step 3.1. The scaffold test parses these tokens to verify review-category
coverage.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "plugins" / "test-commander" / "skills" / "tc-bdd"
SKILL_MD = SKILL_DIR / "SKILL.md"
COMMANDS_DIR = SKILL_DIR / "commands"
METHODOLOGY_DIR = SKILL_DIR / "methodology"
TEMPLATES_DIR = SKILL_DIR / "templates"

FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-bdd"
FIXTURE_README = FIXTURE_DIR / "README.md"
FIXTURE_TEST_IDEA = FIXTURE_DIR / "REQ-001.md"
FIXTURE_SESSION = FIXTURE_DIR / "SESS-20260115-001.md"
FIXTURE_FEATURE = FIXTURE_DIR / "flawed.feature"

COMMANDS = ["/tc:generate-bdd", "/tc:review-bdd"]

# Universal BDD-review categories from the Phase 5 design decisions block.
REVIEW_CATEGORIES = [
    "ambiguous-step",
    "missing-tag",
    "untraceable",
    "ui-coupled-step",
    "missing-examples",
    "conjunction-overload",
]

KNOWLEDGE_TOKEN_RE = re.compile(r"knowledge:\s*([a-z][a-z0-9-]*)")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
CS_HEADING_RE = re.compile(r"^### (CS-\d{3}-\d{3})\s*$", re.MULTILINE)
CS_REF_RE = re.compile(r"CS-\d{3}-\d{3}")
SCENARIO_RE = re.compile(r"^\s*(Scenario|Scenario Outline):", re.MULTILINE)


def collect_knowledge_tokens(root: Path) -> set[str]:
    """Walk every file under root and collect every ``knowledge: <dim>`` token."""
    tokens: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        tokens.update(KNOWLEDGE_TOKEN_RE.findall(text))
    return tokens


def parse_frontmatter(path: Path) -> dict:
    """Extract and strict-parse the YAML frontmatter block as a mapping."""
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    assert match, f"{path.name} must begin with a YAML frontmatter block delimited by ---"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict), f"{path.name} frontmatter must parse to a mapping"
    return data


# ---------------------------------------------------------------------------
# Skill scaffold
# ---------------------------------------------------------------------------


def test_skill_directory_exists():
    assert SKILL_DIR.is_dir(), f"expected {SKILL_DIR.relative_to(REPO)}"


def test_skill_md_exists():
    assert SKILL_MD.is_file(), f"expected {SKILL_MD.relative_to(REPO)}"


def test_skill_md_frontmatter_parses_strict_yaml():
    """Per the Phase 4 Step 4.8 lesson: the description must contain no
    embedded ``key: value`` substring that strict PyYAML rejects. Landed in
    the scaffold step, not deferred to sign-off."""
    data = parse_frontmatter(SKILL_MD)
    assert data.get("name") == "tc-bdd", f"expected name: tc-bdd, got {data.get('name')!r}"
    desc = data.get("description")
    assert isinstance(desc, str) and desc.strip(), "description must be a non-empty string"


def test_skill_md_body_references_both_commands():
    text = SKILL_MD.read_text(encoding="utf-8")
    for cmd in COMMANDS:
        assert cmd in text, f"SKILL.md body must reference {cmd}"


def test_skill_md_body_references_review_sub_mode():
    text = SKILL_MD.read_text(encoding="utf-8").lower()
    assert "review" in text, (
        "SKILL.md must describe the internal review sub-mode (auto-runs at end of "
        "/tc:generate-bdd)"
    )


def test_commands_directory_exists():
    assert COMMANDS_DIR.is_dir(), f"expected {COMMANDS_DIR.relative_to(REPO)} (filled by 5.2-5.3)"


def test_methodology_directory_exists():
    assert METHODOLOGY_DIR.is_dir(), (
        f"expected {METHODOLOGY_DIR.relative_to(REPO)} (filled by 5.2-5.3)"
    )


def test_templates_directory_exists():
    assert TEMPLATES_DIR.is_dir(), f"expected {TEMPLATES_DIR.relative_to(REPO)} (filled by 5.2-5.3)"


# ---------------------------------------------------------------------------
# Fixture - structural presence
# ---------------------------------------------------------------------------


def test_fixture_directory_exists():
    assert FIXTURE_DIR.is_dir(), f"expected {FIXTURE_DIR.relative_to(REPO)}"


def test_fixture_files_present():
    for path in (FIXTURE_README, FIXTURE_TEST_IDEA, FIXTURE_SESSION, FIXTURE_FEATURE):
        assert path.is_file(), f"missing fixture file: {path.relative_to(REPO)}"


def test_fixture_readme_describes_marker_and_linkage_conventions():
    text = FIXTURE_README.read_text(encoding="utf-8")
    assert "knowledge:" in text, "README must document the knowledge-marker convention"
    assert "universal" in text.lower(), "README must describe the narrative as universal (D19)"
    assert "@req:" in text and "@cs:" in text, (
        "README must document the @req:/@cs: linkage-tag convention"
    )


# ---------------------------------------------------------------------------
# Enriched test-idea seed (generator input)
# ---------------------------------------------------------------------------


def test_test_idea_is_enriched_with_phase4_schema():
    data = parse_frontmatter(FIXTURE_TEST_IDEA)
    assert data.get("schema") == "tc-test-idea/v1", "seed must carry the tc-test-idea/v1 schema"
    assert data.get("status") == "enriched", "seed must be enriched (status: enriched)"
    assert data.get("requirement_id") == "REQ-001", "seed must be REQ-001"
    assert "phase_4_sessions" in data, "enriched seed must carry phase_4_sessions"
    assert "candidates" in data, "seed must carry the Phase-2 candidates frontmatter"


def test_test_idea_has_phase4_enrichment_section_with_candidates():
    text = FIXTURE_TEST_IDEA.read_text(encoding="utf-8")
    assert "## Phase 4 enrichment" in text, (
        "enriched seed must carry a ## Phase 4 enrichment section"
    )
    cs_refs = set(CS_REF_RE.findall(text))
    assert len(cs_refs) >= 2, (
        f"enriched seed must reference >= 2 candidate (CS-) scenarios, got {sorted(cs_refs)}"
    )


# ---------------------------------------------------------------------------
# Session summary (generator input)
# ---------------------------------------------------------------------------


def test_session_summary_has_candidate_blocks():
    text = FIXTURE_SESSION.read_text(encoding="utf-8")
    blocks = CS_HEADING_RE.findall(text)
    assert len(blocks) >= 2, (
        f"session summary must carry at least two ### CS-NNN-NNN candidate blocks, got {blocks}"
    )


# ---------------------------------------------------------------------------
# flawed.feature - Gherkin shape and review-category coverage
# ---------------------------------------------------------------------------


def test_flawed_feature_is_gherkin():
    text = FIXTURE_FEATURE.read_text(encoding="utf-8")
    assert re.search(r"^\s*Feature:", text, re.MULTILINE), "flawed.feature must declare a Feature:"
    scenarios = SCENARIO_RE.findall(text)
    assert len(scenarios) >= len(REVIEW_CATEGORIES), (
        f"flawed.feature must carry at least {len(REVIEW_CATEGORIES)} scenarios "
        f"(one per seeded defect), got {len(scenarios)}"
    )


def test_flawed_feature_seeds_every_review_category():
    text = FIXTURE_FEATURE.read_text(encoding="utf-8")
    tokens = set(KNOWLEDGE_TOKEN_RE.findall(text))
    missing = [c for c in REVIEW_CATEGORIES if c not in tokens]
    assert not missing, (
        f"flawed.feature missing seeded knowledge-marker tokens for review categories: "
        f"{missing}; observed: {sorted(tokens)}"
    )


def test_every_review_category_seeded_in_fixture():
    tokens = collect_knowledge_tokens(FIXTURE_DIR)
    missing = [c for c in REVIEW_CATEGORIES if c not in tokens]
    assert not missing, (
        f"fixture missing seeded knowledge-marker tokens for review categories: "
        f"{missing}; observed: {sorted(tokens)}"
    )
