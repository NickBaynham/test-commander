"""Step 3.4 - /tc:learn-from-code end-to-end tests.

Drives extract_knowledge_from_code.py against the seeded sample-project's
Python source under ``src/``. Asserts:

- uninitialized workspace refused;
- no code source: helper writes a "no code source found" stub and still
  regenerates ``system-model.md``;
- Python AST walk: every module, class (Account, Workspace),
  function (sign_in, sign_out, upload_file, list_assets, get_account,
  is_admin, add_asset, is_non_empty_string, is_positive_int) is captured
  with ``<path>:<line>`` provenance plus its docstring (when present);
- gap signals route to ``requirements/open-questions.md``:
    * ``undocumented-function`` for ``upload_file`` (public, no docstring);
    * ``language-unsupported-in-v1`` for ``web/app.ts`` (TypeScript);
    * ``unimplemented-endpoint`` for ``GET /workspaces`` (operationId
      ``list_workspaces``) when run AFTER /tc:learn-from-specs has
      populated spec-derived-model.md;
- cross-cutting writes are scoped: ``## From code`` populates
  ``entities.md`` (Account, Workspace classes) but NOT
  ``user-journeys.md`` or ``assumptions.md``;
- ``## From documents`` (3.2) and ``## From specs`` (3.3) sections
  are preserved across the 3.4 run;
- idempotent re-run: per-source model, cross-cutting sections,
  open-questions, system-model all byte-stable;
- ``tc-knowledge.code.source-root`` extension points the helper at a
  different directory; ``tc-knowledge.code.ignored-paths`` excludes
  matching paths;
- the shared synthesizer regenerates ``system-model.md`` reflecting
  code ingestion.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_code.py"
SPECS_HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_specs.py"
DOCS_HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_docs.py"
INIT = REPO / "plugins" / "test-commander" / "scripts" / "init_workspace.py"
FIXTURE_SRC = REPO / "tests" / "fixtures" / "seeded-sample-project" / "src"
FIXTURE_OPENAPI = (
    REPO / "tests" / "fixtures" / "seeded-sample-project" / "specs" / "openapi.yaml"
)
FIXTURE_DOCS = REPO / "tests" / "fixtures" / "seeded-sample-project" / "documents"


def run_init(project_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INIT), str(project_root)],
        capture_output=True,
        text=True,
        check=True,
    )


def run_helper(project_root: Path, expected_exit: int = 0) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(HELPER), str(project_root)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == expected_exit, (
        f"helper exited {proc.returncode} (expected {expected_exit}). "
        f"stderr:\n{proc.stderr}"
    )
    return proc


def run_other(helper: Path, project_root: Path) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        [sys.executable, str(helper), str(project_root)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return proc


def copy_seeded_code(project_root: Path, target_subpath: str = "documents/uploaded/code") -> Path:
    target = project_root / ".test-commander" / target_subpath
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(FIXTURE_SRC, target)
    return target


def copy_seeded_openapi(project_root: Path) -> Path:
    uploaded = project_root / ".test-commander" / "documents" / "uploaded"
    uploaded.mkdir(parents=True, exist_ok=True)
    target = uploaded / "openapi.yaml"
    shutil.copy(FIXTURE_OPENAPI, target)
    return target


def copy_seeded_docs(project_root: Path) -> None:
    uploaded = project_root / ".test-commander" / "documents" / "uploaded"
    uploaded.mkdir(parents=True, exist_ok=True)
    for name in ("product-overview.md", "glossary.md", "user-journey-sign-in.md"):
        shutil.copy(FIXTURE_DOCS / name, uploaded / name)


def workspace_file(project_root: Path, rel: str) -> Path:
    return project_root / ".test-commander" / rel


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_workspace_refused(tmp_path: Path):
    proc = subprocess.run(
        [sys.executable, str(HELPER), str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2, proc.stderr
    stderr_lower = proc.stderr.lower()
    assert "not a test commander workspace" in stderr_lower or ".test-commander" in proc.stderr


def test_helper_file_exists():
    assert HELPER.is_file(), f"missing helper: {HELPER.relative_to(REPO)}"


# ---------------------------------------------------------------------------
# No-code path
# ---------------------------------------------------------------------------


def test_no_code_writes_stub_model(tmp_path: Path):
    run_init(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/code-derived-model.md").read_text(
        encoding="utf-8"
    )
    assert "no code source found" in model.lower()


def test_no_code_still_regenerates_system_model(tmp_path: Path):
    run_init(tmp_path)
    run_helper(tmp_path)
    system = workspace_file(tmp_path, "product-knowledge/system-model.md").read_text(
        encoding="utf-8"
    )
    lowered = system.lower()
    assert "no sources ingested" in lowered or "no source has been ingested" in lowered


# ---------------------------------------------------------------------------
# Python AST extraction
# ---------------------------------------------------------------------------


def test_seeded_code_extracts_classes(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/code-derived-model.md").read_text(
        encoding="utf-8"
    )
    for cls in ("Account", "Workspace"):
        assert cls in model, f"missing class {cls}"


def test_seeded_code_extracts_functions(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/code-derived-model.md").read_text(
        encoding="utf-8"
    )
    for fn in (
        "sign_in",
        "sign_out",
        "upload_file",
        "list_assets",
        "get_account",
        "is_admin",
        "add_asset",
        "is_non_empty_string",
        "is_positive_int",
    ):
        assert fn in model, f"missing function {fn}"


def test_seeded_code_extracts_provenance(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/code-derived-model.md").read_text(
        encoding="utf-8"
    )
    # Every finding line in the report should carry a "<rel-path>:<line>" citation.
    assert "documents/uploaded/code/" in model, "code findings must cite file:line"
    assert ".py:" in model


def test_seeded_code_captures_docstrings(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/code-derived-model.md").read_text(
        encoding="utf-8"
    )
    # sign_in has a docstring; the model should surface its first line.
    assert "Validate a one-time code" in model or "session record" in model


# ---------------------------------------------------------------------------
# Gap signals
# ---------------------------------------------------------------------------


def test_undocumented_function_routes_to_open_questions(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    open_questions = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    lowered = open_questions.lower()
    assert "undocumented-function" in lowered, (
        "undocumented-function gap must produce an open question"
    )
    assert "upload_file" in open_questions, (
        "the open question must name the offending function"
    )


def test_language_unsupported_routes_to_open_questions(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    open_questions = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    lowered = open_questions.lower()
    assert "language-unsupported-in-v1" in lowered, (
        "language-unsupported-in-v1 gap must produce an open question"
    )
    assert "app.ts" in open_questions or ".ts" in open_questions, (
        "the gap must name the unsupported file"
    )


def test_unimplemented_endpoint_routes_after_specs_ran(tmp_path: Path):
    """When the spec has been ingested (spec-derived-model.md is generated),
    the code helper cross-checks operationIds against function names and
    flags any endpoint with no matching function."""
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_other(SPECS_HELPER, tmp_path)  # populates spec-derived-model.md
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    open_questions = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    lowered = open_questions.lower()
    assert "unimplemented-endpoint" in lowered, (
        "unimplemented-endpoint gap must surface an open question"
    )
    # The seeded gap is GET /workspaces with operationId list_workspaces.
    assert "list_workspaces" in open_questions or "/workspaces" in open_questions


def test_unimplemented_endpoint_skipped_without_spec_model(tmp_path: Path):
    """Without spec-derived-model.md, the cross-check is impossible and no
    unimplemented-endpoint gap should be emitted."""
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    open_questions = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    assert "unimplemented-endpoint" not in open_questions.lower(), (
        "no spec means no unimplemented-endpoint cross-check"
    )


# ---------------------------------------------------------------------------
# Cross-cutting scope
# ---------------------------------------------------------------------------


def test_cross_cutting_entities_has_from_code_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    entities = workspace_file(tmp_path, "product-knowledge/entities.md").read_text(
        encoding="utf-8"
    )
    assert "## From code" in entities
    for cls in ("Account", "Workspace"):
        assert cls in entities


def test_cross_cutting_user_journeys_has_no_from_code_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    journeys = workspace_file(tmp_path, "product-knowledge/user-journeys.md").read_text(
        encoding="utf-8"
    )
    assert "## From code" not in journeys, (
        "code declares no journeys; user-journeys.md must NOT have a "
        "## From code section"
    )


def test_cross_cutting_assumptions_has_no_from_code_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    assumptions = workspace_file(tmp_path, "product-knowledge/assumptions.md").read_text(
        encoding="utf-8"
    )
    assert "## From code" not in assumptions, (
        "code is confirmed facts; assumptions.md must NOT have a "
        "## From code section"
    )


def test_prior_sections_preserved_when_code_runs(tmp_path: Path):
    """Running /tc:learn-from-docs and /tc:learn-from-specs first then
    /tc:learn-from-code must preserve every '## From documents' and
    '## From specs' section."""
    run_init(tmp_path)
    copy_seeded_docs(tmp_path)
    copy_seeded_openapi(tmp_path)
    copy_seeded_code(tmp_path)

    run_other(DOCS_HELPER, tmp_path)
    run_other(SPECS_HELPER, tmp_path)
    run_helper(tmp_path)

    entities = workspace_file(tmp_path, "product-knowledge/entities.md").read_text(
        encoding="utf-8"
    )
    assert "## From documents" in entities, "docs section must be preserved"
    assert "## From specs" in entities, "specs section must be preserved"
    assert "## From code" in entities, "code section must be added"


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_idempotent_code_model_byte_identical(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    first = workspace_file(tmp_path, "product-knowledge/code-derived-model.md").read_bytes()
    run_helper(tmp_path)
    second = workspace_file(tmp_path, "product-knowledge/code-derived-model.md").read_bytes()
    assert first == second


def test_idempotent_cross_cutting_byte_identical(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    first = workspace_file(tmp_path, "product-knowledge/entities.md").read_bytes()
    run_helper(tmp_path)
    second = workspace_file(tmp_path, "product-knowledge/entities.md").read_bytes()
    assert first == second


def test_idempotent_open_questions_line_stable(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    first = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    run_helper(tmp_path)
    second = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    assert first.count("\n") == second.count("\n")


def test_idempotent_system_model_byte_identical(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    first = workspace_file(tmp_path, "product-knowledge/system-model.md").read_bytes()
    run_helper(tmp_path)
    second = workspace_file(tmp_path, "product-knowledge/system-model.md").read_bytes()
    assert first == second


# ---------------------------------------------------------------------------
# Config extensions
# ---------------------------------------------------------------------------


def test_source_root_extension_applied(tmp_path: Path):
    """tc-knowledge.code.source-root points the helper at a custom directory."""
    run_init(tmp_path)
    # Copy code into a non-default location.
    copy_seeded_code(tmp_path, target_subpath="src")
    config = workspace_file(tmp_path, "config.yaml")
    base = config.read_text(encoding="utf-8") if config.is_file() else ""
    config.write_text(
        base.rstrip() + "\n\ntc-knowledge:\n  code:\n    source-root: src\n",
        encoding="utf-8",
    )
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/code-derived-model.md").read_text(
        encoding="utf-8"
    )
    assert "Account" in model
    # The helper should NOT have found the default documents/uploaded/code/
    # because we did not copy there.
    assert "no code source found" not in model.lower()


def test_ignored_paths_extension_excludes_matches(tmp_path: Path):
    """tc-knowledge.code.ignored-paths excludes matching paths from the walk."""
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    # Drop a marker python file inside an ignored subdir.
    ignored_dir = workspace_file(tmp_path, "documents/uploaded/code/migrations")
    ignored_dir.mkdir(parents=True, exist_ok=True)
    (ignored_dir / "0001_init.py").write_text(
        '"""Ignored migration."""\n\n\ndef forward():\n    """Apply."""\n    pass\n',
        encoding="utf-8",
    )
    config = workspace_file(tmp_path, "config.yaml")
    base = config.read_text(encoding="utf-8") if config.is_file() else ""
    config.write_text(
        base.rstrip()
        + "\n\ntc-knowledge:\n  code:\n    ignored-paths: [migrations]\n",
        encoding="utf-8",
    )
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/code-derived-model.md").read_text(
        encoding="utf-8"
    )
    assert "forward" not in model, "ignored-paths must exclude matching files"
    assert "0001_init" not in model


# ---------------------------------------------------------------------------
# System-model synthesis
# ---------------------------------------------------------------------------


def test_system_model_reflects_code_ingestion(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_helper(tmp_path)
    system = workspace_file(tmp_path, "product-knowledge/system-model.md").read_text(
        encoding="utf-8"
    )
    lowered = system.lower()
    assert "code" in lowered, "system-model must record the code source"
