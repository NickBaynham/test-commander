#!/usr/bin/env python3
"""/tc:generate-test-plan and /tc:update-test-plan helper.

Generates and maintains a test plan from the workspace requirements artifacts.

Two artifacts are produced under ``<workspace>/test-plan/``:

- ``test-plan.md`` - the test plan document. Seeded once from the bundled
  template and then OWNED BY THE HUMAN/JUDGMENT LAYER: the helper never
  overwrites it once it exists (so per-test tables, defects, and narrative
  survive). Re-create it with ``--force``.
- ``coverage-map.md`` - a pure generated requirement -> coverage table,
  rewritten byte-deterministically on every run. This is the "keep up to date"
  half: it always reflects the current inventory, test-ideas, and traceability.

Inputs (all under ``<workspace>``):

- ``requirements/requirements-inventory.md`` - the parsed REQ-ID list (required).
- ``traceability/requirements-map.md`` - per-requirement downstream links
  (test ideas / BDD / automation), when present.
- ``requirements/open-questions.md`` - surfaced as plan risks, when present.

The helper is mechanical and universal (D19): it derives a coverage *status*
from whether each requirement has any downstream artifact, and leaves the
per-test tables and pass/fail status to the Claude judgment layer (see
``methodology/test-planning.md``).

Per D18 the helper ships inside the plugin.

Exit codes:
    0 - plan and/or coverage map written
    2 - precondition failure (uninitialized workspace, missing inventory)
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"

INVENTORY_ROW = re.compile(r"^\|\s*(REQ-\d+)\s*\|\s*([^|]*?)\s*\|\s*(.*?)\s*\|\s*$", re.MULTILINE)
MAP_ROW = re.compile(
    r"^\|\s*(REQ-\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$", re.MULTILINE
)
NONE_MARKERS = {"", "_(none)_", "(none)", "-"}

TEMPLATE_REL = Path("skills") / "tc-test-plan" / "templates" / "test-plan-template.md"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class TestPlanError(Exception):
    pass


class UninitializedWorkspaceError(TestPlanError):
    pass


class InventoryMissingError(TestPlanError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Requirement:
    req_id: str
    body: str


@dataclass(frozen=True)
class CoverageRow:
    req_id: str
    body: str
    test_ideas: str
    bdd: str
    automation: str

    @property
    def status(self) -> str:
        downstream = (self.test_ideas, self.bdd, self.automation)
        has_automation = _present(self.automation)
        has_any = any(_present(d) for d in downstream)
        if has_automation:
            return "automated"
        if has_any:
            return "planned"
        return "uncovered"


@dataclass
class PlanOutcome:
    requirement_count: int = 0
    covered_count: int = 0
    plan_written: bool = False
    plan_skipped: bool = False
    coverage_written: bool = False
    paths: list[Path] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Workspace IO
# ---------------------------------------------------------------------------


def workspace_dir(project_root: Path) -> Path:
    ws = project_root / WORKSPACE_DIRNAME
    if not ws.is_dir():
        raise UninitializedWorkspaceError(
            f"workspace not initialized (no {WORKSPACE_DIRNAME}/). Run /tc:init first."
        )
    return ws


def plugin_root() -> Path:
    # scripts/ -> plugin root
    return Path(__file__).resolve().parent.parent


def _present(value: str) -> bool:
    return value.strip().lower() not in NONE_MARKERS


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_inventory(path: Path) -> list[Requirement]:
    if not path.is_file():
        raise InventoryMissingError(
            "requirements inventory not found "
            "(requirements/requirements-inventory.md). Run /tc:review-requirements first."
        )
    text = path.read_text(encoding="utf-8")
    reqs: list[Requirement] = []
    for match in INVENTORY_ROW.finditer(text):
        req_id, _source, body = match.group(1), match.group(2), match.group(3)
        if req_id == "ID":  # header row guard
            continue
        reqs.append(Requirement(req_id=req_id, body=body.strip()))
    if not reqs:
        raise InventoryMissingError(
            "requirements inventory has no REQ rows. Run /tc:review-requirements first."
        )
    return reqs


def parse_requirements_map(path: Path) -> dict[str, tuple[str, str, str]]:
    """Return {REQ-ID: (test_ideas, bdd, automation)} from the traceability map."""
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    out: dict[str, tuple[str, str, str]] = {}
    for match in MAP_ROW.finditer(text):
        req_id, ideas, bdd, automation = match.groups()
        if req_id == "REQ-ID":
            continue
        out[req_id] = (ideas.strip(), bdd.strip(), automation.strip())
    return out


def build_coverage_rows(
    requirements: list[Requirement], req_map: dict[str, tuple[str, str, str]]
) -> list[CoverageRow]:
    rows: list[CoverageRow] = []
    for req in requirements:
        ideas, bdd, automation = req_map.get(req.req_id, ("", "", ""))
        rows.append(
            CoverageRow(
                req_id=req.req_id,
                body=req.body,
                test_ideas=ideas,
                bdd=bdd,
                automation=automation,
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _truncate(text: str, limit: int = 90) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def render_coverage_map(rows: list[CoverageRow]) -> str:
    counts = {"automated": 0, "planned": 0, "uncovered": 0}
    for row in rows:
        counts[row.status] += 1
    lines = [
        "# Requirement → Coverage Map",
        "",
        "Auto-generated by `/tc:update-test-plan` (and `/tc:generate-test-plan`).",
        "Re-running overwrites this file byte-deterministically. The `status` column is a",
        "mechanical signal (does the requirement have any downstream artifact); the Claude",
        "judgment layer refines it to real test files and pass/fail in `test-plan.md`.",
        "",
        "## Summary",
        "",
        f"- Requirements: **{len(rows)}**",
        f"- Automated: **{counts['automated']}**",
        f"- Planned (seed/BDD only): **{counts['planned']}**",
        f"- Uncovered: **{counts['uncovered']}**",
        "",
        "## Coverage matrix",
        "",
        "| REQ | Requirement | Test ideas | BDD | Automation | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        ideas = row.test_ideas if _present(row.test_ideas) else "_(none)_"
        bdd = row.bdd if _present(row.bdd) else "_(none)_"
        automation = row.automation if _present(row.automation) else "_(none)_"
        lines.append(
            f"| {row.req_id} | {_truncate(row.body)} | {ideas} | {bdd} | "
            f"{automation} | {row.status} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_plan_from_template(template_text: str, rows: list[CoverageRow]) -> str:
    """Fill the test-plan template's generated markers from the inventory."""
    inventory_lines = ["| REQ | Requirement | Coverage status |", "| --- | --- | --- |"]
    for row in rows:
        inventory_lines.append(f"| {row.req_id} | {_truncate(row.body)} | {row.status} |")
    inventory_block = "\n".join(inventory_lines)

    replacements = {
        "{{REQUIREMENT_COUNT}}": str(len(rows)),
        "{{REQUIREMENT_INVENTORY}}": inventory_block,
    }
    out = template_text
    for marker, value in replacements.items():
        out = out.replace(marker, value)
    return out


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def build(project_root: Path, *, refresh: bool, force: bool) -> PlanOutcome:
    workspace = workspace_dir(project_root)
    requirements = parse_inventory(workspace / "requirements" / "requirements-inventory.md")
    req_map = parse_requirements_map(workspace / "traceability" / "requirements-map.md")
    rows = build_coverage_rows(requirements, req_map)

    plan_dir = workspace / "test-plan"
    plan_dir.mkdir(parents=True, exist_ok=True)
    outcome = PlanOutcome(
        requirement_count=len(rows),
        covered_count=sum(1 for r in rows if r.status != "uncovered"),
    )

    # coverage-map.md is always (re)generated - the "keep up to date" half.
    coverage_path = plan_dir / "coverage-map.md"
    coverage_path.write_text(render_coverage_map(rows), encoding="utf-8")
    outcome.coverage_written = True
    outcome.paths.append(coverage_path)

    # test-plan.md is seeded once, then human-owned (skip-not-overwrite).
    plan_path = plan_dir / "test-plan.md"
    if refresh:
        outcome.plan_skipped = plan_path.exists()
    elif plan_path.exists() and not force:
        outcome.plan_skipped = True
    else:
        template_text = (plugin_root() / TEMPLATE_REL).read_text(encoding="utf-8")
        plan_path.write_text(render_plan_from_template(template_text, rows), encoding="utf-8")
        outcome.plan_written = True
        outcome.paths.append(plan_path)

    return outcome


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate and maintain a test plan from the workspace requirements: "
            "a human-owned test-plan.md (seeded once) and an always-current "
            "coverage-map.md."
        ),
    )
    parser.add_argument("project_root", nargs="?", default=".", help="Project root (default: cwd).")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Update mode: regenerate coverage-map.md only; never touch test-plan.md.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-create test-plan.md from the template even if it already exists.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        outcome = build(project_root, refresh=args.refresh, force=args.force)
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except InventoryMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if outcome.plan_written:
        plan_state = "written"
    elif outcome.plan_skipped:
        plan_state = "skipped (exists)"
    else:
        plan_state = "n/a"
    print(
        f"requirements: {outcome.requirement_count}  "
        f"covered: {outcome.covered_count}  "
        f"plan: {plan_state}  "
        f"coverage-map: {'written' if outcome.coverage_written else 'n/a'}"
    )
    for path in outcome.paths:
        print(f"  - {path.relative_to(project_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
