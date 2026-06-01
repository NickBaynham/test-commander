#!/usr/bin/env python3
"""tc-evidence indexer - Phase 7 Step 7.3.

The ``tc-evidence`` skill is an internal cross-cutting indexer with no
user-facing command. It is invoked by ``/tc:run`` after a run completes (and
later by the web console). It does three things:

1. **Routes** each run artifact into the workspace evidence tree per the
   evidence policy - screenshots and logs are committed; videos and traces are
   git-ignored by default (with a documented git-lfs opt-in); reports are
   committed.
2. **Writes** ``<workspace>/evidence/evidence-index.md`` listing every artifact
   across all run records with its run + scenario provenance.
3. **Manages** ``<workspace>/evidence/.gitignore`` so the large (video / trace)
   classes are ignored while their directory placeholders stay committed.

The primary entry point is ``index_run_evidence(project_root, run_id)``, which
``/tc:run`` calls automatically after writing its per-run record (suppressible
with ``--no-index``). A thin ``main`` is provided for manual / debugging use.

**Read-from-the-record, not the filesystem.** The index is rebuilt from the
machine-readable ``runs/<RUN-ID>/results.json`` records each phase writes, so
it is deterministic and order-independent: re-running over unchanged records
produces byte-identical output. Artifact files are copied into the evidence
tree when their source is findable (relative to ``source_root``, default the
project root, or absolute as Playwright emits them); a missing source is still
indexed (the record is the source of truth).

Per D18 the helper ships inside the plugin. Per D19 the policy is universal;
project tuning enters via ``<workspace>/config.yaml`` in a later sub-step.

Exit codes (CLI):
    0 - evidence indexed.
    2 - precondition failure (uninitialized workspace, missing run record).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"

# Artifact extension -> (type label, evidence subdirectory, committed?).
EXT_TYPE: dict[str, str] = {
    ".png": "screenshot",
    ".jpg": "screenshot",
    ".jpeg": "screenshot",
    ".gif": "screenshot",
    ".webm": "video",
    ".mp4": "video",
    ".zip": "trace",
    ".txt": "log",
    ".log": "log",
    ".json": "report",
    ".html": "report",
}
TYPE_DIR: dict[str, str] = {
    "screenshot": "screenshots",
    "video": "videos",
    "trace": "traces",
    "log": "logs",
    "report": "logs",
}
# Types whose artifacts are git-ignored by default (large binaries).
IGNORED_TYPES: frozenset[str] = frozenset({"video", "trace"})


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class EvidenceError(Exception):
    pass


class UninitializedWorkspaceError(EvidenceError):
    pass


class RunRecordMissingError(EvidenceError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Artifact:
    """One routed evidence artifact, joined to its run + scenario provenance."""

    dest: str  # workspace-relative logical path, e.g. evidence/screenshots/x.png
    type: str
    committed: bool
    run_id: str
    req_id: str | None
    cs_id: str | None
    scenario: str
    source: str  # the raw attachment path from the run record

    def sort_key(self) -> tuple[str, str]:
        return (self.dest, self.run_id)


@dataclass
class EvidenceOutcome:
    index_path: Path
    gitignore_path: Path
    artifacts: list[Artifact]

    @property
    def committed(self) -> int:
        return sum(1 for a in self.artifacts if a.committed)

    @property
    def ignored(self) -> int:
        return sum(1 for a in self.artifacts if not a.committed)


# ---------------------------------------------------------------------------
# Workspace IO
# ---------------------------------------------------------------------------


def workspace_dir(project_root: Path) -> Path:
    ws = project_root / WORKSPACE_DIRNAME
    if not ws.is_dir():
        raise UninitializedWorkspaceError(
            f"not a Test Commander workspace: {project_root} "
            f"(no {WORKSPACE_DIRNAME}/). Run /tc:init first."
        )
    return ws


def _classify(path: str) -> tuple[str, str, bool]:
    """Return (type, evidence-subdir, committed?) for an artifact path."""
    art_type = EXT_TYPE.get(Path(path).suffix.lower(), "log")
    return art_type, TYPE_DIR[art_type], art_type not in IGNORED_TYPES


def _read_run_records(workspace: Path) -> list[dict]:
    """Every runs/<RUN-ID>/results.json, sorted by run id for determinism."""
    records: list[dict] = []
    for results in sorted((workspace / "runs").glob("*/results.json")):
        records.append(json.loads(results.read_text(encoding="utf-8")))
    return records


def _artifacts_from_records(records: list[dict]) -> list[Artifact]:
    artifacts: list[Artifact] = []
    for record in records:
        run_id = record.get("run_id", "")
        for result in record.get("results", []):
            for source in result.get("attachments", []):
                art_type, subdir, committed = _classify(source)
                artifacts.append(
                    Artifact(
                        dest=f"evidence/{subdir}/{Path(source).name}",
                        type=art_type,
                        committed=committed,
                        run_id=run_id,
                        req_id=result.get("requirement"),
                        cs_id=result.get("candidate"),
                        scenario=result.get("scenario", ""),
                        source=source,
                    )
                )
    return artifacts


# ---------------------------------------------------------------------------
# Routing + rendering
# ---------------------------------------------------------------------------


def _route_file(artifact: Artifact, workspace: Path, source_root: Path) -> None:
    """Copy the raw artifact into the evidence tree when its source is found."""
    src = Path(artifact.source)
    if not src.is_absolute():
        src = source_root / artifact.source
    if src.is_file():
        dest = workspace / artifact.dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)


def render_gitignore() -> str:
    return (
        "# Managed by the tc-evidence indexer (/tc:run). Videos and traces can\n"
        "# be large, so they are git-ignored by default. To version them, enable\n"
        "# git-lfs (see the tc-run evidence-management methodology) and delete\n"
        "# the matching lines below.\n"
        "videos/*\n"
        "!videos/README.md\n"
        "traces/*\n"
        "!traces/README.md\n"
    )


def _md_cell(value: str | None) -> str:
    return value if value else "_(none)_"


def render_index(artifacts: list[Artifact]) -> str:
    lines: list[str] = []
    lines.append("# Evidence index")
    lines.append("")
    lines.append(
        "_Managed by the tc-evidence indexer (`/tc:run`). Screenshots, logs, and "
        "reports are committed; videos and traces are git-ignored by default "
        "(enable git-lfs to version them - see the tc-run evidence-management "
        "methodology)._"
    )
    lines.append("")
    lines.append("| artifact | type | policy | run | requirement | candidate | scenario |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for a in sorted(artifacts, key=lambda x: x.sort_key()):
        policy = "committed" if a.committed else "git-ignored"
        lines.append(
            f"| {a.dest} | {a.type} | {policy} | {a.run_id} | "
            f"{_md_cell(a.req_id)} | {_md_cell(a.cs_id)} | {a.scenario} |"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def index_run_evidence(
    project_root: Path,
    run_id: str,
    *,
    source_root: Path | None = None,
) -> EvidenceOutcome:
    """Route the named run's artifacts and rebuild the evidence index over all
    run records. The entry point ``/tc:run`` auto-runs (suppressible with
    ``--no-index``)."""
    project_root = Path(project_root)
    workspace = workspace_dir(project_root)
    source_root = Path(source_root) if source_root is not None else project_root

    record_path = workspace / "runs" / run_id / "results.json"
    if not record_path.is_file():
        raise RunRecordMissingError(
            f"no run record for {run_id} (expected {record_path.relative_to(project_root)}); "
            "run /tc:run first"
        )

    # Route just the named run's artifacts (their source is available now).
    this_run = json.loads(record_path.read_text(encoding="utf-8"))
    for artifact in _artifacts_from_records([this_run]):
        _route_file(artifact, workspace, source_root)

    # Rebuild the index over every run record (the complete, deterministic view).
    all_artifacts = _artifacts_from_records(_read_run_records(workspace))
    evidence = workspace / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    index_path = evidence / "evidence-index.md"
    gitignore_path = evidence / ".gitignore"
    index_path.write_text(render_index(all_artifacts), encoding="utf-8")
    gitignore_path.write_text(render_gitignore(), encoding="utf-8")
    return EvidenceOutcome(
        index_path=index_path, gitignore_path=gitignore_path, artifacts=all_artifacts
    )


# ---------------------------------------------------------------------------
# CLI (manual / debugging; tc-evidence has no /tc: command)
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Route a run's artifacts into the evidence tree and rebuild the "
            "evidence index. Normally auto-run by /tc:run."
        ),
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    parser.add_argument("--run-id", required=True, help="The RUN-ID whose artifacts to route.")
    parser.add_argument(
        "--source-root",
        default=None,
        help="Root for resolving relative artifact paths (default: project root).",
    )
    args = parser.parse_args(argv if argv is not None else None)
    project_root = Path(args.project_root).resolve()
    source_root = Path(args.source_root) if args.source_root else None

    try:
        outcome = index_run_evidence(project_root, args.run_id, source_root=source_root)
    except EvidenceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"evidence: {len(outcome.artifacts)} artifact(s) "
        f"(committed {outcome.committed}, git-ignored {outcome.ignored})"
    )
    print(f"  index: {outcome.index_path.relative_to(project_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
