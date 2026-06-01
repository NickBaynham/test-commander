# Workflow — Running Tests (Phase 7)

This guide walks you through Test Commander's Phase 7 execution and reporting
commands end to end against a consuming project: `/tc:run` → (auto evidence
index) → `/tc:analyze-results` → `/tc:report` → `/tc:quality-gate`. The examples
use the deliberately-generic seeded fixture from
`tests/fixtures/seeded-results/` (a recorded Playwright run — one passed, one
failed, one flaky case — plus the Phase-6 chain that produced it), so every
output is reproducible.

For the report sections, history, and the gate, see the companion guide
[quality-report.md](quality-report.md).

## What's available in Phase 7

Phase 7 ships three skills that execute the generated suite, capture evidence,
and report quality:

| Command | Reads | Writes |
| --- | --- | --- |
| `/tc:run` | the generated suite (or a recorded report via `--report`) + `traceability/automation-map.md` | `runs/<RUN-ID>/run.md` + `runs/<RUN-ID>/results.json`; auto-runs the evidence indexer (`--no-index` to suppress) |
| `tc-evidence` indexer | `runs/<RUN-ID>/results.json` | routes artifacts into `evidence/{screenshots,videos,traces,logs}/`, writes `evidence/evidence-index.md` + `evidence/.gitignore` (no `/tc:*` command — invoked by `/tc:run`) |
| `/tc:analyze-results` | `runs/<RUN-ID>/results.json` | `runs/<RUN-ID>/analysis.md`; appends `[test-analysis]` gap signals to `requirements/open-questions.md` |
| `/tc:report` | the whole workspace | `quality-report/current-quality-report.md` + `quality-report/history/<YYYY-MM-DD-HHmm>.md`; rebuilds the traceability maps |
| `/tc:quality-gate` | the latest run + the quality report + `config.yaml` | `quality-report/quality-gate.md` (PASS / WARN / FAIL) |

Phase 7 is the first phase that **executes** rather than generates. Per Decision
D19 ([planning/plan.md](../../planning/plan.md)) the run modes, result schema,
triage rubric, evidence policy, report catalog, and gate criteria are universal;
only the gate thresholds tune via `<workspace>/config.yaml` — see
[customizing-for-your-project.md](customizing-for-your-project.md).

## The hermetic boundary

In real use `/tc:run` shells out to `npx playwright test` (and the `postman` CLI
for the API path). That real execution is **refused under pytest** (via the
`PYTEST_CURRENT_TEST` guard) so Test Commander's own test suite never launches a
browser. For a reproducible walkthrough — and for any CI that ingests an
externally-produced report — pass `--report <playwright-json>` to ingest a
recorded report instead of executing. Every example below uses `--report`.

## The traceability chain

```
Requirement -> Test Idea -> BDD Scenario -> Automation Candidate
            -> Automated Test -> Test Result -> Quality Report
```

Phase 7 fills the last two links: `/tc:run` records each result and `/tc:report`
rebuilds the maps, so `test-map.md`'s `Test result` (from `runs/`) and `Quality
report` (from `quality-report/`) columns resolve from `pending` — completing the
chain end to end.

## Prerequisites

1. `<workspace>/.test-commander/` exists (`/tc:init` has run — see
   [workflow.md](workflow.md)).
2. Phase 6 produced a generated spec and `traceability/automation-map.md`. See
   [automation.md](automation.md). The seeded
   `tests/fixtures/seeded-results/` is a worked example of a recorded run plus
   its upstream chain.

The natural order is Phase 6 → Phase 7: run only after the suite exists.

## Step 1: `/tc:run`

Executes the suite (or ingests a recorded report) for a run mode and writes a
per-run record mapping each result to its scenario, candidate, requirement, and
spec. The injected clock (`--now`) makes the `RUN-ID` deterministic.

```console
$ python3 <plugin-root>/scripts/run_tests.py . \
    --report results.json --now 2026-01-15T09:30:00
run: RUN-20260115-093000 (mode: all) - 3 result(s): passed 1, failed 1, flaky 1
  record: .test-commander/runs/RUN-20260115-093000
