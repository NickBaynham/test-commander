"""Step 6.1 - Phase 6 skill scaffolds and the seeded-automation fixture.

Asserts the four Phase 6 skill directories (`tc-build-framework`,
`tc-automation-plan`, `tc-automate`, `tc-test-data`), each SKILL.md's
frontmatter (parsed under strict PyYAML from the start, per the Phase 4
Step 4.8 lesson and the Phase 5 Step 5.1 discipline) and body (every
command referenced), the empty commands/ methodology/ templates/
directories (filled by 6.2-6.6), and the shared seeded-automation
fixture: a *clean*, automatable `<area>.feature` whose scenarios all
carry `@automated-candidate` plus resolvable `@req:`/`@cs:` linkage
tags (the shape `/tc:generate-bdd` emits from clean input, not the
deliberately-flawed Phase-5 unit fixture), plus a README documenting
the universal narrative and the linkage-tag convention.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO / "plugins" / "test-commander" / "skills"

# skill name -> the /tc: commands its SKILL.md body must reference
SKILLS: dict[str, list[str]] = {
    "tc-build-framework": ["/tc:build-framework"],
    "tc-automation-plan": ["/tc:automation-plan"],
    "tc-automate": ["/tc:automate", "/tc:review-automation"],
    "tc-test-data": ["/tc:generate-test-data"],
}
SUBDIRS = ["commands", "methodology", "templates"]

FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-automation"
FIXTURE_README = FIXTURE_DIR / "README.md"

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
FEATURE_RE = re.compile(r"^\s*Feature:", re.MULTILINE)
SCENARIO_RE = re.compile(r"^\s*(Scenario|Scenario Outline):", re.MULTILINE)
REQ_TAG_RE = re.compile(r"@req:REQ-\d{3}")
CS_TAG_RE = re.compile(r"@cs:CS-\d{3}-\d{3}")
AUTOMATED_CANDIDATE = "@automated-candidate"


def parse_frontmatter(path: Path) -> dict:
    """Extract and strict-parse the YAML frontmatter block as a mapping."""
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    assert match, f"{path.name} must begin with a YAML frontmatter block delimited by ---"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict), f"{path.name} frontmatter must parse to a mapping"
    return data


def scenario_blocks(text: str) -> list[str]:
    """Split a feature file into per-scenario text blocks (tags above the
    Scenario keyword belong to that scenario)."""
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if SCENARIO_RE.match(ln)]
    blocks: list[str] = []
    for idx, start in enumerate(starts):
        # include the contiguous tag/comment lines immediately above the keyword
        head = start
        while head > 0 and lines[head - 1].strip().startswith(("@", "#")):
            head -= 1
        end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        # but do not swallow the next scenario's leading tags
        nxt = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        nxt_head = nxt
        while nxt_head > 0 and lines[nxt_head - 1].strip().startswith(("@", "#")):
            nxt_head -= 1
        end = nxt_head if idx + 1 < len(starts) else len(lines)
        blocks.append("\n".join(lines[head:end]))
    return blocks


def find_feature(root: Path) -> Path:
    features = sorted(root.glob("*.feature"))
    assert features, f"expected at least one .feature under {root.relative_to(REPO)}"
    return features[0]


# ---------------------------------------------------------------------------
# Skill scaffolds (parametrized over the four Phase 6 skills)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("skill", sorted(SKILLS))
def test_skill_directory_exists(skill):
    assert (SKILLS_ROOT / skill).is_dir(), f"expected skills/{skill}/"


@pytest.mark.parametrize("skill", sorted(SKILLS))
def test_skill_md_frontmatter_parses_strict_yaml(skill):
    """Strict PyYAML parse from the scaffold step: the description must carry no
    embedded ``key: value`` substring the canonical Claude YAML parser rejects
    (Phase 4 Step 4.8 lesson)."""
    data = parse_frontmatter(SKILLS_ROOT / skill / "SKILL.md")
    assert data.get("name") == skill, f"expected name: {skill}, got {data.get('name')!r}"
    desc = data.get("description")
    assert isinstance(desc, str) and desc.strip(), "description must be a non-empty string"


@pytest.mark.parametrize("skill", sorted(SKILLS))
def test_skill_md_body_references_its_commands(skill):
    text = (SKILLS_ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
    for cmd in SKILLS[skill]:
        assert cmd in text, f"{skill}/SKILL.md body must reference {cmd}"


@pytest.mark.parametrize("skill", sorted(SKILLS))
@pytest.mark.parametrize("subdir", SUBDIRS)
def test_skill_subdirectories_exist(skill, subdir):
    path = SKILLS_ROOT / skill / subdir
    assert path.is_dir(), f"expected skills/{skill}/{subdir}/ (filled by 6.2-6.6)"


# ---------------------------------------------------------------------------
# seeded-automation fixture
# ---------------------------------------------------------------------------


def test_fixture_directory_exists():
    assert FIXTURE_DIR.is_dir(), f"expected {FIXTURE_DIR.relative_to(REPO)}"


def test_fixture_readme_present():
    assert FIXTURE_README.is_file(), f"missing {FIXTURE_README.relative_to(REPO)}"


def test_fixture_readme_documents_narrative_and_linkage_conventions():
    text = FIXTURE_README.read_text(encoding="utf-8")
    assert "universal" in text.lower(), "README must describe the narrative as universal (D19)"
    assert "@req:" in text and "@cs:" in text, (
        "README must document the @req:/@cs: linkage-tag convention"
    )
    assert AUTOMATED_CANDIDATE in text, (
        "README must document the @automated-candidate convention"
    )


def test_fixture_feature_is_clean_automatable_gherkin():
    text = find_feature(FIXTURE_DIR).read_text(encoding="utf-8")
    assert FEATURE_RE.search(text), "fixture feature must declare a Feature:"
    blocks = scenario_blocks(text)
    assert len(blocks) >= 2, f"fixture feature must carry >= 2 scenarios, got {len(blocks)}"


def test_every_scenario_is_an_automated_candidate_with_resolvable_linkage():
    text = find_feature(FIXTURE_DIR).read_text(encoding="utf-8")
    for block in scenario_blocks(text):
        assert AUTOMATED_CANDIDATE in block, (
            f"every fixture scenario must carry {AUTOMATED_CANDIDATE}; block:\n{block}"
        )
        assert REQ_TAG_RE.search(block), f"scenario missing resolvable @req: tag; block:\n{block}"
        assert CS_TAG_RE.search(block), f"scenario missing resolvable @cs: tag; block:\n{block}"
