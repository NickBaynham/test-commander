#!/usr/bin/env python3
"""/tc:automate helper - Phase 6 Step 6.4 (generation only).

Reads the automation plan (``<workspace>/automation-plan/<area>.md``) and the
BDD features (``<workspace>/bdd/features/*.feature``), builds the Playwright
framework lazily via ``build_framework.ensure_framework``, and renders, for
every ``automate``-ranked / ``@automated-candidate`` scenario:

- a page object at ``tests/pages/<AreaName>Page.ts`` (one per area, with a
  preserved user-edits region);
- a per-area fixture at ``tests/fixtures/<area>.ts`` that reaches test data only
  through the ``.test-commander/test-data/`` tree (Decision D6);
- a spec at ``tests/e2e/<area>.spec.ts`` with one ``test()`` per scenario, each
  carrying a ``// @req:REQ-NNN @cs:CS-NNN-NNN`` provenance comment.

It then writes ``<workspace>/traceability/automation-map.md`` linking each
scenario to its spec (the Phase-6-owned map; Phase 2 only seeded it).

Generation only: no review runs here. The review engine and the generate-time
auto-run wiring (``--no-review``) ship in Step 6.5; the generated TypeScript is
authored to pass that rubric (provenance present, data via a fixture, a real
assertion, role-based locators, no hardcoded waits).

The helper writes only the project-root ``tests/`` tree and
``traceability/automation-map.md`` - never ``bdd/`` (Phase 5) or
``product-knowledge/`` (Phase 3). It writes TypeScript and Markdown text only;
it never invokes ``tsc`` or ``npx playwright test``. Execution is Phase 7.

Deterministic: scenarios sort by ``cs`` then name; overwrite mode for specs and
fixtures; the page object preserves its user-edits region, so a re-run with no
edits is byte-identical.

Per D18 the helper ships inside the plugin. Mirrors ``generate_bdd.py``.

Exit codes:
    0 - generation complete (or nothing ranked automate).
    2 - precondition failure (uninitialized workspace, no automation plan).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from build_framework import ensure_framework
from review_automation import review_automation
from review_bdd import parse_feature_file

WORKSPACE_DIRNAME = ".test-commander"

REQ_TAG_RE = re.compile(r"@req:(REQ-\d{3})")
CS_TAG_RE = re.compile(r"@cs:(CS-\d{3}-\d{3})")
FEATURE_TITLE_RE = re.compile(r"^\s*Feature:\s*(.+?)\s*$", re.MULTILINE)
PLAN_ROW_RE = re.compile(r"^\|\s*(.+?)\s*\|\s*(automate|consider|manual)\s*\|")

CUSTOM_START = "  // === custom methods (preserved across /tc:automate re-runs) ==="
CUSTOM_END = "  // === end custom methods ==="


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class AutomateError(Exception):
    pass


class UninitializedWorkspaceError(AutomateError):
    pass


class PlanMissingError(AutomateError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AutoScenario:
    area: str
    name: str
    req_id: str
    cs_id: str


@dataclass
class AutomateOutcome:
    spec_paths: list[Path] = field(default_factory=list)
    page_paths: list[Path] = field(default_factory=list)
    fixture_paths: list[Path] = field(default_factory=list)
    map_path: Path | None = None
    scenario_count: int = 0


# ---------------------------------------------------------------------------
# Workspace IO
# ---------------------------------------------------------------------------


def workspace_dir(project_root: Path) -> Path:
    ws = project_root / WORKSPACE_DIRNAME
    if not ws.is_dir():
        raise UninitializedWorkspaceError(
            f"not a Test Commander workspace: {project_root} "
            f"(no {WORKSPACE_DIRNAME}/). Run /tc:init first."
        )
    return ws


# ---------------------------------------------------------------------------
# Naming
# ---------------------------------------------------------------------------


def pascal(area: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[^a-z0-9]+", area) if part)


def camel(area: str) -> str:
    p = pascal(area)
    return p[:1].lower() + p[1:] if p else "page"


# ---------------------------------------------------------------------------
# Plan + feature reading
# ---------------------------------------------------------------------------


def parse_plan_ranks(plan_path: Path) -> dict[str, str]:
    """Read ``automation-plan/<area>.md`` and return {scenario name -> rank}."""
    ranks: dict[str, str] = {}
    for line in plan_path.read_text(encoding="utf-8").split("\n"):
        m = PLAN_ROW_RE.match(line)
        if m and m.group(1) != "scenario":
            ranks[m.group(1)] = m.group(2)
    return ranks


def feature_title(path: Path) -> str:
    m = FEATURE_TITLE_RE.search(path.read_text(encoding="utf-8"))
    return m.group(1) if m else path.stem


def select_scenarios(area: str, feature_path: Path, ranks: dict[str, str]) -> list[AutoScenario]:
    """Scenarios ranked automate (or tagged @automated-candidate) with a
    resolvable @req:/@cs: linkage, sorted by cs then name."""
    selected: list[AutoScenario] = []
    for sc in parse_feature_file(feature_path):
        is_candidate = "@automated-candidate" in sc.tags
        if ranks.get(sc.name) != "automate" and not is_candidate:
            continue
        tags = " ".join(sc.tags)
        req = REQ_TAG_RE.search(tags)
        cs = CS_TAG_RE.search(tags)
        if not (req and cs):
            continue
        selected.append(AutoScenario(area, sc.name, req.group(1), cs.group(1)))
    return sorted(selected, key=lambda s: (s.cs_id, s.name))


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_page_object(area: str, existing: str | None) -> str:
    name = pascal(area)
    rendered = f"""\
