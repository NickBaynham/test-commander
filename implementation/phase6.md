# Phase 6 — Playwright Framework and Strategic Automation (implementation summary)

Status: implementation complete (sub-steps 6.1–6.8); sign-off (6.9) and the
annotated `phase-6` tag pending. Four skills shipped — `tc-build-framework`,
`tc-automation-plan`, `tc-automate`, `tc-test-data` — adding five commands and
the project's **first executable artifacts** (generated Playwright/TypeScript).
This document summarizes what Phase 6 delivered, the user-facing capabilities it
unlocked, and what already existed prior to Phase 6.

Authoritative sources: [CHANGELOG.md](../CHANGELOG.md) (per-sub-step shipping
log), [planning/plan.md](../planning/plan.md) (the Phase 6 section, To Do, and
lessons learned), and the user walkthrough
[docs/user-guide/automation.md](../docs/user-guide/automation.md).

## What existed prior to Phase 6 (Phases 0–5)

By the close of Phase 5, Test Commander was a Claude Code plugin plus a small
Python runtime that took a project from raw requirements through exploratory
testing, BDD, and traceability — every artifact committed to a `.test-commander/`
workspace, but **nothing executable**: the furthest-downstream artifact was a
reviewed Gherkin `.feature` file, and the `test-map.md` `Automated test` column
read `pending`.

| Phase | Skill | Commands | Capability |
| --- | --- | --- | --- |
| 0 | — | — | Repository foundation: marketplace + plugin manifest, `bootstrap.sh`, `make install`, the verify chain. |
| 1 | `tc-core` | `/tc:init`, `/tc:status`, `/tc:journal`, `/tc:next` | Initialize the committed workspace, summarize state, journal, recommend the next command. |
| 2 | `tc-requirements` | 5 commands | Review requirements / stories / acceptance criteria; build the requirements inventory; seed `test-ideas/REQ-*.md`. |
| 3 | `tc-knowledge` | 5 commands | Ingest docs, specs, code, recorded APIs, and tests into a structured `product-knowledge/` model. |
| 4 | `tc-explore` | 4 commands | Charter-based exploratory testing; enrich the test-idea seeds with candidate scenarios. |
| 5 | `tc-bdd`, `tc-traceability` | `/tc:generate-bdd`, `/tc:review-bdd`, `/tc:traceability-map` | Turn enriched test ideas into reviewable Gherkin with `@req:`/`@cs:` linkage; rebuild the requirement and scenario-level traceability maps (downstream links `pending`). |

What was missing at the end of Phase 5: there was no automation framework, no way
to decide *which* scenarios were worth automating, no generated tests, and no
test-data discipline. The `@automated-candidate` scenarios were a promise with no
machinery behind them. Phase 6 fills that gap.

## What Phase 6 delivered

Phase 6 turns reviewed BDD scenarios into a maintainable Playwright/TypeScript
suite, via four new skills. It is the realization of Decision **D8** (the
framework is built lazily, only when automation first needs it) and Decision
**D6** (test data lives outside test code, reached through fixtures).

### `tc-build-framework` — the lazy framework

- **`/tc:build-framework`** ([command page](../plugins/test-commander/skills/tc-build-framework/commands/build-framework.md)).
  Scaffolds the project-root `tests/{e2e,pages,components,fixtures,utils}/` tree
  plus `playwright.config.ts` (target via the `PLAYWRIGHT_BASE_URL` env var) and
  `package.json` (declaring `@playwright/test` + `typescript`). Each path is
  created only when absent, so a re-run is a byte-stable no-op. Exposes
  `ensure_framework(project_root)` — the lazy-init entry point `/tc:automate`
  calls before generating any TypeScript. Ships the four `.ts` object templates
  that are the v1 rendering contract.

### `tc-automation-plan` — the strategic gate

- **`/tc:automation-plan`** ([command page](../plugins/test-commander/skills/tc-automation-plan/commands/automation-plan.md)).
  Scores every BDD scenario against a universal seven-factor suitability rubric —
  `traceable` (3), `regression-value` (2), `risk-flagged` (2), `deterministic`
  (2), `right-sized` (1), `data-ready` (1), `persona-scoped` (1) — and writes
  `automation-plan/<area>.md` ranking each `automate` / `consider` / `manual`
  with per-factor scores and a recommended order. Two hard overrides bypass the
  score: `@automated-candidate` always `automate`, `@manual` always `manual`.
  Weights tune via `tc-automate.suitability.weights` in `config.yaml`.

### `tc-automate` — generation and review

