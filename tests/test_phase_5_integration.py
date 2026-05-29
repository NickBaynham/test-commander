"""Step 5.6 - Phase 5 integration smoke.

Drives the full Phase 2 + Phase 3 + Phase 4 + Phase 5 helper chain in
workflow order against a fresh tmp consuming project. Complements the
per-command unit tests in 5.2-5.4 by exercising the end-to-end sequence:

    init -> upload ->
    [Phase 2] review_requirements -> requirements_to_tests ->
    [Phase 3] learn-from-* (5 helpers) ->
    [Phase 4] create-charter -> explore -> session-summary -> test-ideas ->
    [Phase 5] generate-bdd (+ auto-review) -> traceability-map ->
    /tc:next post-Phase-5

In-process imports (per the Phase 3 Step 3.8 / Phase 4 Step 4.7 lesson:
in-process beat subprocess for integration speed). Phase 5 runs AFTER
Phase 2-4 so any `[bdd-review]` line lands on top of the upstream
`[exploration-review]` entry rather than clobbering it (the Phase 4 Step
4.7 sequencing lesson, reapplied).

Asserts: generated features are valid Gherkin with resolvable @req:/@cs:
linkage tags; the auto-review runs on every feature (each summary carries
a resolved verdict, never the pre-review placeholder). Because the upstream
fixture is deliberately flawed (vague acceptance criteria), the generated
scenarios inherit that vagueness and the review correctly routes
`[bdd-review]` ambiguous-step signals -- the generate->review pipeline
working end to end on realistic input. The traceability maps rebuild with
REQ -> CS -> scenario links and `pending` downstream; Phase 5's write
boundary holds (product-knowledge/ and test-ideas/ byte-identical before
and after); the Phase-4 `[exploration-review]` line survives the Phase 5
run; and `/tc:next` advances past `/tc:generate-bdd`. A separate test
injects the seeded flawed.feature and asserts all six `[bdd-review]`
categories appear below the upstream entries. Plus the byte-stable re-run
contract.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import create_charter
import enrich_test_ideas
import explore
import extract_knowledge_from_api
import extract_knowledge_from_code
import extract_knowledge_from_docs
import extract_knowledge_from_specs
import extract_knowledge_from_tests
import generate_bdd
import init_workspace
import next_step
import requirements_to_tests
import review_bdd
import review_requirements
import session_summary
import traceability_map

REPO = Path(__file__).resolve().parent.parent
PHASE_3_FIXTURE = REPO / "tests" / "fixtures" / "seeded-sample-project"
PHASE_4_FIXTURE = REPO / "tests" / "fixtures" / "seeded-exploration-session"
PHASE_2_FIXTURE = REPO / "tests" / "fixtures" / "seeded-flawed-requirements"
PHASE_5_FIXTURE = REPO / "tests" / "fixtures" / "seeded-bdd"

CHARTER_TARGET = (
    "Sign-in flow plus workspace-detail asset upload (POST /workspaces/{id}/assets)."
)


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


def setup_consuming_project(tmp_path: Path) -> Path:
    project = tmp_path / "my-project"
    project.mkdir()
    init_workspace.init_workspace(project)
    workspace = project / ".test-commander"
    (workspace / "project.md").write_text(
        "# my-project\n\nPhase 5 integration smoke.\n", encoding="utf-8"
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


def run_phase_2(project: Path) -> None:
    review_requirements.review(project)
    requirements_to_tests.to_tests(project)


def run_phase_3(project: Path) -> None:
    extract_knowledge_from_docs.run(project)
    extract_knowledge_from_specs.run(project)
    extract_knowledge_from_code.run(project)
    extract_knowledge_from_api.run(project)
    extract_knowledge_from_tests.run(project)


def run_phase_4(project: Path) -> str:
    create_charter.run(project, target=CHARTER_TARGET, mission=None, new_id=False)
    explore.run(project, charter_id="CH-001", no_review=False)
    note = next((project / ".test-commander" / "exploration-notes").glob("SESS-*.md"))
    session_id = note.stem
    session_summary.run(project, session_id=session_id)
    enrich_test_ideas.run(project, session_id=session_id)
    return session_id


def run_phase_5(project: Path) -> None:
    generate_bdd.run(project)  # auto-review on
    traceability_map.traceability_map(project)


def run_upstream(project: Path) -> str:
    run_phase_2(project)
    run_phase_3(project)
    return run_phase_4(project)


# ---------------------------------------------------------------------------
# Full workflow
# ---------------------------------------------------------------------------


def test_full_phase_5_workflow(tmp_path: Path) -> None:
    project = setup_consuming_project(tmp_path)
    workspace = project / ".test-commander"
    run_upstream(project)

    pk = workspace / "product-knowledge"
    test_ideas = workspace / "test-ideas"
    pk_pre = snapshot_dir(pk)
    ideas_pre = snapshot_dir(test_ideas)

    # --- Phase 5 ---
    run_phase_5(project)

    # generate-bdd: at least one valid Gherkin feature with linkage tags.
    features = sorted((workspace / "bdd" / "features").glob("*.feature"))
    assert features, "generate-bdd produced no feature files"
    for feat in features:
        text = feat.read_text(encoding="utf-8")
        assert "Feature:" in text, f"{feat.name} is not valid Gherkin"
        tag_lines = [
            ln for ln in text.splitlines()
            if ln.strip().startswith("@") and "@cs:" in ln
        ]
        assert tag_lines, f"{feat.name} has no scenario linkage tags"
        for ln in tag_lines:
            assert "@req:REQ-" in ln, f"{feat.name} scenario missing @req: tag"
            assert "@cs:CS-" in ln, f"{feat.name} scenario missing @cs: tag"

    # index lists the features.
    index = (workspace / "bdd" / "index.md").read_text(encoding="utf-8")
    for feat in features:
        assert feat.name in index

    # The auto-review ran on every feature: each summary carries a resolved
    # verdict (pass or N finding(s)), never the pre-review placeholder. The
    # upstream fixture is deliberately flawed (vague acceptance criteria), so
    # the generated scenarios inherit that vagueness and the review correctly
    # routes [bdd-review] ambiguous-step signals -- the generate->review
    # pipeline working end to end on realistic input.
    summaries = [
        p for p in (workspace / "bdd" / "summaries").glob("*.md") if p.name != "README.md"
    ]
    assert summaries, "no per-feature summaries written"
    for summary in summaries:
        body = summary.read_text(encoding="utf-8")
        assert "Review verdict:" in body, f"{summary.name}: no review verdict line"
        assert "(pending /tc:review-bdd)" not in body, (
            f"{summary.name}: auto-review did not run (verdict still pending)"
        )
    open_q = (workspace / "requirements" / "open-questions.md").read_text(encoding="utf-8")
    assert "[bdd-review]" in open_q, (
        "the flawed-requirement-derived scenarios should route [bdd-review] signals"
    )
    # The Phase-4 [exploration-review] line survives the Phase 5 run.
    assert "[exploration-review]" in open_q, (
        "Phase 5 must not clobber the Phase-4 [exploration-review] entry"
    )

    # traceability maps rebuilt with the chain links.
    req_map = (workspace / "traceability" / "requirements-map.md").read_text(encoding="utf-8")
    assert "REQ-001" in req_map and "bdd/features/" in req_map
    test_map = (workspace / "traceability" / "test-map.md").read_text(encoding="utf-8")
    assert re.search(r"CS-\d{3}-\d{3}", test_map), "test-map missing CS linkage"
    assert "pending" in test_map, "downstream chain links must read pending"

    # Phase 5 write boundary: product-knowledge/ and test-ideas/ untouched.
    assert snapshot_dir(pk) == pk_pre, "Phase 5 must not write product-knowledge/"
    assert snapshot_dir(test_ideas) == ideas_pre, "Phase 5 must not write test-ideas/"

    # /tc:next advances past /tc:generate-bdd.
    rec = next_step.next_step_for(project)
    if rec is not None:
        assert rec.command != "/tc:generate-bdd", (
            f"/tc:next still recommends /tc:generate-bdd after Phase 5: {rec}"
        )


def test_bdd_review_signals_append_below_upstream(tmp_path: Path) -> None:
    """Injecting the seeded flawed.feature and running review surfaces the six
    [bdd-review] categories, appended below the Phase-4 [exploration-review]
    entry (the sequencing lesson: downstream review never clobbers upstream)."""
    project = setup_consuming_project(tmp_path)
    workspace = project / ".test-commander"
    run_upstream(project)
    run_phase_5(project)

    features_dir = workspace / "bdd" / "features"
    shutil.copy(PHASE_5_FIXTURE / "flawed.feature", features_dir / "flawed.feature")
    review_bdd.review_features(project)

    open_q = (workspace / "requirements" / "open-questions.md").read_text(encoding="utf-8")
    assert "[exploration-review]" in open_q, "upstream entry must survive"
    bdd_lines = [ln for ln in open_q.splitlines() if "[bdd-review]" in ln]
    for cat in (
        "ambiguous-step", "missing-tag", "untraceable",
        "ui-coupled-step", "missing-examples", "conjunction-overload",
    ):
        assert any(cat in ln for ln in bdd_lines), f"missing [bdd-review] signal for {cat}"


def test_byte_stable_rerun_across_phase_5(tmp_path: Path) -> None:
    project = setup_consuming_project(tmp_path)
    workspace = project / ".test-commander"
    run_upstream(project)

    run_phase_5(project)
    targets = [
        *sorted((workspace / "bdd" / "features").glob("*.feature")),
        workspace / "bdd" / "index.md",
        workspace / "traceability" / "requirements-map.md",
        workspace / "traceability" / "test-map.md",
    ]
    first = {p.relative_to(workspace): p.read_bytes() for p in targets}
    open_q_first = (workspace / "requirements" / "open-questions.md").read_text(encoding="utf-8")

    run_phase_5(project)
    for rel, snapshot in first.items():
        assert (workspace / rel).read_bytes() == snapshot, f"{rel} not byte-stable on re-run"
    open_q_second = (workspace / "requirements" / "open-questions.md").read_text(encoding="utf-8")
    assert open_q_first.count("\n") == open_q_second.count("\n"), (
        "open-questions.md line count changed on Phase 5 re-run"
    )
