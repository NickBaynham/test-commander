"""Step 10.5.1 - Phase 10.5 governance scaffold.

Asserts the `tc-governance` skill, the `runtime/agent_adapters/` and
`runtime/governance/` trees, the policy/audit workspace template slots, and the
seeded-governance fixture. The pipeline components and the real adapters land in
10.5.2-10.5.10; this is the scaffold the four RED security tests drive toward.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO / "plugins" / "test-commander" / "skills"
TCG = SKILLS_ROOT / "tc-governance"
RUNTIME = REPO / "runtime"
TEMPLATE = REPO / "plugins" / "test-commander" / "templates" / "workspace"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-governance"
VERIFY_SKILLS = REPO / "scripts" / "verify_skills.py"

SUBDIRS = ["commands", "methodology", "templates"]
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    match = FRONTMATTER_RE.match(text)
    assert match, "expected a YAML frontmatter block delimited by ---"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict), "frontmatter must parse to a mapping"
    return data


def test_skill_directory_exists():
    assert TCG.is_dir(), "expected skills/tc-governance/"


def test_skill_md_frontmatter_parses_strict_yaml():
    data = parse_frontmatter((TCG / "SKILL.md").read_text(encoding="utf-8"))
    assert data.get("name") == "tc-governance"
    assert isinstance(data.get("description"), str) and data["description"].strip()


def test_skill_md_body_references_the_pipeline():
    text = (TCG / "SKILL.md").read_text(encoding="utf-8").lower()
    for token in ("permission", "approval", "audit", "bounded"):
        assert token in text, f"tc-governance/SKILL.md must reference {token}"


def test_skill_subdirectories_exist():
    for sub in SUBDIRS:
        assert (TCG / sub).is_dir(), f"expected skills/tc-governance/{sub}/"


def test_agent_adapter_tree_exists():
    assert (RUNTIME / "agent_adapters" / "__init__.py").is_file()
    for name in ("base.py", "mock_agent.py", "claude_code_cli.py", "anthropic_api.py"):
        assert (RUNTIME / "agent_adapters" / name).is_file(), f"missing agent_adapters/{name}"


def test_governance_package_exists():
    assert (RUNTIME / "governance" / "__init__.py").is_file()
    assert (RUNTIME / "governance" / "pipeline.py").is_file()


def test_policy_and_audit_template_slots_exist():
    assert (TEMPLATE / "policy" / "permissions.yaml").is_file()
    assert (TEMPLATE / "policy" / "approvals.yaml").is_file()
    assert (TEMPLATE / "audit" / "actions.jsonl").is_file()
    assert (TEMPLATE / "audit" / "approvals").is_dir()


def test_seeded_governance_fixture():
    assert (FIXTURE / "README.md").is_file()
    perms = yaml.safe_load((FIXTURE / "permissions.yaml").read_text(encoding="utf-8"))
    assert "Viewer" in perms and "Admin" in perms, "fixture must carry a role set"
    requests = yaml.safe_load((FIXTURE / "requests.yaml").read_text(encoding="utf-8"))
    assert any(r.get("unsafe") for r in requests), "fixture must carry at least one unsafe request"


def test_verify_skills_catalog_has_tc_governance_at_phase_10_5():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    assert re.search(r'"tc-governance":\s*10\.5', text), "CATALOG must map tc-governance -> 10.5"
