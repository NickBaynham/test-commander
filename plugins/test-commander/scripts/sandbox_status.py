#!/usr/bin/env python3
"""/tc:sandbox-status - Phase 12 Step 12.3.

Report the sandbox state from the persisted `.test-commander/sandbox/state.json`
(the source of truth for the command layer). No sandbox launched yet -> status
"none".

Self-contained (D18).

Exit codes:
    0 - status reported.
    2 - precondition failure (uninitialized workspace).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sandbox_support import load_state, require_workspace


def status(project_root: Path) -> dict:
    require_workspace(project_root)
    return load_state(project_root) or {"status": "none", "summary": "no sandbox launched"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report the sandbox status.")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    args = parser.parse_args(argv if argv is not None else None)
    try:
        state = status(Path(args.project_root).resolve())
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"sandbox status: {state['status']}")
    if state.get("endpoints"):
        for name, url in state["endpoints"].items():
            print(f"  {name}: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
