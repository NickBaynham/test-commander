"""Step 6.8 - Phase 6 integration smoke.

Drives the full Phase 2 -> 3 -> 4 -> 5 -> 6 helper chain in workflow order
against a fresh tmp consuming project. Complements the per-command unit tests
(6.2-6.6) by exercising the end-to-end sequence:

    init -> upload ->
    [Phase 2] review_requirements -> requirements_to_tests ->
    [Phase 3] learn-from-* (5 helpers) ->
    [Phase 4] create-charter -> explore -> session-summary -> test-ideas ->
    [Phase 5] generate-bdd (+ auto-review) -> traceability-map ->
    [inject the clean seeded-automation feature] ->
    [Phase 6] build-framework -> automation-plan -> automate (+ auto-review)
              -> generate-test-data -> traceability-map (re-run)

In-process imports (the Phase 3/4/5 integration lesson: in-process beats
subprocess for speed). The clean `seeded-automation/sign-in.feature` is injected
into `bdd/features/` for the Phase 6 portion (its `@automated-candidate`
scenarios are what `automate` turns into specs), composing with the Account /
Session / Workspace / Asset narrative the upstream fixtures already use.

Asserts the Step 6.8 contract from planning/plan.md: the framework builds
lazily and idempotently; the plan scores scenarios; `automate` generates
structurally-valid TS with provenance + fixture-mediated data; `automation-map`
links scenario -> spec and a `/tc:traceability-map` re-run resolves the
`Automated test` column of `test-map.md` from `pending`; the write boundary
holds (`bdd/` + `product-knowledge/` byte-identical, the framework lands at the
project-root `tests/` tree outside `.test-commander/`); `/tc:next` advances past
`/tc:automation-plan`; no Playwright execution happens under pytest. Plus the
byte-stable re-run contract.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import automate
import automation_plan
import build_framework
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
import requirements_to_tests
import review_requirements
import session_summary
import traceability_map

REPO = Path(__file__).resolve().parent.parent
PHASE_3_FIXTURE = REPO / "tests" / "fixtures" / "seeded-sample-project"
PHASE_4_FIXTURE = REPO / "tests" / "fixtures" / "seeded-exploration-session"
PHASE_2_FIXTURE = REPO / "tests" / "fixtures" / "seeded-flawed-requirements"
PHASE_6_FIXTURE = REPO / "tests" / "fixtures" / "seeded-automation"

CHARTER_TARGET = (
    "Sign-in flow plus workspace-detail asset upload (POST /workspaces/{id}/assets)."
)


# ---------------------------------------------------------------------------
# Setup (mirrors the Phase 5 integration smoke)
# ---------------------------------------------------------------------------


def setup_consuming_project(tmp_path: Path) -> Path:
    project = tmp_path / "my-project"
    project.mkdir()
    init_workspace.init_workspace(project)
    workspace = project / ".test-commander"
    (workspace / "project.md").write_text(
        "# my-project\n\nPhase 6 integration smoke.\n", encoding="utf-8"
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


def run_upstream(project: Path) -> None:
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
    generate_bdd.run(project)  # auto-review on
    traceability_map.traceability_map(project)


def inject_clean_feature(project: Path) -> None:
    """Add the clean seeded-automation feature so Phase 6 has automate-ranked
    scenarios (its @automated-candidate scenarios)."""
    features = project / ".test-commander" / "bdd" / "features"
    shutil.copy(PHASE_6_FIXTURE / "sign-in.feature", features / "sign-in.feature")


def run_phase_6(project: Path) -> None:
    build_framework.scaffold(project)
    automation_plan.build_plan(project)
    automate.generate(project)  # auto-review on
    generate_test_data.generate_test_data(project)
    traceability_map.traceability_map(project)  # re-run to resolve Automated test


# ---------------------------------------------------------------------------
# Full workflow
# ---------------------------------------------------------------------------


def test_full_phase_6_workflow(tmp_path: Path) -> None:
    project = setup_consuming_project(tmp_path)
    workspace = project / ".test-commander"
    run_upstream(project)
    inject_clean_feature(project)

    bdd = workspace / "bdd"
    pk = workspace / "product-knowledge"
    bdd_pre = snapshot_dir(bdd)
    pk_pre = snapshot_dir(pk)

    # --- Phase 6 ---
    run_phase_6(project)

    # Framework built lazily at the project-root tests/ tree, outside the workspace.
    config = project / "tests" / "playwright.config.ts"
    assert config.is_file(), "framework not built at project-root tests/"
    assert not (workspace / "tests").exists(), "framework must not land inside .test-commander/"

    # Idempotent build: a second scaffold creates nothing.
    second = build_framework.scaffold(project)
    assert second.created == [], f"re-build created {second.created}"

    # The plan scored the clean feature's scenarios.
    plan = (workspace / "automation-plan" / "sign-in.md").read_text(encoding="utf-8")
    assert "automate" in plan, "automation plan did not rank any scenario automate"

    # automate generated a structurally-valid spec with provenance + fixture data.
    spec_path = project / "tests" / "e2e" / "sign-in.spec.ts"
    assert spec_path.is_file(), "automate produced no sign-in spec"
    spec = spec_path.read_text(encoding="utf-8")
    assert "@req:REQ-001" in spec and "@cs:CS-001-" in spec, "spec missing provenance"
    assert "../fixtures/sign-in" in spec, "spec must reach data via its fixture"
    assert (project / "tests" / "fixtures" / "sign-in.ts").is_file(), "no fixture generated"

    # generate-test-data closed the D6 loop: the fixture's seed file exists.
    assert (workspace / "test-data" / "seed" / "sign-in.json").is_file(), (
        "generate-test-data did not create the fixture's seed file"
    )

    # automation-map links scenario -> spec.
    amap = (workspace / "traceability" / "automation-map.md").read_text(encoding="utf-8")
    assert "tests/e2e/sign-in.spec.ts" in amap and "CS-001-001" in amap

    # The traceability-map re-run resolved the Automated test column from pending.
    test_map = (workspace / "traceability" / "test-map.md").read_text(encoding="utf-8")
    assert "tests/e2e/sign-in.spec.ts" in test_map, (
        "test-map Automated test column did not resolve from the automation map"
    )
    assert "pending" in test_map, "Test result / Quality report must still read pending"

    # Write boundary: bdd/ and product-knowledge/ untouched by Phase 6.
    assert snapshot_dir(bdd) == bdd_pre, "Phase 6 must not write bdd/"
    assert snapshot_dir(pk) == pk_pre, "Phase 6 must not write product-knowledge/"

    # No Playwright execution under pytest: only generated text, no runtime output.
    for artifact in ("node_modules", "test-results", "playwright-report"):
        assert not (project / "tests" / artifact).exists(), (
            f"Playwright execution leaked into the suite (found tests/{artifact})"
        )

    # /tc:next advances past /tc:automation-plan.
    rec = next_step.next_step_for(project)
    if rec is not None:
        assert rec.command != "/tc:automation-plan", (
            f"/tc:next still recommends /tc:automation-plan after Phase 6: {rec}"
        )


def test_byte_stable_rerun_across_phase_6(tmp_path: Path) -> None:
    project = setup_consuming_project(tmp_path)
    workspace = project / ".test-commander"
    run_upstream(project)
    inject_clean_feature(project)

    run_phase_6(project)
    targets = [
        *sorted((project / "tests" / "e2e").glob("*.spec.ts")),
        *sorted((project / "tests" / "pages").glob("*.ts")),
        *sorted((project / "tests" / "fixtures").glob("*.ts")),
        workspace / "traceability" / "automation-map.md",
        workspace / "traceability" / "test-map.md",
        workspace / "automation-plan" / "sign-in.md",
        workspace / "test-data" / "seed" / "sign-in.json",
    ]
    first = {p: p.read_bytes() for p in targets}

    run_phase_6(project)
    for path, snapshot in first.items():
        assert path.read_bytes() == snapshot, f"{path.name} not byte-stable on Phase 6 re-run"
