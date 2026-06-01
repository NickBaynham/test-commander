---
name: tc-run
description: Test execution and failure analysis for Test Commander. Use when the user runs /tc:run or /tc:analyze-results, or asks about executing the generated Playwright and Postman suites in a chosen run mode, capturing per-run records that map results back to scenarios and requirements, triaging failures, or detecting flaky tests. Owns the two commands that run the automated suite and analyze the results, the project's first commands that execute rather than generate.
---

# tc-run

The test-execution skill for Test Commander. Owns the two commands that run the generated automated suite and analyze its results, mapping every result back to the scenario and requirement it exercises. This is the first Test Commander skill that **executes** rather than generates: real runs shell out to `npx playwright test` (and the `postman` CLI for the API path), while the result-ingestion and analysis logic stays hermetic and is fully testable against a recorded report.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Status

Phase 7 scaffold (Step 7.1). The two commands are registered but their behavior is not yet shipped:

- `/tc:run` — behavior arrives in Step 7.2. It will execute the generated suite for the requested run mode (smoke, regression, feature-specific, failed-only, tagged), ingest the Playwright JSON report, and write a per-run record under `<workspace>/runs/<RUN-ID>/` mapping each result to its scenario and requirement via `@req:`/`@cs:` provenance and the Phase-6 `automation-map.md`. Real execution is refused under pytest (the hermetic boundary); the evidence-index auto-run wires in Step 7.3.
- `/tc:analyze-results` — behavior arrives in Step 7.4. It will classify each failure against a universal triage rubric (product-defect, test-defect, environment, flaky), detect flaky tests from the pass-on-retry signal, and route confirmed gaps to `requirements/open-questions.md` as deduplicated `[test-analysis]` signals.

When Steps 7.2 and 7.4 land, this SKILL.md is updated to describe the shipped behavior and the deferral wording above is removed.

## Commands

### `/tc:run`

Executes the generated automated suite for a chosen run mode and writes a per-run record that maps each result to its scenario and requirement. Full behavior is documented in the per-command page once Step 7.2 ships the helper.

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
