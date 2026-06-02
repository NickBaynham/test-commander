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

## Phase 7 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:run` | `tc-run` | [run.md](../plugins/test-commander/skills/tc-run/commands/run.md) |
| `/tc:analyze-results` | `tc-run` | [analyze-results.md](../plugins/test-commander/skills/tc-run/commands/analyze-results.md) |
| `/tc:report` | `tc-quality-report` | [report.md](../plugins/test-commander/skills/tc-quality-report/commands/report.md) |
| `/tc:quality-gate` | `tc-quality-report` | [quality-gate.md](../plugins/test-commander/skills/tc-quality-report/commands/quality-gate.md) |

`/tc:run` executes the generated suite (or ingests a recorded Playwright JSON report with `--report`) for a run mode — `all`, `smoke`, `regression`, `feature`, `failed-only`, `tagged` — and writes a per-run record under `runs/<RUN-ID>/` mapping each `passed` / `failed` / `flaky` result to its requirement, candidate, scenario, and spec; the real `npx playwright test` invocation is refused under pytest (the hermetic boundary). It auto-runs the `tc-evidence` indexer (`--no-index` to suppress), which routes screenshots (committed), videos, and traces (git-ignored via `evidence/.gitignore`, with a git-lfs opt-in) into `evidence/` and writes `evidence/evidence-index.md`. `/tc:analyze-results` triages every non-passed result (`product-defect` / `test-defect` / `environment` / `flaky`), writes `runs/<RUN-ID>/analysis.md`, and routes deduplicated `[test-analysis]` signals. `/tc:report` aggregates the workspace into `quality-report/current-quality-report.md` with all fifteen sections (keeping `[fact]` / `[interpretation]` / `[review]` separated), snapshots a full copy to `quality-report/history/<YYYY-MM-DD-HHmm>.md`, and rebuilds the traceability maps so `test-map.md`'s `Test result` and `Quality report` columns resolve from `pending`. `/tc:quality-gate` evaluates the latest run against `tc-quality-report.gate.thresholds` and returns PASS / WARN / FAIL (the CLI exits `1` on FAIL).

`/tc:run` and `/tc:report` take an injected clock (`--now`) for byte-stable artifacts. For the methodology, see [test-execution.md](../plugins/test-commander/skills/tc-run/methodology/test-execution.md), [failure-triage.md](../plugins/test-commander/skills/tc-run/methodology/failure-triage.md), [evidence-management.md](../plugins/test-commander/skills/tc-evidence/methodology/evidence-management.md), [quality-reporting.md](../plugins/test-commander/skills/tc-quality-report/methodology/quality-reporting.md), and [quality-gates.md](../plugins/test-commander/skills/tc-quality-report/methodology/quality-gates.md). End-to-end walkthroughs: [user-guide/running-tests.md](user-guide/running-tests.md) and [user-guide/quality-report.md](user-guide/quality-report.md).

## Phase 8 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:learn` | `tc-learning` | [learn.md](../plugins/test-commander/skills/tc-learning/commands/learn.md) |
| `/tc:learn-from-failures` | `tc-learning` | [learn-from-failures.md](../plugins/test-commander/skills/tc-learning/commands/learn-from-failures.md) |
| `/tc:learn-from-exploration` | `tc-learning` | [learn-from-exploration.md](../plugins/test-commander/skills/tc-learning/commands/learn-from-exploration.md) |
| `/tc:learn-from-feedback` | `tc-learning` | [learn-from-feedback.md](../plugins/test-commander/skills/tc-learning/commands/learn-from-feedback.md) |
| `/tc:review-lessons` | `tc-learning` | [review-lessons.md](../plugins/test-commander/skills/tc-learning/commands/review-lessons.md) |
| `/tc:promote-lessons` | `tc-learning` | [promote-lessons.md](../plugins/test-commander/skills/tc-learning/commands/promote-lessons.md) |

The four capture commands append `tc-lesson/v1` candidates to `learning/lessons-inbox.md` through one shared engine (monotonic `LESSON-NNN` ids, `(source, origin, summary)` dedup, `path:line` provenance): `/tc:learn` from a freeform `--note`, `/tc:learn-from-failures` from the Phase-7 `runs/<RUN-ID>/analysis.md` triage, `/tc:learn-from-exploration` from `exploration-notes/` anomalies and coverage gaps, and `/tc:learn-from-feedback` from resolved open questions and uploaded feedback. `/tc:review-lessons` classifies each candidate into `accepted` / `rejected` / `needs-human-review` (rubric: `severity: high` → needs-human-review; a summary already accepted → rejected; otherwise accepted) and clears the inbox. `/tc:promote-lessons` proposes by default and, only with `--apply` (the human-approval gate), moves accepted lessons into `learning/promoted-guidance.md` (`status: promoted`) and renders a `core-promotion-proposal.md` for any `core: true` lesson. The loop writes **only** under `learning/` — it never rewrites Test Commander's shipped methodology or any third-party skill (Open Question Q6). For the methodology, see [learning-loop.md](../plugins/test-commander/skills/tc-learning/methodology/learning-loop.md), [lesson-taxonomy.md](../plugins/test-commander/skills/tc-learning/methodology/lesson-taxonomy.md), and [improvement-governance.md](../plugins/test-commander/skills/tc-learning/methodology/improvement-governance.md). End-to-end walkthrough: [user-guide/learning-loop.md](user-guide/learning-loop.md).

