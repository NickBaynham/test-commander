"""Step 10.5.13 - Phase 10.5 sign-off pre-flight tests.

Lands red before the plan/CHANGELOG closing edits, green after. Covers Phase
10.5's surface: the tc-governance skill, the runtime governance modules + agent
adapters, the four security tests + integration smoke, the six docs, the verifier
cap bump (>= 10.5), lessons coverage for 10.5.1-10.5.13, plan + CHANGELOG closing
markers, and a pytest-count floor. The SKILL.md must parse as strict YAML and
carry no deferral wording.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLAN = REPO / "planning" / "plan.md"
CHANGELOG = REPO / "CHANGELOG.md"
VERIFY_SKILLS = REPO / "scripts" / "verify_skills.py"
PLUGIN = REPO / "plugins" / "test-commander"
TCG = PLUGIN / "skills" / "tc-governance"
RUNTIME = REPO / "runtime"
CUSTOMIZING = REPO / "docs" / "user-guide" / "customizing-for-your-project.md"
WALKTHROUGH = REPO / "docs" / "user-guide" / "governance.md"
TESTS_DIR = REPO / "tests"

GOVERNANCE_MODULES = ["policy.py", "intent.py", "planner.py", "approval.py",
                      "executor.py", "validation.py", "audit.py", "pipeline.py"]
ADAPTERS = ["base.py", "mock_agent.py", "claude_code_cli.py", "anthropic_api.py"]
METHODOLOGY = ["agent-adapters.md", "permission-policy.md", "intent-and-planning.md",
               "approval-and-audit.md", "output-validation.md"]
DOCS = ["docs/controlled-agent-execution.md", "docs/security-and-permissions.md",
        "docs/chat-command-governance.md", "docs/runtime-approval-flow.md",
        "docs/agent-adapters.md", "docs/user-guide/governance.md"]
PHASE_TEST_FILES = (
    "test_phase_10_5_scaffolds.py", "test_phase_10_5_security.py",
    "test_agent_adapters.py", "test_policy.py", "test_intent.py", "test_planner.py",
    "test_approval.py", "test_executor.py", "test_validation.py", "test_audit.py",
    "test_claude_adapter_and_console.py", "test_phase_10_5_integration.py",
    "test_phase_10_5_signoff.py",
)


def test_all_phase_test_files_exist():
    for name in PHASE_TEST_FILES:
        assert (TESTS_DIR / name).is_file(), f"missing test file tests/{name}"


def test_governance_modules_exist():
    for name in GOVERNANCE_MODULES:
        assert (RUNTIME / "governance" / name).is_file(), f"missing governance/{name}"


def test_agent_adapters_exist():
    for name in ADAPTERS:
        assert (RUNTIME / "agent_adapters" / name).is_file(), f"missing agent_adapters/{name}"


def test_methodology_files_exist():
    for name in METHODOLOGY:
        assert (TCG / "methodology" / name).is_file(), f"missing methodology/{name}"


def test_six_governance_docs_exist():
    for rel in DOCS:
        assert (REPO / rel).is_file(), f"missing {rel}"


def test_verify_skills_catalog_has_tc_governance():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    assert re.search(r'"tc-governance":\s*10\.5', text)


def test_verify_skills_cap_at_least_10_5():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r"DEFAULT_PHASE_CAP:\s*float\s*=\s*([\d.]+)", text)
    assert match and float(match.group(1)) >= 10.5, "DEFAULT_PHASE_CAP must be >= 10.5"


def test_skill_md_strict_yaml_and_no_deferral():
    import yaml

    text = (TCG / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match, "tc-governance/SKILL.md missing frontmatter"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict) and data.get("name") == "tc-governance"
    low = text.lower()
    for marker in ("behavior arrives in", "coming in phase", "not yet shipped",
                   "until each lands", "once that step ships"):
        assert marker not in low, f"SKILL.md carries deferral wording: {marker!r}"


def test_customizing_guide_has_governance_surface():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 10.5 governance" in text
    assert "permissions.yaml" in text and "approvals.yaml" in text


def test_lessons_cover_every_substep():
    text = PLAN.read_text(encoding="utf-8")
    for sub in ("10.5.1", "10.5.2", "10.5.3", "10.5.4", "10.5.5", "10.5.6", "10.5.7",
                "10.5.8", "10.5.9", "10.5.10", "10.5.11", "10.5.12", "10.5.13"):
        assert re.search(rf"- \*\*Step {re.escape(sub)} ", text), (
            f"plan.md Phase 10.5 Lessons missing an entry for Step {sub}"
        )


def test_changelog_phase_10_5_marked_complete():
    text = CHANGELOG.read_text(encoding="utf-8")
    assert re.search(
        r"^### Phase 10\.5 — Controlled agent execution and policy-governed chat "
        r"\(complete (\d{4}-\d{2}-\d{2})\)",
        text, flags=re.MULTILINE,
    ), "CHANGELOG must mark Phase 10.5 complete with a date"


def test_plan_completed_has_phase_10_5_entry():
    text = PLAN.read_text(encoding="utf-8")
    assert re.search(
        r"^### Phase 10\.5 — Controlled agent execution and policy-governed chat "
        r"\((\d{4}-\d{2}-\d{2})\)",
        text, flags=re.MULTILINE,
    ), "plan.md ## Completed must have a Phase 10.5 subsection with a date"


def test_plan_todo_phase_10_5_collapsed():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 10\.5\s*$\n+(.*?)(?=^### Phase 11|^## Completed|\Z)",
        text, flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "could not locate the To Do Phase 10.5 block"
    body = match.group(1)
    assert not re.findall(r"^\s*-\s+\[ \]", body, flags=re.MULTILINE)
    assert re.search(r"Phase 10\.5 complete \(\d{4}-\d{2}-\d{2}\)", body)


def test_pytest_count_meets_floor():
    count = 0
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if "fixtures" in path.parts:
            continue
        count += len(re.findall(r"^def\s+test_\w+", path.read_text(encoding="utf-8"),
                                flags=re.MULTILINE))
    assert count >= 950, f"expected pytest test-def count >= 950 at Phase 10.5 close, got {count}"


def test_governance_walkthrough_exists():
    assert WALKTHROUGH.is_file()
    text = WALKTHROUGH.read_text(encoding="utf-8")
    assert "approval" in text.lower() and "audit" in text.lower()
