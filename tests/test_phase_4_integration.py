"""Step 4.7 - Phase 4 integration smoke.

Drives the full Phase 2 + Phase 3 + Phase 4 helper chain in workflow
order against a fresh tmp consuming project. Complements the per-command
unit tests in 4.2-4.5 by exercising the four-step Phase-4 sequence end
to end:

    init -> upload (Phase 2 reqs + Phase 3 sample-project + Phase 4 recording) ->
    [Phase 2] review_requirements -> requirements_to_tests ->
    [Phase 3] learn-from-docs -> learn-from-specs -> learn-from-code ->
              learn-from-api -> learn-from-tests ->
    [Phase 4] create-charter -> explore -> session-summary -> test-ideas ->
    /tc:next post-Phase-4

In-process imports (per the Phase 3 Step 3.8 lesson that in-process beat
subprocess for integration speed by 10x). At every transition the
integration test asserts the expected artifact landed; the cross-phase
write-boundary is enforced (Phase 4 reads but never writes to
`<workspace>/product-knowledge/` or `<workspace>/traceability/`); the
`tc-test-idea/v1` Phase-2-to-Phase-4 frontmatter contract is preserved
byte-for-byte; and `/tc:next` advances past `/tc:create-charter`.

The Phase 4 helpers run AFTER Phase 2 + Phase 3 so the `[exploration-review]`
open-questions line lands on top of Phase-2 + Phase-3 entries rather
than being clobbered by them (per the Step 4.6 lesson).

Also asserts the byte-stable re-run contract (full Phase-4 sweep twice
in sequence is byte-identical) and the live-mode refusal under pytest
(`tc-explore.exploration.mode: live` triggers `LiveModeRefusedError`
before any MCP connection is constructed).
"""

from __future__ import annotations

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
import init_workspace
import next_step
import pytest
import requirements_to_tests
import review_requirements
import session_summary

REPO = Path(__file__).resolve().parent.parent
PHASE_3_FIXTURE = REPO / "tests" / "fixtures" / "seeded-sample-project"
PHASE_4_FIXTURE = REPO / "tests" / "fixtures" / "seeded-exploration-session"
PHASE_2_FIXTURE = REPO / "tests" / "fixtures" / "seeded-flawed-requirements"

CHARTER_TARGET = (
    "Sign-in flow plus workspace-detail asset upload (POST /workspaces/{id}/assets)."
)


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------


def setup_consuming_project(tmp_path: Path) -> Path:
    """Init a workspace + upload every fixture's inputs. Does not run any
    helpers; the caller drives the Phase-2/3/4 chain in workflow order."""
    project = tmp_path / "my-project"
    project.mkdir()
    init_workspace.init_workspace(project)
    workspace = project / ".test-commander"

    # Phase-1 metadata so /tc:next does not get stuck on R2.
    (workspace / "project.md").write_text(
        "# my-project\n\nPhase 4 integration smoke.\n", encoding="utf-8"
    )

    uploaded = workspace / "documents" / "uploaded"

    # Phase 2 inputs: the flawed-requirements fixture.
    shutil.copy(PHASE_2_FIXTURE / "requirements.md", uploaded / "requirements.md")
    shutil.copy(
        PHASE_2_FIXTURE / "acceptance-criteria.md",
        uploaded / "acceptance-criteria.md",
    )
    shutil.copy(PHASE_2_FIXTURE / "user-stories.md", uploaded / "user-stories.md")

    # Phase 3 inputs: the sample-project fixture.
    for name in ("product-overview.md", "glossary.md", "user-journey-sign-in.md"):
        shutil.copy(PHASE_3_FIXTURE / "documents" / name, uploaded / name)
    shutil.copy(PHASE_3_FIXTURE / "specs" / "openapi.yaml", uploaded / "openapi.yaml")
    shutil.copytree(PHASE_3_FIXTURE / "src", uploaded / "code")
    shutil.copytree(PHASE_3_FIXTURE / "recorded-api", uploaded / "recorded-api")
    shutil.copytree(PHASE_3_FIXTURE / "tests", uploaded / "tests")

    # Phase 4 input: the recorded Playwright session JSON for CH-001.
    recorded_dir = uploaded / "recorded-sessions"
    recorded_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        PHASE_4_FIXTURE / "recorded-session.json",
        recorded_dir / "CH-001.json",
    )

    return project


