"""Step 0.5 — plugin scaffold validation.

Maps to the 8 automated DoD checks for Step 0.5 in planning/plan.md.
Interactive checks 9 and 10 are confirmed separately in Claude Code.
"""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MARKETPLACE_JSON = REPO / ".claude-plugin" / "marketplace.json"
PLUGIN_DIR = REPO / "plugins" / "test-commander"
PLUGIN_JSON = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
PLUGIN_README = PLUGIN_DIR / "README.md"
PLUGIN_LICENSE = PLUGIN_DIR / "LICENSE"
TC_CORE_SKILL = PLUGIN_DIR / "skills" / "tc-core" / "SKILL.md"
TC_CORE_COMMANDS = PLUGIN_DIR / "skills" / "tc-core" / "commands"


def test_marketplace_manifest_exists():
    assert MARKETPLACE_JSON.exists(), f"expected {MARKETPLACE_JSON.relative_to(REPO)}"


def test_marketplace_manifest_parses():
    data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("name"), "marketplace.json: name is required"
    assert isinstance(data.get("plugins"), list), "marketplace.json: plugins must be a list"


def test_marketplace_lists_test_commander():
    data = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
    names = [p.get("name") for p in data.get("plugins", [])]
    assert "test-commander" in names, (
        f"marketplace.json plugins missing test-commander; got {names}"
    )


def test_plugin_manifest_exists():
    assert PLUGIN_JSON.exists(), f"expected {PLUGIN_JSON.relative_to(REPO)}"


def test_plugin_manifest_parses_and_has_required_fields():
    data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    assert data.get("name") == "test-commander"
    assert data.get("description"), "plugin.json: description is required"
    assert data.get("version"), "plugin.json: version is required"


def test_plugin_readme_exists():
    assert PLUGIN_README.exists(), f"expected {PLUGIN_README.relative_to(REPO)}"


def test_plugin_license_exists():
    assert PLUGIN_LICENSE.exists(), f"expected {PLUGIN_LICENSE.relative_to(REPO)}"


def test_tc_core_skill_exists():
    assert TC_CORE_SKILL.exists(), f"expected {TC_CORE_SKILL.relative_to(REPO)}"


def test_tc_core_skill_has_valid_frontmatter():
    text = TC_CORE_SKILL.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md must begin with a YAML frontmatter block delimited by ---"
    fm = match.group(1)
    name_match = re.search(r"^name:\s*(\S+)\s*$", fm, re.MULTILINE)
    desc_match = re.search(r"^description:\s*(.+?)\s*$", fm, re.MULTILINE)
    assert name_match, "frontmatter missing name"
    assert desc_match, "frontmatter missing description"
    assert name_match.group(1) == "tc-core", f"expected name: tc-core, got {name_match.group(1)}"
    assert re.fullmatch(r"[a-z][a-z0-9-]*", name_match.group(1)), "name must be kebab-case"
    assert desc_match.group(1).strip(), "description must be non-empty"


def test_tc_core_skill_references_three_commands():
    text = TC_CORE_SKILL.read_text(encoding="utf-8")
    for cmd in ("/tc:init", "/tc:status", "/tc:journal"):
        assert cmd in text, f"SKILL.md body must reference {cmd}"


# Note: a Phase 0 guard `test_no_command_behavior_yet` previously asserted
# that tc-core/commands/ was empty. Removed when Phase 1 Step 1.2 landed the
# first command file (init.md). Per-command coverage now lives in the
# individual command tests (test_init_workspace.py, etc.).