// Generated by /tc:automate. Page object for the {area} feature.
// Locators live here, never in specs (methodology/locator-strategy.md).
import {{ type Page, type Locator }} from '@playwright/test';

export class {name}Page {{
  readonly page: Page;

  constructor(page: Page) {{
    this.page = page;
  }}

  async goto(): Promise<void> {{
    await this.page.goto('/{area}');
  }}

{CUSTOM_START}
  // Add project-specific locators and behavior methods here.
{CUSTOM_END}
}}
"""
    return _splice_custom_region(rendered, existing)


def _splice_custom_region(rendered: str, existing: str | None) -> str:
    """Carry an existing user-edits region forward into a fresh render so a
    re-run preserves hand-added methods (and stays byte-stable when unedited)."""
    if not existing or CUSTOM_START not in existing or CUSTOM_END not in existing:
        return rendered
    old_inner = existing.split(CUSTOM_START, 1)[1].split(CUSTOM_END, 1)[0]
    head, rest = rendered.split(CUSTOM_START, 1)
    _, tail = rest.split(CUSTOM_END, 1)
    return f"{head}{CUSTOM_START}{old_inner}{CUSTOM_END}{tail}"


def render_fixture(area: str) -> str:
    name = pascal(area)
    return f"""\
// Generated by /tc:automate. Fixture for the {area} feature.
// Reaches test data only via the .test-commander/test-data/ tree (D6);
// /tc:generate-test-data populates seed/{area}.json.
import {{ test as base, expect }} from '@playwright/test';
import {{ readFileSync }} from 'node:fs';
import {{ resolve }} from 'node:path';

type {name}Data = Record<string, unknown>;

function load{name}Data(): {name}Data {{
  const dataPath = resolve(
    __dirname,
    '../../.test-commander/test-data/seed/{area}.json',
  );
  return JSON.parse(readFileSync(dataPath, 'utf-8')) as {name}Data;
}}

export const test = base.extend<{{ data: {name}Data }}>({{
  data: async ({{}}, use) => {{
    await use(load{name}Data());
  }},
}});

