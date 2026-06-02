"""Step 10.9 - Phase 10 sign-off pre-flight tests.

Lands red before the plan/CHANGELOG closing edits, green after. Covers Phase
10's surface: the tc-web skill (five commands), the FastAPI backend modules, the
five plugin helpers, the five command pages, the methodology, the Next.js
frontend (pages + nav + chat), the three docs, the verifier cap bump (`>=`),
lessons coverage for 10.1-10.9, plan + CHANGELOG closing markers, and a
pytest-count floor. The SKILL.md must parse as strict YAML and carry no deferral
wording.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLAN = REPO / "planning" / "plan.md"
CHANGELOG = REPO / "CHANGELOG.md"
VERIFY_SKILLS = REPO / "scripts" / "verify_skills.py"
PLUGIN = REPO / "plugins" / "test-commander"
SCRIPTS = PLUGIN / "scripts"
TCW = PLUGIN / "skills" / "tc-web"
APPS = REPO / "apps"
CUSTOMIZING = REPO / "docs" / "user-guide" / "customizing-for-your-project.md"
WALKTHROUGH = REPO / "docs" / "user-guide" / "web-console.md"
TESTS_DIR = REPO / "tests"

COMMANDS = ["/tc:web-init", "/tc:web-start", "/tc:web-sync",
            "/tc:web-index-artifacts", "/tc:web-export"]
COMMAND_PAGES = ["web-init", "web-start", "web-sync", "web-index-artifacts", "web-export"]
HELPERS = ["web_init.py", "web_start.py", "web_sync.py",
           "web_index_artifacts.py", "web_export.py"]
BACKEND = ["main.py", "config.py", "db.py", "indexer.py", "queries.py",
           "routes.py", "sse.py", "proposals.py", "chat.py", "exporter.py"]
PHASE_10_TEST_FILES = (
    "test_phase_10_scaffolds.py", "test_web_indexer.py", "test_web_api.py",
    "test_phase_10_frontend.py", "test_web_chat.py", "test_web_export.py",
    "test_phase_10_integration.py", "test_phase_10_signoff.py",
)
PAGES = ["", "quality-report", "journal", "sessions", "requirements", "runs",
         "evidence", "chat", "settings"]


def test_all_phase_10_test_files_exist():
    for name in PHASE_10_TEST_FILES:
        assert (TESTS_DIR / name).is_file(), f"missing Phase 10 test file: tests/{name}"


def test_all_backend_modules_exist():
    for name in BACKEND:
        assert (APPS / "api" / "tcweb" / name).is_file(), f"missing backend module {name}"


def test_all_helpers_exist():
    for name in HELPERS:
        assert (SCRIPTS / name).is_file(), f"missing helper scripts/{name}"


def test_all_command_pages_exist():
    for name in COMMAND_PAGES:
        assert (TCW / "commands" / f"{name}.md").is_file(), f"missing command page {name}.md"


def test_methodology_exists():
    assert (TCW / "methodology" / "web-architecture.md").is_file()


def test_frontend_pages_exist():
    app_dir = APPS / "web" / "app"
    for route in PAGES:
        page = app_dir / route / "page.tsx" if route else app_dir / "page.tsx"
        assert page.is_file(), f"missing frontend page app/{route}/page.tsx"
    assert (APPS / "web" / "components" / "Nav.tsx").is_file()
    assert (APPS / "web" / "components" / "LiveBadge.tsx").is_file()


def test_docs_exist():
    for rel in ("docs/web-console.md", "docs/runtime-api.md", "docs/user-guide/web-console.md"):
        assert (REPO / rel).is_file(), f"missing {rel}"


def test_verify_skills_catalog_has_tc_web_at_phase_10():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    assert re.search(r'"tc-web":\s*10', text), "CATALOG must map tc-web -> 10"


def test_verify_skills_default_phase_cap_at_least_10():
    text = VERIFY_SKILLS.read_text(encoding="utf-8")
    match = re.search(r"DEFAULT_PHASE_CAP:\s*float\s*=\s*(\d+)", text)
    assert match and int(match.group(1)) >= 10, "DEFAULT_PHASE_CAP must be >= 10 at Phase 10 close"


def test_skill_md_lists_all_five_commands():
    text = (TCW / "SKILL.md").read_text(encoding="utf-8")
    for cmd in COMMANDS:
        assert cmd in text, f"tc-web/SKILL.md missing {cmd}"


def test_skill_md_has_no_deferral_wording():
    text = (TCW / "SKILL.md").read_text(encoding="utf-8").lower()
    for marker in ("behavior arrives in", "coming in phase", "not yet shipped",
                   "once that step ships"):
        assert marker not in text, f"tc-web/SKILL.md carries deferral wording: {marker!r}"


def test_skill_md_frontmatter_parses_strict_yaml():
    import yaml

    text = (TCW / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert match, "tc-web/SKILL.md missing YAML frontmatter"
    data = yaml.safe_load(match.group(1))
    assert isinstance(data, dict) and data.get("name") == "tc-web"
    assert isinstance(data.get("description"), str) and data["description"].strip()


def test_customizing_guide_records_phase_10_no_new_surface():
    text = CUSTOMIZING.read_text(encoding="utf-8")
    assert "Phase 10 — what landed (no new extensible surface)" in text


def test_phase_10_lessons_learned_covers_every_substep():
    text = PLAN.read_text(encoding="utf-8")
    for substep in ("10.1", "10.2", "10.3", "10.4", "10.5", "10.6", "10.7", "10.8", "10.9"):
        assert re.search(rf"- \*\*Step {re.escape(substep)} ", text), (
            f"plan.md Phase 10 Lessons learned missing an entry for Step {substep}"
        )


def test_changelog_phase_10_marked_complete():
    text = CHANGELOG.read_text(encoding="utf-8")
    assert re.search(
        r"^### Phase 10 — Web console MVP \(complete (\d{4}-\d{2}-\d{2})\)",
        text, flags=re.MULTILINE,
    ), "CHANGELOG must mark Phase 10 complete with a date"


def test_plan_completed_has_phase_10_entry():
    text = PLAN.read_text(encoding="utf-8")
    assert re.search(
        r"^### Phase 10 — Web console MVP \((\d{4}-\d{2}-\d{2})\)",
        text, flags=re.MULTILINE,
    ), "plan.md ## Completed must have a Phase 10 subsection with a date"


def test_plan_todo_phase_10_collapsed_to_marker():
    text = PLAN.read_text(encoding="utf-8")
    match = re.search(
        r"^### Phase 10\s*$\n+(.*?)(?=^### Phase 10\.5|^## Completed|\Z)",
        text, flags=re.MULTILINE | re.DOTALL,
    )
    assert match, "could not locate the To Do Phase 10 block"
    body = match.group(1)
    unchecked = re.findall(r"^\s*-\s+\[ \]", body, flags=re.MULTILINE)
    assert not unchecked, f"To Do Phase 10 still has {len(unchecked)} unchecked items"
    assert re.search(r"Phase 10 complete \(\d{4}-\d{2}-\d{2}\)", body), (
        "To Do Phase 10 must be a single marker line"
    )


def test_make_has_run_and_web_lanes():
    body = (REPO / "Makefile").read_text(encoding="utf-8")
    assert "docker compose" in body
    assert re.search(r"^web-test:", body, flags=re.MULTILINE)
    assert re.search(r"^web-e2e:", body, flags=re.MULTILINE)


def test_pytest_count_meets_phase_10_floor():
    count = 0
    for path in sorted(TESTS_DIR.rglob("test_*.py")):
        if "fixtures" in path.parts:
            continue
        count += len(re.findall(r"^def\s+test_\w+", path.read_text(encoding="utf-8"),
                                flags=re.MULTILINE))
    assert count >= 865, f"expected pytest test-def count >= 865 at Phase 10 close, got {count}"


def test_phase_10_walkthrough_exists():
    assert WALKTHROUGH.is_file(), "docs/user-guide/web-console.md missing"
    text = WALKTHROUGH.read_text(encoding="utf-8")
    for cmd in ("/tc:web-init", "/tc:web-index-artifacts", "/tc:web-export"):
        assert cmd in text, f"web-console.md missing reference to {cmd}"
