# /tc:automate

Generate Playwright/TypeScript page objects, per-area fixtures, and specs for
`automate`-ranked BDD scenarios, each carrying `@req:`/`@cs:` provenance and
reaching test data only through a fixture. Writes the automation map, then
auto-runs the automation review (suppressible with `--no-review`).

## Inputs

- `<workspace>/automation-plan/<area>.md` - the ranking from
  `/tc:automation-plan`. Required: at least one real plan (the
  `automation-plan/README.md` placeholder does not count).
- `<workspace>/bdd/features/<area>.feature` - the scenarios (tags + steps).
- `<workspace>/product-knowledge/`, `<workspace>/test-ideas/` - read by Claude
  for the judgment layer.
- CLI: `--area <slug>` for a single feature; `--scenario "<name>"` for a single
  scenario; omit both for all `automate`-ranked scenarios.

## Outputs

- `tests/pages/<AreaName>Page.ts` - one page object per area, with a preserved
  user-edits region.
- `tests/fixtures/<area>.ts` - the per-area fixture (data via the
  `.test-commander/test-data/` tree, D6).
- `tests/e2e/<area>.spec.ts` - one `test()` per scenario with `@req:`/`@cs:`
  provenance.
- `<workspace>/traceability/automation-map.md` - scenario -> spec links (the
  Phase-6-owned map).

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- At least one real automation plan exists. Otherwise exit 2 with an error
  directing the user at `/tc:automation-plan`.

## Behavior

1. **Resolve** the workspace and discover the automation plans (`--area`
   selects one).
2. **Select** the scenarios each plan ranks `automate` (or that carry
   `@automated-candidate`) with a resolvable `@req:`/`@cs:` linkage.
3. **Build** the framework lazily via `ensure_framework` before writing any
   TypeScript.
4. **Render** the page object (preserving its user-edits region), the per-area
   fixture, and the spec - one `test()` per scenario with provenance.
5. **Write** `traceability/automation-map.md` linking every generated scenario
   to its spec.

Deterministic: scenarios sort by `cs` then name; overwrite mode for specs and
fixtures; the page object's user-edits region is carried forward, so a re-run
with no edits is byte-identical.

After writing the automation map, this command auto-runs the shared
`review_automation()` (the same engine `/tc:review-automation` uses), updating
the review summary and routing findings to `requirements/open-questions.md`.
Pass `--no-review` to suppress the auto-run. The generated TypeScript is authored
to pass the review rubric (provenance, fixture-mediated data, a real assertion,
role-based locators, no hardcoded waits).

## Safety

- Writes only the project-root `tests/` tree and
  `traceability/automation-map.md`. Never writes `bdd/` (Phase 5) or
  `product-knowledge/` (Phase 3).
- No network, no browser. Writes TypeScript and Markdown text only - never
  invokes `tsc` or `npx playwright test`. Execution is Phase 7's `/tc:run`.

## Implementation

- Helper: `plugins/test-commander/scripts/automate.py` (per D18).
- Run: `python3 <plugin-root>/scripts/automate.py <project-root> [--area <slug>] [--scenario "<name>"]`.
- Mirrors `generate_bdd.py`; imports `build_framework.ensure_framework` (lazy
  init) and reuses `review_bdd.parse_feature_file`. Renders from the four
  `tc-build-framework` object templates' shapes.

## Definition of Done

- Generates structurally-valid TS with `@req:`/`@cs:` provenance and
  fixture-mediated data (nothing inline).
- Lazy-init wired (framework auto-built when absent).
- `automation-map.md` links each scenario to its spec.
- Idempotent (byte-identical re-run; user-edits region preserved).
- `tc-automate/SKILL.md` describes the shipped generation behavior.

## See also

- [Automation generation methodology](../methodology/automation-generation.md) - the workflow, locator/fixture discipline, lazy-init, write boundary, and judgment layer.
- [Playwright standards](../../tc-build-framework/methodology/playwright-standards.md), [locator strategy](../../tc-build-framework/methodology/locator-strategy.md).
- [Object templates](../../tc-build-framework/templates/) - the v1 rendering contract.
- [tc-automate skill](../SKILL.md)
- [tc-automation-plan skill](../../tc-automation-plan/SKILL.md) - produces the plan this command consumes.
