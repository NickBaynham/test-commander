"""Step 8.1 - Phase 8 skill scaffold and the seeded-learning fixture.

Asserts the `tc-learning` skill directory, its SKILL.md (strict-PyYAML
frontmatter from the start, body referencing all six commands), the empty
commands/ methodology/ templates/ directories (filled by 8.2-8.7), and the
shared seeded-learning fixture: the upstream artifacts the capture commands
read (a Phase-7 analysis.md, an exploration note, a resolved-feedback
open-questions excerpt) plus a lessons-inbox.md pre-seeded with one candidate
per review-classification (accepted / rejected / needs-human-review), each
carrying valid `tc-lesson/v1` frontmatter and a `# knowledge: <classification>`
marker.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO / "plugins" / "test-commander" / "skills"
TCL = SKILLS_ROOT / "tc-learning"

COMMANDS = [
    "/tc:learn",
    "/tc:learn-from-failures",
    "/tc:learn-from-exploration",
    "/tc:learn-from-feedback",
    "/tc:review-lessons",
    "/tc:promote-lessons",
]
SUBDIRS = ["commands", "methodology", "templates"]

FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-learning"
FIXTURE_README = FIXTURE_DIR / "README.md"
FIXTURE_INBOX = FIXTURE_DIR / "lessons-inbox.md"
FIXTURE_ANALYSIS = FIXTURE_DIR / "analysis.md"
FIXTURE_OPEN_Q = FIXTURE_DIR / "open-questions.md"

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
LESSON_BLOCK_RE = re.compile(r"^---\n(.*?)\n---\n(.*?)(?=^---\n|\Z)", re.DOTALL | re.MULTILINE)
KNOWLEDGE_RE = re.compile(r"#\s*knowledge:\s*([\w-]+)")
CLASSIFICATIONS = {"accepted", "rejected", "needs-human-review"}


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
    assert TCL.is_dir(), "expected skills/tc-learning/"


def test_skill_md_frontmatter_parses_strict_yaml():
    data = parse_frontmatter((TCL / "SKILL.md").read_text(encoding="utf-8"))
    assert data.get("name") == "tc-learning"
    desc = data.get("description")
    assert isinstance(desc, str) and desc.strip(), "description must be a non-empty string"


def test_skill_md_body_references_all_six_commands():
    text = (TCL / "SKILL.md").read_text(encoding="utf-8")
    for cmd in COMMANDS:
        assert cmd in text, f"tc-learning/SKILL.md body must reference {cmd}"


def test_skill_subdirectories_exist():
    for sub in SUBDIRS:
        assert (TCL / sub).is_dir(), f"expected skills/tc-learning/{sub}/ (filled by 8.2-8.7)"


# ---------------------------------------------------------------------------
# seeded-learning fixture
# ---------------------------------------------------------------------------


def test_fixture_directory_and_upstream_artifacts_exist():
    assert FIXTURE_DIR.is_dir(), "expected tests/fixtures/seeded-learning/"
    assert FIXTURE_ANALYSIS.is_file(), "fixture must carry a Phase-7 analysis.md"
    assert FIXTURE_OPEN_Q.is_file(), "fixture must carry a resolved-feedback open-questions.md"
    exploration = list(FIXTURE_DIR.glob("SESS-*.md"))
    assert exploration, "fixture must carry an exploration note (SESS-*.md)"


def test_fixture_readme_documents_schema_governance_and_linkage():
    text = FIXTURE_README.read_text(encoding="utf-8")
    lower = text.lower()
    assert "tc-lesson/v1" in text, "README must document the lesson schema"
    assert "universal" in lower, "README must frame the narrative as universal (D19)"
    for word in ("accepted", "rejected", "needs-human-review"):
        assert word in lower, f"README must document the {word} classification"


def test_fixture_analysis_carries_triaged_failures():
    text = FIXTURE_ANALYSIS.read_text(encoding="utf-8")
    assert "product-defect" in text and "flaky" in text, (
        "analysis.md must carry a product-defect and a flaky row for learn-from-failures"
    )


def test_seeded_inbox_has_one_candidate_per_classification():
    text = FIXTURE_INBOX.read_text(encoding="utf-8")
    blocks = LESSON_BLOCK_RE.findall(text)
    assert len(blocks) >= 3, f"inbox must carry >= 3 candidates, got {len(blocks)}"
    seen: set[str] = set()
    for fm_text, body in blocks:
        fm = yaml.safe_load(fm_text)
        assert fm.get("schema") == "tc-lesson/v1", "each candidate must be tc-lesson/v1"
        assert fm.get("id", "").startswith("LESSON-"), "each candidate needs a LESSON-NNN id"
        assert fm.get("status") == "candidate", "inbox candidates carry status: candidate"
        assert fm.get("origin"), "each candidate must carry path:line origin provenance"
        m = KNOWLEDGE_RE.search(body)
        assert m, "each candidate needs a `# knowledge: <classification>` marker"
        seen.add(m.group(1))
    assert seen >= CLASSIFICATIONS, (
        f"inbox must seed one candidate per classification; missing {CLASSIFICATIONS - seen}"
    )
