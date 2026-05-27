"""Step 3.3 - /tc:learn-from-specs end-to-end tests.

Drives extract_knowledge_from_specs.py against the seeded sample-project's
``specs/openapi.yaml`` plus a synthetic Postman v2.1 collection. Asserts:

- uninitialized workspace refused;
- no-spec path writes a "no spec found" stub and still regenerates
  ``system-model.md``;
- OpenAPI YAML: six endpoints, six schemas, and the ``bearerAuth`` security
  scheme are extracted with ``<path>:<line>`` provenance;
- gap signals route to ``requirements/open-questions.md``:
    * ``unspecified-status`` from ``POST /workspaces/{id}/assets`` (no
      ``responses`` keys);
    * ``schema-without-type`` from ``AssetUpload`` (no ``type`` and no
      ``$ref``);
- cross-cutting writes are scoped: ``## From specs`` appears in
  ``entities.md`` (endpoints as resources) and ``business-rules.md``
  (auth schemes as rules) but NOT in ``user-journeys.md`` or
  ``assumptions.md``;
- ``## From documents`` sections written by Step 3.2 are preserved;
- idempotent re-run: per-source model, cross-cutting sections,
  open-questions line count, and system-model are all byte-stable;
- Postman v2.1 collection auto-detected and parsed; endpoints/auth/
  schemas surface in the spec-derived model;
- the shared synthesizer regenerates system-model.md reflecting specs
  ingestion.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_specs.py"
DOCS_HELPER = REPO / "plugins" / "test-commander" / "scripts" / "extract_knowledge_from_docs.py"
INIT = REPO / "plugins" / "test-commander" / "scripts" / "init_workspace.py"
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


def write_minimal_postman_collection(uploaded: Path) -> Path:
    """A synthetic Postman v2.1 collection used to verify auto-detection."""
    collection = {
        "info": {
            "name": "Sample Project Collection",
            "schema": (
                "https://schema.getpostman.com/json/collection/v2.1.0/"
                "collection.json"
            ),
        },
        "item": [
            {
                "name": "Sign in",
                "request": {
                    "method": "POST",
                    "header": [],
                    "body": {
                        "mode": "raw",
                        "raw": '{"account_id": "acc-1", "code": "abc"}',
                    },
                    "url": {
                        "raw": "{{base_url}}/sessions",
                        "host": ["{{base_url}}"],
                        "path": ["sessions"],
                    },
                },
            },
            {
                "name": "List workspaces",
                "request": {
                    "method": "GET",
                    "auth": {"type": "bearer"},
                    "header": [],
                    "url": {
                        "raw": "{{base_url}}/workspaces",
                        "host": ["{{base_url}}"],
                        "path": ["workspaces"],
                    },
                },
            },
        ],
    }
    target = uploaded / "sample.postman_collection.json"
    target.write_text(json.dumps(collection, indent=2), encoding="utf-8")
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
# No-spec path
# ---------------------------------------------------------------------------


def test_no_spec_writes_stub_model(tmp_path: Path):
    run_init(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/spec-derived-model.md").read_text(
        encoding="utf-8"
    )
    assert "no spec found" in model.lower()


def test_no_spec_still_regenerates_system_model(tmp_path: Path):
    run_init(tmp_path)
    run_helper(tmp_path)
    system = workspace_file(tmp_path, "product-knowledge/system-model.md").read_text(
        encoding="utf-8"
    )
    lowered = system.lower()
    assert "no sources ingested" in lowered or "no source has been ingested" in lowered


# ---------------------------------------------------------------------------
# OpenAPI extraction
# ---------------------------------------------------------------------------


def test_seeded_openapi_extracts_all_six_endpoints(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/spec-derived-model.md").read_text(
        encoding="utf-8"
    )
    for method, path in [
        ("POST", "/sessions"),
        ("DELETE", "/sessions/{id}"),
        ("GET", "/accounts/{id}"),
        ("GET", "/workspaces"),
        ("POST", "/workspaces/{id}/assets"),
        ("GET", "/workspaces/{id}/assets"),
    ]:
        assert f"{method} {path}" in model, f"missing endpoint {method} {path}"


def test_seeded_openapi_extracts_provenance(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/spec-derived-model.md").read_text(
        encoding="utf-8"
    )
    assert "openapi.yaml:" in model, "endpoints must carry <path>:<line> provenance"


def test_seeded_openapi_extracts_schemas(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/spec-derived-model.md").read_text(
        encoding="utf-8"
    )
    for name in ("SignInRequest", "Session", "Account", "Workspace", "Asset", "AssetUpload"):
        assert name in model, f"missing schema {name}"


def test_seeded_openapi_extracts_security_schemes(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/spec-derived-model.md").read_text(
        encoding="utf-8"
    )
    assert "bearerAuth" in model
    assert "bearer" in model.lower()


# ---------------------------------------------------------------------------
# Gap signals
# ---------------------------------------------------------------------------


def test_unspecified_status_gap_routes_to_open_questions(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_helper(tmp_path)
    open_questions = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    lowered = open_questions.lower()
    # POST /workspaces/{id}/assets is the seeded unspecified-status defect.
    assert "unspecified-status" in lowered or "no responses" in lowered, (
        "unspecified-status gap must surface an open question"
    )
    assert "/workspaces/{id}/assets" in open_questions or "post" in lowered, (
        "the open question must name the offending endpoint"
    )


def test_schema_without_type_gap_routes_to_open_questions(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_helper(tmp_path)
    open_questions = workspace_file(tmp_path, "requirements/open-questions.md").read_text(
        encoding="utf-8"
    )
    assert "AssetUpload" in open_questions, (
        "schema-without-type gap must surface an open question naming the schema"
    )


# ---------------------------------------------------------------------------
# Cross-cutting scope
# ---------------------------------------------------------------------------


def test_cross_cutting_entities_has_from_specs_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_helper(tmp_path)
    entities = workspace_file(tmp_path, "product-knowledge/entities.md").read_text(
        encoding="utf-8"
    )
    assert "## From specs" in entities
    # The endpoints contribute as resources (their path-segment).
    assert "sessions" in entities.lower() or "workspaces" in entities.lower()


def test_cross_cutting_business_rules_has_from_specs_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_helper(tmp_path)
    rules = workspace_file(tmp_path, "product-knowledge/business-rules.md").read_text(
        encoding="utf-8"
    )
    assert "## From specs" in rules
    assert "bearerAuth" in rules or "bearer" in rules.lower()


def test_cross_cutting_user_journeys_has_no_from_specs_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_helper(tmp_path)
    journeys = workspace_file(tmp_path, "product-knowledge/user-journeys.md").read_text(
        encoding="utf-8"
    )
    assert "## From specs" not in journeys, (
        "specs contribute no journeys; user-journeys.md must NOT have a "
        "## From specs section"
    )


def test_cross_cutting_assumptions_has_no_from_specs_section(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_helper(tmp_path)
    assumptions = workspace_file(tmp_path, "product-knowledge/assumptions.md").read_text(
        encoding="utf-8"
    )
    assert "## From specs" not in assumptions, (
        "specs are confirmed facts; assumptions.md must NOT have a "
        "## From specs section"
    )


def test_documents_sections_preserved_when_specs_runs(tmp_path: Path):
    """Running /tc:learn-from-docs first then /tc:learn-from-specs must
    preserve every '## From documents' section across all cross-cutting
    files."""
    run_init(tmp_path)
    copy_seeded_docs(tmp_path)
    copy_seeded_openapi(tmp_path)

    # Run docs first.
    proc = subprocess.run(
        [sys.executable, str(DOCS_HELPER), str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr

    # Then specs.
    run_helper(tmp_path)

    entities = workspace_file(tmp_path, "product-knowledge/entities.md").read_text(
        encoding="utf-8"
    )
    assert "## From documents" in entities, "docs section must be preserved"
    assert "## From specs" in entities, "specs section must be added"
    # And docs entity names should still appear in the docs section.
    assert "Account" in entities


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_idempotent_spec_model_byte_identical(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_helper(tmp_path)
    first = workspace_file(tmp_path, "product-knowledge/spec-derived-model.md").read_bytes()
    run_helper(tmp_path)
    second = workspace_file(tmp_path, "product-knowledge/spec-derived-model.md").read_bytes()
    assert first == second


def test_idempotent_cross_cutting_byte_identical(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
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
    copy_seeded_openapi(tmp_path)
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
    copy_seeded_openapi(tmp_path)
    run_helper(tmp_path)
    first = workspace_file(tmp_path, "product-knowledge/system-model.md").read_bytes()
    run_helper(tmp_path)
    second = workspace_file(tmp_path, "product-knowledge/system-model.md").read_bytes()
    assert first == second


# ---------------------------------------------------------------------------
# Postman auto-detection
# ---------------------------------------------------------------------------


def test_postman_collection_autodetected(tmp_path: Path):
    """A *.postman_collection.json file is parsed even without openapi.yaml."""
    run_init(tmp_path)
    uploaded = workspace_file(tmp_path, "documents/uploaded")
    uploaded.mkdir(parents=True, exist_ok=True)
    write_minimal_postman_collection(uploaded)
    run_helper(tmp_path)
    model = workspace_file(tmp_path, "product-knowledge/spec-derived-model.md").read_text(
        encoding="utf-8"
    )
    assert "POST /sessions" in model
    assert "GET /workspaces" in model
    # bearer auth declared on the List workspaces request.
    assert "bearer" in model.lower()


# ---------------------------------------------------------------------------
# System-model synthesis
# ---------------------------------------------------------------------------


def test_system_model_reflects_specs_ingestion(tmp_path: Path):
    run_init(tmp_path)
    copy_seeded_openapi(tmp_path)
    run_helper(tmp_path)
    system = workspace_file(tmp_path, "product-knowledge/system-model.md").read_text(
        encoding="utf-8"
    )
    lowered = system.lower()
    assert "specs" in lowered, "system-model must record the specs source"
