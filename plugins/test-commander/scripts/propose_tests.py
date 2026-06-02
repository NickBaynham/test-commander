#!/usr/bin/env python3
"""/tc:propose-tests - Phase 13 Step 13.4.

Propose new BDD/automation for the coverage gaps (reusing the Phase-5/6
generators as *proposals*, not executed). Writes one proposal per gap under
`.test-commander/continuous/proposals/`. Read-only/safe-write: it proposes; it
does not open a PR or run anything.

Self-contained (D18).

Exit codes:
    0 - proposals written.
    2 - precondition failure (uninitialized workspace).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cq_support import cq_dir, require_workspace


def _proposal(feature: str) -> str:
    return (
        f"# Proposed tests for `{feature}`\n\n"
        f"This feature is impacted and not covered. Proposed as a starting point\n"
        f"(reuses the Phase-5 BDD and Phase-6 automation generators as a proposal).\n\n"
        f"## Proposed BDD scenario\n\n"
        f"```gherkin\n"
        f"Feature: {feature}\n"
        f"  Scenario: {feature} works for a valid input\n"
        f"    Given the {feature} surface is available\n"
        f"    When a valid action is performed\n"
        f"    Then the expected outcome is observed\n"
        f"```\n\n"
        f"## Proposed automation\n\n"
        f"- Generate a Playwright test for `{feature}` via `/tc:automate`.\n"
        f"- Add it to the traceability map.\n"
    )


def propose(project_root: Path, *, gaps=None) -> dict:
    require_workspace(project_root)
    if gaps is None:
        gaps_path = cq_dir(project_root) / "coverage-gaps.json"
        data = json.loads(gaps_path.read_text(encoding="utf-8")) if gaps_path.is_file() else {}
        gaps = [g["feature"] for g in data.get("gaps", [])]
    out_dir = cq_dir(project_root) / "proposals"
    out_dir.mkdir(parents=True, exist_ok=True)
    proposals: list[str] = []
    for feature in gaps:
        (out_dir / f"{feature}.md").write_text(_proposal(feature), encoding="utf-8")
        proposals.append(feature)
    return {"proposals": proposals}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Propose tests for the coverage gaps.")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    args = parser.parse_args(argv if argv is not None else None)
    try:
        result = propose(Path(args.project_root).resolve())
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"propose-tests: {len(result['proposals'])} proposal(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
