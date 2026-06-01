"""Step 7.8 - Phase 7 integration smoke.

Drives the full Phase 2 -> 3 -> 4 -> 5 -> 6 -> 7 helper chain in workflow order
against a fresh tmp consuming project. Complements the per-command unit tests
(7.2-7.6) by exercising the end-to-end sequence through execution and reporting:

    [Phase 2-6 as in test_phase_6_integration] ->
    [Phase 7] run (ingest the recorded report; auto evidence-index)
              -> analyze-results -> report (rebuilds the maps) -> quality-gate

In-process imports (the integration lesson: faster than subprocess). The Phase 7
portion ingests the recorded `seeded-results/results.json` (a one-pass /
one-fail / one-flaky run whose `@req:`/`@cs:` provenance matches the
Phase-6-generated `sign-in` spec and automation map), so the run record joins
results -> scenarios -> requirements, and `/tc:report` resolves the test-map's
`Test result` + `Quality report` columns. Injected clock throughout, so every
artifact is byte-stable.

Asserts the Step 7.8 contract from planning/plan.md: run records written from
the recorded report; evidence routed per the policy split; analysis classifies
the failure + flaky case; the report carries every section + a history
snapshot; the gate returns a verdict; `test-map.md`'s `Test result` + `Quality
report` columns resolve from `pending`; the write boundary holds (`bdd/`,
`product-knowledge/`, and the project-root `tests/` framework byte-identical
before/after Phase 7); Playwright execution refused under pytest; `/tc:next`
advances past `/tc:run`. Plus the byte-stable re-run contract.
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import analyze_results
import automate
import automation_plan
import build_framework
import build_report
import create_charter
import enrich_test_ideas
import explore
import extract_knowledge_from_api
import extract_knowledge_from_code
import extract_knowledge_from_docs
import extract_knowledge_from_specs
import extract_knowledge_from_tests
import generate_bdd
import generate_test_data
import init_workspace
import next_step
import quality_gate
import requirements_to_tests
import review_requirements
import run_tests
import session_summary
import traceability_map

REPO = Path(__file__).resolve().parent.parent
PHASE_3_FIXTURE = REPO / "tests" / "fixtures" / "seeded-sample-project"
PHASE_4_FIXTURE = REPO / "tests" / "fixtures" / "seeded-exploration-session"
PHASE_2_FIXTURE = REPO / "tests" / "fixtures" / "seeded-flawed-requirements"
PHASE_6_FIXTURE = REPO / "tests" / "fixtures" / "seeded-automation"
PHASE_7_FIXTURE = REPO / "tests" / "fixtures" / "seeded-results"
RECORDED_REPORT = PHASE_7_FIXTURE / "results.json"

CHARTER_TARGET = (
    "Sign-in flow plus workspace-detail asset upload (POST /workspaces/{id}/assets)."
)
NOW = datetime(2026, 1, 15, 9, 30, 0)
RUN_ID = "RUN-20260115-093000"
SNAPSHOT_NAME = "2026-01-15-0930.md"


# ---------------------------------------------------------------------------
# Setup (mirrors the Phase 6 integration smoke)
# ---------------------------------------------------------------------------


def setup_consuming_project(tmp_path: Path) -> Path:
    project = tmp_path / "my-project"
    project.mkdir()
    init_workspace.init_workspace(project)
    workspace = project / ".test-commander"
    (workspace / "project.md").write_text(
        "# my-project\n\nPhase 7 integration smoke.\n", encoding="utf-8"
    )
    uploaded = workspace / "documents" / "uploaded"

    shutil.copy(PHASE_2_FIXTURE / "requirements.md", uploaded / "requirements.md")
    shutil.copy(PHASE_2_FIXTURE / "acceptance-criteria.md", uploaded / "acceptance-criteria.md")
    shutil.copy(PHASE_2_FIXTURE / "user-stories.md", uploaded / "user-stories.md")

    for name in ("product-overview.md", "glossary.md", "user-journey-sign-in.md"):
        shutil.copy(PHASE_3_FIXTURE / "documents" / name, uploaded / name)
    shutil.copy(PHASE_3_FIXTURE / "specs" / "openapi.yaml", uploaded / "openapi.yaml")
    shutil.copytree(PHASE_3_FIXTURE / "src", uploaded / "code")
    shutil.copytree(PHASE_3_FIXTURE / "recorded-api", uploaded / "recorded-api")
    shutil.copytree(PHASE_3_FIXTURE / "tests", uploaded / "tests")

    recorded_dir = uploaded / "recorded-sessions"
    recorded_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(PHASE_4_FIXTURE / "recorded-session.json", recorded_dir / "CH-001.json")
    return project


def snapshot_dir(root: Path) -> dict[Path, bytes]:
    return {
        p.relative_to(root): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def run_through_phase_6(project: Path) -> None:
    review_requirements.review(project)
    requirements_to_tests.to_tests(project)
    extract_knowledge_from_docs.run(project)
    extract_knowledge_from_specs.run(project)
    extract_knowledge_from_code.run(project)
    extract_knowledge_from_api.run(project)
    extract_knowledge_from_tests.run(project)
    create_charter.run(project, target=CHARTER_TARGET, mission=None, new_id=False)
    explore.run(project, charter_id="CH-001", no_review=False)
    note = next((project / ".test-commander" / "exploration-notes").glob("SESS-*.md"))
    session_id = note.stem
    session_summary.run(project, session_id=session_id)
    enrich_test_ideas.run(project, session_id=session_id)
    generate_bdd.run(project)
    traceability_map.traceability_map(project)
    # Inject the clean automatable feature so Phase 6 generates the sign-in spec.
    shutil.copy(
        PHASE_6_FIXTURE / "sign-in.feature",
        project / ".test-commander" / "bdd" / "features" / "sign-in.feature",
    )
    build_framework.scaffold(project)
    automation_plan.build_plan(project)
    automate.generate(project)
    generate_test_data.generate_test_data(project)
    traceability_map.traceability_map(project)


def run_phase_7(project: Path) -> None:
    run_tests.run(project, now=NOW, report=RECORDED_REPORT)  # auto evidence-index on
    analyze_results.analyze(project)
    build_report.build_report(project, now=NOW)  # rebuilds the maps -> resolves downstream
    quality_gate.gate(project)


# ---------------------------------------------------------------------------
# Full workflow
# ---------------------------------------------------------------------------


def test_full_phase_7_workflow(tmp_path: Path) -> None:
    project = setup_consuming_project(tmp_path)
    workspace = project / ".test-commander"
    run_through_phase_6(project)

    bdd_pre = snapshot_dir(workspace / "bdd")
    pk_pre = snapshot_dir(workspace / "product-knowledge")
    tests_pre = snapshot_dir(project / "tests")

    # --- Phase 7 ---
    run_phase_7(project)

    # Run record written from the recorded report, mapping results -> scenarios.
    run_md = (workspace / "runs" / RUN_ID / "run.md").read_text(encoding="utf-8")
    assert "REQ-001" in run_md and "CS-001-002" in run_md
    assert "passed" in run_md and "failed" in run_md and "flaky" in run_md
    assert (workspace / "runs" / RUN_ID / "results.json").is_file()

    # Evidence routed per the policy split (screenshot committed; video/trace ignored).
    assert (workspace / "evidence" / "screenshots" / "CS-001-002-failure.png").is_file()
    assert (workspace / "evidence" / "videos" / "CS-001-002-failure.webm").is_file()
    gitignore = (workspace / "evidence" / ".gitignore").read_text(encoding="utf-8")
    assert "videos/" in gitignore and "traces/" in gitignore
    assert (workspace / "evidence" / "evidence-index.md").is_file()

    # Analysis classifies the failure (product-defect) and the flaky case.
    analysis = (workspace / "runs" / RUN_ID / "analysis.md").read_text(encoding="utf-8")
    assert "product-defect" in analysis and "flaky" in analysis

    # Report carries every section + a history snapshot.
    report = (workspace / "quality-report" / "current-quality-report.md").read_text(
        encoding="utf-8"
    )
    for title in ("Executive summary", "Automated regression status", "Evidence summary",
                  "Release readiness", "Recent changes"):
        assert f"## {title}" in report, f"report missing section: {title}"
    assert "[fact]" in report and "[interpretation]" in report and "[review]" in report
    snapshot = workspace / "quality-report" / "history" / SNAPSHOT_NAME
    assert snapshot.is_file() and snapshot.read_bytes() == (
        workspace / "quality-report" / "current-quality-report.md"
    ).read_bytes()

    # The gate returns a verdict (FAIL under the zero-tolerance defaults).
    gate_md = (workspace / "quality-report" / "quality-gate.md").read_text(encoding="utf-8")
    assert "FAIL" in gate_md

    # test-map downstream columns resolve from pending.
    test_map = (workspace / "traceability" / "test-map.md").read_text(encoding="utf-8")
    rows = [ln for ln in test_map.split("\n") if ln.startswith("| REQ-001 |")]
    assert rows, "test-map has no REQ-001 scenario rows"
    for cs, status in (("CS-001-001", "passed"), ("CS-001-002", "failed"),
                       ("CS-001-003", "flaky")):
        row = next(r for r in rows if cs in r)
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert cells[4] == status, f"{cs} Test result should be {status}"
        assert cells[5] != "pending", f"{cs} Quality report must resolve"

    # Write boundary: bdd/, product-knowledge/, and the project-root tests/ framework.
    assert snapshot_dir(workspace / "bdd") == bdd_pre, "Phase 7 must not write bdd/"
    assert snapshot_dir(workspace / "product-knowledge") == pk_pre, (
        "Phase 7 must not write product-knowledge/"
    )
    assert snapshot_dir(project / "tests") == tests_pre, (
        "Phase 7 must not modify the project-root tests/ framework"
    )

    # Playwright execution refused under pytest.
    try:
        run_tests.run(project, now=NOW, report=None)
    except run_tests.ExecutionRefusedError as exc:
        assert "pytest" in str(exc).lower()
    else:
        raise AssertionError("real execution must be refused under pytest")
    for artifact in ("node_modules", "test-results", "playwright-report"):
        assert not (project / "tests" / artifact).exists(), f"execution leaked: tests/{artifact}"

    # /tc:next advances past /tc:run.
    rec = next_step.next_step_for(project)
    if rec is not None:
        assert rec.command != "/tc:run", f"/tc:next still recommends /tc:run after Phase 7: {rec}"


def test_byte_stable_rerun_across_phase_7(tmp_path: Path) -> None:
    project = setup_consuming_project(tmp_path)
    workspace = project / ".test-commander"
    run_through_phase_6(project)

    run_phase_7(project)
    targets = [
        workspace / "runs" / RUN_ID / "run.md",
        workspace / "runs" / RUN_ID / "results.json",
        workspace / "runs" / RUN_ID / "analysis.md",
        workspace / "evidence" / "evidence-index.md",
        workspace / "evidence" / ".gitignore",
        workspace / "quality-report" / "current-quality-report.md",
        workspace / "quality-report" / "history" / SNAPSHOT_NAME,
        workspace / "quality-report" / "quality-gate.md",
        workspace / "traceability" / "test-map.md",
    ]
    first = {p: p.read_bytes() for p in targets}

    run_phase_7(project)
    for path, snap in first.items():
        assert path.read_bytes() == snap, f"{path.name} not byte-stable on Phase 7 re-run"
