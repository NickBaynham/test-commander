# Open questions

Append-only log of questions raised by tc-bdd and other commands. Deduplicated by source-id + question text.

- [tc-requirements/req-review-REQ-001] [requirements-review] testability: REQ-001 does not state the expected error copy for a rejected sign-in. _Resolved: the error must read "Invalid email or password"; add an explicit assertion._
- [tc-run/test-analysis-CS-001-003] [test-analysis] flaky: scenario 'Session expires after the idle timeout' is flaky (passed on retry) - investigate the non-determinism before trusting it.
