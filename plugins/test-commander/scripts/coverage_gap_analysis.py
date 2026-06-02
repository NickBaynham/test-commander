#!/usr/bin/env python3
"""/tc:coverage-gap-analysis - Phase 13 Step 13.3.

Check the impacted set against existing coverage (traceability/coverage.yaml). An
impacted feature that is not automated - or has no coverage record at all - is a
gap, surfaced with provenance. Read-only and deterministic; never invents
coverage (an unknown feature is a gap, not assumed covered).

Self-contained (D18).

Exit codes:
    0 - gap analysis written.
    2 - precondition failure (uninitialized workspace or missing coverage map).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cq_support import (
    cq_dir,
    load_coverage,
    load_impacted_features,
    require_workspace,
    write_json,
)


def _render(result: dict) -> str:
    lines = ["# Coverage gap analysis", "", "## Gaps (impacted but not covered)"]
    if result["gaps"]:
        lines += [f"- **{g['feature']}** — {g['reason']}"
                  + (f" (source: {g['source']})" if g["source"] else "")
                  for g in result["gaps"]]
    else:
        lines.append("_No gaps: every impacted feature is covered._")
    lines += ["", "## Covered impacted features"]
    lines += [f"- {f}" for f in result["covered"]] or ["_None._"]
    return "\n".join(lines) + "\n"


def analyze(project_root: Path, *, impacted_features=None) -> dict:
    require_workspace(project_root)
    coverage = load_coverage(project_root)
    if impacted_features is None:
        impacted_features = load_impacted_features(project_root)
    gaps: list[dict] = []
    covered: list[str] = []
    for feat in impacted_features:
        entry = coverage.get(feat)
        if entry is None:
            gaps.append({"feature": feat, "reason": "no coverage record", "source": None})
        elif not entry.get("automated"):
            gaps.append({"feature": feat, "reason": "not automated",
                         "source": entry.get("source")})
        else:
            covered.append(feat)
    result = {"gaps": gaps, "covered": sorted(covered)}
    write_json(cq_dir(project_root) / "coverage-gaps.json", result)
    (cq_dir(project_root) / "coverage-gap-analysis.md").write_text(
        _render(result), encoding="utf-8"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze coverage gaps for the impacted set.")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    args = parser.parse_args(argv if argv is not None else None)
    try:
        result = analyze(Path(args.project_root).resolve())
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"coverage-gap-analysis: {len(result['gaps'])} gap(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
