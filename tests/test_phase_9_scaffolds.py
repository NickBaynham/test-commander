"""Step 9.1 - Phase 9 skill scaffold and the seeded-visuals fixture.

Asserts the `tc-visualize` skill directory, its SKILL.md (strict-PyYAML
frontmatter from the start, body referencing all eleven commands), the empty
commands/ methodology/ templates/ directories (filled by 9.2-9.6), and the
shared seeded-visuals fixture: a populated workspace slice carrying every
source artifact the diagram generators read (a traceability/test-map.md, a
requirements/requirements-inventory.md, a risk-register.md, a
quality-report/current-quality-report.md, a product-knowledge/system-model.md,
and a product-knowledge/user-journeys.md), plus a README documenting the
per-diagram source map and the D19 framing.

The fixture artifacts mirror the real producer formats (review_requirements,
traceability_render, build_report, synthesize_system_model) so the diagram
helpers parse fixture and live workspaces identically.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO / "plugins" / "test-commander" / "skills"
TCV = SKILLS_ROOT / "tc-visualize"

COMMANDS = [
    "/tc:visualize",
    "/tc:diagram-flow",
    "/tc:diagram-sequence",
    "/tc:diagram-state",
    "/tc:diagram-risk",
    "/tc:diagram-coverage",
    "/tc:diagram-traceability",
    "/tc:diagram-test-strategy",
    "/tc:diagram-architecture",
    "/tc:generate-infographic",
    "/tc:render-visuals",
]
SUBDIRS = ["commands", "methodology", "templates"]

FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-visuals"
FIXTURE_README = FIXTURE_DIR / "README.md"
FIXTURE_SOURCES = [
    "traceability/test-map.md",
    "traceability/requirements-map.md",
    "requirements/requirements-inventory.md",
    "risk-register/risk-register.md",
    "quality-report/current-quality-report.md",
    "product-knowledge/system-model.md",
    "product-knowledge/user-journeys.md",
]

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    match = FRONTMATTER_RE.match(text)
    assert match, "expected a YAML frontmatter block delimited by ---"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict), "frontmatter must parse to a mapping"
    return data


# ---------------------------------------------------------------------------
# Skill scaffold
# ---------------------------------------------------------------------------


def test_skill_directory_exists():
    assert TCV.is_dir(), "expected skills/tc-visualize/"


def test_skill_md_frontmatter_parses_strict_yaml():
    data = parse_frontmatter((TCV / "SKILL.md").read_text(encoding="utf-8"))
    assert data.get("name") == "tc-visualize"
    desc = data.get("description")
    assert isinstance(desc, str) and desc.strip(), "description must be a non-empty string"


def test_skill_md_body_references_all_eleven_commands():
    text = (TCV / "SKILL.md").read_text(encoding="utf-8")
    for cmd in COMMANDS:
        assert cmd in text, f"tc-visualize/SKILL.md body must reference {cmd}"


def test_skill_subdirectories_exist():
    for sub in SUBDIRS:
        assert (TCV / sub).is_dir(), f"expected skills/tc-visualize/{sub}/ (filled by 9.2-9.6)"


# ---------------------------------------------------------------------------
# seeded-visuals fixture
# ---------------------------------------------------------------------------


def test_fixture_directory_and_source_artifacts_exist():
    assert FIXTURE_DIR.is_dir(), "expected tests/fixtures/seeded-visuals/"
    for rel in FIXTURE_SOURCES:
        assert (FIXTURE_DIR / rel).is_file(), f"fixture must carry the source artifact {rel}"


def test_fixture_artifacts_carry_generator_markers_not_stubs():
    """Each source must look generated (a producer ran), not a template stub."""
    test_map = (FIXTURE_DIR / "traceability/test-map.md").read_text(encoding="utf-8")
    assert "| Requirement | Test idea |" in test_map, "test-map.md must carry the generated table"
    req_map = (FIXTURE_DIR / "traceability/requirements-map.md").read_text(encoding="utf-8")
    assert "| REQ-ID | Test ideas |" in req_map, "requirements-map.md must carry the table"
    inventory = (FIXTURE_DIR / "requirements/requirements-inventory.md").read_text(encoding="utf-8")
    assert "Total: **" in inventory, "requirements-inventory.md must look generated"
    risk = (FIXTURE_DIR / "risk-register/risk-register.md").read_text(encoding="utf-8")
    assert "RISK-" in risk, "risk-register.md must carry RISK-NNN rows"
    report = (FIXTURE_DIR / "quality-report/current-quality-report.md").read_text(encoding="utf-8")
    assert "## Executive summary" in report, "quality report must carry the generated sections"
    model = (FIXTURE_DIR / "product-knowledge/system-model.md").read_text(encoding="utf-8")
    assert "## Cross-source summary" in model, "system-model.md must look synthesized"
    journeys = (FIXTURE_DIR / "product-knowledge/user-journeys.md").read_text(encoding="utf-8")
    assert "## From " in journeys, "user-journeys.md must carry a per-source section"


def test_fixture_readme_documents_source_map_and_d19():
    text = FIXTURE_README.read_text(encoding="utf-8")
    lower = text.lower()
    assert "universal" in lower, "README must frame the narrative as universal (D19)"
    for token in ("diagram-flow", "diagram-risk", "diagram-traceability", "generate-infographic"):
        assert token in lower, f"README must document the source for {token}"
