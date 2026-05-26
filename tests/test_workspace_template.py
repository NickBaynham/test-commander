"""Step 1.1 — workspace template tests.

Asserts that templates/workspace/ contains every directory and starter file
from the Workspace Layout block in planning/plan.md, with valid starter
content. REQUIRED_DIRS and REQUIRED_FILES are kept in sync with the plan
by code review (failure mode documented in Step 1.1 of the plan).
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "plugins" / "test-commander" / "templates" / "workspace"

REQUIRED_DIRS = [
    "documents",
    "documents/uploaded",
    "requirements",
    "product-knowledge",
    "charters",
    "exploration-notes",
    "test-ideas",
    "bdd",
    "bdd/features",
    "bdd/summaries",
    "automation-plan",
    "test-data",
    "test-data/seed",
    "test-data/scenarios",
    "test-data/factories",
    "risk-register",
    "quality-report",
    "quality-report/history",
    "traceability",
    "evidence",
    "evidence/screenshots",
    "evidence/videos",
    "evidence/traces",
    "evidence/logs",
    "learning",
    "visuals",
    "visuals/mermaid",
    "visuals/svg",
    "visuals/png",
    "visuals/infographic",
    "sessions",
    "journal",
    "runs",
    "policy",
    "audit",
    "audit/approvals",
]

# Explicitly-named files from the Workspace Layout block. Per-directory
# README.md placeholders are allowed extras (not in this list).
REQUIRED_FILES = [
    "project.md",
    "config.yaml",
    "methodology.md",
    "documents/index.md",
    "requirements/requirements-inventory.md",
    "requirements/requirements-review.md",
    "requirements/user-story-review.md",
    "requirements/acceptance-criteria-review.md",
    "requirements/open-questions.md",
    "requirements/requirements-coverage.md",
    "product-knowledge/system-model.md",
    "product-knowledge/business-rules.md",
    "product-knowledge/user-journeys.md",
    "product-knowledge/entities.md",
    "product-knowledge/assumptions.md",
    "product-knowledge/code-derived-model.md",
    "product-knowledge/spec-derived-model.md",
    "product-knowledge/documentation-model.md",
    "product-knowledge/api-model.md",
    "test-data/README.md",
    "risk-register/risk-register.md",
    "quality-report/current-quality-report.md",
    "traceability/requirements-map.md",
    "traceability/test-map.md",
    "traceability/automation-map.md",
    "learning/lessons-inbox.md",
    "learning/accepted-lessons.md",
    "learning/rejected-lessons.md",
    "learning/needs-human-review.md",
    "policy/permissions.yaml",
    "policy/approvals.yaml",
    "audit/actions.jsonl",
]

PHASE_NOTE_RE = re.compile(r"Phase\s+\d")
H1_RE = re.compile(r"^#\s+\S", re.MULTILINE)


def test_template_root_exists():
    assert TEMPLATE.exists() and TEMPLATE.is_dir(), (
        f"expected template at {TEMPLATE.relative_to(REPO)}"
    )


def test_all_required_directories_exist():
    missing = [d for d in REQUIRED_DIRS if not (TEMPLATE / d).is_dir()]
    assert not missing, f"template missing directories: {missing}"


def test_all_required_files_exist():
    missing = [f for f in REQUIRED_FILES if not (TEMPLATE / f).is_file()]
    assert not missing, f"template missing files: {missing}"


def test_markdown_starter_files_have_heading_and_phase_note():
    markdown_files = [f for f in REQUIRED_FILES if f.endswith(".md")]
    failures = []
    for rel in markdown_files:
        text = (TEMPLATE / rel).read_text(encoding="utf-8")
        if not H1_RE.search(text):
            failures.append(f"{rel}: missing H1 heading")
            continue
        if not PHASE_NOTE_RE.search(text):
            failures.append(f"{rel}: missing 'Phase N' note")
    assert not failures, "starter Markdown issues:\n  " + "\n  ".join(failures)


def test_yaml_starter_files_have_comment_header_with_phase_note():
    yaml_files = [f for f in REQUIRED_FILES if f.endswith(".yaml")]
    failures = []
    for rel in yaml_files:
        text = (TEMPLATE / rel).read_text(encoding="utf-8")
        if not text.lstrip().startswith("#"):
            failures.append(f"{rel}: missing '#' comment header")
            continue
        if not PHASE_NOTE_RE.search(text):
            failures.append(f"{rel}: missing 'Phase N' note in header")
    assert not failures, "starter YAML issues:\n  " + "\n  ".join(failures)


def test_actions_jsonl_starter_is_empty():
    """JSONL has no comment syntax; the starter file is empty (append-only log)."""
    path = TEMPLATE / "audit" / "actions.jsonl"
    assert path.exists(), "audit/actions.jsonl missing"
    content = path.read_text(encoding="utf-8").strip()
    assert content == "", (
        f"audit/actions.jsonl should be empty in the starter; got: {content[:80]!r}"
    )


def test_per_directory_readmes_are_well_formed():
    """Every directory that exists should be reachable through git (no empty dirs).
    We commit a README.md in each otherwise-empty directory; those READMEs follow
    the same heading + phase-note convention as named files."""
    failures = []
    for d in REQUIRED_DIRS:
        dir_path = TEMPLATE / d
        # Collect committed files in this dir (non-recursive)
        files_here = [p for p in dir_path.iterdir() if p.is_file()]
        if not files_here:
            failures.append(f"{d}: empty directory (no committed files)")
            continue
        # If a README.md is present, check it for the standard shape
        readme = dir_path / "README.md"
        if readme.exists():
            text = readme.read_text(encoding="utf-8")
            if not H1_RE.search(text):
                failures.append(f"{d}/README.md: missing H1 heading")
            if not PHASE_NOTE_RE.search(text):
                failures.append(f"{d}/README.md: missing 'Phase N' note")
    assert not failures, "per-directory README issues:\n  " + "\n  ".join(failures)