## Phase 9 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:visualize` | `tc-visualize` | [visualize.md](../plugins/test-commander/skills/tc-visualize/commands/visualize.md) |
| `/tc:diagram-flow` | `tc-visualize` | [diagram-flow.md](../plugins/test-commander/skills/tc-visualize/commands/diagram-flow.md) |
| `/tc:diagram-sequence` | `tc-visualize` | [diagram-sequence.md](../plugins/test-commander/skills/tc-visualize/commands/diagram-sequence.md) |
| `/tc:diagram-state` | `tc-visualize` | [diagram-state.md](../plugins/test-commander/skills/tc-visualize/commands/diagram-state.md) |
| `/tc:diagram-architecture` | `tc-visualize` | [diagram-architecture.md](../plugins/test-commander/skills/tc-visualize/commands/diagram-architecture.md) |
| `/tc:diagram-risk` | `tc-visualize` | [diagram-risk.md](../plugins/test-commander/skills/tc-visualize/commands/diagram-risk.md) |
| `/tc:diagram-coverage` | `tc-visualize` | [diagram-coverage.md](../plugins/test-commander/skills/tc-visualize/commands/diagram-coverage.md) |
| `/tc:diagram-traceability` | `tc-visualize` | [diagram-traceability.md](../plugins/test-commander/skills/tc-visualize/commands/diagram-traceability.md) |
| `/tc:diagram-test-strategy` | `tc-visualize` | [diagram-test-strategy.md](../plugins/test-commander/skills/tc-visualize/commands/diagram-test-strategy.md) |
| `/tc:generate-infographic` | `tc-visualize` | [generate-infographic.md](../plugins/test-commander/skills/tc-visualize/commands/generate-infographic.md) |
| `/tc:render-visuals` | `tc-visualize` | [render-visuals.md](../plugins/test-commander/skills/tc-visualize/commands/render-visuals.md) |

Every visual is generated only from committed workspace artifacts and carries a `> Sources:` footer; a generator refuses (exit 2) a missing source and points at the producing command. `/tc:visualize` runs every diagram generator (skipping any whose source is absent); the eight `/tc:diagram-*` commands generate individual Mermaid diagrams under `visuals/mermaid/`; `/tc:generate-infographic` writes a brief + spec of measured facts under `visuals/infographic/`; and `/tc:render-visuals` renders the Mermaid sources to SVG/PNG via the Mermaid CLI (the only command that shells out — refused under pytest, graceful when the CLI is absent). End-to-end walkthrough: [user-guide/visuals.md](user-guide/visuals.md).

## Phase 10 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:web-init` | `tc-web` | [web-init.md](../plugins/test-commander/skills/tc-web/commands/web-init.md) |
| `/tc:web-start` | `tc-web` | [web-start.md](../plugins/test-commander/skills/tc-web/commands/web-start.md) |
| `/tc:web-sync` | `tc-web` | [web-sync.md](../plugins/test-commander/skills/tc-web/commands/web-sync.md) |
| `/tc:web-index-artifacts` | `tc-web` | [web-index-artifacts.md](../plugins/test-commander/skills/tc-web/commands/web-index-artifacts.md) |
| `/tc:web-export` | `tc-web` | [web-export.md](../plugins/test-commander/skills/tc-web/commands/web-export.md) |

The web console is a team-facing, **read-only and proposal-only** viewer over the workspace (a Next.js frontend + a FastAPI backend, brought up by `make run` on docker compose). `/tc:web-init` provisions the console config; `/tc:web-index-artifacts` and `/tc:web-sync` (re)build the SQLite index (a rebuildable derivative — the workspace stays authoritative); `/tc:web-start` brings the stack up; `/tc:web-export` writes a shareable static bundle. The console also ships a read-only chat that answers from the index and surfaces command **proposal cards** — it never changes the workspace or runs a command (execution is gated behind the Phase 10.5 governance pipeline). End-to-end walkthrough: [user-guide/web-console.md](user-guide/web-console.md); architecture: [web-console.md](web-console.md); API: [runtime-api.md](runtime-api.md).

## Phase 10.5 governance (shipped — no `/tc:*` commands)

`tc-governance` ships no `/tc:*` commands; it is the controlled-execution pipeline the console invokes through `POST /api/execute` (intent → command planner → permission policy → approval gate → bounded execution → output validation → audit log). Default deny: nothing above `read-only` runs without passing the policy engine and, where required, an approval gate, and the agent never sees the raw user prompt. Roles and approval policy are configured in `<workspace>/policy/permissions.yaml` and `approvals.yaml`. See [controlled-agent-execution.md](controlled-agent-execution.md), [security-and-permissions.md](security-and-permissions.md), [runtime-approval-flow.md](runtime-approval-flow.md), [agent-adapters.md](agent-adapters.md), and the tester guide [user-guide/governance.md](user-guide/governance.md).

