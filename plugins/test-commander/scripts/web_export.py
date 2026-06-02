#!/usr/bin/env python3
"""/tc:web-export - Phase 10 Step 10.6.

Exports the console's current view (quality report + requirements + runs +
evidence + traceability) as a shareable static bundle (`data.json` +
`index.html`) under `.test-commander/.web/export/`. Read-only and deterministic;
writes only the export bundle, never a workspace artifact.

Per D18 the command ships inside the plugin and delegates to the runtime backend.

Exit codes:
    0 - bundle exported.
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
        description="Export the web console view as a shareable static bundle.",
    )
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    parser.add_argument("--out", default=None, help="Output directory (default: .web/export/).")
    args = parser.parse_args(argv if argv is not None else None)

    _ensure_backend_on_path()
    from tcweb import exporter, indexer

    project_root = Path(args.project_root).resolve()
    out_dir = Path(args.out).resolve() if args.out else None
    try:
        written = exporter.export(project_root, out_dir=out_dir)
    except indexer.UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"exported: {len(written)} file(s)")
    for p in written:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
