# /tc:report

Aggregate the whole workspace into a single living quality report, snapshot it
into a committed history, and resolve the downstream traceability columns.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- Whatever artifacts exist: the latest `runs/<RUN-ID>/` record, the evidence
  index, the requirements inventory, the open questions, the risk register, the
  traceability maps. Each is read defensively - a section with no real source
  reads `_None recorded._` (never a guessed value).
- CLI: `<project-root>` (defaults to the current directory), plus:
  - `--now <ISO-8601>` injected clock for a deterministic report and snapshot
    filename (defaults to the wall clock).

## Outputs

- `<workspace>/quality-report/current-quality-report.md` - the report, replaced
  in full each run, with all fifteen sections (executive summary, coverage,
  requirements readiness, exploratory findings, automated regression status,
  known risks, known defects, open questions, automation health, flaky tests,
  evidence summary, traceability summary, recommendations, release readiness,
  recent changes), keeping `[fact]` / `[interpretation]` / `[review]` content
  clearly separated.
- `<workspace>/quality-report/history/<YYYY-MM-DD-HHmm>.md` - a byte-identical
  full snapshot (Q3), kept forever in git (Q10).
- `<workspace>/traceability/test-map.md` - rebuilt so the `Test result` and
  `Quality report` columns resolve from `pending` (best effort; see Behavior).

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2. A report can be
  built before any test has run (the run-derived sections read "no run yet").

## Behavior

1. **Resolve** the workspace.
2. **Aggregate** every section from its artifact, tagging each line `[fact]`,
   `[interpretation]`, or `[review]`. Facts are measured; missing sources read
   `_None recorded._` (never invented).
3. **Write** `current-quality-report.md` and a byte-identical snapshot to
   `history/<YYYY-MM-DD-HHmm>.md`.
4. **Rebuild the traceability maps** so `test-map.md`'s `Test result` (from
   `runs/`) and `Quality report` (now that this report exists) columns resolve
   from `pending`. Best effort: skipped when the requirements inventory is not
   yet generated.

Deterministic: the same inputs plus the same injected clock produce a
byte-identical report and snapshot.

## Safety

- Replaces `current-quality-report.md` in full and appends a new history
  snapshot; it never deletes a prior snapshot. It reads every other artifact
  read-only.
- No network, no browser - aggregation is mechanical over committed artifacts.

## Implementation

- Helper: `plugins/test-commander/scripts/build_report.py` (per D18).
- Run: `python3 <plugin-root>/scripts/build_report.py <project-root> [--now <ISO-8601>]`.
- Exposes `build_report(project_root, *, now=None)` returning a `ReportOutcome`
  (report path, snapshot path, latest run id, section count).
- The `Test result` / `Quality report` resolution lives in `traceability_map`
  (`scan_run_results` + `quality_report_ref`, extending the Phase-6
  `render_test_map`); `/tc:report` calls it after writing the report.

## Definition of Done

- Report carries all fifteen sections with facts / interpretation / review
  separated; uninitialized workspace refused (exit 2).
- History snapshot written under the injected-clock filename, byte-identical to
  the current report.
- Deterministic (byte-stable re-run).
- `test-map.md` `Test result` + `Quality report` columns resolve once a run and
  this report exist.
- `tc-quality-report/SKILL.md` describes the shipped `/tc:report` behavior.

## See also

- [Quality reporting methodology](../methodology/quality-reporting.md) - the section catalog, the facts-vs-interpretation separation, the never-invent-metrics rule, the history discipline.
- [Quality report template](../templates/quality-report-template.md) - the report shape.
- [tc-quality-report skill](../SKILL.md)
- [/tc:run](../../tc-run/commands/run.md) and [/tc:analyze-results](../../tc-run/commands/analyze-results.md) - the run and triage the report aggregates.
- [tc-traceability skill](../../tc-traceability/SKILL.md) - the maps `/tc:report` rebuilds.
