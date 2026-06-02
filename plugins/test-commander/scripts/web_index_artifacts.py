#!/usr/bin/env python3
"""/tc:web-index-artifacts - Phase 10 Step 10.2.

Triggers a full (re)build of the web console's SQLite index from the committed
`.test-commander/` workspace. The workspace is authoritative; the index is a
rebuildable derivative. Read-only with respect to workspace artifacts — it
writes only the derived index DB.

The console runtime lives under the repo's `apps/api/` (it is not copied into a
consuming project's plugin cache); this thin command locates that backend and
delegates to its indexer. Per D18 the command itself ships inside the plugin.

Exit codes:
    0 - index rebuilt.
    2 - precondition failure (uninitialized workspace).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_backend_on_path() -> None:
    """Add the repo's apps/api to sys.path so `tcweb` imports resolve."""
    apps_api = Path(__file__).resolve().parents[3] / "apps" / "api"
    if apps_api.is_dir() and str(apps_api) not in sys.path:
        sys.path.insert(0, str(apps_api))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild the web console's SQLite index from the workspace.",
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    args = parser.parse_args(argv if argv is not None else None)

    _ensure_backend_on_path()
    from tcweb import indexer  # imported after path setup

    project_root = Path(args.project_root).resolve()
    try:
        counts = indexer.rebuild(project_root)
    except indexer.UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    total = sum(counts.values())
    print(f"indexed: {total} row(s) across {len(counts)} tables")
    for table, n in counts.items():
        print(f"  {table:<14} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
