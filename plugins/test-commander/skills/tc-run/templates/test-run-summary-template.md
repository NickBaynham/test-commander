# Test run <RUN-ID>

- Mode: <all | smoke | regression | feature | failed-only | tagged>
- Generated: <ISO-8601 timestamp> (injected clock)
- Results: <N> (passed: <a>, failed: <b>, flaky: <c>)

> Evidence indexing wires in Step 7.3 (`/tc:run` auto-runs the `tc-evidence` indexer; `--no-index` suppresses it).

| requirement | candidate | scenario | spec | result | retries |
| --- | --- | --- | --- | --- | --- |
| REQ-NNN | CS-NNN-NNN | <scenario title> | tests/e2e/<area>.spec.ts | passed | 0 |
| REQ-NNN | CS-NNN-NNN | <scenario title> | tests/e2e/<area>.spec.ts | failed | 0 |
| REQ-NNN | CS-NNN-NNN | <scenario title> | tests/e2e/<area>.spec.ts | flaky | 1 |

<!--
This is the shape /tc:run writes to runs/<RUN-ID>/run.md. Rows are sorted by
requirement, then candidate, then scenario, so a re-run with the same injected
clock is byte-identical. The companion runs/<RUN-ID>/results.json carries the
same data in machine-readable form for /tc:analyze-results and the tc-evidence
indexer.
-->
