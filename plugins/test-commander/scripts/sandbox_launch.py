#!/usr/bin/env python3
"""/tc:sandbox-launch - Phase 12 Step 12.3.

Launch the sandbox: load the config, resolve the provider, run its `launch`, and
persist the resulting state to `.test-commander/sandbox/state.json`. Idempotent:
a sandbox that is already running is left as is (no re-provision). A real launch
is a dry run by default; pass `--real` to actually shell out (refused under
pytest).

Self-contained (D18).

Exit codes:
    0 - launched (or already running).
    2 - precondition failure (uninitialized workspace or missing config).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sandbox_support import load_config, load_state, resolve_provider, save_state


def launch(project_root: Path, *, provider=None, dry_run: bool = True) -> dict:
    config = load_config(project_root)
    state = load_state(project_root)
    if state and state.get("status") == "running":
        return state  # idempotent: already running
    prov = provider or resolve_provider(config.get("provider", "docker-compose"))
    new_state = prov.launch(config, dry_run=dry_run).to_dict()
    save_state(project_root, new_state)
    return new_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Launch the sandbox.")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    parser.add_argument("--real", action="store_true", help="Actually launch (not a dry run).")
    args = parser.parse_args(argv if argv is not None else None)
    try:
        state = launch(Path(args.project_root).resolve(), dry_run=not args.real)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"sandbox {state['status']}: {state.get('summary', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