## Phase 11 runtime integrations (shipped — no `/tc:*` commands)

`tc-mcp` ships no `/tc:*` commands; it exposes Test Commander to other tools and agents two ways, both governed by the Phase-10.5 pipeline (no direct-execution backdoor):

- the **Runtime API** (`apps/api`) — the Phase-10 read-only console API expanded with the `/api/runtime/` namespace: `GET /info` (the seven permission levels), `POST /plan` (a read-only dry run), `POST /execute` (governed execution). See [runtime-api.md](runtime-api.md).
- the **MCP server** (`apps/mcp`) — a schema-first Model Context Protocol server (`python -m tcmcp`, stdio) with three tools: `tc_status`, `tc_plan`, and `tc_run_command`. See [mcp-server.md](mcp-server.md).

The seven permission levels are enforced server-side on both front-ends; a destructive action is refused for an unauthorized role, and an approval with no approver is held. Integration walkthrough: [user-guide/integrating.md](user-guide/integrating.md).

## Phase 12 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:sandbox-init` | `tc-sandbox` | [sandbox-init.md](../plugins/test-commander/skills/tc-sandbox/commands/sandbox-init.md) |
| `/tc:sandbox-launch` | `tc-sandbox` | [sandbox-launch.md](../plugins/test-commander/skills/tc-sandbox/commands/sandbox-launch.md) |
| `/tc:sandbox-status` | `tc-sandbox` | [sandbox-status.md](../plugins/test-commander/skills/tc-sandbox/commands/sandbox-status.md) |
| `/tc:sandbox-sync` | `tc-sandbox` | [sandbox-sync.md](../plugins/test-commander/skills/tc-sandbox/commands/sandbox-sync.md) |
| `/tc:sandbox-stop` | `tc-sandbox` | [sandbox-stop.md](../plugins/test-commander/skills/tc-sandbox/commands/sandbox-stop.md) |
| `/tc:sandbox-export` | `tc-sandbox` | [sandbox-export.md](../plugins/test-commander/skills/tc-sandbox/commands/sandbox-export.md) |

A sandbox is an on-demand, team-accessible Test Commander environment launched from GitHub Actions and governed exactly as the local runtime is — the Phase-10.5 pipeline runs inside it, so a sandbox cannot execute above its approved level. Targeting is safe-by-default (allow-listed hosts, blocked private ranges). The provider abstraction (`sandbox/providers/`) backs the commands; the MVP default is docker-compose-local. Architecture: [sandboxed-environments.md](sandboxed-environments.md); workflow: [github-actions-sandbox.md](github-actions-sandbox.md); walkthrough: [user-guide/sandbox.md](user-guide/sandbox.md).

## Phase 13 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:watch-changes` | `tc-continuous-quality` | [watch-changes.md](../plugins/test-commander/skills/tc-continuous-quality/commands/watch-changes.md) |
| `/tc:impact-analysis` | `tc-continuous-quality` | [impact-analysis.md](../plugins/test-commander/skills/tc-continuous-quality/commands/impact-analysis.md) |
| `/tc:coverage-gap-analysis` | `tc-continuous-quality` | [coverage-gap-analysis.md](../plugins/test-commander/skills/tc-continuous-quality/commands/coverage-gap-analysis.md) |
| `/tc:propose-tests` | `tc-continuous-quality` | [propose-tests.md](../plugins/test-commander/skills/tc-continuous-quality/commands/propose-tests.md) |
| `/tc:create-test-pr` | `tc-continuous-quality` | [create-test-pr.md](../plugins/test-commander/skills/tc-continuous-quality/commands/create-test-pr.md) |
| `/tc:continuous-quality-check` | `tc-continuous-quality` | [continuous-quality-check.md](../plugins/test-commander/skills/tc-continuous-quality/commands/continuous-quality-check.md) |

Continuous quality mode watches application changes, maps them to impacted features, finds coverage gaps, proposes tests, and opens clearly-labeled PRs when the configured autonomy mode allows it. It runs the watch → analyze → propose → PR loop through the same Phase-10.5 pipeline; the autonomy mode (0–4) is a ceiling on what auto-approves, and `destructive`/`admin` never auto-approve. Architecture: [continuous-quality-agent.md](continuous-quality-agent.md); autonomy: [autonomy-levels.md](autonomy-levels.md); walkthrough: [user-guide/continuous-quality.md](user-guide/continuous-quality.md).

## All phases shipped

Phases 0–13 are complete. Test Commander ships the full workflow from workspace initialization through requirements, knowledge, exploration, BDD, automation, execution, learning, visualization, the web console, governance, the Runtime API + MCP server, sandboxes, and continuous quality.
