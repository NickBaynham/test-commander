"""Step 11.7 - Phase 11 sign-off pre-flight tests.

Lands red before the plan/CHANGELOG/status closing edits, green after. Covers
Phase 11's surface: the tc-mcp skill, the apps/mcp server package + the expanded
Runtime API, the contract/round-trip/security/integration tests, the three new
docs, the verifier cap bump (>= 11, UNEXPECTED=0), lessons coverage for
11.1-11.7, plan + CHANGELOG closing markers, the status-line flip, and a
pytest-count floor. The SKILL.md must parse as strict YAML and carry no deferral
wording anywhere under the skill tree.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLAN = REPO / "planning" / "plan.md"
CHANGELOG = REPO / "CHANGELOG.md"
README = REPO / "README.md"
VERIFY_SKILLS = REPO / "scripts" / "verify_skills.py"
PLUGIN = REPO / "plugins" / "test-commander"
TCM = PLUGIN / "skills" / "tc-mcp"
MCP_APP = REPO / "apps" / "mcp"
API_APP = REPO / "apps" / "api"
CUSTOMIZING = REPO / "docs" / "user-guide" / "customizing-for-your-project.md"
INTEGRATING = REPO / "docs" / "user-guide" / "integrating.md"
TESTS_DIR = REPO / "tests"

MCP_FILES = ["tcmcp/__init__.py", "tcmcp/server.py", "tcmcp/__main__.py", "Dockerfile"]
METHODOLOGY = ["runtime-api.md", "mcp-tools.md"]
DOCS = ["docs/runtime-api.md", "docs/mcp-server.md", "docs/user-guide/integrating.md"]
PHASE_TEST_FILES = (
    "test_phase_11_scaffolds.py", "test_runtime_api.py", "test_mcp_server.py",
    "test_permission_gates.py", "test_phase_11_integration.py", "test_phase_11_signoff.py",
)
SUBSTEPS = ("11.1", "11.2", "11.3", "11.4", "11.5", "11.6", "11.7")


def test_all_phase_test_files_exist():
    for name in PHASE_TEST_FILES:
        assert (TESTS_DIR / name).is_file(), f"missing test file tests/{name}"


def test_mcp_server_package_exists():
    for rel in MCP_FILES:
        assert (MCP_APP / rel).is_file(), f"missing apps/mcp/{rel}"


def test_runtime_api_module_exists():
    assert (API_APP / "tcweb" / "runtime_api.py").is_file()


def test_skill_methodology_and_template_exist():
    for name in METHODOLOGY:
        assert (TCM / "methodology" / name).is_file(), f"missing methodology/{name}"
    assert (TCM / "templates" / "tool-schema.json").is_file()


def test_three_docs_exist():
    for rel in DOCS:
        assert (REPO / rel).is_file(), f"missing {rel}"


def test_verify_skills_catalog_has_tc_mcp():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    assert re.search(r'"tc-mcp":\s*11', text)


def test_verify_skills_cap_at_least_11():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r"DEFAULT_PHASE_CAP:\s*float\s*=\s*([\d.]+)", text)
    assert match and float(match.group(1)) >= 11, "DEFAULT_PHASE_CAP must be >= 11"


def test_skill_md_strict_yaml_and_no_deferral_anywhere():
    import yaml

    text = (TCM / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match, "tc-mcp/SKILL.md missing frontmatter"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict) and data.get("name") == "tc-mcp"
    # No deferral wording anywhere under the skill tree (SKILL.md + methodology).
    markers = ("behavior arrives in", "arrives in step", "lands in step",
               "coming in phase", "not yet shipped", "scaffold spec")
    for md in TCM.rglob("*.md"):
        low = md.read_text(encoding="utf-8").lower()
        for marker in markers:
            assert marker not in low, f"{md.name} carries deferral wording: {marker!r}"


def test_customizing_guide_records_phase_11():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 11 — what landed" in text


def test_integrating_guide_exists_and_shows_both_front_ends():
    text = INTEGRATING.read_text(encoding="utf-8").lower()
    assert "runtime api" in text and "mcp server" in text
    assert "approve" in text and "approver" in text


def test_lessons_cover_every_substep():
    text = PLAN.read_text(encoding="utf-8")
    for sub in SUBSTEPS:
        assert re.search(rf"- \*\*Step {re.escape(sub)} ", text), (
            f"plan.md Phase 11 Lessons missing an entry for Step {sub}"
        )


def test_changelog_phase_11_marked_complete():
    text = CHANGELOG.read_text(encoding="utf-8")
    assert re.search(
        r"^### Phase 11 — Runtime API and MCP Server \(complete (\d{4}-\d{2}-\d{2})\)",
        text, flags=re.MULTILINE,
    ), "CHANGELOG must mark Phase 11 complete with a date"


def test_plan_completed_has_phase_11_entry():
    text = PLAN.read_text(encoding="utf-8")
    assert re.search(
        r"^### Phase 11 — Runtime API and MCP Server \((\d{4}-\d{2}-\d{2})\)",
        text, flags=re.MULTILINE,
    ), "plan.md ## Completed must have a Phase 11 subsection with a date"


def test_plan_todo_phase_11_collapsed():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 11\s*$\n+(.*?)(?=^### Phase 12|^## Completed|\Z)",
        text, flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "could not locate the To Do Phase 11 block"
    body = match.group(1)
    assert not re.findall(r"^\s*-\s+\[ \]", body, flags=re.MULTILINE)
    assert re.search(r"Phase 11 complete \(\d{4}-\d{2}-\d{2}\)", body)


def test_status_line_marks_phase_11_complete():
    text = README.read_text(encoding="utf-8")
    assert re.search(r"Phase 11 complete \(\d{4}-\d{2}-\d{2}\)", text), (
        "README status line must mark Phase 11 complete"
    )


def test_pytest_count_meets_floor():
    count = 0
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if "fixtures" in path.parts:
            continue
        count += len(re.findall(r"^def\s+test_\w+", path.read_text(encoding="utf-8"),
                                flags=re.MULTILINE))
    assert count >= 1000, f"expected pytest test-def count >= 1000 at Phase 11 close, got {count}"
