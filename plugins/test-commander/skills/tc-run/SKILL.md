---
name: tc-run
description: Test execution and failure analysis for Test Commander. Use when the user runs /tc:run or /tc:analyze-results, or asks about executing the generated Playwright and Postman suites in a chosen run mode, capturing per-run records that map results back to scenarios and requirements, triaging failures, or detecting flaky tests. Owns the two commands that run the automated suite and analyze the results, the project's first commands that execute rather than generate.
---

# tc-run

The test-execution skill for Test Commander. Owns the two commands that run the generated automated suite and analyze its results, mapping every result back to the scenario and requirement it exercises. This is the first Test Commander skill that **executes** rather than generates: real runs shell out to `npx playwright test` (and the `postman` CLI for the API path), while the result-ingestion and analysis logic stays hermetic and is fully testable against a recorded report.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Status

Phase 7 (Step 7.2). `/tc:run` is end-to-end runnable; `/tc:analyze-results` is registered but not yet shipped:

- `/tc:run` — **shipped (Step 7.2; evidence auto-index wired in Step 7.3).** Executes the generated suite for the requested run mode (or ingests a recorded Playwright JSON report with `--report`) and writes a per-run record under `<workspace>/runs/<RUN-ID>/` mapping each result to its scenario, candidate, requirement, and spec via `@req:`/`@cs:` provenance and the Phase-6 `automation-map.md`. Real execution is refused under pytest (the hermetic boundary). Upstream is read-only. After writing the record it auto-runs the `tc-evidence` indexer (routing artifacts into `evidence/` and rebuilding `evidence/evidence-index.md`); pass `--no-index` to suppress it.
- `/tc:analyze-results` — behavior arrives in Step 7.4. It will classify each failure against a universal triage rubric (product-defect, test-defect, environment, flaky), detect flaky tests from the pass-on-retry signal, and route confirmed gaps to `requirements/open-questions.md` as deduplicated `[test-analysis]` signals.

When Step 7.4 lands, this SKILL.md is updated to describe the shipped `/tc:analyze-results` behavior and the deferral wording above is removed.

## Commands

### `/tc:run`

Executes the generated automated suite for a chosen run mode — `all` (default), `smoke`, `regression`, `feature` (with `--area`), `failed-only`, or `tagged` (with `--tag`) — or ingests a recorded Playwright JSON report with `--report`. Ingests the report into a per-run record under `<workspace>/runs/<RUN-ID>/` (`run.md` plus `results.json`), mapping each `passed` / `failed` / `flaky` result to its requirement, candidate, scenario, and spec via the report's `@req:`/`@cs:` tags and `traceability/automation-map.md`. Deterministic via an injected clock (`--now`): the same report plus the same clock produce a byte-identical record. Writes only under `runs/<RUN-ID>/` — `automation-map.md` and the generated specs are read-only.

**Run:**

```sh
python3 <plugin-root>/scripts/run_tests.py <project-root> [--mode all|smoke|regression|feature|failed-only|tagged] [--area <slug>] [--tag <tag>] [--report <playwright-json>] [--now <ISO-8601>] [--no-index]
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2) and refuses the real `npx playwright test` invocation under pytest (exit 2; the message directs the caller to pass `--report`). After writing the record it auto-runs the `tc-evidence` indexer; `--no-index` suppresses it.

Full spec: [commands/run.md](commands/run.md). Methodology: [methodology/test-execution.md](methodology/test-execution.md).

### `/tc:analyze-results`

Triages failures and flags flaky tests from the recorded run records. Full behavior is documented in the per-command page once Step 7.4 ships the helper.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-quality-report skill](../tc-quality-report/SKILL.md)
- [tc-evidence skill](../tc-evidence/SKILL.md)
- [tc-automate skill](../tc-automate/SKILL.md)
