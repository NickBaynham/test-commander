# /tc:quality-gate

Evaluate the latest run and the quality report against project-defined
thresholds and return a release-readiness verdict: PASS, WARN, or FAIL.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- A generated quality report (`quality-report/current-quality-report.md`).
- The latest `runs/<RUN-ID>/results.json` record and
  `requirements/open-questions.md` (the measured values).
- Optional `tc-quality-report.gate.thresholds` in `<workspace>/config.yaml`.
- CLI: `<project-root>` (defaults to the current directory). No other flags.

## Outputs

- `<workspace>/quality-report/quality-gate.md` - the verdict and the
  per-criterion breakdown (pass rate, failed tests, flaky tests, open
  questions), each with its measured value, threshold, and verdict.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- A quality report has been generated. Otherwise exit 2 (the error directs the
  user at `/tc:report`).

## Behavior

1. **Resolve** the workspace and require a generated quality report.
2. **Load thresholds** from `tc-quality-report.gate.thresholds` merged over the
   universal defaults (`min-pass-rate` 1.0, `max-failed` 0, `max-flaky` 0,
   `max-open-questions` 0).
3. **Evaluate** four criteria over the latest run and the open questions:
   pass rate and failed tests are hard (breach -> FAIL); flaky tests and open
   questions are soft (breach -> WARN).
4. **Write** `quality-report/quality-gate.md` with the verdict (the worst
   per-criterion verdict, `PASS < WARN < FAIL`) and the breakdown.

Deterministic: the verdict is derived from the run record and open questions (no
clock), so a re-run over unchanged inputs is byte-identical.

## Safety

- Reads measured values and writes only `quality-report/quality-gate.md`. It
  never invents a metric - with no run record the pass-rate criterion reads
  `n/a` and passes vacuously.
- No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/quality_gate.py` (per D18).
- Run: `python3 <plugin-root>/scripts/quality_gate.py <project-root>`.
- Exposes `gate(project_root)` returning a `GateOutcome` (verdict and the
  per-criterion list).
- CLI exit codes: `0` for PASS/WARN, `1` for FAIL (so CI can branch on the
  gate), `2` for a precondition failure.

## Definition of Done

- Gate returns PASS / WARN / FAIL against the thresholds; uninitialized
  workspace refused (exit 2); no report refused (exit 2) pointing at
  `/tc:report`.
- Thresholds are config-tunable via `tc-quality-report.gate.thresholds`.
- Deterministic (byte-stable verdict file).
- `tc-quality-report/SKILL.md` describes the shipped `/tc:quality-gate` behavior.

## See also

- [Quality gates methodology](../methodology/quality-gates.md) - the criteria, the PASS/WARN/FAIL thresholds, the config schema, and the Claude judgment layer.
- [Quality gate template](../templates/quality-gate-template.md) - the verdict shape.
- [tc-quality-report skill](../SKILL.md)
- [/tc:report](report.md) - the report this gate evaluates.
- [Customizing for your project](../../../../../docs/user-guide/customizing-for-your-project.md) - tuning `tc-quality-report.gate.thresholds`.
