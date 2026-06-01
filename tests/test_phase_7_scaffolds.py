"""Step 7.1 - Phase 7 skill scaffolds and the seeded-results fixture.

Asserts the three Phase 7 skill directories (`tc-run`, `tc-quality-report`,
`tc-evidence`), each SKILL.md's frontmatter (parsed under strict PyYAML from
the start, per the Phase 4 Step 4.8 lesson and the Phase 5/6 scaffold
discipline) and body (every command referenced; `tc-evidence` documents that
it is an internal cross-cutting indexer with no user-facing command), the
empty commands/ methodology/ templates/ directories (filled by 7.2-7.6), and
the shared seeded-results fixture: a recorded Playwright JSON report with at
least one passed, one failed, and one flaky (pass-on-retry) case, each
carrying resolvable `@req:`/`@cs:` linkage tags; the upstream Phase-6 chain
(`automation-map.md` + a generated `<area>.spec.ts`) so `/tc:run` can map
results to scenarios to requirements; and evidence stubs that exercise the
committed-vs-ignored policy split.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO / "plugins" / "test-commander" / "skills"

# skill name -> the /tc: commands its SKILL.md body must reference.
# tc-evidence is an internal indexer with no user-facing command (asserted
# separately below).
SKILLS: dict[str, list[str]] = {
    "tc-run": ["/tc:run", "/tc:analyze-results"],
    "tc-quality-report": ["/tc:report", "/tc:quality-gate"],
}
COMMANDLESS_SKILLS = ["tc-evidence"]
ALL_SKILLS = sorted([*SKILLS, *COMMANDLESS_SKILLS])
SUBDIRS = ["commands", "methodology", "templates"]

FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-results"
FIXTURE_README = FIXTURE_DIR / "README.md"
FIXTURE_RESULTS = FIXTURE_DIR / "results.json"
FIXTURE_MAP = FIXTURE_DIR / "automation-map.md"

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
REQ_TAG_RE = re.compile(r"@req:REQ-\d{3}")
CS_TAG_RE = re.compile(r"@cs:CS-\d{3}-\d{3}")


def parse_frontmatter(path: Path) -> dict:
    """Extract and strict-parse the YAML frontmatter block as a mapping."""
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    assert match, f"{path.name} must begin with a YAML frontmatter block delimited by ---"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict), f"{path.name} frontmatter must parse to a mapping"
    return data


def iter_test_statuses(report: dict) -> list[str]:
    """Walk a Playwright JSON report and collect every test-level status."""
    statuses: list[str] = []
    for suite in report.get("suites", []):
        for spec in suite.get("specs", []):
            for test in spec.get("tests", []):
                statuses.append(test.get("status", ""))
    return statuses


def iter_result_statuses(report: dict) -> list[str]:
    """Collect every per-attempt result status (passed / failed / ...)."""
    statuses: list[str] = []
    for suite in report.get("suites", []):
        for spec in suite.get("specs", []):
            for test in spec.get("tests", []):
                for result in test.get("results", []):
                    statuses.append(result.get("status", ""))
    return statuses


# ---------------------------------------------------------------------------
# Skill scaffolds (parametrized over the three Phase 7 skills)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("skill", ALL_SKILLS)
def test_skill_directory_exists(skill):
    assert (SKILLS_ROOT / skill).is_dir(), f"expected skills/{skill}/"


@pytest.mark.parametrize("skill", ALL_SKILLS)
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


def test_evidence_skill_md_documents_internal_indexer():
    """tc-evidence has no user-facing command; its SKILL.md must say so and
    name its invoker (tc-run)."""
    text = (SKILLS_ROOT / "tc-evidence" / "SKILL.md").read_text(encoding="utf-8").lower()
    assert "indexer" in text, "tc-evidence SKILL.md must describe itself as an indexer"
    assert "internal" in text, "tc-evidence SKILL.md must say it is internal (no user command)"
    assert "tc-run" in text, "tc-evidence SKILL.md must name tc-run as its invoker"


@pytest.mark.parametrize("skill", ALL_SKILLS)
@pytest.mark.parametrize("subdir", SUBDIRS)
def test_skill_subdirectories_exist(skill, subdir):
    path = SKILLS_ROOT / skill / subdir
    assert path.is_dir(), f"expected skills/{skill}/{subdir}/ (filled by 7.2-7.6)"


# ---------------------------------------------------------------------------
# seeded-results fixture
# ---------------------------------------------------------------------------


def test_fixture_directory_exists():
    assert FIXTURE_DIR.is_dir(), f"expected {FIXTURE_DIR.relative_to(REPO)}"


def test_fixture_readme_documents_schema_policy_and_linkage():
    text = FIXTURE_README.read_text(encoding="utf-8")
    lower = text.lower()
    assert "universal" in lower, "README must frame the narrative as universal (D19)"
    assert "@req:" in text and "@cs:" in text, "README must document the linkage convention"
    assert "evidence" in lower, "README must document the evidence-policy categories"


def test_results_json_parses_and_carries_passed_failed_flaky():
    report = json.loads(FIXTURE_RESULTS.read_text(encoding="utf-8"))
    assert isinstance(report, dict) and report.get("suites"), "results.json must be a PW report"
    test_statuses = set(iter_test_statuses(report))
    result_statuses = set(iter_result_statuses(report))
    assert "flaky" in test_statuses, "fixture must carry a flaky (pass-on-retry) test"
    assert "passed" in result_statuses, "fixture must carry a passed result"
    assert "failed" in result_statuses, "fixture must carry a failed result"


def test_results_json_cases_carry_resolvable_linkage_tags():
    text = FIXTURE_RESULTS.read_text(encoding="utf-8")
    assert REQ_TAG_RE.search(text), "results.json must carry resolvable @req: tags"
    assert CS_TAG_RE.search(text), "results.json must carry resolvable @cs: tags"


def test_fixture_carries_upstream_automation_map_and_generated_spec():
    """The Phase-6 chain so /tc:run maps results -> scenario -> requirement."""
    assert FIXTURE_MAP.is_file(), "fixture must carry a Phase-6 automation-map.md"
    map_text = FIXTURE_MAP.read_text(encoding="utf-8")
    assert REQ_TAG_RE.search(map_text) or re.search(r"REQ-\d{3}", map_text), (
        "automation-map.md must link scenarios to requirements"
    )
    specs = sorted(FIXTURE_DIR.glob("*.spec.ts"))
    assert specs, "fixture must carry a generated <area>.spec.ts"
    spec_text = specs[0].read_text(encoding="utf-8")
    assert REQ_TAG_RE.search(spec_text), "the generated spec must carry @req: provenance comments"


def test_fixture_evidence_stubs_exercise_the_policy_split():
    """A committed-class screenshot plus ignored-class video/trace stubs."""
    screenshots = list((FIXTURE_DIR / "evidence" / "screenshots").glob("*.png"))
    videos = list((FIXTURE_DIR / "evidence" / "videos").glob("*"))
    traces = list((FIXTURE_DIR / "evidence" / "traces").glob("*"))
    assert screenshots, "fixture must carry a committed-class screenshot stub"
    assert videos, "fixture must carry an ignored-class video stub"
    assert traces, "fixture must carry an ignored-class trace stub"
