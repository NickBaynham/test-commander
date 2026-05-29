#!/usr/bin/env python3
"""/tc:traceability-map helper - Phase 5 Step 5.4.

The authoritative regenerator of the cross-cutting traceability maps under
``<workspace>/traceability/``. Scans the requirement inventory, the
Phase-4-enriched test-idea seeds, and the Gherkin feature files (parsing the
``@req:``/``@cs:`` linkage tags ``/tc:generate-bdd`` emits), then writes:

- ``traceability/requirements-map.md`` - the shared 4-column requirement ->
  downstream map, rendered by ``traceability_render.render_requirements_map``
  (byte-identical to what ``/tc:requirements-coverage`` writes; no drift).
- ``traceability/test-map.md`` - the scenario-level chain: Requirement -> Test
  idea (CS) -> BDD scenario -> Automated test -> Test result -> Quality report.
  Downstream links render ``pending`` until Phases 6-7 populate them; they are
  never invented.

Reuses ``requirements_coverage``'s scan functions and ``review_bdd``'s feature
parser for DRY. From Phase 5 onward this helper is the authoritative writer of
both maps; the Phase-2 ``requirements_coverage`` write is a compatible interim
seed (the shared renderer guarantees no format drift).

Per D18 the helper ships inside the plugin.

Exit codes:
    0 - maps written.
    2 - precondition failure (uninitialized workspace, missing inventory).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import traceability_render
from requirements_coverage import (
    InventoryMissingError,
    UninitializedWorkspaceError,
    _inventory_is_generated,
    assemble_coverage,
    parse_inventory,
    scan_automation_map,
    scan_bdd_features,
    scan_test_ideas,
)
from review_bdd import parse_feature_file

WORKSPACE_DIRNAME = ".test-commander"

REQ_TAG_RE = re.compile(r"@req:(REQ-\d+)")
CS_TAG_RE = re.compile(r"@cs:(CS-\d{3}-\d{3})")


@dataclass
class TraceResult:
    workspace: Path
    requirements_count: int
    scenario_count: int
    requirements_map_path: Path
    test_map_path: Path


# ---------------------------------------------------------------------------
# Test-map assembly
# ---------------------------------------------------------------------------


def scan_scenarios(features_dir: Path) -> list[traceability_render.TestMapRow]:
    """Parse every feature's scenarios into test-map rows via their @req:/@cs:
    linkage tags. Deterministic: sorted by (req_id, cs_id, feature, scenario)."""
    rows: list[traceability_render.TestMapRow] = []
    if not features_dir.is_dir():
        return rows
    for path in sorted(features_dir.glob("*.feature")):
        rel = f"bdd/features/{path.name}"
        for sc in parse_feature_file(path):
            tag_text = " ".join(sc.tags)
            reqs = REQ_TAG_RE.findall(tag_text)
            css = CS_TAG_RE.findall(tag_text)
            if not reqs:
                continue
            cs_id = css[0] if css else "-"
            for req_id in reqs:
                rows.append(
                    traceability_render.TestMapRow(
                        req_id=req_id,
                        cs_id=cs_id,
                        scenario=sc.name,
                        feature=rel,
                    )
                )
    rows.sort(key=lambda r: (r.req_id, r.cs_id, r.feature, r.scenario))
    return rows


# ---------------------------------------------------------------------------
# Top-level entry
# ---------------------------------------------------------------------------


def traceability_map(project_root: Path) -> TraceResult:
    project_root = Path(project_root)
    workspace = project_root / WORKSPACE_DIRNAME
    if not workspace.is_dir():
        raise UninitializedWorkspaceError(
            f"workspace not found: {workspace} (run /tc:init first)"
        )

    inventory_path = workspace / "requirements" / "requirements-inventory.md"
    if not inventory_path.is_file() or not _inventory_is_generated(inventory_path):
        raise InventoryMissingError(
            "requirements-inventory.md not found or not yet generated; "
            "run /tc:review-requirements first"
        )

    req_ids = parse_inventory(inventory_path)
    test_ideas = scan_test_ideas(workspace / "test-ideas")
    bdd_features = scan_bdd_features(workspace / "bdd" / "features")
    automation = scan_automation_map(workspace / "traceability" / "automation-map.md")
    links, _orphans = assemble_coverage(req_ids, test_ideas, bdd_features, automation)
    rows = [(li.req_id, li.test_ideas, li.bdd_features, li.automation) for li in links]

    scenarios = scan_scenarios(workspace / "bdd" / "features")

    trace_dir = workspace / "traceability"
    trace_dir.mkdir(parents=True, exist_ok=True)
    requirements_map_path = trace_dir / "requirements-map.md"
    test_map_path = trace_dir / "test-map.md"
    requirements_map_path.write_text(
        traceability_render.render_requirements_map(req_ids, rows), encoding="utf-8"
    )
    test_map_path.write_text(
        traceability_render.render_test_map(scenarios), encoding="utf-8"
    )

    return TraceResult(
        workspace=workspace,
        requirements_count=len(req_ids),
        scenario_count=len(scenarios),
        requirements_map_path=requirements_map_path,
        test_map_path=test_map_path,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild the cross-cutting traceability maps (requirements-map.md "
            "and test-map.md) from the inventory, enriched test ideas, and the "
            "@req:/@cs: linkage tags in bdd/features/."
        ),
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Path to the consuming project root (default: cwd).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        result = traceability_map(Path(args.project_root))
    except (UninitializedWorkspaceError, InventoryMissingError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"workspace:        {result.workspace}")
    print(f"requirements:     {result.requirements_count}")
    print(f"scenarios:        {result.scenario_count}")
    print(f"requirements map: {result.requirements_map_path}")
    print(f"test map:         {result.test_map_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
