#!/usr/bin/env python3
"""/tc:requirements-coverage helper.

Cross-references the requirement IDs in `<workspace>/requirements/
requirements-inventory.md` with downstream artifacts:
  - test ideas under `<workspace>/test-ideas/`
  - BDD scenarios under `<workspace>/bdd/features/*.feature`
  - the automation map at `<workspace>/traceability/automation-map.md`

Writes `<workspace>/requirements/requirements-coverage.md` and
`<workspace>/traceability/requirements-map.md`. Both files are
overwritten byte-deterministically on every run (idempotent).

In Phase 2 the downstream directories are largely empty — Phases 4-6
populate them. The coverage file accurately reports `not yet covered`
for every requirement until Step 2.6 lands seed test ideas; downstream
artifacts that name a requirement not in the inventory are flagged as
orphans.

Per D18 the helper ships inside the plugin so consuming-project users
can invoke it after `claude plugin install`.

Exit codes:
    0 - coverage written
    2 - uninitialized workspace, missing inventory
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from traceability_render import format_cell as _format_links
from traceability_render import render_requirements_map

WORKSPACE_DIRNAME = ".test-commander"
REQ_PATTERN = re.compile(r"\bREQ-(\d{1,4})\b")
INVENTORY_ROW = re.compile(r"^\|\s*(REQ-\d+)\s*\|", re.MULTILINE)


# ---------------------------------------------------------------------------
# Exceptions and dataclasses
# ---------------------------------------------------------------------------

class CoverageError(Exception):
    """Base class for requirements_coverage errors."""


class UninitializedWorkspaceError(CoverageError):
    """Raised when `<project>/.test-commander/` does not exist."""


class InventoryMissingError(CoverageError):
    """Raised when `requirements/requirements-inventory.md` is absent.

    `/tc:requirements-coverage` depends on the inventory artifact produced
    by `/tc:review-requirements`. Run `/tc:review-requirements` first.
    """


@dataclass
class CoverageLink:
    req_id: str
    test_ideas: list[str] = field(default_factory=list)
    bdd_features: list[str] = field(default_factory=list)
    automation: list[str] = field(default_factory=list)

    @property
    def is_covered(self) -> bool:
        return bool(self.test_ideas or self.bdd_features or self.automation)


@dataclass
class Orphan:
    target: str
    source: str
    kind: str  # 'test-ideas' | 'bdd' | 'automation'


@dataclass
class CoverageResult:
    workspace: Path
    requirements_count: int
    covered_count: int
    unmapped_count: int
    coverage_links: list[CoverageLink]
    orphans: list[Orphan]
    coverage_path: Path | None = None
    trace_path: Path | None = None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_inventory(inventory_path: Path) -> list[str]:
    """Extract REQ-IDs from the inventory file in document order."""
    text = inventory_path.read_text(encoding="utf-8")
    return [m.group(1) for m in INVENTORY_ROW.finditer(text)]


def _inventory_is_generated(inventory_path: Path) -> bool:
    """True iff the inventory file shows signs of being written by
    `/tc:review-requirements` (Step 2.2).

    The workspace template ships an inventory placeholder that does not
    have these markers; if /tc:review-requirements has not run yet, the
    template stub is still in place and coverage cannot proceed.
    """
    text = inventory_path.read_text(encoding="utf-8")
    return "Total: **" in text or "_No requirements parsed yet._" in text


def scan_test_ideas(test_ideas_dir: Path) -> dict[str, list[str]]:
    """Return {req-id -> [relative-path]} for every test-idea file linking to it.

    A test-ideas file is considered to link a requirement if either:
      - the file is named `REQ-NNN.md` (canonical convention), or
      - the file body contains a `REQ-NNN` reference.
    """
    links: dict[str, list[str]] = {}
    if not test_ideas_dir.is_dir():
        return links
    for path in sorted(test_ideas_dir.glob("*.md")):
        rel = f"test-ideas/{path.name}"
        # Filename convention
        stem_match = re.fullmatch(r"REQ-(\d{1,4})", path.stem)
        if stem_match:
            rid = f"REQ-{int(stem_match.group(1)):03d}"
            links.setdefault(rid, []).append(rel)
        # Body references
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in REQ_PATTERN.finditer(text):
            rid = f"REQ-{int(m.group(1)):03d}"
            if rel not in links.setdefault(rid, []):
                links[rid].append(rel)
    return links


def scan_bdd_features(features_dir: Path) -> dict[str, list[str]]:
    """Return {req-id -> [relative-path]} for every .feature file linking to it."""
    links: dict[str, list[str]] = {}
    if not features_dir.is_dir():
        return links
    for path in sorted(features_dir.glob("*.feature")):
        rel = f"bdd/features/{path.name}"
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in REQ_PATTERN.finditer(text):
            rid = f"REQ-{int(m.group(1)):03d}"
            if rel not in links.setdefault(rid, []):
                links[rid].append(rel)
    return links


def scan_automation_map(automation_path: Path) -> dict[str, list[str]]:
    """Return {req-id -> [relative-path]} from the automation map."""
    links: dict[str, list[str]] = {}
    if not automation_path.is_file():
        return links
    try:
        text = automation_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return links
    rel = "traceability/automation-map.md"
    for m in REQ_PATTERN.finditer(text):
        rid = f"REQ-{int(m.group(1)):03d}"
        if rel not in links.setdefault(rid, []):
            links[rid].append(rel)
    return links


# ---------------------------------------------------------------------------
# Coverage assembly
# ---------------------------------------------------------------------------

def assemble_coverage(
    req_ids: list[str],
    test_ideas: dict[str, list[str]],
    bdd_features: dict[str, list[str]],
    automation: dict[str, list[str]],
) -> tuple[list[CoverageLink], list[Orphan]]:
    """Build per-requirement coverage links and an orphan list.

    A downstream artifact reference whose target REQ-ID is not in `req_ids`
    is an orphan.
    """
    known = set(req_ids)
    coverage_links: list[CoverageLink] = []
    for rid in req_ids:
        coverage_links.append(CoverageLink(
            req_id=rid,
            test_ideas=test_ideas.get(rid, []),
            bdd_features=bdd_features.get(rid, []),
            automation=automation.get(rid, []),
        ))

    orphans: list[Orphan] = []
    for source_map, kind in (
        (test_ideas, "test-ideas"),
        (bdd_features, "bdd"),
        (automation, "automation"),
    ):
        for target, paths in source_map.items():
            if target in known:
                continue
            for p in paths:
                orphans.append(Orphan(target=target, source=p, kind=kind))
    orphans.sort(key=lambda o: (o.target, o.kind, o.source))
    return coverage_links, orphans


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def _render_coverage(
    req_ids: list[str],
    links: list[CoverageLink],
    orphans: list[Orphan],
) -> str:
    out = ["# Requirements Coverage", ""]
    if not req_ids:
        out.append("_Inventory is empty — no requirements to cover._")
        out.append("")
        return "\n".join(out)

    covered = sum(1 for link in links if link.is_covered)
    uncovered = len(req_ids) - covered

    out.append("## Executive summary")
    out.append("")
    out.append(f"- Requirements: **{len(req_ids)}**")
    out.append(f"- Covered (any downstream artifact): **{covered}**")
    out.append(f"- Not yet covered: **{uncovered}**")
    out.append(f"- Orphan downstream artifacts: **{len(orphans)}**")
    out.append("")

    out.append("## Coverage matrix")
    out.append("")
    out.append("| REQ-ID | Test ideas | BDD features | Automation |")
    out.append("| --- | --- | --- | --- |")
    for link in links:
        out.append(
            f"| {link.req_id} | {_format_links(link.test_ideas)} | "
            f"{_format_links(link.bdd_features)} | {_format_links(link.automation)} |"
        )
    out.append("")

    unmapped = [link.req_id for link in links if not link.is_covered]
    out.append("## Not yet covered")
    out.append("")
    if unmapped:
        out.append(
            f"_{len(unmapped)} requirement(s) have no downstream artifact yet. "
            "Phases 4-6 populate the downstream surfaces; Step 2.6 lands seed test ideas._"
        )
        out.append("")
        for rid in unmapped:
            out.append(f"- {rid}")
        out.append("")
    else:
        out.append("_Every requirement has at least one downstream artifact._")
        out.append("")

    out.append("## Orphan downstream artifacts")
    out.append("")
    if orphans:
        out.append(
            "_Downstream artifacts that reference a REQ-ID not present in the inventory. "
            "Either the referenced REQ was removed, renamed, or never authored — "
            "resolve before re-running coverage._"
        )
        out.append("")
        out.append("| Source | Kind | Target |")
        out.append("| --- | --- | --- |")
        for o in orphans:
            out.append(f"| `{o.source}` | `{o.kind}` | {o.target} |")
        out.append("")
    else:
        out.append("_No orphan downstream artifacts detected._")
        out.append("")

    out.append("## Traceability")
    out.append("")
    out.append("Inventory IDs (document order):")
    out.append("")
    out.append(", ".join(req_ids))
    out.append("")
    return "\n".join(out)


def _render_traceability_map(req_ids: list[str], links: list[CoverageLink]) -> str:
    """Delegate to the shared renderer (Step 5.4) so /tc:requirements-coverage
    and /tc:traceability-map produce byte-identical requirements-map.md."""
    rows = [
        (link.req_id, link.test_ideas, link.bdd_features, link.automation)
        for link in links
    ]
    return render_requirements_map(req_ids, rows)


# ---------------------------------------------------------------------------
# Top-level entry
# ---------------------------------------------------------------------------

def coverage(project_root: Path) -> CoverageResult:
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

    links, orphans = assemble_coverage(req_ids, test_ideas, bdd_features, automation)

    coverage_path = workspace / "requirements" / "requirements-coverage.md"
    trace_path = workspace / "traceability" / "requirements-map.md"
    coverage_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.parent.mkdir(parents=True, exist_ok=True)

    coverage_path.write_text(_render_coverage(req_ids, links, orphans), encoding="utf-8")
    trace_path.write_text(_render_traceability_map(req_ids, links), encoding="utf-8")

    covered_count = sum(1 for link in links if link.is_covered)
    return CoverageResult(
        workspace=workspace,
        requirements_count=len(req_ids),
        covered_count=covered_count,
        unmapped_count=len(req_ids) - covered_count,
        coverage_links=links,
        orphans=orphans,
        coverage_path=coverage_path,
        trace_path=trace_path,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Cross-reference requirement IDs with downstream artifacts "
            "(test ideas, BDD features, automation map) and write the "
            "Phase 2 coverage + traceability artifacts."
        ),
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Path to the consuming project root (default: cwd).",
    )
    args = parser.parse_args(argv)

    try:
        result = coverage(Path(args.project_root))
    except (UninitializedWorkspaceError, InventoryMissingError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"workspace:        {result.workspace}")
    print(f"requirements:     {result.requirements_count}")
    print(f"covered:          {result.covered_count}")
    print(f"not yet covered:  {result.unmapped_count}")
    print(f"orphans:          {len(result.orphans)}")
    print(f"coverage:         {result.coverage_path}")
    print(f"traceability:     {result.trace_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
