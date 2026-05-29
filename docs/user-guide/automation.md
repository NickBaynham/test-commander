# Workflow — Strategic Automation (Phase 6)

This guide walks you through Test Commander's five Phase 6 commands end to end against a consuming project. The examples use the deliberately-generic seeded fixture from `tests/fixtures/seeded-automation/` (a clean, automatable `sign-in.feature` whose every scenario is an `@automated-candidate` with resolvable `@req:`/`@cs:` tags), so every output is reproducible.

## What's available in Phase 6

Phase 6 ships four skills that turn reviewed BDD scenarios into a maintainable Playwright/TypeScript suite:

| Command | Reads | Writes |
| --- | --- | --- |
| `/tc:build-framework` | the initialized workspace | the project-root `tests/{e2e,pages,components,fixtures,utils}/` tree + `tests/playwright.config.ts` + `tests/package.json` (lazily, only when absent) |
| `/tc:automation-plan` | `bdd/features/*.feature` + `config.yaml` | `automation-plan/<area>.md` (the seven-factor suitability ranking) |
| `/tc:automate` | `automation-plan/<area>.md` + `bdd/features/*.feature` | `tests/pages/<AreaName>Page.ts`, `tests/fixtures/<area>.ts`, `tests/e2e/<area>.spec.ts`, `traceability/automation-map.md`; auto-runs the review (suppressible with `--no-review`) |
| `/tc:review-automation` | `tests/e2e/*.spec.ts` + `automation-map.md` | `automation-plan/review-summary.md`; appends `[automation-review]` gap signals to `requirements/open-questions.md` |
| `/tc:generate-test-data` | `bdd/features/*.feature` | `test-data/seed/<area>.json` + `test-data/scenarios/<area>.md` |

Phase 6 **reads broadly** but writes only the project-root `tests/` tree and, inside the workspace, `automation-plan/`, `test-data/`, `traceability/automation-map.md`, and the `[automation-review]` line in `open-questions.md`. It does not write `bdd/` (Phase 5) or `product-knowledge/` (Phase 3).

Per Decision D19 ([planning/plan.md](../../planning/plan.md)) the shipped framework, rubric, and data shape are universal. The target URL is a runtime env var (`PLAYWRIGHT_BASE_URL`) and the suitability weights tune via `<workspace>/config.yaml` — see [customizing-for-your-project.md](customizing-for-your-project.md).

## The traceability chain

```
Requirement -> Test Idea -> BDD Scenario -> Automation Candidate
            -> Automated Test -> Test Result -> Quality Report
```

Phase 6 fills the **Automated Test** link: `/tc:automate` stamps each generated `test()` with a `// @req:REQ-NNN @cs:CS-NNN-NNN` provenance comment and writes `automation-map.md`, so a `/tc:traceability-map` re-run resolves the `Automated test` column of `test-map.md` from `pending`. Test Result and Quality Report stay `pending` until Phase 7.

## Prerequisites

1. `<workspace>/.test-commander/` exists (`/tc:init` has run — see [workflow.md](workflow.md)).
2. Phase 5 produced at least one reviewed feature at `<workspace>/bdd/features/<area>.feature`. See [generating-bdd.md](generating-bdd.md). The seeded `tests/fixtures/seeded-automation/sign-in.feature` is a worked example of a clean, automatable feature.

The natural order is Phase 5 → Phase 6: plan and automate only after the BDD scenarios exist and are reviewed.

## Step 1: `/tc:build-framework`

Scaffolds the project-root Playwright/TypeScript framework lazily (Decision D8): the directory tree, `playwright.config.ts`, and `package.json`. Each path is created only when absent, so a re-run is a byte-stable no-op.

**Run:**

```sh
python3 <plugin-root>/scripts/build_framework.py <project-root>
```

**Sample output** (first run):

```
framework: created 7, skipped 0
  + tests/e2e/.gitkeep
  + tests/pages/.gitkeep
  + tests/components/.gitkeep
  + tests/fixtures/.gitkeep
  + tests/utils/.gitkeep
  + tests/playwright.config.ts
  + tests/package.json
```

