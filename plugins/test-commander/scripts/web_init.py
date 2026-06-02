#!/usr/bin/env python3
"""/tc:web-init - Phase 10 Step 10.4.

Provisions the web console's configuration inside the workspace
(`.test-commander/.web/console.json`): the API base URL and the web port the
stack uses. Idempotent — re-running leaves the config byte-identical. Writes only
the console's own config; never a workspace artifact.

Self-contained (no backend import) so it runs as a plain plugin script (D18).

Exit codes:
    0 - config provisioned (or already present and unchanged).
    2 - precondition failure (uninitialized workspace).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"
DEFAULT_CONFIG = {
    "schema": "tc-web-console/v1",
    "api_base": "http://localhost:8100",
    "web_port": 3100,
}


def init(project_root: Path) -> Path:
    ws = Path(project_root) / WORKSPACE_DIRNAME
    if not ws.is_dir():
        raise FileNotFoundError(
            f"not a Test Commander workspace: {project_root} (no {WORKSPACE_DIRNAME}/)"
        )
    web_dir = ws / ".web"
    web_dir.mkdir(parents=True, exist_ok=True)
    cfg = web_dir / "console.json"
    cfg.write_text(json.dumps(DEFAULT_CONFIG, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return cfg


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Provision the web console config.")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    args = parser.parse_args(argv if argv is not None else None)
    try:
        cfg = init(Path(args.project_root).resolve())
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"web console config provisioned: {cfg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