def workspace_file(project: Path, rel: str) -> Path:
    return project / ".test-commander" / rel


def run_phase_2(project: Path) -> None:
    """Phase 2 in workflow order. Lands seed test-ideas for the 17 REQs."""
    review_requirements.review(project)
    requirements_to_tests.to_tests(project)


def run_phase_3(project: Path) -> None:
    """Phase 3 in workflow order. Populates product-knowledge/."""
    extract_knowledge_from_docs.run(project)
    extract_knowledge_from_specs.run(project)
    extract_knowledge_from_code.run(project)
    extract_knowledge_from_api.run(project)
    extract_knowledge_from_tests.run(project)


def run_phase_4(project: Path) -> tuple[str, ...]:
    """Phase 4 in workflow order. Returns the SESS-ID for downstream tests."""
    create_charter.run(project, target=CHARTER_TARGET, mission=None, new_id=False)
    explore.run(project, charter_id="CH-001", no_review=False)
    notes = list(
        workspace_file(project, "exploration-notes").glob("SESS-*.md")
    )
    assert len(notes) == 1, (
        f"expected exactly one exploration note; got {[n.name for n in notes]}"
    )
    session_id = notes[0].stem
    session_summary.run(project, session_id=session_id)
    enrich_test_ideas.run(project, session_id=session_id)
    return (session_id,)