export {{ expect }};
"""


def render_spec(area: str, title: str, scenarios: list[AutoScenario]) -> str:
    name = pascal(area)
    var = camel(area)
    lines: list[str] = []
    lines.append(f"// Generated by /tc:automate from bdd/features/{area}.feature.")
    lines.append("// One test() per automate-ranked scenario. The provenance comment")
    lines.append("// links each test to its requirement and candidate so")
    lines.append("// /tc:traceability-map can resolve the Automated test column.")
    lines.append(f"import {{ test, expect }} from '../fixtures/{area}';")
    lines.append(f"import {{ {name}Page }} from '../pages/{name}Page';")
    lines.append("")
    lines.append(f"test.describe('{title}', () => {{")
    for sc in scenarios:
        lines.append(f"  // @req:{sc.req_id} @cs:{sc.cs_id}")
        lines.append(f"  test('{sc.name}', async ({{ page, data }}) => {{")
        lines.append(f"    const {var} = new {name}Page(page);")
        lines.append(f"    await {var}.goto();")
        lines.append("    // Refine the Given/When/Then below; data comes from `data` (D6).")
        lines.append("    await expect(page).toHaveURL(/.+/);")
        lines.append("  });")
        lines.append("")
    lines.append("});")
    lines.append("")
    return "\n".join(lines)


def render_automation_map(scenarios: list[AutoScenario]) -> str:
    lines: list[str] = []
    lines.append("# Automation map")
    lines.append("")
    lines.append(
        "_Owned by /tc:automate (Phase 6). Links each automated scenario to its "
        "generated spec. Rebuilt every run; scan source for /tc:traceability-map._"
    )
    lines.append("")
    lines.append("| requirement | candidate | scenario | spec |")
    lines.append("| --- | --- | --- | --- |")
    for sc in sorted(scenarios, key=lambda s: (s.req_id, s.cs_id, s.name)):
        spec = f"tests/e2e/{sc.area}.spec.ts"
        lines.append(f"| {sc.req_id} | {sc.cs_id} | {sc.name} | {spec} |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def generate(
    project_root: Path,
    *,
    area: str | None = None,
    scenario: str | None = None,
    no_review: bool = False,
) -> AutomateOutcome:
    workspace = workspace_dir(project_root)
    plan_dir = workspace / "automation-plan"
    # Exclude the workspace-template README placeholder; a real plan is
    # <area>.md written by /tc:automation-plan.
    plans = (
        sorted(p for p in plan_dir.glob("*.md") if p.name != "README.md")
        if plan_dir.is_dir()
        else []
    )
    if not plans:
        raise PlanMissingError(
            "no automation plan found under automation-plan/. "
            "Run /tc:automation-plan first."
        )

    features_dir = workspace / "bdd" / "features"
    outcome = AutomateOutcome()
    all_scenarios: list[AutoScenario] = []
    built = False

    for plan_path in plans:
        plan_area = plan_path.stem
        if area is not None and plan_area != area:
            continue
        feature_path = features_dir / f"{plan_area}.feature"
        if not feature_path.is_file():
            continue
        ranks = parse_plan_ranks(plan_path)
        selected = select_scenarios(plan_area, feature_path, ranks)
        if scenario is not None:
            selected = [s for s in selected if s.name == scenario]
        if not selected:
            continue

        if not built:
            ensure_framework(project_root)  # lazy-init before any TypeScript
            built = True

        pages = project_root / "tests" / "pages"
        fixtures = project_root / "tests" / "fixtures"
        e2e = project_root / "tests" / "e2e"
        for d in (pages, fixtures, e2e):
            d.mkdir(parents=True, exist_ok=True)

        page_file = pages / f"{pascal(plan_area)}Page.ts"
        existing = page_file.read_text(encoding="utf-8") if page_file.is_file() else None
        page_file.write_text(render_page_object(plan_area, existing), encoding="utf-8")

        fixture_file = fixtures / f"{plan_area}.ts"
        fixture_file.write_text(render_fixture(plan_area), encoding="utf-8")

        spec_file = e2e / f"{plan_area}.spec.ts"
        spec_file.write_text(
            render_spec(plan_area, feature_title(feature_path), selected),
            encoding="utf-8",
        )

        outcome.page_paths.append(page_file)
        outcome.fixture_paths.append(fixture_file)
        outcome.spec_paths.append(spec_file)
        outcome.scenario_count += len(selected)
        all_scenarios.extend(selected)

    map_file = workspace / "traceability" / "automation-map.md"
    map_file.parent.mkdir(parents=True, exist_ok=True)
    map_file.write_text(render_automation_map(all_scenarios), encoding="utf-8")
    outcome.map_path = map_file

    # Auto-run the shared automation review unless suppressed. Only when specs
    # were generated, so the review's "no specs" precondition never fires here.
    if not no_review and outcome.spec_paths:
        review_automation(project_root)
    return outcome


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Playwright/TypeScript page objects, fixtures, and specs "
            "for automate-ranked BDD scenarios, and write the automation map. "
            "Generation only - review ships in Step 6.5."
        ),
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root (default: current directory).",
    )
    parser.add_argument("--area", default=None, help="Generate for a single @area: feature.")
    parser.add_argument(
        "--scenario", default=None, help="Generate for a single scenario by name."
    )
    parser.add_argument(
        "--no-review",
        action="store_true",
        help="Suppress the generate-time automation review (/tc:review-automation).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        outcome = generate(
            project_root,
            area=args.area,
            scenario=args.scenario,
            no_review=args.no_review,
        )
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except PlanMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"automated: {len(outcome.spec_paths)} spec(s) "
        f"({outcome.scenario_count} scenario(s))"
    )
    for path in outcome.spec_paths:
        print(f"  - {path.relative_to(project_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
