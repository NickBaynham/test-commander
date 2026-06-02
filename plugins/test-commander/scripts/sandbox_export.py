#!/usr/bin/env python3
"""/tc:sandbox-export - Phase 12 Step 12.3.

Export a shareable bundle of the sandbox's endpoints, labels, and status to
`.test-commander/sandbox/export.json` so a team can find and reach the
environment (and so a CI job can publish it to a PR comment). Read-only with
respect to the sandbox; writes only the export bundle.

Self-contained (D18).

Exit codes:
    0 - bundle written.
    2 - precondition failure (uninitialized workspace).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sandbox_support import load_config, load_state, require_workspace, sandbox_dir


def export(project_root: Path) -> Path:
    require_workspace(project_root)
    state = load_state(project_root) or {"status": "none"}
    has_config = (sandbox_dir(project_root) / "config.yaml").is_file()
    config = load_config(project_root) if has_config else {}
    bundle = {
        "name": state.get("name", "tc-sandbox"),
        "provider": state.get("provider", config.get("provider", "")),
        "status": state.get("status", "none"),
        "environment_label": state.get("labels", {}).get("environment")
        or config.get("environment_label", "Test Commander Sandbox"),
        "endpoints": state.get("endpoints", {}),
        "target": config.get("target", {}),
    }
    out = sandbox_dir(project_root) / "export.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a shareable sandbox bundle.")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    args = parser.parse_args(argv if argv is not None else None)
    try:
        out = export(Path(args.project_root).resolve())
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"sandbox bundle exported: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
