# Command Reference

This file is the index. Per-command pages — inputs, outputs, preconditions, behavior, safety, definition of done — live next to their skill at `plugins/test-commander/skills/<skill>/commands/<command>.md`. Per the Phase 1 design decision, the per-command page is the single source of truth that Claude reads at runtime and that users read for reference.

## Phase 1 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:init` | `tc-core` | [init.md](../plugins/test-commander/skills/tc-core/commands/init.md) |
| `/tc:status` | `tc-core` | [status.md](../plugins/test-commander/skills/tc-core/commands/status.md) |
| `/tc:journal` | `tc-core` | [journal.md](../plugins/test-commander/skills/tc-core/commands/journal.md) |
| `/tc:next` | `tc-core` | [next.md](../plugins/test-commander/skills/tc-core/commands/next.md) |

For the methodology behind `/tc:next`'s recommendations, see [next-step-inference.md](../plugins/test-commander/skills/tc-core/methodology/next-step-inference.md).

## Phase 2 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:review-requirements` | `tc-requirements` | [review-requirements.md](../plugins/test-commander/skills/tc-requirements/commands/review-requirements.md) |
| `/tc:review-user-stories` | `tc-requirements` | [review-user-stories.md](../plugins/test-commander/skills/tc-requirements/commands/review-user-stories.md) |
| `/tc:review-acceptance-criteria` | `tc-requirements` | [review-acceptance-criteria.md](../plugins/test-commander/skills/tc-requirements/commands/review-acceptance-criteria.md) |
| `/tc:requirements-coverage` | `tc-requirements` | [requirements-coverage.md](../plugins/test-commander/skills/tc-requirements/commands/requirements-coverage.md) |
| `/tc:requirements-to-tests` | `tc-requirements` | [requirements-to-tests.md](../plugins/test-commander/skills/tc-requirements/commands/requirements-to-tests.md) |

For the rubric methodology, see [requirements-quality-review.md](../plugins/test-commander/skills/tc-requirements/methodology/requirements-quality-review.md), [user-story-readiness.md](../plugins/test-commander/skills/tc-requirements/methodology/user-story-readiness.md), and [acceptance-criteria-quality.md](../plugins/test-commander/skills/tc-requirements/methodology/acceptance-criteria-quality.md). End-to-end walkthrough: [user-guide/reviewing-requirements.md](user-guide/reviewing-requirements.md).

## Phase 3 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:learn-from-docs` | `tc-knowledge` | [learn-from-docs.md](../plugins/test-commander/skills/tc-knowledge/commands/learn-from-docs.md) |
| `/tc:learn-from-specs` | `tc-knowledge` | [learn-from-specs.md](../plugins/test-commander/skills/tc-knowledge/commands/learn-from-specs.md) |
| `/tc:learn-from-code` | `tc-knowledge` | [learn-from-code.md](../plugins/test-commander/skills/tc-knowledge/commands/learn-from-code.md) |
| `/tc:learn-from-api` | `tc-knowledge` | [learn-from-api.md](../plugins/test-commander/skills/tc-knowledge/commands/learn-from-api.md) |
| `/tc:learn-from-tests` | `tc-knowledge` | [learn-from-tests.md](../plugins/test-commander/skills/tc-knowledge/commands/learn-from-tests.md) |

All five commands write per-source models under `<workspace>/product-knowledge/`, contribute scoped `## From <source>` sections to the cross-cutting artifacts (`entities.md`, `user-journeys.md`, `business-rules.md`, `assumptions.md`), and call the shared `synthesize_system_model.py` to regenerate `system-model.md`. Gap signals route to `<workspace>/requirements/open-questions.md` with a `[<kind>]` prefix.

For the methodology behind each helper, see [project-knowledge.md](../plugins/test-commander/skills/tc-knowledge/methodology/project-knowledge.md) (umbrella) plus [learning-from-documents.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-documents.md), [learning-from-specs.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-specs.md), [learning-from-code.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-code.md), [learning-from-api.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-api.md), and [learning-from-tests.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-tests.md). End-to-end walkthrough: [user-guide/building-project-knowledge.md](user-guide/building-project-knowledge.md).

