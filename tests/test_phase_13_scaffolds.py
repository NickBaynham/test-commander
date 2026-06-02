"""Step 13.1 - Phase 13 continuous-quality scaffold.

Asserts the `tc-continuous-quality` skill, the `continuous/` autonomy package
skeleton (the five modes), the continuous-quality CI workflow skeleton, and the
seeded-continuous fixture (a sample PR diff + an impacted-feature map). The
commands land across 13.2-13.5, the workflow in 13.6; this is the scaffold those
sub-steps build toward.

Continuous mode runs through the same Phase-10.5 pipeline; the configured
autonomy level (0-4) decides which permission levels are auto-approved, and
nothing above it executes without explicit human approval.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

SKILLS_ROOT = REPO / "plugins" / "test-commander" / "skills"
TCQ = SKILLS_ROOT / "tc-continuous-quality"
CONTINUOUS = REPO / "continuous"
WORKFLOW = REPO / ".github" / "workflows" / "test-commander-continuous-quality.yml"
FIXTURE = REPO / "tests" / "fixtures" / "seeded-continuous"
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
# tc-continuous-quality skill
# ---------------------------------------------------------------------------


def test_skill_directory_exists():
    assert TCQ.is_dir(), "expected skills/tc-continuous-quality/"


def test_skill_md_frontmatter_parses_strict_yaml():
    data = parse_frontmatter((TCQ / "SKILL.md").read_text(encoding="utf-8"))
    assert data.get("name") == "tc-continuous-quality"
    assert isinstance(data.get("description"), str) and data["description"].strip()


def test_skill_md_body_references_autonomy_and_the_pipeline():
    text = (TCQ / "SKILL.md").read_text(encoding="utf-8").lower()
    for token in ("autonomy", "pipeline", "impact", "pull request"):
        assert token in text, f"tc-continuous-quality/SKILL.md must reference {token}"


def test_skill_subdirectories_exist():
    for sub in SUBDIRS:
        assert (TCQ / sub).is_dir(), f"expected skills/tc-continuous-quality/{sub}/"


# ---------------------------------------------------------------------------
# continuous/ autonomy package
# ---------------------------------------------------------------------------


def test_continuous_package_exists():
    assert (CONTINUOUS / "__init__.py").is_file()
    assert (CONTINUOUS / "autonomy.py").is_file()


def test_five_autonomy_modes_defined():
    from continuous.autonomy import AUTONOMY_MODES

    assert set(AUTONOMY_MODES) == {0, 1, 2, 3, 4}
    assert AUTONOMY_MODES[0] == "read-only-advisor"
    assert AUTONOMY_MODES[4] == "governed-autonomy"


# ---------------------------------------------------------------------------
# CI workflow skeleton
# ---------------------------------------------------------------------------


def test_workflow_skeleton_has_the_four_triggers():
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    on = data.get(True, data.get("on"))  # PyYAML parses bare `on:` as the bool True
    for trigger in ("pull_request", "push", "schedule", "workflow_dispatch"):
        assert trigger in on, f"workflow must trigger on {trigger}"
    assert "jobs" in data


# ---------------------------------------------------------------------------
# seeded-continuous fixture
# ---------------------------------------------------------------------------


def test_seeded_continuous_fixture():
    assert (FIXTURE / "README.md").is_file()
    assert (FIXTURE / "pr-diff.txt").is_file(), "fixture must carry a sample PR diff"
    impact = yaml.safe_load((FIXTURE / "impact-map.yaml").read_text(encoding="utf-8"))
    assert isinstance(impact, list) and impact, "fixture must carry an impacted-feature map"
    assert all("pattern" in e and "features" in e for e in impact)


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


def test_verify_skills_catalog_has_tc_continuous_quality_at_phase_13():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    assert re.search(r'"tc-continuous-quality":\s*13', text), "CATALOG must map -> 13"
