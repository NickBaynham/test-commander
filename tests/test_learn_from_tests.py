"""Step 3.6 - /tc:learn-from-tests end-to-end tests.

Drives extract_knowledge_from_tests.py against the seeded sample-project's
``tests/`` tree. Asserts:

- uninitialized workspace refused;
- no tests root: helper writes a "no tests found" stub and still
  regenerates ``system-model.md``;
- pytest extraction: two pytest files (``test_auth.py``,
  ``test_validation.py``) yield four test functions
  (``test_sign_in_returns_session``, ``test_sign_out_is_idempotent``,
  ``test_non_empty_string_accepts_string``,
  ``test_non_empty_string_rejects_empty`` etc.) with
  ``<path>:<line>`` provenance;
- covered-symbols: each test function's referenced names are captured;
- Playwright detection: ``web.spec.ts`` counted as a test file and
  flagged as ``unsupported-test-runner`` (routes to open-questions);
- ``untested-function`` cross-check: fires for code functions not
  referenced by any test (e.g. ``upload_file``) ONLY when
  ``code-derived-model.md`` is generated;
- cross-cutting scope: ``## From tests`` populates ``entities.md``
  (covered classes from code-derived-model) but NOT
  ``user-journeys.md``, ``assumptions.md``, OR ``business-rules.md``;
- prior ``## From <source>`` sections (docs/specs/code/api) preserved
  across the 3.6 run;
- idempotency holds across every output;
- ``tc-knowledge.tests.source-root`` extension points the walker at a
  custom directory;
- the shared synthesizer regenerates ``system-model.md`` reflecting
  tests ingestion.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_tests.py"
CODE_HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_code.py"
SPECS_HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_specs.py"
DOCS_HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_docs.py"
API_HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_api.py"
INIT = REPO / "plugins" / "test-commander" / "scripts" / "init_workspace.py"
FIXTURE_TESTS = REPO / "tests" / "fixtures" / "seeded-sample-project" / "tests"
FIXTURE_SRC = REPO / "tests" / "fixtures" / "seeded-sample-project" / "src"
FIXTURE_OPENAPI = (
    REPO / "tests" / "fixtures" / "seeded-sample-project" / "specs" / "openapi.yaml"
)
FIXTURE_DOCS = REPO / "tests" / "fixtures" / "seeded-sample-project" / "documents"
FIXTURE_RESPONSES = (
    REPO
    / "tests"
    / "fixtures"
    / "seeded-sample-project"
    / "recorded-api"
    / "responses.json"
)


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


def copy_seeded_tests(project_root: Path, target_subpath: str = "documents/uploaded/tests") -> Path:
    target = project_root / ".test-commander" / target_subpath
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(FIXTURE_TESTS, target)
    return target


def copy_seeded_code(project_root: Path) -> Path:
    target = project_root / ".test-commander" / "documents" / "uploaded" / "code"
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


def copy_seeded_responses(project_root: Path) -> Path:
    target = (
        project_root
        / ".test-commander"
        / "documents"
        / "uploaded"
        / "recorded-api"
        / "responses.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_RESPONSES, target)
    return target


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
# No-tests path
# ---------------------------------------------------------------------------


def test_no_tests_writes_stub_model(tmp_path: Path):
    run_init(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/tests-coverage.md").read_text(
        encoding="utf-8"
    )
    assert "no tests found" in model.lower()


def test_no_tests_still_regenerates_system_model(tmp_path: Path):
    run_init(tmp_path)
    run_helper(tmp_path)
    system = workspace_file(tmp_path, "product-knowledge/system-model.md").read_text(
        encoding="utf-8"
    )
    lowered = system.lower()
    assert "no sources ingested" in lowered or "no source has been ingested" in lowered


# ---------------------------------------------------------------------------
# Pytest detection
# ---------------------------------------------------------------------------


def test_seeded_tests_extracts_pytest_files(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/tests-coverage.md").read_text(
        encoding="utf-8"
    )
    for name in ("test_auth.py", "test_validation.py"):
        assert name in model, f"pytest file {name} missing"


def test_seeded_tests_extracts_test_functions(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/tests-coverage.md").read_text(
        encoding="utf-8"
    )
    for fn in (
        "test_sign_in_returns_session",
        "test_sign_out_is_idempotent",
        "test_non_empty_string_accepts_string",
        "test_positive_int_accepts_positive",
    ):
        assert fn in model, f"test function {fn} missing"


def test_seeded_tests_carries_provenance(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/tests-coverage.md").read_text(
        encoding="utf-8"
    )
    assert ".py:" in model, "test functions must carry <path>:<line> provenance"
    assert "documents/uploaded/tests/" in model


def test_covered_symbols_captured(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/tests-coverage.md").read_text(
        encoding="utf-8"
    )
    # The seeded tests reference sign_in, sign_out, is_non_empty_string,
    # is_positive_int. At least one should surface as a covered symbol.
    lowered = model.lower()
    assert "sign_in" in lowered or "is_non_empty_string" in lowered, (
        "covered-symbols section must list referenced identifiers"
    )


# ---------------------------------------------------------------------------
# Playwright / unsupported runner
# ---------------------------------------------------------------------------


def test_playwright_file_detected(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/tests-coverage.md").read_text(
        encoding="utf-8"
    )
    assert "web.spec.ts" in model, "Playwright spec file must be detected"


def test_unsupported_runner_routes_to_open_questions(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    open_questions = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    lowered = open_questions.lower()
    assert "[unsupported-test-runner]" in lowered, (
        "unsupported-test-runner gap must surface an open question"
    )
    assert "web.spec.ts" in open_questions or ".spec.ts" in open_questions


# ---------------------------------------------------------------------------
# Untested-function cross-check
# ---------------------------------------------------------------------------


def test_untested_function_routes_after_code_ran(tmp_path: Path):
    """When code-derived-model.md is generated, public functions not
    referenced by any test surface as untested-function gaps."""
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_other(CODE_HELPER, tmp_path)  # populates code-derived-model.md
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    open_questions = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    lowered = open_questions.lower()
    assert "[untested-function]" in lowered, (
        "untested-function gap must surface an open question with [kind] prefix"
    )
    # upload_file is the seeded untested function.
    assert "upload_file" in open_questions


def test_untested_function_skipped_without_code_model(tmp_path: Path):
    """Without code-derived-model.md, the cross-check is impossible."""
    run_init(tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    open_questions = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    assert "[untested-function]" not in open_questions.lower(), (
        "no code means no untested-function cross-check"
    )


# ---------------------------------------------------------------------------
# Cross-cutting scope
# ---------------------------------------------------------------------------


def test_cross_cutting_entities_has_from_tests_section(tmp_path: Path):
    """## From tests populates entities.md when code-derived-model.md is
    generated (so covered classes can be identified)."""
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_other(CODE_HELPER, tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    entities = workspace_file(tmp_path, "product-knowledge/entities.md").read_text(
        encoding="utf-8"
    )
    assert "## From tests" in entities


def test_cross_cutting_user_journeys_has_no_from_tests_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    journeys = workspace_file(tmp_path, "product-knowledge/user-journeys.md").read_text(
        encoding="utf-8"
    )
    assert "## From tests" not in journeys


def test_cross_cutting_assumptions_has_no_from_tests_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    assumptions = workspace_file(tmp_path, "product-knowledge/assumptions.md").read_text(
        encoding="utf-8"
    )
    assert "## From tests" not in assumptions


def test_cross_cutting_business_rules_has_no_from_tests_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    rules = workspace_file(tmp_path, "product-knowledge/business-rules.md").read_text(
        encoding="utf-8"
    )
    assert "## From tests" not in rules, (
        "tests contribute coverage signal to entities only; business-rules.md "
        "must NOT have a ## From tests section in v1"
    )


def test_prior_sections_preserved_when_tests_runs(tmp_path: Path):
    """Running every other helper first and then 3.6 must preserve every prior
    ## From <source> section."""
    run_init(tmp_path)
    copy_seeded_docs(tmp_path)
    copy_seeded_openapi(tmp_path)
    copy_seeded_code(tmp_path)
    copy_seeded_responses(tmp_path)
    copy_seeded_tests(tmp_path)

    run_other(DOCS_HELPER, tmp_path)
    run_other(SPECS_HELPER, tmp_path)
    run_other(CODE_HELPER, tmp_path)
    run_other(API_HELPER, tmp_path)
    run_helper(tmp_path)

    entities = workspace_file(tmp_path, "product-knowledge/entities.md").read_text(
        encoding="utf-8"
    )
    for label in ("documents", "specs", "code", "api", "tests"):
        assert f"## From {label}" in entities, f"{label} section must be present"


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_idempotent_coverage_model_byte_identical(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    first = workspace_file(tmp_path, "product-knowledge/tests-coverage.md").read_bytes()
    run_helper(tmp_path)
    second = workspace_file(tmp_path, "product-knowledge/tests-coverage.md").read_bytes()
    assert first == second


def test_idempotent_cross_cutting_byte_identical(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_code(tmp_path)
    run_other(CODE_HELPER, tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    first = workspace_file(tmp_path, "product-knowledge/entities.md").read_bytes()
    run_helper(tmp_path)
    second = workspace_file(tmp_path, "product-knowledge/entities.md").read_bytes()
    assert first == second


def test_idempotent_open_questions_line_stable(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_tests(tmp_path)
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
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    first = workspace_file(tmp_path, "product-knowledge/system-model.md").read_bytes()
    run_helper(tmp_path)
    second = workspace_file(tmp_path, "product-knowledge/system-model.md").read_bytes()
    assert first == second


# ---------------------------------------------------------------------------
# Config extensions
# ---------------------------------------------------------------------------


def test_source_root_extension_applied(tmp_path: Path):
    """tc-knowledge.tests.source-root points the walker at a custom directory."""
    run_init(tmp_path)
    copy_seeded_tests(tmp_path, target_subpath="my-tests")
    config = workspace_file(tmp_path, "config.yaml")
    base = config.read_text(encoding="utf-8") if config.is_file() else ""
    config.write_text(
        base.rstrip()
        + "\n\ntc-knowledge:\n  tests:\n    source-root: my-tests\n",
        encoding="utf-8",
    )
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/tests-coverage.md").read_text(
        encoding="utf-8"
    )
    assert "test_auth.py" in model
    assert "no tests found" not in model.lower()


# ---------------------------------------------------------------------------
# System-model synthesis
# ---------------------------------------------------------------------------


def test_system_model_reflects_tests_ingestion(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_tests(tmp_path)
    run_helper(tmp_path)
    system = workspace_file(tmp_path, "product-knowledge/system-model.md").read_text(
        encoding="utf-8"
    )
    lowered = system.lower()
    assert "tests" in lowered, "system-model must record the tests source"
