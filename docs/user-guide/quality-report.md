# Workflow — The Quality Report and Gate (Phase 7)

This companion to [running-tests.md](running-tests.md) covers what `/tc:report`
produces — the living quality report and its committed history — and how
`/tc:quality-gate` turns it into a release verdict.

## The report

`/tc:report` aggregates the whole workspace into a single page at
`<workspace>/quality-report/current-quality-report.md`, replaced in full each
run. It carries fifteen sections, in order:

1. Executive summary
2. Coverage
3. Requirements readiness
4. Exploratory findings
5. Automated regression status
6. Known risks
7. Known defects
8. Open questions
9. Automation health
10. Flaky tests
11. Evidence summary
12. Traceability summary
13. Recommendations
14. Release readiness
15. Recent changes

## Facts, interpretation, and review — kept separate

Every section is tagged with its content class, and key lines carry the class
inline:

- **`[fact]`** — measured directly from a workspace artifact.
- **`[interpretation]`** — synthesis a human or Claude adds; not a measured value.
- **`[review]`** — an item that needs human review before release.

This separation is the report's core discipline: a reader must never mistake a
synthesized conclusion for a measured fact. A representative excerpt from the
seeded run:

```markdown
## How to read this report

- **[fact]** - measured directly from a workspace artifact.
- **[interpretation]** - synthesis a human or Claude adds; not a measured value.
- **[review]** - an item that needs human review before release.

## Executive summary [interpretation]

_[fact]_ 1 requirement(s); latest run RUN-20260115-093000 (passed: 1, failed: 1, flaky: 1); 0 open question(s).

_[interpretation] Claude summarizes overall quality posture from the facts below._

## Automated regression status [fact]

Latest run: RUN-20260115-093000 - passed: 1, failed: 1, flaky: 1.
```

## Never invent metrics

A `[fact]` line is only ever populated from an artifact. When the source is
absent, the section reads `_None recorded._` (or `_no run yet_`) — never a
guessed value. The mechanical helper fills every `[fact]`; Claude writes the
`[interpretation]` and resolves the `[review]` items.

## History snapshots

Each run also writes a byte-identical full copy to
`quality-report/history/<YYYY-MM-DD-HHmm>.md` (the filename from the injected
clock). Snapshots are full copies (not diffs) and kept forever in git, so the
quality trend is auditable from history. Because the report is deterministic
under a fixed clock, snapshots diff cleanly.

## The quality gate

`/tc:quality-gate` evaluates the latest run against four criteria and returns
the worst verdict (`PASS < WARN < FAIL`):

| Criterion | Measured | Default | Breach |
| --- | --- | --- | --- |
| pass rate | `passed / total` | `>= 1.0` | FAIL |
| failed tests | count of `failed` | `<= 0` | FAIL |
| flaky tests | count of `flaky` | `<= 0` | WARN |
| open questions | count in open-questions.md | `<= 0` | WARN |

Pass rate and failed tests are **hard** (breach → FAIL); flaky tests and open
questions are **soft** (breach → WARN). The verdict and breakdown are written to
`quality-report/quality-gate.md`, and the CLI exits `1` on FAIL so a CI pipeline
can branch on it.

```console
$ python3 <plugin-root>/scripts/quality_gate.py .
quality gate: FAIL
  pass rate: 0.33 (>= 1) -> FAIL
  failed tests: 1 (<= 0) -> FAIL
  flaky tests: 1 (<= 0) -> WARN
  open questions: 0 (<= 0) -> PASS
```

Tune the bar under `tc-quality-report.gate.thresholds` in
`<workspace>/config.yaml` — a regulated platform keeps the zero-tolerance
defaults; an early-stage product allows a small transient margin. See the
"Phase 7 schema (`tc-quality-report`)" section of
[customizing-for-your-project.md](customizing-for-your-project.md).

## Visualizing the report

Phase 9's `tc-visualize` commands turn this report and its upstream artifacts
into diffable visuals: `/tc:generate-infographic` aggregates the report's
headline facts into an infographic brief + spec, and `/tc:diagram-coverage`,
`/tc:diagram-traceability`, and `/tc:diagram-risk` render the coverage map, the
traceability chain, and the risk register. See [visuals.md](visuals.md).

## See also

- [Visual documentation (Phase 9)](visuals.md) — diagrams and the quality infographic.
- [Running tests (Phase 7)](running-tests.md) — the run → analyze → report → gate walkthrough.
- [tc-quality-report report command page](../../plugins/test-commander/skills/tc-quality-report/commands/report.md)
- [tc-quality-report quality-gate command page](../../plugins/test-commander/skills/tc-quality-report/commands/quality-gate.md)
- [Quality reporting methodology](../../plugins/test-commander/skills/tc-quality-report/methodology/quality-reporting.md)
- [Quality gates methodology](../../plugins/test-commander/skills/tc-quality-report/methodology/quality-gates.md)
- [Command reference](../command-reference.md)
- [Workspace reference](../workspace-reference.md)