You rarely run this directly — `/tc:automate` calls the same `ensure_framework` entry point before generating. The config reads the target from the `PLAYWRIGHT_BASE_URL` environment variable; the four `.ts` object templates under the skill's `templates/` are the v1 rendering contract `/tc:automate` consumes. Full methodology: [`tc-build-framework/methodology/playwright-standards.md`](../../plugins/test-commander/skills/tc-build-framework/methodology/playwright-standards.md).

## Step 2: `/tc:automation-plan`

Scores every scenario against the universal seven-factor suitability rubric (`traceable`, `regression-value`, `risk-flagged`, `deterministic`, `right-sized`, `data-ready`, `persona-scoped`) and ranks it `automate` / `consider` / `manual`. `@automated-candidate` always ranks `automate`; `@manual` always `manual`.

**Run:**

```sh
python3 <plugin-root>/scripts/automation_plan.py <project-root>
```

**Sample output:**

```
planned: 1 area(s) (3 scenario(s))
  - .test-commander/automation-plan/sign-in.md
```

**What lands** — `automation-plan/sign-in.md`:

```
## Ranking

| scenario | rank | score | traceable | regression-value | risk-flagged | deterministic | right-sized | data-ready | persona-scoped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Session expires after the idle timeout | automate | 9 | 3 | 2 | 0 | 2 | 1 | 1 | 0 |
| Sign in is rejected with an invalid password | automate | 9 | 3 | 2 | 0 | 2 | 1 | 1 | 0 |
| Sign in with valid credentials | automate | 9 | 3 | 2 | 0 | 2 | 1 | 1 | 0 |

## Recommended order

1. Session expires after the idle timeout (automate, score 9)
2. Sign in is rejected with an invalid password (automate, score 9)
3. Sign in with valid credentials (automate, score 9)
```

The score is a deterministic first pass; Claude then reviews the plan against `product-knowledge/` and may promote or hold back a scenario. Tune the weights via `tc-automate.suitability.weights`. Full methodology: [`tc-automation-plan/methodology/automation-suitability.md`](../../plugins/test-commander/skills/tc-automation-plan/methodology/automation-suitability.md).

## Step 3: `/tc:automate`

Reads the plan and the features, builds the framework lazily, and renders — for every `automate`-ranked scenario — a page object, a per-area fixture, and a spec with one `test()` per scenario. Then it writes `automation-map.md` and auto-runs the review.

**Run:**

```sh
python3 <plugin-root>/scripts/automate.py <project-root> [--area <slug>] [--scenario "<name>"] [--no-review]
```

**Sample output:**

```
automated: 1 spec(s) (3 scenario(s))
  - tests/e2e/sign-in.spec.ts
```

**What lands** — `tests/e2e/sign-in.spec.ts` (one `test()` per scenario, each with provenance and fixture-mediated data):

```typescript
import { test, expect } from '../fixtures/sign-in';
import { SignInPage } from '../pages/SignInPage';

test.describe('Sign-in and session lifecycle (seeded automation fixture)', () => {
  // @req:REQ-001 @cs:CS-001-001
  test('Sign in with valid credentials', async ({ page, data }) => {
    const signIn = new SignInPage(page);
    await signIn.goto();
    // Refine the Given/When/Then below; data comes from `data` (D6).
    await expect(page).toHaveURL(/.+/);
  });
});
```

The spec imports `test`/`expect` from its per-area fixture, never inlining data (Decision D6). The page object owns the locators; the spec drives behavior. `automation-map.md` links each scenario to the spec:

```
| requirement | candidate | scenario | spec |
| --- | --- | --- | --- |
| REQ-001 | CS-001-001 | Sign in with valid credentials | tests/e2e/sign-in.spec.ts |
```

The generated TypeScript is a deterministic scaffold; Claude refines the Given/When/Then, replaces the generic assertion with the real expected outcome, and factors shared UI into component objects — within the page object's preserved user-edits region. Full methodology: [`tc-automate/methodology/automation-generation.md`](../../plugins/test-commander/skills/tc-automate/methodology/automation-generation.md).

## Step 4: `/tc:review-automation`

Runs the six-category universal rubric over every spec: `inline-test-data`, `hardcoded-wait`, `missing-provenance`, `weak-locator`, `untraceable-spec`, `assertion-free` (one finding per category per spec). Writes a per-spec verdict and routes failures to `requirements/open-questions.md`. The same implementation is what `/tc:automate` auto-runs.