- **`/tc:automate`** ([command page](../plugins/test-commander/skills/tc-automate/commands/automate.md)).
  Reads the plan + features, builds the framework lazily, and renders — for every
  `automate`-ranked scenario — a page object (`tests/pages/<AreaName>Page.ts`,
  with a preserved user-edits region), a per-area fixture
  (`tests/fixtures/<area>.ts`, reaching data only via `.test-commander/test-data/`),
  and a spec (`tests/e2e/<area>.spec.ts`, one `test()` per scenario opened by a
  `// @req:REQ-NNN @cs:CS-NNN-NNN` provenance comment). Writes the Phase-6-owned
  `traceability/automation-map.md`, then auto-runs the review (suppress with
  `--no-review`).
- **`/tc:review-automation`** ([command page](../plugins/test-commander/skills/tc-automate/commands/review-automation.md)).
  Runs a six-category universal rubric over the generated specs —
  `inline-test-data`, `hardcoded-wait`, `missing-provenance`, `weak-locator`,
  `untraceable-spec`, `assertion-free` — writes a verdict to
  `automation-plan/review-summary.md`, and routes failures to
  `requirements/open-questions.md` as deduplicated `[automation-review]` signals.
  The shared `review_automation()` is exactly what `/tc:automate` auto-runs.

### `tc-test-data` — the data discipline

- **`/tc:generate-test-data`** ([command page](../plugins/test-commander/skills/tc-test-data/commands/generate-test-data.md)).
  Populates `test-data/seed/<area>.json` (the file the generated fixture loads)
  and `test-data/scenarios/<area>.md` (the declarative data spec) from the BDD
  scenarios. Closes the D6 loop: the fixture's data reference resolves to a real
  file, so nothing is inlined in the spec. Generated files (carrying a marker)
  are overwritten; user-authored files are preserved.

### Cross-cutting concepts introduced

