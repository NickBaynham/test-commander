# /tc:run

Execute the generated automated suite (or ingest a recorded Playwright JSON
report) for a chosen run mode, and write a per-run record under
`<workspace>/runs/<RUN-ID>/` that maps every result back to its scenario,
candidate, requirement, and spec.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- The Phase-6 chain the results belong to: `traceability/automation-map.md`
  (the `@cs:` -> spec join) and the generated `tests/e2e/*.spec.ts` at the
  project root.
- CLI: `<project-root>` (defaults to the current directory), plus:
  - `--mode {all,smoke,regression,feature,failed-only,tagged}` (default `all`).
  - `--area <slug>` (required for `--mode feature`).
  - `--tag <tag>` (required for `--mode tagged`).
  - `--report <path>` ingest a recorded Playwright JSON report instead of
    executing the suite (the hermetic path; also how an externally-produced
    report is ingested).
  - `--now <ISO-8601>` injected clock for a deterministic RUN-ID (defaults to
    the wall clock).
  - `--no-index` suppress the post-run `tc-evidence` indexing.

## Outputs

- `<workspace>/runs/<RUN-ID>/run.md` - the human-readable run summary: mode,
  totals (passed / failed / flaky), and a table mapping each result to its
  requirement, candidate, scenario, spec, status, and retry count.
- `<workspace>/runs/<RUN-ID>/results.json` - the machine-readable per-result
  record (the structured input `/tc:analyze-results` and the `tc-evidence`
  indexer consume).

`RUN-ID` is `RUN-<YYYYMMDD>-<HHMMSS>` from the clock.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- Either `--report <path>` points at a readable report, or the suite is
  executed. Real execution is **refused under pytest** (exit 2) - see Safety.

## Behavior

1. **Resolve** the workspace (refuse if `.test-commander/` is absent).
2. **Obtain a report.** With `--report`, read that Playwright JSON file. Without
   it, execute `npx playwright test` for the run mode and read the report it
   writes (refused under pytest).
3. **Ingest** the report: for each spec/test, derive the result class
   (`passed` / `failed` / `flaky`), the retry count, the `@req:`/`@cs:`
   provenance from the report's tags, and the spec path from
   `automation-map.md` (falling back to the report's file).
4. **Filter** by run mode (`smoke`/`regression` by class tag, `feature` by
   `@area:<slug>`, `failed-only` by status, `tagged` by an arbitrary tag).
5. **Write** the per-run record (`run.md` + `results.json`) under
   `runs/<RUN-ID>/`, results sorted by requirement, candidate, scenario.
6. **Index evidence** (unless `--no-index`): auto-run the `tc-evidence`
   indexer, which routes the run's artifacts into the `evidence/` tree per the
   commit-versus-ignore policy and rebuilds `evidence/evidence-index.md`.

Deterministic: the same report plus the same injected clock produce a
byte-identical record.

## Safety

- **Hermetic boundary.** The real `npx playwright test` (and `postman` for the
  API path) invocation is refused under pytest via the `PYTEST_CURRENT_TEST`
  guard, so the test suite never reaches a browser. Tests ingest a recorded
  report through `--report`.
- **Read-only upstream.** The helper never mutates `automation-map.md` or the
  generated specs. It writes only under `runs/<RUN-ID>/`.
- No network beyond the (operator-environment) Playwright run itself.

## Implementation

- Helper: `plugins/test-commander/scripts/run_tests.py` (per D18).
- Run: `python3 <plugin-root>/scripts/run_tests.py <project-root> [--mode ...] [--report ...] [--now ...]`.
- Exposes `run(project_root, *, mode, now, report, area, tag, no_index)`
  returning a `RunOutcome` (run id, mode, record dir, per-result records).
- After writing the record, `run` calls `index_evidence.index_run_evidence`
  (the `tc-evidence` indexer) to route screenshots / videos / traces into the
  `evidence/` tree and rebuild `evidence/evidence-index.md`, unless
  `--no-index` is passed.

## Definition of Done

- Recorded report ingested into a `runs/<RUN-ID>/` record mapping each result
  to its scenario via provenance; uninitialized workspace refused (exit 2).
- Real execution refused under pytest with a directing message.
- Run modes filter the result set; `feature`/`tagged` validate their argument.
- Re-run with the same injected clock is byte-stable.
- `tc-run/SKILL.md` describes the shipped `/tc:run` behavior.

## See also

- [Test execution methodology](../methodology/test-execution.md) - run modes, the hermetic boundary, the injected-clock contract, the result schema.
- [Run summary template](../templates/test-run-summary-template.md) - the per-run record shape.
- [tc-run skill](../SKILL.md)
- [tc-evidence skill](../../tc-evidence/SKILL.md) - the indexer `/tc:run` auto-runs from Step 7.3.
- [tc-automate skill](../../tc-automate/SKILL.md) - the generator that produces the specs and the automation map this command reads.
