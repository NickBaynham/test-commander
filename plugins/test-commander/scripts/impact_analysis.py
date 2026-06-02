#!/usr/bin/env python3
"""/tc:impact-analysis - Phase 13 Step 13.2.

Map changed files to impacted features and requirements via the workspace impact
map (product-knowledge/impact-map.yaml, produced from Phase-3 knowledge and
Phase-5 traceability). Deterministic and read-only; writes the analysis report.
Never invents impact — a file matching no pattern contributes nothing.

Self-contained (D18).

Exit codes:
    0 - impact analysis written.
    2 - precondition failure (uninitialized workspace, missing impact map/diff).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cq_support import (
    cq_dir,
    impacted,
    load_changed_files,
    load_impact_map,
    require_workspace,
    write_json,
)


def _render(result: dict, changed: list[str]) -> str:
    lines = ["# Impact analysis", "", f"Changed files: {len(changed)}", ""]
    lines.append("## Impacted features")
    lines += [f"- {f}" for f in result["features"]] or ["_None._"]
    lines += ["", "## Impacted requirements"]
    lines += [f"- {r}" for r in result["requirements"]] or ["_None._"]
    lines += ["", "## Provenance"]
    lines += [f"- `{p['file']}` matched `{p['pattern']}`" for p in result["provenance"]] or [
        "_None._"
    ]
    return "\n".join(lines) + "\n"


def analyze(project_root: Path, *, changed_files=None, diff_path: Path | None = None) -> dict:
    require_workspace(project_root)
    if changed_files is None:
        changed_files = load_changed_files(project_root, diff_path=diff_path)
    impact_map = load_impact_map(project_root)
    result = impacted(changed_files, impact_map)
    write_json(cq_dir(project_root) / "impact.json", result)
    (cq_dir(project_root) / "impact-analysis.md").write_text(
        _render(result, changed_files), encoding="utf-8"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze the impact of changes.")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    parser.add_argument("--diff", help="Path to a unified diff (else use changes.json).")
    args = parser.parse_args(argv if argv is not None else None)
    diff = Path(args.diff) if args.diff else None
    try:
        result = analyze(Path(args.project_root).resolve(), diff_path=diff)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"impact-analysis: {len(result['features'])} feature(s), "
          f"{len(result['requirements'])} requirement(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
