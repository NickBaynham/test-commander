#!/usr/bin/env python3
"""/tc:sandbox-init - Phase 12 Step 12.3.

Provision the sandbox configuration inside the workspace
(`.test-commander/sandbox/config.yaml`): the provider, the target, the
allow-list, the private-range block, and the approval requirements. Idempotent
and skip-not-overwrite: a config that already exists is preserved (it is a
user-editable seed), so re-running never clobbers an edited allow-list.

Self-contained (D18).

Exit codes:
    0 - config provisioned (or already present and preserved).
    2 - precondition failure (uninitialized workspace).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from sandbox_support import DEFAULT_CONFIG, config_path, require_workspace, sandbox_dir


def init(project_root: Path) -> Path:
    require_workspace(project_root)
    sandbox_dir(project_root).mkdir(parents=True, exist_ok=True)
    cfg = config_path(project_root)
    if not cfg.is_file():
        cfg.write_text(
            yaml.safe_dump(DEFAULT_CONFIG, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
    return cfg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Provision the sandbox config.")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    args = parser.parse_args(argv if argv is not None else None)
    try:
        cfg = init(Path(args.project_root).resolve())
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"sandbox config provisioned: {cfg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
