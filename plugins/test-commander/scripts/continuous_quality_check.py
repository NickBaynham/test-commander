#!/usr/bin/env python3
"""/tc:continuous-quality-check - Phase 13 Step 13.5.

The orchestrator. Runs the read-only analysis (watch -> impact -> coverage-gap ->
propose) automatically, then opens a clearly-labeled pull request for each gap
*only when the configured autonomy mode allows it*. The mode is a ceiling: modes
0-2 produce advice only (no PR); modes 3-4 open labeled PRs through the
Phase-10.5 pipeline (auto-approved by the autonomy gate, audited). Nothing above
the mode executes without explicit human approval.

Self-contained (D18).

Exit codes:
    0 - the check ran.
    2 - precondition failure (uninitialized workspace).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import coverage_gap_analysis
import create_test_pr
import impact_analysis
import propose_tests
import watch_changes
from cq_support import load_config, require_workspace, resolve_repo_root


def check(project_root: Path, *, diff_path: Path, mode: int | None = None, adapter=None) -> dict:
    require_workspace(project_root)
    config = load_config(project_root)
    mode = config["autonomy_mode"] if mode is None else mode

    # Read-only analysis (always runs).
    watch_changes.watch(project_root, diff_path=Path(diff_path))
    impact = impact_analysis.analyze(project_root, diff_path=Path(diff_path))
    gaps = coverage_gap_analysis.analyze(project_root)
    proposals = propose_tests.propose(project_root)

    resolve_repo_root()
    from continuous.autonomy import can_open_pr, mode_name

    result = {
        "mode": mode_name(mode),
        "impact": impact,
        "gaps": gaps,
        "proposals": proposals["proposals"],
        "prs": [],
    }
    # Gated execution: open labeled PRs for the gaps only when the mode allows it.
    if can_open_pr(mode):
        for feature in proposals["proposals"]:
            result["prs"].append(
                create_test_pr.create_pr(
                    project_root, gap_feature=feature, mode=mode, adapter=adapter
                )
            )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the continuous-quality check.")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    parser.add_argument("--diff", required=True, help="Path to the PR/push diff.")
    parser.add_argument("--mode", type=int, default=None, help="Override the autonomy mode.")
    args = parser.parse_args(argv if argv is not None else None)
    try:
        result = check(
            Path(args.project_root).resolve(), diff_path=Path(args.diff), mode=args.mode
        )
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    opened = sum(1 for pr in result["prs"] if pr.get("opened"))
    print(f"continuous-quality-check [{result['mode']}]: "
          f"{len(result['proposals'])} proposal(s), {opened} PR(s) opened")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
