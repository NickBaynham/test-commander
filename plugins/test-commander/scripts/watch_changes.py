#!/usr/bin/env python3
"""/tc:watch-changes - Phase 13 Step 13.2.

Detect changes from a PR/push diff: parse the diff into a list of changed files
and persist them to `.test-commander/continuous/changes.json` for the downstream
analysis. Read-only with respect to the application; writes only the changes
record.

Self-contained (D18).

Exit codes:
    0 - changes detected and persisted.
    2 - precondition failure (uninitialized workspace or missing diff).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cq_support import cq_dir, parse_diff, require_workspace, write_json


def watch(project_root: Path, *, diff_path: Path) -> dict:
    require_workspace(project_root)
    changed = parse_diff(Path(diff_path).read_text(encoding="utf-8"))
    summary = {"changed_files": changed, "count": len(changed)}
    write_json(cq_dir(project_root) / "changes.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Detect changes from a diff.")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    parser.add_argument("--diff", required=True, help="Path to a unified diff.")
    args = parser.parse_args(argv if argv is not None else None)
    try:
        summary = watch(Path(args.project_root).resolve(), diff_path=Path(args.diff))
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"watch-changes: {summary['count']} changed file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
