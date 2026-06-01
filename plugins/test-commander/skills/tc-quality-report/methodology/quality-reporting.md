# Quality reporting methodology

How `/tc:report` aggregates the whole workspace into a single living quality
report - and why every number in it is traceable to an artifact.

## The section catalog

The report carries fifteen sections, in this order:

1. **Executive summary** - the one-paragraph posture.
2. **Coverage** - how much of the requirement space is exercised.
3. **Requirements readiness** - are the requirements testable and complete.
4. **Exploratory findings** - what the exploration sessions surfaced.
5. **Automated regression status** - the latest run's pass/fail/flaky picture.
6. **Known risks** - the risk register.
7. **Known defects** - the failing tests in the latest run.
8. **Open questions** - unresolved questions routed by the review commands.
9. **Automation health** - the automation review verdict.
10. **Flaky tests** - the pass-on-retry results.
11. **Evidence summary** - the indexed evidence artifacts.
12. **Traceability summary** - the requirement -> result chain.
13. **Recommendations** - proposed next actions.
14. **Release readiness** - the gate verdict and the human sign-off.
15. **Recent changes** - the recent runs.

## Facts, interpretation, and human review - kept separate

Every section is tagged with its dominant content class, and individual lines
carry the class inline:

- `[fact]` - measured directly from a workspace artifact. The number came from
  somewhere you can open and check.
- `[interpretation]` - synthesis a human (or Claude) adds. Not a measured value.
- `[review]` - an item that needs human review before release.

This separation is the report's core discipline: a reader must never mistake a
synthesized conclusion for a measured fact. The mechanical helper fills every
`[fact]`; Claude fills the `[interpretation]` and resolves the `[review]` items.

## Never invent metrics

A `[fact]` line is only ever populated from an artifact. When the source is
absent, the section reads `_None recorded._` (or `_no run yet_`) - never a
guessed or zero-by-assumption value. If a section says "0 open questions", it is
because `requirements/open-questions.md` was read and parsed, not assumed.

## History snapshots

Each run writes `quality-report/current-quality-report.md` (replaced in full)
and a byte-identical snapshot to `quality-report/history/<YYYY-MM-DD-HHmm>.md`
(Q3: full snapshot, not a diff; Q10: kept forever in git). The snapshot filename
comes from an injected clock, so the same inputs and clock produce a
byte-identical current report and snapshot - the report is safe to commit and
diff like any other source artifact.

## Resolving the traceability chain

After writing the report, `/tc:report` rebuilds the traceability maps so
`traceability/test-map.md` resolves its `Test result` column (from the run
records) and its `Quality report` column (now that this report exists) from
`pending` - the columns Phase 6 left pending. The full chain
(Requirement -> Test idea -> BDD scenario -> Automated test -> Test result ->
Quality report) is now complete end to end.

## The Claude judgment layer

The helper is mechanical and conservative: it counts, aggregates, and tags. The
report is only half-finished until Claude:

- writes the executive summary and recommendations from the facts;
- decides which defects and open questions are release-blocking;
- interprets a `flaky` rate as a determinism debt rather than a pass;
- frames release readiness for the audience (the gate gives PASS/WARN/FAIL; the
  human decides what to do about it).
