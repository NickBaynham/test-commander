"""Step 3.8 — Phase 3 integration smoke.

Drives all five Phase 3 helpers in workflow order against a fresh tmp
consuming project seeded with the deliberately-generic sample-project
fixture. Complements the per-command unit tests in 3.2–3.6 by exercising
the full

    init -> upload (docs + spec + code + recordings + tests) ->
    learn-from-docs -> learn-from-specs -> learn-from-code ->
    learn-from-api -> learn-from-tests -> /tc:next post-Phase-3

workflow end to end. At every transition the integration test asserts the
expected artifact landed, the cross-cutting section was added without
trampling sibling sections, the synthesizer regenerated ``system-model.md``,
and the expected gap-signal open questions were appended without
duplication. Final assertions cover the union state across all five
sources, the byte-stable re-run contract, the Phase-3 "no writes to
``traceability/``" discipline, and the live-mode refusal under pytest.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import extract_knowledge_from_api
import extract_knowledge_from_code
import extract_knowledge_from_docs
import extract_knowledge_from_specs
import extract_knowledge_from_tests
import init_workspace
import next_step
import pytest

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "tests" / "fixtures" / "seeded-sample-project"


# ---------------------------------------------------------------------------
# Setup helper
# ---------------------------------------------------------------------------


def setup_consuming_project(tmp_path: Path) -> Path:
    project = tmp_path / "my-project"
    project.mkdir()
    init_workspace.init_workspace(project)
    workspace = project / ".test-commander"
    # Phase-1 metadata so /tc:next does not get stuck on R2.
    (workspace / "project.md").write_text(
        "# my-project\n\nPhase 3 integration smoke.\n", encoding="utf-8"
    )

    uploaded = workspace / "documents" / "uploaded"

    # Narrative documents
    for name in ("product-overview.md", "glossary.md", "user-journey-sign-in.md"):
        shutil.copy(FIXTURE / "documents" / name, uploaded / name)

    # OpenAPI spec
    shutil.copy(FIXTURE / "specs" / "openapi.yaml", uploaded / "openapi.yaml")

    # Source code tree
    shutil.copytree(FIXTURE / "src", uploaded / "code")

    # Recorded API responses
    shutil.copytree(FIXTURE / "recorded-api", uploaded / "recorded-api")

    # Tests tree
    shutil.copytree(FIXTURE / "tests", uploaded / "tests")

    return project


def workspace_file(project: Path, rel: str) -> Path:
    return project / ".test-commander" / rel


# ---------------------------------------------------------------------------
# Main end-to-end workflow
# ---------------------------------------------------------------------------


def test_full_phase_3_workflow(tmp_path: Path) -> None:
    project = setup_consuming_project(tmp_path)
    workspace = project / ".test-commander"
    pk = workspace / "product-knowledge"
    open_questions = workspace / "requirements" / "open-questions.md"

    # --- A. /tc:learn-from-docs ---
    extract_knowledge_from_docs.run(project)

    doc_model = (pk / "documentation-model.md").read_text(encoding="utf-8")
    assert "Account" in doc_model, "documentation-model must extract entities"
    assert "documents/uploaded/glossary.md:" in doc_model, "provenance citations expected"

    for cross in ("entities", "user-journeys", "business-rules", "assumptions"):
        text = (pk / f"{cross}.md").read_text(encoding="utf-8")
        assert "## From documents" in text, f"{cross}.md missing ## From documents"

    system = (pk / "system-model.md").read_text(encoding="utf-8")
    assert "documents" in system.lower(), "system-model must record docs source"

    open_q_a = open_questions.read_text(encoding="utf-8")
    assert "Telemetry" in open_q_a, "undefined-term gap must surface for Telemetry"
    assert "contradict" in open_q_a.lower(), "contradictory-rule gap must surface"

    # --- B. /tc:learn-from-specs ---
    extract_knowledge_from_specs.run(project)

    spec_text = (pk / "spec-derived-model.md").read_text(encoding="utf-8")
    for endpoint in (
        "POST /sessions",
        "DELETE /sessions/{id}",
        "GET /accounts/{id}",
        "GET /workspaces",
        "POST /workspaces/{id}/assets",
        "GET /workspaces/{id}/assets",
    ):
        assert endpoint in spec_text, f"spec-derived-model missing {endpoint}"
    for schema in ("SignInRequest", "Session", "Account", "Workspace", "Asset", "AssetUpload"):
        assert schema in spec_text, f"spec-derived-model missing schema {schema}"
    assert "bearerAuth" in spec_text, "security scheme must surface"

    entities = (pk / "entities.md").read_text(encoding="utf-8")
    assert "## From documents" in entities, "docs section preserved"
    assert "## From specs" in entities, "specs section added"

    rules = (pk / "business-rules.md").read_text(encoding="utf-8")
    assert "## From documents" in rules
    assert "## From specs" in rules, "specs contribute auth schemes as rules"

    # specs add no journeys or assumptions
    journeys = (pk / "user-journeys.md").read_text(encoding="utf-8")
    assumptions = (pk / "assumptions.md").read_text(encoding="utf-8")
    assert "## From specs" not in journeys, "specs encode no journeys"
    assert "## From specs" not in assumptions, "specs are confirmed facts"

    # --- C. /tc:learn-from-code ---
    extract_knowledge_from_code.run(project)

    code_text = (pk / "code-derived-model.md").read_text(encoding="utf-8")
    for class_name in ("Account", "Workspace"):
        assert class_name in code_text, f"code-derived-model missing class {class_name}"
    assert "sign_in" in code_text, "code-derived-model must capture function names"

    entities = (pk / "entities.md").read_text(encoding="utf-8")
    for source in ("documents", "specs", "code"):
        assert f"## From {source}" in entities, f"entities.md missing ## From {source}"

    # Code helper emits undocumented-function for upload_file, language-unsupported-in-v1
    # for web/app.ts, and unimplemented-endpoint for GET /workspaces (no list_workspaces fn).
    open_q_c = open_questions.read_text(encoding="utf-8")
    assert "[undocumented-function]" in open_q_c.lower()
    assert "[language-unsupported-in-v1]" in open_q_c.lower()
    assert "[unimplemented-endpoint]" in open_q_c.lower()

    # --- D. /tc:learn-from-api ---
    extract_knowledge_from_api.run(project)

    api_text = (pk / "api-model.md").read_text(encoding="utf-8")
    for rec in (
        "POST /sessions",
        "DELETE /sessions/{id}",
        "GET /accounts/{id}",
        "GET /workspaces",
        "POST /workspaces/{id}/assets",
        "GET /workspaces/{id}/assets",
        "GET /accounts/me",
    ):
        assert rec in api_text, f"api-model missing recording {rec}"
    assert "auth-required" in api_text.lower(), "auth-required dimension must surface"

    entities = (pk / "entities.md").read_text(encoding="utf-8")
    rules = (pk / "business-rules.md").read_text(encoding="utf-8")
    for source in ("documents", "specs", "code", "api"):
        assert f"## From {source}" in entities, f"entities.md missing ## From {source}"
    for source in ("documents", "specs", "api"):
        assert f"## From {source}" in rules, f"business-rules.md missing ## From {source}"

    # Spec cross-check fires: GET /accounts/me is unspecified-endpoint;
    # DELETE /sessions/{id} returning 500 mismatches spec's 204.
    open_q_d = open_questions.read_text(encoding="utf-8")
    assert "[unspecified-endpoint]" in open_q_d.lower()
    assert "[mismatched-status]" in open_q_d.lower()
    assert "/accounts/me" in open_q_d
    assert "500" in open_q_d

    # --- E. /tc:learn-from-tests ---
    extract_knowledge_from_tests.run(project)

    tests_text = (pk / "tests-coverage.md").read_text(encoding="utf-8")
    assert "test_auth.py" in tests_text or "sign_in" in tests_text, (
        "tests-coverage must capture pytest functions"
    )

    entities = (pk / "entities.md").read_text(encoding="utf-8")
    for source in ("documents", "specs", "code", "api", "tests"):
        assert f"## From {source}" in entities, f"entities.md missing ## From {source}"

    # Per-source/cross-cutting scope discipline (final state).
    journeys = (pk / "user-journeys.md").read_text(encoding="utf-8")
    assumptions = (pk / "assumptions.md").read_text(encoding="utf-8")
    assert "## From documents" in journeys
    assert "## From specs" not in journeys
    assert "## From code" not in journeys
    assert "## From api" not in journeys
    assert "## From tests" not in journeys
    assert "## From documents" in assumptions
    for other in ("specs", "code", "api", "tests"):
        assert f"## From {other}" not in assumptions

    rules = (pk / "business-rules.md").read_text(encoding="utf-8")
    assert "## From code" not in rules, (
        "code emits rules only when module constants carry rule docstrings; "
        "the seeded fixture has none"
    )
    assert "## From tests" not in rules, "tests do not contribute business rules"

    # untested-function (upload_file) + unsupported-test-runner (web.spec.ts) both route.
    open_q_e = open_questions.read_text(encoding="utf-8")
    assert "[untested-function]" in open_q_e.lower()
    assert "upload_file" in open_q_e
    assert "[unsupported-test-runner]" in open_q_e.lower()

    # --- Final synthesis state ---
    system = (pk / "system-model.md").read_text(encoding="utf-8")
    for source in ("documents", "specs", "code", "api", "tests"):
        assert source in system.lower(), f"system-model must list {source} as ingested"

    # --- Phase 3 must NOT have written to traceability/ ---
    traceability = workspace / "traceability"
    if traceability.is_dir():
        for tp in traceability.rglob("*.md"):
            # Phase 3 leaves the workspace-template stubs alone. The stubs all
            # carry "_(empty until ... ships.)_" or a similar placeholder.
            text = tp.read_text(encoding="utf-8")
            assert "tc-knowledge" not in text, (
                f"Phase 3 must not write tc-knowledge content into {tp}; got:\n{text[:200]}"
            )

    # --- /tc:next advances past /tc:learn-from-docs ---
    # Per the Phase-2 Step-2.9 lesson, assert command != /tc:learn-from-docs
    # rather than pinning a specific next command. R-rules may route to any
    # Phase 4+ command depending on which downstream phases the cross-cutting
    # writes bumped to in_progress.
    rec = next_step.next_step_for(project)
    if rec is not None:
        assert rec.command != "/tc:learn-from-docs", (
            f"/tc:next still recommends /tc:learn-from-docs after Phase 3 "
            f"helper sweep: {rec}"
        )


# ---------------------------------------------------------------------------
# Idempotent re-run
# ---------------------------------------------------------------------------


def test_byte_stable_rerun_across_all_five_helpers(tmp_path: Path) -> None:
    """Running every helper twice produces byte-identical per-source models +
    cross-cutting artifacts + system-model, and a line-stable
    open-questions.md."""
    project = setup_consuming_project(tmp_path)
    workspace = project / ".test-commander"
    pk = workspace / "product-knowledge"

    helpers = [
        extract_knowledge_from_docs,
        extract_knowledge_from_specs,
        extract_knowledge_from_code,
        extract_knowledge_from_api,
        extract_knowledge_from_tests,
    ]
    for helper in helpers:
        helper.run(project)

    # Snapshot every product-knowledge artifact.
    pk_files = sorted(pk.rglob("*.md"))
    snapshots: dict[Path, bytes] = {f.relative_to(pk): f.read_bytes() for f in pk_files}
    open_q_first = (workspace / "requirements" / "open-questions.md").read_text(
        encoding="utf-8"
    )

    # Second pass.
    for helper in helpers:
        helper.run(project)

    for rel, snapshot in snapshots.items():
        current = (pk / rel).read_bytes()
        assert current == snapshot, f"{rel} not byte-identical on re-run"

    open_q_second = (workspace / "requirements" / "open-questions.md").read_text(
        encoding="utf-8"
    )
    assert open_q_first.count("\n") == open_q_second.count("\n"), (
        "open-questions.md line count changed on re-run"
    )


# ---------------------------------------------------------------------------
# Live-mode refusal under pytest
# ---------------------------------------------------------------------------


def test_live_mode_refused_under_pytest(tmp_path: Path) -> None:
    """tc-knowledge.api.mode: live must refuse when PYTEST_CURRENT_TEST is
    set so no real network call can leak from the suite."""
    project = setup_consuming_project(tmp_path)
    workspace = project / ".test-commander"
    config = workspace / "config.yaml"
    base = config.read_text(encoding="utf-8") if config.is_file() else ""
    config.write_text(
        base.rstrip()
        + '\n\ntc-knowledge:\n  api:\n    mode: live\n'
          '    base-url: "http://localhost:9999"\n',
        encoding="utf-8",
    )
    with pytest.raises(extract_knowledge_from_api.LiveModeRefusedError):
        extract_knowledge_from_api.run(project)
