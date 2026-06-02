# Heuristics

Rules of thumb worth following next time — the kind of lesson `/tc:learn` and
`/tc:learn-from-feedback` capture as `heuristic`. Shipped universal starters; a
project's promoted guidance adds its own (this file is never auto-edited).

- **Smoke before merge, regression before release.** Match the run mode to the
  question being asked.
- **Triage every failure before trusting a verdict.** A red gate with no triage
  is noise; classify product-defect / test-defect / environment / flaky first.
- **One lesson per root cause.** Three flaky candidates with the same cause are
  one lesson — consolidate before promoting.
- **Quote the evidence.** A lesson with a `path:line` origin survives review; an
  opinion without one usually does not.
- **Prefer the smallest guidance that changes behavior.** A promoted lesson the
  team will actually follow beats an exhaustive one they will not.

Heuristics are advisory by design — they inform judgment, they do not gate
anything automatically.
