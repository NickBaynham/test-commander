"""Step 5.1 - tc-traceability skill scaffold.

Asserts the tc-traceability skill directory, SKILL.md frontmatter (parsed
under strict PyYAML, per the Phase 4 Step 4.8 lesson) and body, and the
empty commands/ methodology/ templates/ directories (filled by 5.4).

The seeded-bdd fixture is shared with tc-bdd and asserted there
(tests/test_tc_bdd_scaffold.py); this file covers only the second skill's
scaffold so each skill's structural contract is independently enforced.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "plugins" / "test-commander" / "skills" / "tc-traceability"
SKILL_MD = SKILL_DIR / "SKILL.md"
COMMANDS_DIR = SKILL_DIR / "commands"
METHODOLOGY_DIR = SKILL_DIR / "methodology"
TEMPLATES_DIR = SKILL_DIR / "templates"

COMMAND = "/tc:traceability-map"

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    assert match, f"{path.name} must begin with a YAML frontmatter block delimited by ---"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict), f"{path.name} frontmatter must parse to a mapping"
    return data


def test_skill_directory_exists():
    assert SKILL_DIR.is_dir(), f"expected {SKILL_DIR.relative_to(REPO)}"


def test_skill_md_exists():
    assert SKILL_MD.is_file(), f"expected {SKILL_MD.relative_to(REPO)}"


def test_skill_md_frontmatter_parses_strict_yaml():
    data = parse_frontmatter(SKILL_MD)
    assert data.get("name") == "tc-traceability", (
        f"expected name: tc-traceability, got {data.get('name')!r}"
    )
    desc = data.get("description")
    assert isinstance(desc, str) and desc.strip(), "description must be a non-empty string"


def test_skill_md_body_references_command():
    text = SKILL_MD.read_text(encoding="utf-8")
    assert COMMAND in text, f"SKILL.md body must reference {COMMAND}"


def test_skill_md_body_references_traceability_chain():
    text = SKILL_MD.read_text(encoding="utf-8").lower()
    assert "traceability" in text, "SKILL.md must describe the traceability map"


def test_commands_directory_exists():
    assert COMMANDS_DIR.is_dir(), f"expected {COMMANDS_DIR.relative_to(REPO)} (filled by 5.4)"


def test_methodology_directory_exists():
    assert METHODOLOGY_DIR.is_dir(), f"expected {METHODOLOGY_DIR.relative_to(REPO)} (filled by 5.4)"


def test_templates_directory_exists():
    assert TEMPLATES_DIR.is_dir(), f"expected {TEMPLATES_DIR.relative_to(REPO)} (filled by 5.4)"
