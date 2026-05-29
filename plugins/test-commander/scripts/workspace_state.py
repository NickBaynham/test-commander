#!/usr/bin/env python3
"""Read a Test Commander workspace and return a structured snapshot.

Shared between `/tc:status` (formats the snapshot for users) and
`/tc:next` (uses the snapshot to recommend the next command).

A file is "populated" iff its content differs from the bundled template.
A workspace file with no template counterpart is treated as populated
(user-created content).

A phase is "in_progress" iff at least one file in that phase's
status-signal directories is populated. Otherwise "not_started".

The status-signal directories are those a phase *uniquely* produces. A
directory that an earlier phase also writes is not a reliable signal that
the later phase ran, so it is excluded (see PHASE_OWNERSHIP comments). This
prevents /tc:next from skipping phases: e.g. Phase 2 seeds ``test-ideas/``
(Phase-4-owned) and writes ``traceability/`` (Phase-5-owned), and the user
uploads inputs to ``documents/`` before any phase runs -- none of those
mean Phase 3/4/5 have actually started.
"""

import argparse
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "workspace"
WORKSPACE_DIRNAME = ".test-commander"

# Phase -> list of workspace-relative status-signal paths it *uniquely*
# produces. A directory an earlier phase also writes is deliberately excluded
# so it cannot mark this phase in_progress prematurely:
#   - "documents" is user-uploaded input (populated before any phase) -> not a
#     Phase-3 signal (Phase 3 is signalled by "product-knowledge").
#   - "test-ideas" is seeded by Phase 2's /tc:requirements-to-tests -> not a
#     Phase-4 signal (Phase 4 is signalled by charters/exploration-notes/sessions).
#   - "traceability" is written by Phase 2's /tc:requirements-coverage -> not a
#     Phase-5 signal (Phase 5 is signalled by "bdd").
# Drift between this map and the per-phase plan content is caught by code review.
PHASE_OWNERSHIP: dict[str, list[str]] = {
    "1": ["project.md", "config.yaml", "methodology.md", "journal"],
    "2": ["requirements", "risk-register"],
    "3": ["product-knowledge"],
    "4": ["charters", "exploration-notes", "sessions"],
    "5": ["bdd"],
    "6": ["automation-plan", "test-data"],
    "7": ["quality-report", "evidence", "runs"],
    "8": ["learning"],
    "9": ["visuals"],
    "10.5": ["policy", "audit"],
}

PHASE_LABELS: dict[str, str] = {
    "1": "Workspace",
    "2": "Requirements",
    "3": "Project knowledge",
    "4": "Exploratory testing",
    "5": "BDD and traceability",
    "6": "Playwright automation",
    "7": "Execution and reporting",
    "8": "Learning",
    "9": "Visuals",
    "10.5": "Controlled execution",
}


@dataclass(frozen=True)
class WorkspaceSnapshot:
    workspace: Path
    exists: bool
    initialized: bool
    last_modified: datetime | None
    counts: dict[str, int] = field(default_factory=dict)
    populated: dict[str, int] = field(default_factory=dict)
    phase_status: dict[str, str] = field(default_factory=dict)


def _bucket(rel: Path) -> str:
    """Top-level bucket: dir name for nested files, file name for root files."""
    return rel.parts[0]


def _files_differ(workspace_path: Path, template_path: Path) -> bool:
    """Treat orphan workspace files as populated."""
    if not template_path.is_file():
        return True
    try:
        return workspace_path.read_bytes() != template_path.read_bytes()
    except OSError:
        return True


def _has_user_content(workspace: Path, template_root: Path, rel: str) -> bool:
    """Does the workspace path (file or dir) contain anything different from the template?"""
    ws_target = workspace / rel
    tpl_target = template_root / rel
    if ws_target.is_file():
        return _files_differ(ws_target, tpl_target)
    if ws_target.is_dir():
        # Any workspace file that differs from (or is missing from) the template
        for src in tpl_target.rglob("*") if tpl_target.is_dir() else []:
            if not src.is_file():
                continue
            dest = workspace / src.relative_to(template_root)
            if dest.is_file() and dest.read_bytes() != src.read_bytes():
                return True
        # Any orphan workspace file with no template counterpart
        for dest in ws_target.rglob("*"):
            if not dest.is_file():
                continue
            src = template_root / dest.relative_to(workspace)
            if not src.exists():
                return True
        return False
    return False


def _empty_phase_status() -> dict[str, str]:
    return {phase: "not_started" for phase in PHASE_OWNERSHIP}


def snapshot(
    project_root: Path,
    template_root: Path = DEFAULT_TEMPLATE,
) -> WorkspaceSnapshot:
    """Build a deterministic snapshot of the workspace under project_root."""
    project_root = Path(project_root)
    workspace = project_root / WORKSPACE_DIRNAME

    if not workspace.is_dir():
        return WorkspaceSnapshot(
            workspace=workspace,
            exists=False,
            initialized=False,
            last_modified=None,
            counts={},
            populated={},
            phase_status=_empty_phase_status(),
        )

    counts: dict[str, int] = defaultdict(int)
    populated: dict[str, int] = defaultdict(int)
    last_modified: datetime | None = None

    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(workspace)
        bucket = _bucket(rel)
        counts[bucket] += 1
        template_path = template_root / rel
        if _files_differ(path, template_path):
            populated[bucket] += 1
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        if last_modified is None or mtime > last_modified:
            last_modified = mtime

    phase_status = {
        phase: ("in_progress" if any(
            _has_user_content(workspace, template_root, rel) for rel in owned
        ) else "not_started")
        for phase, owned in PHASE_OWNERSHIP.items()
    }

    return WorkspaceSnapshot(
        workspace=workspace,
        exists=True,
        initialized=(workspace / "project.md").is_file(),
        last_modified=last_modified,
        counts=dict(counts),
        populated=dict(populated),
        phase_status=phase_status,
    )


def format_snapshot(snap: WorkspaceSnapshot) -> str:
    """Render the snapshot as a grep-friendly user-facing report."""
    lines: list[str] = []
    state = "initialized" if snap.initialized else "not initialized"
    lines.append(f"workspace: {snap.workspace}  ({state})")
    if not snap.exists:
        lines.append("status: workspace does not exist; run /tc:init")
        return "\n".join(lines)
    if snap.last_modified is not None:
        lines.append(f"last activity: {snap.last_modified.isoformat(timespec='seconds')}")
    total = sum(snap.counts.values())
    pop = sum(snap.populated.values())
    lines.append(f"files: {total} total, {pop} populated")
    if snap.counts:
        lines.append("")
        lines.append("by bucket:")
        for name in sorted(snap.counts):
            c = snap.counts[name]
            p = snap.populated.get(name, 0)
            lines.append(f"  {name:<26} {c:>3}  ({p} populated)")
    lines.append("")
    lines.append("phase status:")
    for phase in sorted(snap.phase_status, key=lambda s: float(s)):
        label = PHASE_LABELS.get(phase, "?")
        lines.append(f"  {phase:<5} {label:<26} {snap.phase_status[phase]}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print a snapshot of a Test Commander workspace.",
    )
    parser.add_argument(
        "target",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Project root (default: current directory).",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE,
        help=f"Workspace template directory (default: bundled at {DEFAULT_TEMPLATE}).",
    )
    args = parser.parse_args(argv)
    snap = snapshot(args.target, template_root=args.template)
    print(format_snapshot(snap))
    return 0


if __name__ == "__main__":
    sys.exit(main())