## Phase 4 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:create-charter` | `tc-explore` | [create-charter.md](../plugins/test-commander/skills/tc-explore/commands/create-charter.md) |
| `/tc:explore` | `tc-explore` | [explore.md](../plugins/test-commander/skills/tc-explore/commands/explore.md) |
| `/tc:session-summary` | `tc-explore` | [session-summary.md](../plugins/test-commander/skills/tc-explore/commands/session-summary.md) |
| `/tc:test-ideas` | `tc-explore` | [test-ideas.md](../plugins/test-commander/skills/tc-explore/commands/test-ideas.md) |

`/tc:create-charter` scopes an exploration session against Phase-3 product-knowledge + Phase-2 open questions. `/tc:explore` replays a recorded Playwright MCP session against the charter, classifies events into Observations / Evidence / Anomalies / Charter Coverage, and runs the internal exploration-review sub-mode (suppressible with `--no-review`) that appends `[exploration-review]` gap signals to `<workspace>/requirements/open-questions.md`. `/tc:session-summary` synthesizes a per-session summary with aggregate counts and structured candidate scenarios, plus rebuilds `<workspace>/sessions/index.md`. `/tc:test-ideas` enriches the Phase-2 `tc-test-idea/v1` seeds under `<workspace>/test-ideas/REQ-*.md`, preserving every Phase-2 frontmatter key byte-for-byte, flipping `status: seed` → `status: enriched`, merging `phase_4_sessions:`, and appending a `## Phase 4 enrichment` body section.

For the methodology behind each helper, see [exploratory-testing.md](../plugins/test-commander/skills/tc-explore/methodology/exploratory-testing.md) (umbrella) plus [charter-based-exploration.md](../plugins/test-commander/skills/tc-explore/methodology/charter-based-exploration.md), [session-based-test-management.md](../plugins/test-commander/skills/tc-explore/methodology/session-based-test-management.md), and [test-idea-model.md](../plugins/test-commander/skills/tc-explore/methodology/test-idea-model.md). End-to-end walkthrough: [user-guide/exploring-an-app.md](user-guide/exploring-an-app.md).

## Phase 5 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:generate-bdd` | `tc-bdd` | [generate-bdd.md](../plugins/test-commander/skills/tc-bdd/commands/generate-bdd.md) |
| `/tc:review-bdd` | `tc-bdd` | [review-bdd.md](../plugins/test-commander/skills/tc-bdd/commands/review-bdd.md) |
| `/tc:traceability-map` | `tc-traceability` | [traceability-map.md](../plugins/test-commander/skills/tc-traceability/commands/traceability-map.md) |

`/tc:generate-bdd` turns Phase-4-enriched test-idea seeds into Gherkin `.feature` files — one scenario per `CS-NNN-NNN` candidate, each carrying `@req:`/`@cs:` linkage tags, an `@area:` namespace tag, and a type-mapped class tag — then writes a per-feature summary, rebuilds `bdd/index.md`, and auto-runs the review sub-mode (suppressible with `--no-review`). `/tc:review-bdd` runs the six-category universal rubric (`ambiguous-step`, `missing-tag`, `untraceable`, `ui-coupled-step`, `missing-examples`, `conjunction-overload`), writes a verdict into each summary, and routes failures to `<workspace>/requirements/open-questions.md` as deduplicated `[bdd-review]` gap signals; it shares one `review_features()` implementation with the generate-time auto-run. `/tc:traceability-map` is the authoritative regenerator of `<workspace>/traceability/requirements-map.md` (the shared 4-column format `/tc:requirements-coverage` also writes) and `<workspace>/traceability/test-map.md` (the scenario-level chain with `pending` downstream links).

For the methodology behind each helper, see [bdd-generation.md](../plugins/test-commander/skills/tc-bdd/methodology/bdd-generation.md) (umbrella) plus [bdd-quality-review.md](../plugins/test-commander/skills/tc-bdd/methodology/bdd-quality-review.md) and [traceability.md](../plugins/test-commander/skills/tc-traceability/methodology/traceability.md). End-to-end walkthrough: [user-guide/generating-bdd.md](user-guide/generating-bdd.md).