def snapshot_dir(root: Path) -> dict[Path, bytes]:
    """Recursive byte snapshot of every file under ``root`` keyed by
    path relative to ``root``."""
    snapshots: dict[Path, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            snapshots[path.relative_to(root)] = path.read_bytes()
    return snapshots


# ---------------------------------------------------------------------------
# Main end-to-end workflow
# ---------------------------------------------------------------------------


def test_full_phase_4_workflow(tmp_path: Path) -> None:
    project = setup_consuming_project(tmp_path)
    workspace = project / ".test-commander"
    pk = workspace / "product-knowledge"

    # --- Phase 2: requirements review + test-idea seeds ---
    run_phase_2(project)
    test_ideas_dir = workspace / "test-ideas"
    pre_phase4_seeds = sorted(test_ideas_dir.glob("REQ-*.md"))
    assert len(pre_phase4_seeds) == 17, (
        f"Phase 2 must seed 17 REQ-*.md test-ideas; got {len(pre_phase4_seeds)}"
    )
    # Every seed ships status: seed.
    for seed in pre_phase4_seeds:
        text = seed.read_text(encoding="utf-8")
        assert "status: seed" in text, (
            f"Phase 2 seed {seed.name} missing status: seed"
        )

    # --- Phase 3: populate product-knowledge ---
    run_phase_3(project)
    # All 10 product-knowledge artifacts present.
    pk_artifacts = sorted(pk.glob("*.md"))
    assert len(pk_artifacts) >= 10, (
        f"Phase 3 must populate at least 10 product-knowledge artifacts; "
        f"got {len(pk_artifacts)}: {[p.name for p in pk_artifacts]}"
    )
    # Snapshot product-knowledge BEFORE Phase 4 fires.
    pk_snapshot_pre = snapshot_dir(pk)

    # --- Phase 4: charter -> explore -> session-summary -> test-ideas ---
    (session_id,) = run_phase_4(project)

    # --- A. /tc:create-charter ---
    charter_path = workspace / "charters" / "CH-001.md"
    assert charter_path.is_file(), "charter file must exist after /tc:create-charter"
    charter_text = charter_path.read_text(encoding="utf-8")
    # Valid YAML frontmatter; every CHARTER_REQUIRED_FIELDS key present.
    assert charter_text.startswith("---\n"), "charter must begin with frontmatter"
    fm_end = charter_text.find("\n---\n", 4)
    assert fm_end > 0, "charter frontmatter must end with ---"
    fm = charter_text[4:fm_end]
    for key in ("id", "mission", "target", "time-box", "risk-areas",
                "acceptance-criteria"):
        assert f"{key}:" in fm, f"charter frontmatter missing {key}:"
    assert "id: CH-001" in fm

    # --- B. /tc:explore ---
    note_path = workspace / "exploration-notes" / f"{session_id}.md"
    assert note_path.is_file(), "exploration note must exist after /tc:explore"
    note_text = note_path.read_text(encoding="utf-8")
    # All 6 universal anomaly categories captured from the seeded recording.
    for category in (
        "slow-response", "console-error", "broken-link",
        "missing-evidence", "auth-mismatch", "unexpected-state",
    ):
        assert category in note_text, (
            f"exploration note missing seeded anomaly category {category!r}"
        )
    # All 6 universal observation event types surface.
    for event_type in (
        "page_load", "click", "fill", "screenshot",
        "console_message", "network_request",
    ):
        assert event_type in note_text, (
            f"exploration note missing observation event_type {event_type!r}"
        )

    # The internal review sub-mode appended an [exploration-review] entry
    # to open-questions.md (the seeded missing-evidence gap).
    open_q = (workspace / "requirements" / "open-questions.md").read_text(
        encoding="utf-8"
    )
    assert "[exploration-review]" in open_q, (
        "Phase 4 internal review sub-mode must append an [exploration-review] "
        "line to open-questions.md for the seeded missing-evidence anomaly"
    )

    # --- C. /tc:session-summary ---
    summary_path = workspace / "sessions" / f"{session_id}.md"
    assert summary_path.is_file(), "session summary must exist after /tc:session-summary"
    summary_text = summary_path.read_text(encoding="utf-8")
    # Charter resolved (CH-001 + target appear in the summary).
    assert "CH-001" in summary_text, "summary must cite the resolved charter"
    assert "Sign-in flow" in summary_text, (
        "summary must surface the charter target text"
    )
    # Candidate scenarios listed (at least 6: one per seeded anomaly).
    import re
    cs_ids = re.findall(r"CS-\d{3}-\d{3}", summary_text)
    assert len(cs_ids) >= 6, (
        f"summary must list >= 6 candidate scenarios "
        f"(one per anomaly); got {len(cs_ids)}"
    )
    # Sessions index updated.
    index_path = workspace / "sessions" / "index.md"
    assert index_path.is_file(), "sessions/index.md must exist"
    assert session_id in index_path.read_text(encoding="utf-8")

    # --- D. /tc:test-ideas ---
    enriched = [
        p for p in sorted(test_ideas_dir.glob("REQ-*.md"))
        if "## Phase 4 enrichment" in p.read_text(encoding="utf-8")
    ]
    assert len(enriched) >= 3, (
        f"Phase 4 enrichment must touch at least 3 test-idea seeds against "
        f"the seeded fixture; got {len(enriched)}"
    )
    # Phase-2 frontmatter contract preserved byte-for-byte on every enriched file.
    pre_by_name = {p.name: p.read_text(encoding="utf-8") for p in pre_phase4_seeds}
    for path in enriched:
        post_text = path.read_text(encoding="utf-8")
        pre_text = pre_by_name[path.name]
        # Every Phase-2 scalar key still present with its original value
        # (status: seed flips to status: enriched; phase_4_sessions: is new).
        for key in ("schema", "requirement_id", "requirement_title", "source",
                    "ac_review_present", "generated_by"):
            pre_line = next(
                (line for line in pre_text.split("\n") if line.startswith(f"{key}:")),
                None,
            )
            assert pre_line is not None, (
                f"{path.name}: Phase-2 seed missing expected key {key!r} (pre-state)"
            )
            assert pre_line in post_text, (
                f"{path.name}: Phase-2 scalar {key!r} value mutated by Phase 4"
            )
        # Status bumped to enriched on enriched files.
        assert "status: enriched" in post_text, (
            f"{path.name}: enriched file must carry status: enriched"
        )
        assert "status: seed" not in post_text, (
            f"{path.name}: status: seed still present after enrichment"
        )
        # phase_4_sessions populated with the contributing SESS-ID.
        assert f"phase_4_sessions: [{session_id}]" in post_text, (
            f"{path.name}: phase_4_sessions: not populated with {session_id}"
        )

    # --- E. Phase 4 write-boundary discipline ---
    # product-knowledge byte-identical before and after Phase 4.
    pk_snapshot_post = snapshot_dir(pk)
    assert pk_snapshot_pre == pk_snapshot_post, (
        "Phase 4 must NOT write to product-knowledge/; "
        f"diff: {set(pk_snapshot_pre) ^ set(pk_snapshot_post)} "
        "(file set) or mutated bytes within."
    )
    # traceability/ carries no tc-explore content.
    traceability = workspace / "traceability"
    if traceability.is_dir():
        for tp in traceability.rglob("*.md"):
            text = tp.read_text(encoding="utf-8")
            assert "tc-explore" not in text, (
                f"Phase 4 must not write tc-explore content into {tp}; "
                f"got:\n{text[:200]}"
            )

    # --- F. Full union state correct ---
    # All four Phase 4 artifact slots populated.
    assert (workspace / "charters" / "CH-001.md").is_file()
    assert (workspace / "exploration-notes" / f"{session_id}.md").is_file()
    assert (workspace / "sessions" / f"{session_id}.md").is_file()
    assert (workspace / "sessions" / "index.md").is_file()
    # At least one Phase 4 enriched test-idea.
    assert enriched, "Phase 4 enrichment produced zero enriched files"

    # --- G. /tc:next advances past /tc:create-charter ---
    # Per the Phase-2 Step-2.9 + Phase-3 Step-3.8 lesson: assert command
    # != /tc:create-charter rather than pinning a specific next command.
    rec = next_step.next_step_for(project)
    if rec is not None:
        assert rec.command != "/tc:create-charter", (
            f"/tc:next still recommends /tc:create-charter after Phase 4 "
            f"helper sweep: {rec}"
        )


# ---------------------------------------------------------------------------
# Idempotent re-run
# ---------------------------------------------------------------------------


def test_byte_stable_rerun_across_phase_4(tmp_path: Path) -> None:
    """Running the full Phase 4 helper sweep twice in sequence produces
    byte-identical artifacts for every Phase 4 file and a line-stable
    open-questions.md. Mirrors the Phase 3 Step 3.8 byte-stable
    re-run contract."""
    project = setup_consuming_project(tmp_path)
    workspace = project / ".test-commander"

    # Run Phase 2 + Phase 3 once (their byte-stability is asserted by their
    # own integration tests).
    run_phase_2(project)
    run_phase_3(project)

    # Phase 4 first pass.
    (session_id,) = run_phase_4(project)

    phase_4_dirs = ("charters", "exploration-notes", "sessions", "test-ideas")
    first_snapshot: dict[Path, bytes] = {}
    for dirname in phase_4_dirs:
        d = workspace / dirname
        if d.is_dir():
            for entry in sorted(d.rglob("*.md")):
                first_snapshot[entry.relative_to(workspace)] = entry.read_bytes()

    open_q_first = (workspace / "requirements" / "open-questions.md").read_text(
        encoding="utf-8"
    )

    # Phase 4 second pass.
    run_phase_4(project)

    for rel, snapshot in first_snapshot.items():
        current = (workspace / rel).read_bytes()
        assert current == snapshot, (
            f"{rel} not byte-identical on Phase 4 re-run"
        )

    open_q_second = (workspace / "requirements" / "open-questions.md").read_text(
        encoding="utf-8"
    )
    assert open_q_first.count("\n") == open_q_second.count("\n"), (
        "open-questions.md line count changed on Phase 4 re-run"
    )


# ---------------------------------------------------------------------------
# Live-mode refusal under pytest
# ---------------------------------------------------------------------------


def test_live_mode_refused_under_pytest(tmp_path: Path) -> None:
    """tc-explore.exploration.mode: live must refuse when PYTEST_CURRENT_TEST
    is set so no real MCP connection can leak from the suite."""
    project = setup_consuming_project(tmp_path)
    workspace = project / ".test-commander"

    # Seed minimal Phase 3 state so /tc:create-charter succeeds (we want
    # the live-mode refusal to fire INSIDE /tc:explore, not earlier on
    # the precondition gate).
    run_phase_3(project)
    create_charter.run(project, target=CHARTER_TARGET, mission=None, new_id=False)

    # Append the live-mode config extension.
    config = workspace / "config.yaml"
    base = config.read_text(encoding="utf-8") if config.is_file() else ""
    config.write_text(
        base.rstrip()
        + '\n\ntc-explore:\n  exploration:\n    mode: live\n'
          '    mcp-endpoint: "http://localhost:9999"\n'
          '    target-url: "http://localhost:8000"\n',
        encoding="utf-8",
    )

    with pytest.raises(explore.LiveModeRefusedError):
        explore.run(project, charter_id="CH-001", no_review=False)
