"""Step 3.5 - /tc:learn-from-api end-to-end tests.

Drives extract_knowledge_from_api.py against the seeded sample-project's
recorded-api/responses.json. Asserts:

- uninitialized workspace refused;
- no recorded file: helper writes a "no recorded API responses found"
  stub and still regenerates ``system-model.md``;
- recorded mode: seven entries are extracted with
  ``<METHOD> <path> <status>`` provenance;
- gap signals route to ``requirements/open-questions.md`` with the
  ``[<kind>]`` prefix established in Step 3.4:
    * ``unspecified-endpoint`` for the recorded ``GET /accounts/me``
      that is not in the spec;
    * ``mismatched-status`` for ``DELETE /sessions/{id}`` returning 500
      when the spec declares only 204 (fires only when
      ``spec-derived-model.md`` has been generated);
- ``auth-required`` is detected for endpoints carrying an
  ``Authorization`` header in the recorded request;
- cross-cutting writes are scoped: ``## From api`` populates
  ``entities.md`` (resources confirmed reachable) and
  ``business-rules.md`` (auth-required rules) but NOT
  ``user-journeys.md`` or ``assumptions.md``;
- ``## From documents`` (3.2), ``## From specs`` (3.3), and
  ``## From code`` (3.4) sections are preserved across the 3.5 run;
- idempotency holds across every output;
- ``tc-knowledge.api.recorded-path`` extension points the helper at a
  custom playback file;
- ``tc-knowledge.api.mode: live`` is refused when running under pytest
  (``PYTEST_CURRENT_TEST`` is in the environment) so no real network
  calls leak from the suite;
- the shared synthesizer regenerates ``system-model.md`` reflecting
  api ingestion.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_api.py"
SPECS_HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_specs.py"
DOCS_HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_docs.py"
CODE_HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_code.py"
INIT = REPO / "plugins" / "test-commander" / "scripts" / "init_workspace.py"
FIXTURE_RESPONSES = (
    REPO
    / "tests"
    / "fixtures"
    / "seeded-sample-project"
    / "recorded-api"
    / "responses.json"
)
FIXTURE_OPENAPI = (
    REPO / "tests" / "fixtures" / "seeded-sample-project" / "specs" / "openapi.yaml"
)
FIXTURE_DOCS = REPO / "tests" / "fixtures" / "seeded-sample-project" / "documents"
FIXTURE_SRC = REPO / "tests" / "fixtures" / "seeded-sample-project" / "src"


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


def copy_seeded_responses(project_root: Path, target_rel: str | None = None) -> Path:
    rel = target_rel or "documents/uploaded/recorded-api/responses.json"
    target = project_root / ".test-commander" / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_RESPONSES, target)
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


def copy_seeded_code(project_root: Path) -> None:
    target = project_root / ".test-commander" / "documents" / "uploaded" / "code"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(FIXTURE_SRC, target)


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
# No-recorded-file path
# ---------------------------------------------------------------------------


def test_no_recorded_file_writes_stub_model(tmp_path: Path):
    run_init(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/api-model.md").read_text(
        encoding="utf-8"
    )
    assert "no recorded api responses found" in model.lower()


def test_no_recorded_file_still_regenerates_system_model(tmp_path: Path):
    run_init(tmp_path)
    run_helper(tmp_path)
    system = workspace_file(tmp_path, "product-knowledge/system-model.md").read_text(
        encoding="utf-8"
    )
    lowered = system.lower()
    assert "no sources ingested" in lowered or "no source has been ingested" in lowered


# ---------------------------------------------------------------------------
# Recorded mode extraction
# ---------------------------------------------------------------------------


def test_seeded_responses_extracts_all_seven_entries(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/api-model.md").read_text(
        encoding="utf-8"
    )
    expected = [
        ("POST", "/sessions"),
        ("DELETE", "/sessions/{id}"),
        ("GET", "/accounts/{id}"),
        ("GET", "/workspaces"),
        ("POST", "/workspaces/{id}/assets"),
        ("GET", "/workspaces/{id}/assets"),
        ("GET", "/accounts/me"),
    ]
    for method, path in expected:
        assert f"{method} {path}" in model, f"missing recorded request {method} {path}"


def test_seeded_responses_carries_provenance(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/api-model.md").read_text(
        encoding="utf-8"
    )
    # Provenance is `<source-file>:<index>` style for recorded playback.
    assert "responses.json" in model


def test_response_shapes_captured(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/api-model.md").read_text(
        encoding="utf-8"
    )
    # Top-level keys from the response body shapes.
    assert "account_id" in model or "display_name" in model


# ---------------------------------------------------------------------------
# Gap signals
# ---------------------------------------------------------------------------


def test_unspecified_endpoint_routes_after_specs_ran(tmp_path: Path):
    """When the spec has been ingested, recorded endpoints absent from the
    spec are flagged as unspecified-endpoint."""
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_other(SPECS_HELPER, tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    open_questions = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    lowered = open_questions.lower()
    assert "[unspecified-endpoint]" in lowered, (
        "unspecified-endpoint gap must surface an open question with [kind] prefix"
    )
    assert "/accounts/me" in open_questions


def test_mismatched_status_routes_after_specs_ran(tmp_path: Path):
    """When the spec has been ingested, recorded statuses outside the spec's
    declared response codes are flagged."""
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_other(SPECS_HELPER, tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    open_questions = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    lowered = open_questions.lower()
    assert "[mismatched-status]" in lowered, (
        "mismatched-status gap must surface an open question with [kind] prefix"
    )
    # The seeded gap is DELETE /sessions/{id} returning 500 vs declared 204.
    assert "500" in open_questions
    assert "/sessions/{id}" in open_questions or "delete" in lowered


def test_unspecified_endpoint_skipped_without_spec_model(tmp_path: Path):
    """Without spec-derived-model.md, no cross-check is possible."""
    run_init(tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    open_questions = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    lowered = open_questions.lower()
    assert "[unspecified-endpoint]" not in lowered, (
        "no spec means no unspecified-endpoint cross-check"
    )
    assert "[mismatched-status]" not in lowered


def test_auth_required_detected_from_authorization_header(tmp_path: Path):
    """Recordings carrying an Authorization header surface as auth-required
    endpoints in the per-source model AND in business-rules.md."""
    run_init(tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/api-model.md").read_text(
        encoding="utf-8"
    )
    lowered = model.lower()
    assert "auth-required" in lowered, "auth-required dimension must be surfaced"
    # The fixture has Authorization on /workspaces, /workspaces/{id}/assets, and /accounts/me.
    assert "/workspaces" in model


# ---------------------------------------------------------------------------
# Cross-cutting scope
# ---------------------------------------------------------------------------


def test_cross_cutting_entities_has_from_api_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    entities = workspace_file(tmp_path, "product-knowledge/entities.md").read_text(
        encoding="utf-8"
    )
    assert "## From api" in entities
    # The resources observed live in the first non-templated URL segment.
    assert "sessions" in entities.lower() or "workspaces" in entities.lower()


def test_cross_cutting_business_rules_has_from_api_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    rules = workspace_file(tmp_path, "product-knowledge/business-rules.md").read_text(
        encoding="utf-8"
    )
    assert "## From api" in rules
    assert "auth" in rules.lower(), "auth-required endpoints must surface as rules"


def test_cross_cutting_user_journeys_has_no_from_api_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    journeys = workspace_file(tmp_path, "product-knowledge/user-journeys.md").read_text(
        encoding="utf-8"
    )
    assert "## From api" not in journeys, (
        "API runtime declares no journeys; user-journeys.md must NOT have "
        "a ## From api section"
    )


def test_cross_cutting_assumptions_has_no_from_api_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    assumptions = workspace_file(tmp_path, "product-knowledge/assumptions.md").read_text(
        encoding="utf-8"
    )
    assert "## From api" not in assumptions, (
        "API recordings are confirmed facts; assumptions.md must NOT have "
        "a ## From api section"
    )


def test_prior_sections_preserved_when_api_runs(tmp_path: Path):
    """Running 3.2/3.3/3.4 first then 3.5 must preserve every prior
    ## From <source> section."""
    run_init(tmp_path)
    copy_seeded_docs(tmp_path)
    copy_seeded_openapi(tmp_path)
    copy_seeded_code(tmp_path)
    copy_seeded_responses(tmp_path)

    run_other(DOCS_HELPER, tmp_path)
    run_other(SPECS_HELPER, tmp_path)
    run_other(CODE_HELPER, tmp_path)
    run_helper(tmp_path)

    entities = workspace_file(tmp_path, "product-knowledge/entities.md").read_text(
        encoding="utf-8"
    )
    for label in ("documents", "specs", "code", "api"):
        assert f"## From {label}" in entities, f"{label} section must be present"


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_idempotent_api_model_byte_identical(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    first = workspace_file(tmp_path, "product-knowledge/api-model.md").read_bytes()
    run_helper(tmp_path)
    second = workspace_file(tmp_path, "product-knowledge/api-model.md").read_bytes()
    assert first == second


def test_idempotent_cross_cutting_byte_identical(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    snapshots = {
        name: workspace_file(tmp_path, f"product-knowledge/{name}.md").read_bytes()
        for name in ("entities", "business-rules")
    }
    run_helper(tmp_path)
    for name, snapshot in snapshots.items():
        current = workspace_file(tmp_path, f"product-knowledge/{name}.md").read_bytes()
        assert current == snapshot, f"{name}.md must be byte-identical on re-run"


def test_idempotent_open_questions_line_stable(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_responses(tmp_path)
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
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    first = workspace_file(tmp_path, "product-knowledge/system-model.md").read_bytes()
    run_helper(tmp_path)
    second = workspace_file(tmp_path, "product-knowledge/system-model.md").read_bytes()
    assert first == second


# ---------------------------------------------------------------------------
# Config extensions
# ---------------------------------------------------------------------------


def test_recorded_path_extension_applied(tmp_path: Path):
    """tc-knowledge.api.recorded-path points the helper at a custom playback."""
    run_init(tmp_path)
    custom = workspace_file(tmp_path, "fixtures/custom-recordings.json")
    custom.parent.mkdir(parents=True, exist_ok=True)
    custom.write_text(
        json.dumps(
            [
                {
                    "method": "GET",
                    "path": "/health",
                    "status": 200,
                    "headers": {"content-type": "application/json"},
                    "body": {"status": "ok"},
                }
            ]
        ),
        encoding="utf-8",
    )
    config = workspace_file(tmp_path, "config.yaml")
    base = config.read_text(encoding="utf-8") if config.is_file() else ""
    config.write_text(
        base.rstrip()
        + "\n\ntc-knowledge:\n  api:\n    recorded-path: fixtures/custom-recordings.json\n",
        encoding="utf-8",
    )
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/api-model.md").read_text(
        encoding="utf-8"
    )
    assert "GET /health" in model
    assert "no recorded api responses found" not in model.lower()


def test_live_mode_refused_under_pytest(tmp_path: Path):
    """tc-knowledge.api.mode: live must refuse when the helper detects pytest
    via the PYTEST_CURRENT_TEST environment variable. No real network calls."""
    run_init(tmp_path)
    config = workspace_file(tmp_path, "config.yaml")
    base = config.read_text(encoding="utf-8") if config.is_file() else ""
    config.write_text(
        base.rstrip()
        + '\n\ntc-knowledge:\n  api:\n    mode: live\n    base-url: "http://localhost:9999"\n',
        encoding="utf-8",
    )
    # The subprocess inherits PYTEST_CURRENT_TEST automatically when invoked from a pytest test.
    proc = subprocess.run(
        [sys.executable, str(HELPER), str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2, (
        f"live mode must be refused under pytest. stderr:\n{proc.stderr}"
    )
    stderr_lower = proc.stderr.lower()
    assert "live mode" in stderr_lower or "refused" in stderr_lower


# ---------------------------------------------------------------------------
# System-model synthesis
# ---------------------------------------------------------------------------


def test_system_model_reflects_api_ingestion(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_responses(tmp_path)
    run_helper(tmp_path)
    system = workspace_file(tmp_path, "product-knowledge/system-model.md").read_text(
        encoding="utf-8"
    )
    lowered = system.lower()
    assert "api" in lowered, "system-model must record the api source"
