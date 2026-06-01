# /tc:analyze-results

Triage the results of a test run: classify every non-passed result against the
universal rubric (product-defect / test-defect / environment / flaky), write a
per-run `analysis.md`, and route deduplicated `[test-analysis]` gap signals to
`requirements/open-questions.md`.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- A `/tc:run` record under `runs/<RUN-ID>/results.json` (carrying each result's
  status, retry count, and failure error message).
- CLI: `<project-root>` (defaults to the current directory), plus:
  - `--run-id <RUN-ID>` the run to analyze (default: the latest run).

## Outputs

- `<workspace>/runs/<RUN-ID>/analysis.md` - the per-run triage: a count line and
  a table of every non-passed result with its requirement, candidate, scenario,
  status, and classification.
- `<workspace>/requirements/open-questions.md` - one deduplicated
  `[test-analysis]` signal per non-passed result.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- At least one run record exists under `runs/`. Otherwise exit 2 (the error
  directs the user at `/tc:run`).

## Behavior

1. **Resolve** the workspace and the run (the named `--run-id`, or the latest).
2. **Triage** each result: a `flaky` status is `flaky` (pass-on-retry); a
   `failed` status is `environment` (infra/timeout error), `test-defect`
   (locator/selector error), or `product-defect` (the default assertion
   failure). Passed results are not triaged.
3. **Write** `runs/<RUN-ID>/analysis.md`.
4. **Route** a deduplicated `[test-analysis]` signal per non-passed result to
   `requirements/open-questions.md` (`source-id = tc-run/test-analysis-<CS>`,
   the Phase-2 dedup contract), so the same scenario+category is one open
   question, not one-per-run.

Deterministic: the analysis is derived from the run record (no clock), so a
re-run over an unchanged record is byte-identical and routes no duplicate
signals. A clean (all-passed) run produces no signals.

## Safety

- Reads the run record and writes only `runs/<RUN-ID>/analysis.md` and the
  append-only `requirements/open-questions.md`. It never mutates the results,
  the specs, or the automation map.
- No network, no browser - the triage is mechanical over the recorded report.

## Implementation

- Helper: `plugins/test-commander/scripts/analyze_results.py` (per D18).
- Run: `python3 <plugin-root>/scripts/analyze_results.py <project-root> [--run-id <RUN-ID>]`.
- Exposes `analyze(project_root, *, run_id=None)` returning an `AnalyzeOutcome`
  (run id and per-result classifications).
- The rubric (`classify`) keys on the result status and the failure error text
  `/tc:run` persists in `runs/<RUN-ID>/results.json`.

## Definition of Done

- Failures triaged and flaky tests flagged, each classified exactly once;
  uninitialized workspace refused (exit 2); no runs refused (exit 2) pointing at
  `/tc:run`.
- `[test-analysis]` signals routed and deduplicated; a clean run produces none.
- Deterministic (byte-stable re-run).
- `tc-run/SKILL.md` describes the shipped `/tc:analyze-results` behavior.

## See also

- [Failure triage methodology](../methodology/failure-triage.md) - the rubric categories with worked examples and the Claude judgment layer.
- [Analysis template](../templates/analysis-template.md) - the per-run analysis shape.
- [tc-run skill](../SKILL.md)
- [/tc:run](run.md) - the command that produces the run records this command reads.
