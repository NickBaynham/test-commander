# Test run RUN-20260601-093000

- Mode: all
- Generated: 2026-06-01T09:30:00 (injected clock)
- Results: 3 (passed: 1, failed: 1, flaky: 1)

> Evidence routed to `evidence/` and indexed in `evidence/evidence-index.md` by the `tc-evidence` indexer.

| requirement | candidate | scenario | spec | result | retries |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | CS-001-001 | Sign in with valid credentials | `tests/e2e/sign-in.spec.ts` | passed | 0 |
| REQ-001 | CS-001-002 | Sign in is rejected with an invalid password | `tests/e2e/sign-in.spec.ts` | failed | 0 |
| REQ-001 | CS-001-003 | Expired session routes the holder back to sign-in | `tests/e2e/sign-in.spec.ts` | flaky | 1 |
