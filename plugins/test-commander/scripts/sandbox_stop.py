#!/usr/bin/env python3
"""/tc:sandbox-stop - Phase 12 Step 12.3.

Tear the sandbox down: resolve the provider, run its `teardown`, and persist the
stopped state. Idempotent: a sandbox that is already stopped (or was never
launched) is a no-op. A dry run by default; pass `--real` to actually shell out
(refused under pytest).

Self-contained (D18).

Exit codes:
    0 - stopped (or already stopped).
    2 - precondition failure (uninitialized workspace or missing config).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sandbox_support import load_config, load_state, resolve_provider, save_state


def stop(project_root: Path, *, provider=None, dry_run: bool = True) -> dict:
    state = load_state(project_root)
    if not state or state.get("status") == "stopped":
        return state or {"status": "stopped", "summary": "no sandbox to stop"}
    config = load_config(project_root)
    prov = provider or resolve_provider(config.get("provider", "docker-compose"))
    new_state = prov.teardown(config, dry_run=dry_run).to_dict()
    save_state(project_root, new_state)
    return new_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Tear the sandbox down.")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    parser.add_argument("--real", action="store_true", help="Actually tear down (not a dry run).")
    args = parser.parse_args(argv if argv is not None else None)
    try:
        state = stop(Path(args.project_root).resolve(), dry_run=not args.real)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"sandbox {state['status']}: {state.get('summary', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
