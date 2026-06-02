#!/usr/bin/env python3
"""/tc:web-sync - Phase 10 Step 10.3.

Reconciles the web console's SQLite index with the committed `.test-commander/`
workspace. Because the index is a full rebuildable derivative, a sync is a clean
rebuild — the workspace stays authoritative. Read-only with respect to workspace
artifacts; writes only the derived index DB.

Per D18 the command ships inside the plugin and delegates to the runtime backend
under `apps/api/`.

Exit codes:
    0 - index reconciled.
    2 - precondition failure (uninitialized workspace).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_backend_on_path() -> None:
    apps_api = Path(__file__).resolve().parents[3] / "apps" / "api"
    if apps_api.is_dir() and str(apps_api) not in sys.path:
        sys.path.insert(0, str(apps_api))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reconcile the web console's SQLite index with the workspace.",
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    args = parser.parse_args(argv if argv is not None else None)

    _ensure_backend_on_path()
    from tcweb import indexer

    project_root = Path(args.project_root).resolve()
    try:
        counts = indexer.rebuild(project_root)
    except indexer.UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"synced: index reconciled ({sum(counts.values())} row(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
