# Failure triage methodology

How `/tc:analyze-results` turns a run's raw pass/fail/flaky results into a
triaged analysis - so the team knows *why* a test failed, not just *that* it
did. Design reference: `agentic-playwright-automation:investigate-playwright-failure`.

## The universal triage rubric

Every non-passed result is classified into exactly one category. The mechanical
signals are read from the run record (`runs/<RUN-ID>/results.json`): the result
status and the failure error message `/tc:run` captured.

| Category | Mechanical signal | What it means | Worked example |
| --- | --- | --- | --- |
| `flaky` | the test passed on retry (status `flaky`) | non-determinism, not a real failure - but not trustworthy either | A scenario fails with `TimeoutError` on attempt 1, passes on attempt 2. Classified `flaky` regardless of the error text - the pass-on-retry signal wins. |
| `environment` | the error names an infra / network / timeout signal | the target environment, not the code, is the problem | `net::ERR_CONNECTION_REFUSED`, `navigation timeout`, `target closed`. The app was unreachable; re-run against a healthy environment before drawing conclusions. |
| `test-defect` | the error names a locator / selector / strict-mode problem | the test is wrong, not the product | `locator.click: strict mode violation: resolved to 2 elements`. The selector is ambiguous - fix the page object, not the app. |
| `product-defect` | the default for a genuine assertion failure | the product behaved differently from what the scenario asserts | `expect(received).toHaveText(expected)` with a content mismatch. The app is misbehaving; confirm the expected behavior or file a defect. |

Precedence for a genuine failure (status `failed`): `environment` → `test-defect`
→ `product-defect` (the default). A `flaky` status short-circuits to `flaky`
before the error text is consulted.

## What it writes

1. **`runs/<RUN-ID>/analysis.md`** - the per-run triage: a count line and a
   table of every non-passed result with its requirement, candidate, scenario,
   status, and classification. A clean (all-passed) run records that there were
   no failures.
2. **`requirements/open-questions.md`** - one deduplicated `[test-analysis]`
   signal per non-passed result, keyed by `source-id = tc-run/test-analysis-<CS>`
   and the question text (the Phase-2 dedup contract). The same scenario+category
   is one open question, not one-per-run, so re-analyzing a run - or hitting the
   same failure across runs - never spams the log.

## Determinism

The analysis is derived purely from the run record - there is no clock - so a
re-run over an unchanged record produces a byte-identical `analysis.md`, and the
open-questions routing adds nothing on the second pass.

## The Claude judgment layer

The rubric is mechanical and deliberately conservative: it keys on signals that
are present in the error text, and defaults an unrecognized assertion failure to
`product-defect`. Claude adds the judgment the mechanics cannot:

- distinguishing a *real* product defect from a stale assertion the requirement
  has outgrown (the test asserts old behavior; the product is correct);
- recognizing a `flaky` result as a determinism debt to pay down, not a pass;
- spotting an `environment` classification that is actually masking a real race
  condition in the product;
- deciding which triaged failures are release-blocking (feeding `/tc:report`
  and the quality gate) versus known-and-accepted.
