# Quality gates methodology

How `/tc:quality-gate` turns the latest run and the quality report into a single
release-readiness verdict: PASS, WARN, or FAIL.

## The criteria

The gate evaluates four criteria over the latest `runs/<RUN-ID>/results.json`
record and `requirements/open-questions.md`:

| Criterion | Measured | Default threshold | Breach verdict |
| --- | --- | --- | --- |
| pass rate | `passed / total` | `>= min-pass-rate` (1.0) | FAIL |
| failed tests | count of `failed` results | `<= max-failed` (0) | FAIL |
| flaky tests | count of `flaky` results | `<= max-flaky` (0) | WARN |
| open questions | count in open-questions.md | `<= max-open-questions` (0) | WARN |

A breach of a **hard** criterion (pass rate, failed tests) is a `FAIL`; a breach
of a **soft** criterion (flaky tests, open questions) is a `WARN`. The overall
verdict is the worst per-criterion verdict (`PASS < WARN < FAIL`).

## PASS / WARN / FAIL

- **PASS** - every criterion is within threshold. The build is releasable on the
  measured evidence.
- **WARN** - no hard failure, but a soft criterion is breached (flaky tests, or
  unresolved open questions). Releasable with eyes open; the warning is recorded.
- **FAIL** - a hard criterion is breached (a failing test, or the pass rate is
  below the floor). Not releasable until addressed.

The CLI exits `0` for PASS/WARN and `1` for FAIL, so a CI pipeline can branch on
the gate directly. (A precondition failure - no workspace, no report - exits
`2`.)

## Never invent metrics

Every measured value is read from an artifact. When there is no run record, the
pass-rate criterion reads `n/a` and passes vacuously (nothing has failed) rather
than assuming a rate. The gate reports what was measured, not what is hoped.

## Project-tunable thresholds

The thresholds are universal defaults; a project tunes them under
`tc-quality-report.gate.thresholds` in `<workspace>/config.yaml`:

```yaml
tc-quality-report:
  gate:
    thresholds:
      min-pass-rate: 0.95      # allow a 5% transient-failure margin
      max-failed: 0            # but never ship a hard failure
      max-flaky: 3             # tolerate a few known-flaky tests (WARN above)
      max-open-questions: 10   # WARN above ten unresolved questions
```

Any unset key keeps its default. Unknown keys and unparseable values are
ignored (the gate falls back to the default for that criterion).

## Determinism

The verdict is derived purely from the run record and the open questions (no
clock), so a re-run over unchanged inputs produces a byte-identical
`quality-report/quality-gate.md`.

## The Claude judgment layer

The gate is mechanical and threshold-driven. Claude adds the judgment a fixed
threshold cannot:

- deciding whether a `WARN` is acceptable for this release or worth blocking on;
- recognizing that a passing gate over thin coverage is not the same as quality;
- weighing a known-flaky test that is `WARN`-ing against the risk it masks;
- recommending which thresholds a maturing project should tighten next.