- **First executable artifacts (D2/D8).** Phase 6 is where Test Commander stops
  being purely Markdown skills and starts generating runnable code — but it
  *generates and structurally validates* only; it never invokes `tsc` or
  `npx playwright test` (execution is Phase 7's `/tc:run`).
- **Provenance as the join key.** Every generated `test()` carries
  `// @req: @cs:`, and `automation-map.md` links each scenario to its spec — so
  `/tc:traceability-map` now resolves the `Automated test` column of
  `test-map.md` from `pending` (the new wiring added in Step 6.8).
- **Test data outside test code (D6).** A spec never inlines data; it flows
  through a fixture from `test-data/`. The automation review enforces this.
- **Project extensibility (D19).** The framework, rubrics, and seed shape are
  universal; the only `config.yaml` surface is `tc-automate.suitability.weights`,
  and the target URL is the `PLAYWRIGHT_BASE_URL` env var. See
  [customizing-for-your-project.md](../docs/user-guide/customizing-for-your-project.md).

## Key features available to the user after Phase 6, and how to use them

The five commands run as one workflow after Phase 5 has produced reviewed BDD.
Walkthrough with verbatim output: [automation.md](../docs/user-guide/automation.md).
In Claude Code you invoke the slash commands; under the hood each is a bundled
Python helper run as `python3 <plugin-root>/scripts/<helper>.py <project-root>`.

1. **Build the Playwright framework on demand.** Run `/tc:build-framework` (or
   just run `/tc:automate`, which builds it lazily first). It scaffolds the
   project-root `tests/` tree, `playwright.config.ts`, and `package.json` only if
   absent — re-running changes nothing. Point it at your app with
   `PLAYWRIGHT_BASE_URL`.

2. **Decide what to automate, defensibly.** Run `/tc:automation-plan`. It scores
   every reviewed scenario and writes `automation-plan/<area>.md` ranking each
   `automate` / `consider` / `manual`. To automate by risk first (or smoke first,
   or stability first), set `tc-automate.suitability.weights` in
   `<workspace>/config.yaml` and re-run — the ranking changes accordingly.

3. **Generate a traceable TypeScript suite.** Run `/tc:automate`. For every
   `automate`-ranked scenario it writes a page object, a fixture, and a spec with
   `@req:`/`@cs:` provenance and fixture-mediated data, then writes
   `automation-map.md` and auto-runs the review. Use `--area <slug>` or
   `--scenario "<name>"` to generate a subset, `--no-review` to skip the
   auto-run. Claude then refines the generated scaffolds (real steps, real
   assertions, shared components) inside the preserved regions.

4. **Review automation quality mechanically.** Run `/tc:review-automation` (or
   rely on the `/tc:automate` auto-run). It flags inlined data, hardcoded waits,
   missing provenance, weak locators, untraceable specs, and assertion-free
   tests, records a per-spec verdict, and files deduplicated `[automation-review]`
   open questions.

5. **Populate test data, kept out of the code.** Run `/tc:generate-test-data`.
   It writes `test-data/seed/<area>.json` (what the fixture loads) and a
   per-area data spec; hand-edit the seed for real values (your edits are
   preserved on re-run), or drop in a Python factory under `test-data/factories/`.

6. **See automation in the traceability map.** Re-run `/tc:traceability-map`
   after `/tc:automate`: the `Automated test` column of `test-map.md` resolves
   from `pending` to the generated spec path for each automated scenario, while
   `Test result` and `Quality report` stay `pending` until Phase 7.

7. **The full chain end to end.** Requirements → knowledge → exploration →
   enriched test ideas → BDD → traceability → **automation plan → generated
   suite → review → test data**, all committed under `.test-commander/` (and the
   framework at the project-root `tests/` tree). `/tc:next` walks you through it.

## Implementation breakdown (sub-steps 6.1–6.8)

| Sub-step | What landed |
| --- | --- |
| 6.1 | Scaffolded all four skills + the `seeded-automation` fixture (a clean, automatable `sign-in.feature`); one parametrized scaffold test, strict-PyYAML frontmatter from the start. |
| 6.2 | `/tc:build-framework` — `build_framework.py` (lazy + idempotent, `ensure_framework`), the four `.ts` object templates, `playwright-standards.md` + `locator-strategy.md`; retired the stale `make build` runtime-guard placeholder. |
| 6.3 | `/tc:automation-plan` — `automation_plan.py` (the seven-factor rubric, config-tunable weights), `automation-suitability.md`, the plan template, and the first Phase-6 customization-guide entry. |
| 6.4 | `/tc:automate` (generation only) — `automate.py` (page objects + fixtures + specs with provenance + fixture data, lazy-init), the umbrella `automation-generation.md`, and the Phase-6-owned `automation-map.md`. |
| 6.5 | `/tc:review-automation` + the shared `review_automation()` + wiring the `/tc:automate` auto-run (`--no-review`); the six-category rubric, `automation-review.md`, the flawed-spec fixture. |
| 6.6 | `/tc:generate-test-data` — `generate_test_data.py` (JSON seed + Markdown spec, skip-not-overwrite), `test-data-strategy.md`, the data template; closed the D6 fixture-data loop. |
| 6.7 | Documentation pass — `automation.md`, command/workspace references, the customization-guide Phase 6 schema with three project-shape examples, and the six status-line surfaces. |
| 6.8 | Testing finalization — `DEFAULT_PHASE_CAP` 5 → 6 (all four skills flip `PRESENT`), `test_phase_6_integration.py` (full Phase 2 → 6 sweep), and the `test-map` `Automated test` resolution wiring. |

Deliberate plan refinements recorded as lessons: review wiring deferred from 6.4
to 6.5 (avoiding a forward dependency, the Phase-5 pattern); the recurring
"template ships a `README.md` placeholder" trap caught by a RED test in 6.4 (the
automation-plan glob mistook the placeholder for a real plan); and the 6.8
discovery that the `test-map` `Automated test` resolution was not yet wired —
the integration test landed RED on exactly that and drove the fix.

## Quality state at Phase 6 implementation close (pre-sign-off)

- 600 tests passing; `ruff` clean; `check_links.py` clean across 192 files.
- `verify_skills.py` reports all ten shipped skills `PRESENT`
  (`tc-core`, `tc-requirements`, `tc-knowledge`, `tc-explore`, `tc-bdd`,
  `tc-traceability`, `tc-build-framework`, `tc-automation-plan`, `tc-automate`,
  `tc-test-data`) with `UNEXPECTED=0`.
- All four Phase 6 `SKILL.md` files describe every shipped command with no
  deferral wording.

## What comes next (Phase 6.9, then Phase 7)

Step 6.9 is the sign-off: a cold-user walkthrough from a clean `make install`,
the per-step DoD audit, the plan + CHANGELOG closing (flip the status to "Phase 6
complete"), the test-first `test_phase_6_signoff.py`, and the annotated `phase-6`
tag. Then Phase 7 (`tc-run`, `tc-quality-report`, `tc-evidence`) executes the
generated suite, captures evidence, and fills the `Test result` and `Quality
report` columns of `test-map.md` that Phase 6 left `pending`.
