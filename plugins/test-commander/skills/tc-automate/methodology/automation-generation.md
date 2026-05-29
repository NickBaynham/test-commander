# Automation generation

How Test Commander turns `automate`-ranked BDD scenarios into maintainable
Playwright/TypeScript. This is the umbrella methodology for the `tc-automate`
skill; it covers the generation workflow, the locator and fixture discipline,
the lazy-init contract, the cross-phase write boundary, and the Claude judgment
layer. The conventions are universal (Decision D19).

## The BDD -> page-object -> spec workflow

`/tc:automate` reads the automation plan and the feature files and, for every
scenario the plan ranks `automate` (or that carries `@automated-candidate`) with
a resolvable `@req:`/`@cs:` linkage, renders three artifacts per `@area:`:

1. **Page object** (`tests/pages/<AreaName>Page.ts`) - one per area. All
   locators live here, never in the spec. Carries a preserved user-edits region
   so hand-added methods survive regeneration.
2. **Fixture** (`tests/fixtures/<area>.ts`) - the only path test data reaches a
   spec (D6). It loads declarative data from the
   `.test-commander/test-data/seed/<area>.json` manifest that
   `/tc:generate-test-data` (Step 6.6) populates.
3. **Spec** (`tests/e2e/<area>.spec.ts`) - one `test()` per scenario, each
   opened by a `// @req:REQ-NNN @cs:CS-NNN-NNN` provenance comment, driving the
   page object and asserting on the fixture data.

## Provenance is mandatory

Every generated `test()` carries the `// @req: @cs:` comment linking it back to
its requirement and candidate scenario. This is what lets `/tc:traceability-map`
resolve the `Automated test` column and what the Step 6.5 review enforces
(`missing-provenance`, `untraceable-spec`). A generated test without provenance
is a defect.

## Locator and fixture discipline

- **Locators**: page objects follow the [locator strategy](../../tc-build-framework/methodology/locator-strategy.md) -
  role/label/test-id before CSS/XPath. A spec that reaches for a raw selector is
  a `weak-locator` finding.
- **Data via fixtures only (D6)**: specs never inline credentials, payloads, or
  records. Data flows through the per-area fixture from the
  `.test-commander/test-data/` tree. An inlined literal is an `inline-test-data`
  finding.
- **No hardcoded waits**: rely on Playwright's auto-waiting and web-first
  assertions, never `page.waitForTimeout(...)` (`hardcoded-wait`).

## The lazy-init contract

`/tc:automate` calls `build_framework.ensure_framework(project_root)` before
writing any TypeScript, so the framework is scaffolded on first use (Decision
D8) and the command works from a clean checkout with no separate build step.
`ensure_framework` is a byte-stable no-op when the framework already exists.

## Cross-phase write boundary

`/tc:automate` reads `automation-plan/`, `bdd/features/`, `test-ideas/`, and
`product-knowledge/`. It writes only the project-root `tests/` tree and
`<workspace>/traceability/automation-map.md` (the Phase-6-owned map; Phase 2
only seeded it). It never writes `bdd/` (Phase 5) or `product-knowledge/`
(Phase 3).

## Generation, then review

Step 6.4 ships generation only; the generated TypeScript is authored to pass the
Step 6.5 review rubric (provenance present, data via a fixture, a real
assertion, role-based locators, no hardcoded waits). Step 6.5 adds
`/tc:review-automation` and wires it as an auto-run at the end of `/tc:automate`
(suppressible with `--no-review`).

## The Claude judgment layer

The generated specs are a deterministic scaffold, not the finished suite. Claude
refines the Given/When/Then into concrete page interactions, replaces the
generic assertion with the scenario's real expected outcome, factors shared UI
into component objects, and shapes the fixture data - all within the preserved
regions and the generated structure. The mechanical generation guarantees
traceability and structure; Claude's judgment makes the tests meaningful.

## See also

- [/tc:automate](../commands/automate.md) - the command spec.
- [Playwright standards](../../tc-build-framework/methodology/playwright-standards.md) - framework layout and the generate-and-structurally-validate discipline.
- [Automation suitability](../../tc-automation-plan/methodology/automation-suitability.md) - how scenarios are ranked.
- [tc-build-framework skill](../../tc-build-framework/SKILL.md) - the lazy framework and object templates.