## Phase 6 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:build-framework` | `tc-build-framework` | [build-framework.md](../plugins/test-commander/skills/tc-build-framework/commands/build-framework.md) |
| `/tc:automation-plan` | `tc-automation-plan` | [automation-plan.md](../plugins/test-commander/skills/tc-automation-plan/commands/automation-plan.md) |
| `/tc:automate` | `tc-automate` | [automate.md](../plugins/test-commander/skills/tc-automate/commands/automate.md) |
| `/tc:review-automation` | `tc-automate` | [review-automation.md](../plugins/test-commander/skills/tc-automate/commands/review-automation.md) |
| `/tc:generate-test-data` | `tc-test-data` | [generate-test-data.md](../plugins/test-commander/skills/tc-test-data/commands/generate-test-data.md) |

`/tc:build-framework` scaffolds the project-root Playwright/TypeScript framework lazily (Decision D8) — the `tests/{e2e,pages,components,fixtures,utils}/` tree plus `playwright.config.ts` and `package.json`, created only when absent. `/tc:automation-plan` scores every BDD scenario against the universal seven-factor suitability rubric (`traceable`, `regression-value`, `risk-flagged`, `deterministic`, `right-sized`, `data-ready`, `persona-scoped`) and writes `automation-plan/<area>.md` ranking each `automate` / `consider` / `manual`. `/tc:automate` renders page objects, per-area fixtures, and specs for `automate`-ranked scenarios — each `test()` carrying a `// @req:`/`@cs:` provenance comment and reaching data only through its fixture — writes `traceability/automation-map.md`, and auto-runs the review (suppressible with `--no-review`). `/tc:review-automation` runs the six-category universal rubric (`inline-test-data`, `hardcoded-wait`, `missing-provenance`, `weak-locator`, `untraceable-spec`, `assertion-free`), writes `automation-plan/review-summary.md`, and routes failures to `requirements/open-questions.md` as deduplicated `[automation-review]` signals; it shares one `review_automation()` implementation with the auto-run. `/tc:generate-test-data` populates `test-data/seed/<area>.json` and `test-data/scenarios/<area>.md` so the generated fixtures reach data through a file, never inline (Decision D6).

The Phase 6 commands generate and structurally validate TypeScript — they never invoke `tsc` or `npx playwright test` (execution is Phase 7's `/tc:run`). For the methodology, see [playwright-standards.md](../plugins/test-commander/skills/tc-build-framework/methodology/playwright-standards.md), [automation-suitability.md](../plugins/test-commander/skills/tc-automation-plan/methodology/automation-suitability.md), [automation-generation.md](../plugins/test-commander/skills/tc-automate/methodology/automation-generation.md), and [test-data-strategy.md](../plugins/test-commander/skills/tc-test-data/methodology/test-data-strategy.md). End-to-end walkthrough: [user-guide/automation.md](user-guide/automation.md).

## Planned commands (not yet implemented)

These will gain per-command pages as their phases ship.

| Command | Skill | Phase |
| --- | --- | --- |
| `/tc:run` | `tc-run` | 7 |
| `/tc:analyze-results` | `tc-run` | 7 |
| `/tc:report` | `tc-quality-report` | 7 |
| `/tc:quality-gate` | `tc-quality-report` | 7 |
| `/tc:learn` | `tc-learning` | 8 |
| `/tc:learn-from-failures` | `tc-learning` | 8 |
| `/tc:learn-from-exploration` | `tc-learning` | 8 |
| `/tc:learn-from-feedback` | `tc-learning` | 8 |
| `/tc:review-lessons` | `tc-learning` | 8 |
| `/tc:promote-lessons` | `tc-learning` | 8 |
| `/tc:visualize`, `/tc:diagram-*` | `tc-visualize` | 9 |
| `/tc:generate-infographic` | `tc-visualize` | 9 |
| `/tc:render-visuals` | `tc-visualize` | 9 |
| `/tc:web-*` | `tc-web` | 10 |
| `/tc:sandbox-*` | `tc-sandbox` | 12 |
| `/tc:watch-changes`, continuous-quality | `tc-continuous-quality` | 13 |
