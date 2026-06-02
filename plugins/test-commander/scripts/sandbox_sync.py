#!/usr/bin/env python3
"""/tc:sandbox-sync - Phase 12 Step 12.3.

Sync the committed workspace into the sandbox: load the config, resolve the
provider, run its `sync`, and persist the resulting state. A dry run by default;
pass `--real` to actually shell out (refused under pytest).

Self-contained (D18).

Exit codes:
    0 - synced.
    2 - precondition failure (uninitialized workspace or missing config).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sandbox_support import load_config, resolve_provider, save_state


def sync(project_root: Path, *, provider=None, dry_run: bool = True) -> dict:
    config = load_config(project_root)
    prov = provider or resolve_provider(config.get("provider", "docker-compose"))
    new_state = prov.sync(config, dry_run=dry_run).to_dict()
    save_state(project_root, new_state)
    return new_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync the workspace into the sandbox.")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    parser.add_argument("--real", action="store_true", help="Actually sync (not a dry run).")
    args = parser.parse_args(argv if argv is not None else None)
    try:
        state = sync(Path(args.project_root).resolve(), dry_run=not args.real)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"sandbox synced: {state.get('summary', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