**Run:**

```sh
python3 <plugin-root>/scripts/review_automation.py <project-root>
```

**Sample output** (the generated spec is clean, so it passes):

```
reviewed: 1 spec(s) (0 finding(s))
  - tests/e2e/sign-in.spec.ts: pass
```

When a spec has defects, each finding becomes a deduplicated line in `requirements/open-questions.md`:

```
- [tc-automate/automation-review-<area>] [automation-review] <category>: spec '<path>' <message>.
```

The rubric is the inverse of the generation discipline — see [`tc-automate/methodology/automation-review.md`](../../plugins/test-commander/skills/tc-automate/methodology/automation-review.md).

## Step 5: `/tc:generate-test-data`

Populates `test-data/` so the per-area fixture reaches its data through a file rather than inlining it (Decision D6). Closes the loop: the fixture's `seed/<area>.json` reference now resolves.

**Run:**

```sh
python3 <plugin-root>/scripts/generate_test_data.py <project-root>
```

**Sample output:**

```
test-data: 1 area(s) (1 seed file(s), skipped 0)
  - .test-commander/test-data/seed/sign-in.json
```

**What lands** — `test-data/seed/sign-in.json` (one record per candidate, universal shape):

```json
{
  "_generated_by": "/tc:generate-test-data",
  "area": "sign-in",
  "records": {
    "CS-001-001": { "id": "CS-001-001", "label": "Sign in with valid credentials", "requirement": "REQ-001" }
  }
}
```

Generated files (those carrying the marker) are overwritten on re-run; user-authored files (no marker) are preserved. Claude fleshes the records out with realistic, scenario-appropriate values from `product-knowledge/`. Full methodology: [`tc-test-data/methodology/test-data-strategy.md`](../../plugins/test-commander/skills/tc-test-data/methodology/test-data-strategy.md).

## What changed on disk

```
<project-root>/
  tests/                                    # the framework (outside the workspace)
    e2e/sign-in.spec.ts                      # generated (provenance + fixture data)
    pages/SignInPage.ts                      # generated (preserved user-edits region)
    fixtures/sign-in.ts                      # generated (reads test-data/)
    playwright.config.ts, package.json       # scaffolded lazily
  .test-commander/
    automation-plan/sign-in.md               # the suitability ranking
    automation-plan/review-summary.md        # the review verdicts
    test-data/seed/sign-in.json              # the fixture's data
    test-data/scenarios/sign-in.md           # the data spec
    traceability/automation-map.md           # scenario -> spec links
    requirements/open-questions.md           # [automation-review] signals (if any)
```

## Re-running

All five commands are idempotent and byte-deterministic: re-running against unchanged inputs reproduces identical files (the page object's user-edits region is preserved), and `[automation-review]` gap signals are deduplicated. `/tc:build-framework` is a no-op once the framework exists; `/tc:automate` owns `automation-map.md`.

## Customizing for your project

Phase 6 ships a universal framework, rubric, and data shape. The only `config.yaml` surface is `tc-automate.suitability.weights` (re-weight the seven factors); the target URL is the `PLAYWRIGHT_BASE_URL` env var. See the "Phase 6 schema (`tc-automate`)" section of [customizing-for-your-project.md](customizing-for-your-project.md).

## Beyond Phase 6

Phase 7 runs the generated suite (`/tc:run`), captures evidence, and fills the `Test result` and `Quality report` columns of `test-map.md`, then gates quality (`/tc:quality-gate`).

## See also

- [tc-build-framework build-framework command page](../../plugins/test-commander/skills/tc-build-framework/commands/build-framework.md)
- [tc-automation-plan automation-plan command page](../../plugins/test-commander/skills/tc-automation-plan/commands/automation-plan.md)
- [tc-automate automate command page](../../plugins/test-commander/skills/tc-automate/commands/automate.md)
- [tc-automate review-automation command page](../../plugins/test-commander/skills/tc-automate/commands/review-automation.md)
- [tc-test-data generate-test-data command page](../../plugins/test-commander/skills/tc-test-data/commands/generate-test-data.md)
- [Command reference](../command-reference.md)
- [Workspace reference](../workspace-reference.md)
- [Generating BDD (Phase 5)](generating-bdd.md) — produces the reviewed scenarios this phase consumes.
```
