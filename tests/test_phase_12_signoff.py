"""Step 12.7 - Phase 12 sign-off pre-flight tests.

Lands red before the plan/CHANGELOG/status closing edits, green after. Covers
Phase 12's surface: the tc-sandbox skill (six commands), the sandbox/ provider
abstraction + safety + governance, the workflow, the four docs, the verifier cap
bump (>= 12, UNEXPECTED=0), lessons coverage for 12.1-12.7, plan + CHANGELOG
closing markers, the status-line flip, and a pytest-count floor. The SKILL.md
must parse as strict YAML and carry no deferral wording anywhere under the tree.
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
TCS = PLUGIN / "skills" / "tc-sandbox"
SCRIPTS = PLUGIN / "scripts"
SANDBOX = REPO / "sandbox"
WORKFLOW = REPO / ".github" / "workflows" / "test-commander-sandbox.yml"
CUSTOMIZING = REPO / "docs" / "user-guide" / "customizing-for-your-project.md"
TESTS_DIR = REPO / "tests"

COMMANDS = ["sandbox-init", "sandbox-launch", "sandbox-status", "sandbox-sync",
            "sandbox-stop", "sandbox-export"]
HELPERS = ["sandbox_support.py", "sandbox_init.py", "sandbox_launch.py", "sandbox_status.py",
           "sandbox_sync.py", "sandbox_stop.py", "sandbox_export.py"]
SANDBOX_MODULES = ["__init__.py", "safety.py", "governance.py",
                   "providers/__init__.py", "providers/base.py", "providers/docker_compose.py",
                   "providers/stubs.py", "providers/mock.py"]
DOCS = ["docs/sandboxed-environments.md", "docs/github-actions-sandbox.md",
        "docs/no-code-tester-workflow.md", "docs/user-guide/sandbox.md"]
PHASE_TEST_FILES = (
    "test_phase_12_scaffolds.py", "test_sandbox_providers.py", "test_sandbox_commands.py",
    "test_sandbox_safety.py", "test_phase_12_integration.py", "test_phase_12_signoff.py",
)
SUBSTEPS = ("12.1", "12.2", "12.3", "12.4", "12.5", "12.6", "12.7")


def test_all_phase_test_files_exist():
    for name in PHASE_TEST_FILES:
        assert (TESTS_DIR / name).is_file(), f"missing test file tests/{name}"


def test_sandbox_package_modules_exist():
    for rel in SANDBOX_MODULES:
        assert (SANDBOX / rel).is_file(), f"missing sandbox/{rel}"


def test_command_helpers_exist():
    for name in HELPERS:
        assert (SCRIPTS / name).is_file(), f"missing scripts/{name}"


def test_command_pages_exist():
    for name in COMMANDS:
        assert (TCS / "commands" / f"{name}.md").is_file(), f"missing commands/{name}.md"


def test_methodology_and_template_exist():
    assert (TCS / "methodology" / "provider-abstraction.md").is_file()
    assert (TCS / "methodology" / "sandbox-safety.md").is_file()
    assert (TCS / "templates" / "sandbox-config.yaml").is_file()


def test_workflow_exists_and_is_manual_only():
    data = __import__("yaml").safe_load(WORKFLOW.read_text(encoding="utf-8"))
    on = data.get(True, data.get("on"))
    assert "workflow_dispatch" in on and "push" not in on and "pull_request" not in on


def test_four_docs_exist():
    for rel in DOCS:
        assert (REPO / rel).is_file(), f"missing {rel}"


def test_verify_skills_catalog_has_tc_sandbox():
    assert re.search(r'"tc-sandbox":\s*12', VERIFY_SKILLS.read_text(encoding="utf-8"))


def test_verify_skills_cap_at_least_12():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r"DEFAULT_PHASE_CAP:\s*float\s*=\s*([\d.]+)", text)
    assert match and float(match.group(1)) >= 12, "DEFAULT_PHASE_CAP must be >= 12"


def test_skill_md_strict_yaml_and_no_deferral_anywhere():
    import yaml

    text = (TCS / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match, "tc-sandbox/SKILL.md missing frontmatter"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict) and data.get("name") == "tc-sandbox"
    markers = ("behavior arrives in", "arrives in step", "lands in step",
               "coming in phase", "not yet shipped", "scaffold spec")
    for md in TCS.rglob("*.md"):
        low = md.read_text(encoding="utf-8").lower()
        for marker in markers:
            assert marker not in low, f"{md.name} carries deferral wording: {marker!r}"


def test_customizing_guide_records_phase_12():
    assert "Phase 12 sandbox" in CUSTOMIZING.read_text(encoding="utf-8")


def test_lessons_cover_every_substep():
    text = PLAN.read_text(encoding="utf-8")
    for sub in SUBSTEPS:
        assert re.search(rf"- \*\*Step {re.escape(sub)} ", text), (
            f"plan.md Phase 12 Lessons missing an entry for Step {sub}"
        )


def test_changelog_phase_12_marked_complete():
    assert re.search(
        r"^### Phase 12 — Sandboxed Testing Environment \(complete (\d{4}-\d{2}-\d{2})\)",
        CHANGELOG.read_text(encoding="utf-8"), flags=re.MULTILINE,
    ), "CHANGELOG must mark Phase 12 complete with a date"


def test_plan_completed_has_phase_12_entry():
    assert re.search(
        r"^### Phase 12 — Sandboxed Testing Environment \((\d{4}-\d{2}-\d{2})\)",
        PLAN.read_text(encoding="utf-8"), flags=re.MULTILINE,
    ), "plan.md ## Completed must have a Phase 12 subsection with a date"


def test_plan_todo_phase_12_collapsed():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 12\s*$\n+(.*?)(?=^### Phase 13|^## Completed|\Z)",
        text, flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "could not locate the To Do Phase 12 block"
    body = match.group(1)
    assert not re.findall(r"^\s*-\s+\[ \]", body, flags=re.MULTILINE)
    assert re.search(r"Phase 12 complete \(\d{4}-\d{2}-\d{2}\)", body)


def test_status_line_marks_phase_12_complete():
    # Robust to later phases: the rolling status line names the latest complete
    # phase, so Phase 12 or any later phase satisfies "Phase 12 has closed".
    text = README.read_text(encoding="utf-8")
    pattern = r"Phase (\d+(?:\.\d+)?) complete \(\d{4}-\d{2}-\d{2}\)"
    completed = [float(m) for m in re.findall(pattern, text)]
    assert completed and max(completed) >= 12, "README must mark Phase 12 (or later) complete"


def test_pytest_count_meets_floor():
    count = 0
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if "fixtures" in path.parts:
            continue
        count += len(re.findall(r"^def\s+test_\w+", path.read_text(encoding="utf-8"),
                                flags=re.MULTILINE))
    assert count >= 1050, f"expected pytest test-def count >= 1050 at Phase 12 close, got {count}"