```

It writes `runs/RUN-20260115-093000/run.md` (the human summary) and
`results.json` (the machine-readable record), and — unless `--no-index` —
auto-runs the `tc-evidence` indexer, which routes the run's screenshots
(committed), videos, and traces (git-ignored) into `evidence/` and writes
`evidence/evidence-index.md`.

**Run modes** select which results are captured: `all` (default), `smoke`
(`@smoke`), `regression` (`@regression`), `feature` (`--area <slug>`),
`failed-only` (status), `tagged` (`--tag <tag>`).

## Step 2: `/tc:analyze-results`

Triages every non-passed result against the universal rubric — `flaky`
(pass-on-retry), `environment` (infra/timeout), `test-defect`
(locator/selector), `product-defect` (the default assertion failure) — writes
`runs/<RUN-ID>/analysis.md`, and routes deduplicated `[test-analysis]` signals.

```console
$ python3 <plugin-root>/scripts/analyze_results.py .
analyzed: RUN-20260115-093000 - 2 triaged (product-defect: 1, flaky: 1)
```

The failing assertion is classified `product-defect`; the pass-on-retry case is
`flaky`. The passed result is not triaged.

## Step 3: `/tc:report`

Aggregates the whole workspace into the quality report and snapshots it. See
[quality-report.md](quality-report.md) for the section catalog.

```console
$ python3 <plugin-root>/scripts/build_report.py . --now 2026-01-15T09:30:00
report: .test-commander/quality-report/current-quality-report.md
  snapshot: .test-commander/quality-report/history/2026-01-15-0930.md
```

`/tc:report` also rebuilds the traceability maps, so `test-map.md` now resolves
its downstream columns:

```text
| Requirement | Test idea | BDD scenario | Automated test | Test result | Quality report |
| REQ-001 | CS-001-001 | ... Sign in with valid credentials | `tests/e2e/sign-in.spec.ts` | passed | `quality-report/current-quality-report.md` |
| REQ-001 | CS-001-002 | ... rejected with an invalid password | `tests/e2e/sign-in.spec.ts` | failed | `quality-report/current-quality-report.md` |
| REQ-001 | CS-001-003 | ... Session expires after the idle timeout | `tests/e2e/sign-in.spec.ts` | flaky | `quality-report/current-quality-report.md` |
```

## Step 4: `/tc:quality-gate`

Evaluates the latest run against project thresholds and returns a verdict. The
CLI exits `1` on FAIL so CI can branch on it.

```console
$ python3 <plugin-root>/scripts/quality_gate.py .
quality gate: FAIL
  pass rate: 0.33 (>= 1) -> FAIL
  failed tests: 1 (<= 0) -> FAIL
  flaky tests: 1 (<= 0) -> WARN
  open questions: 0 (<= 0) -> PASS
```

The seeded run has a failing test, so it FAILs the default (zero-tolerance)
thresholds. Tune the bar under `tc-quality-report.gate.thresholds` — see
[customizing-for-your-project.md](customizing-for-your-project.md).

## Determinism

Every Phase 7 artifact is deterministic. `/tc:run` and `/tc:report` take an
injected clock (`--now`), so the RUN-ID, report timestamp, and history-snapshot
filename are byte-stable; `/tc:analyze-results` and `/tc:quality-gate` derive
their output purely from the records, so they need no clock. Re-running over
unchanged inputs produces byte-identical artifacts — the whole workspace is safe
to commit and diff.

## Customizing for your project

Phase 7 ships universal run modes, a universal evidence policy, a universal
triage rubric, a universal report catalog, and universal gate criteria. The only
`config.yaml` surface is `tc-quality-report.gate.thresholds` (the release bar);
the Playwright target is the `PLAYWRIGHT_BASE_URL` env var. See the "Phase 7
schema (`tc-quality-report`)" section of
[customizing-for-your-project.md](customizing-for-your-project.md).

## Beyond Phase 7

Phase 8 turns the workspace into a governed learning loop: lessons from
failures, exploration, and feedback are reviewed and promoted into project
guidance — nothing silently rewritten.

## See also

- [tc-run run command page](../../plugins/test-commander/skills/tc-run/commands/run.md)
- [tc-run analyze-results command page](../../plugins/test-commander/skills/tc-run/commands/analyze-results.md)
- [tc-evidence skill](../../plugins/test-commander/skills/tc-evidence/SKILL.md)
- [tc-quality-report report command page](../../plugins/test-commander/skills/tc-quality-report/commands/report.md)
- [tc-quality-report quality-gate command page](../../plugins/test-commander/skills/tc-quality-report/commands/quality-gate.md)
- [Quality report and gate (Phase 7)](quality-report.md)
- [Command reference](../command-reference.md)
- [Workspace reference](../workspace-reference.md)
- [Strategic automation (Phase 6)](automation.md) — produces the suite this phase runs.
