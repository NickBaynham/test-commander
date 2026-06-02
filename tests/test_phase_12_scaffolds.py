"""Step 12.1 - Phase 12 sandboxed-environment scaffold.

Asserts the `tc-sandbox` skill, the `sandbox/providers/` abstraction skeleton
(the `SandboxProvider` interface), the `.github/workflows/` sandbox workflow
skeleton, and the seeded-sandbox fixture. The provider implementations land in
12.2, the six `/tc:sandbox-*` commands in 12.3, the workflows + safety guards in
12.4; this is the scaffold those sub-steps build toward.

A sandbox is an on-demand Test Commander environment launched from GitHub
Actions, and the Phase-10.5 governance pipeline runs inside it exactly as it does
locally — sandboxing never relaxes governance.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

SKILLS_ROOT = REPO / "plugins" / "test-commander" / "skills"
TCS = SKILLS_ROOT / "tc-sandbox"
SANDBOX = REPO / "sandbox"
WORKFLOWS = REPO / ".github" / "workflows"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-sandbox"
VERIFY_SKILLS = REPO / "scripts" / "verify_skills.py"

SUBDIRS = ["commands", "methodology", "templates"]
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict:
    match = FRONTMATTER_RE.match(text)
    assert match, "expected a YAML frontmatter block delimited by ---"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict), "frontmatter must parse to a mapping"
    return data


# ---------------------------------------------------------------------------
# tc-sandbox skill
# ---------------------------------------------------------------------------


def test_skill_directory_exists():
    assert TCS.is_dir(), "expected skills/tc-sandbox/"


def test_skill_md_frontmatter_parses_strict_yaml():
    data = parse_frontmatter((TCS / "SKILL.md").read_text(encoding="utf-8"))
    assert data.get("name") == "tc-sandbox"
    assert isinstance(data.get("description"), str) and data["description"].strip()


def test_skill_md_body_references_sandbox_and_governance():
    text = (TCS / "SKILL.md").read_text(encoding="utf-8").lower()
    for token in ("sandbox", "provider", "governance", "github actions"):
        assert token in text, f"tc-sandbox/SKILL.md must reference {token}"


def test_skill_subdirectories_exist():
    for sub in SUBDIRS:
        assert (TCS / sub).is_dir(), f"expected skills/tc-sandbox/{sub}/"


# ---------------------------------------------------------------------------
# sandbox/ provider abstraction
# ---------------------------------------------------------------------------


def test_sandbox_package_exists():
    assert (SANDBOX / "__init__.py").is_file()
    assert (SANDBOX / "providers" / "__init__.py").is_file()
    assert (SANDBOX / "providers" / "base.py").is_file()


def test_sandbox_provider_interface_is_abstract():
    from sandbox.providers.base import SandboxProvider, SandboxState

    # The interface cannot be instantiated directly (it is abstract).
    with pytest.raises(TypeError):
        SandboxProvider()  # type: ignore[abstract]
    for method in ("launch", "status", "sync", "teardown"):
        assert hasattr(SandboxProvider, method), f"SandboxProvider must declare {method}"
    # The state carrier exists.
    state = SandboxState(name="demo", provider="mock")
    assert state.status == "stopped"


# ---------------------------------------------------------------------------
# GitHub Actions workflow skeleton
# ---------------------------------------------------------------------------


def test_sandbox_workflow_skeleton_is_valid_yaml():
    wf = WORKFLOWS / "test-commander-sandbox.yml"
    assert wf.is_file(), "expected .github/workflows/test-commander-sandbox.yml"
    data = yaml.safe_load(wf.read_text(encoding="utf-8"))
    assert isinstance(data, dict) and "jobs" in data


# ---------------------------------------------------------------------------
# seeded-sandbox fixture
# ---------------------------------------------------------------------------


def test_seeded_sandbox_fixture():
    assert (FIXTURE / "README.md").is_file()
    config = yaml.safe_load((FIXTURE / "config.yaml").read_text(encoding="utf-8"))
    assert config.get("provider"), "fixture config must name a provider"
    targets = yaml.safe_load((FIXTURE / "targets.yaml").read_text(encoding="utf-8"))
    assert isinstance(targets, list) and any(t.get("unsafe") for t in targets), (
        "fixture must carry at least one unsafe target"
    )


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


def test_verify_skills_catalog_has_tc_sandbox_at_phase_12():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    assert re.search(r'"tc-sandbox":\s*12', text), "CATALOG must map tc-sandbox -> 12"
