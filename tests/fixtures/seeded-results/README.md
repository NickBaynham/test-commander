# Seeded results fixture

This directory is the shared fixture for Phase 7 (`tc-run`, `tc-quality-report`,
`tc-evidence`). It is the recorded output of a Playwright run plus the upstream
Phase-6 chain that produced it, so the Phase 7 helpers can be tested against a
real result set **without ever launching a browser** (the hermetic boundary —
the real `npx playwright test` invocation is refused under pytest; the suite
exercises only the result-ingestion, evidence-routing, analysis, and reporting
logic). It is a **deliberately generic, universal SaaS narrative** (sign-in /
sessions), reusing the entity vocabulary of the earlier seeded fixtures so the
Phase 7 integration smoke composes without translation. Nothing here is a claim
about any real product's scope (per Decision D19).

## Files

| File | Role |
| --- | --- |
| `results.json` | A recorded Playwright JSON report carrying one `passed`, one `failed`, and one `flaky` (pass-on-retry) case, each with resolvable `@req:`/`@cs:` linkage. The input to `/tc:run`'s result ingestion and `/tc:analyze-results`. |
| `automation-map.md` | The Phase-6 `/tc:automate` map linking each scenario to its generated spec. The join `/tc:run` uses to map a result to its scenario and requirement. |
| `sign-in.spec.ts` | The generated spec the report's results belong to, carrying `// @req:`/`@cs:` provenance comments. |
| `evidence/` | Evidence stubs that exercise the commit-versus-ignore policy split. |
| `README.md` | This file. |

## Result schema

The report follows the Playwright JSON reporter shape: `suites[] -> specs[] ->
tests[] -> results[]`. A test's `status` is `expected` (passed), `unexpected`
(failed), or `flaky` (failed then passed on retry); each `results[]` attempt
carries a per-attempt `status` of `passed` or `failed` and a `retry` index. The
`flaky` case has a `retry: 0` failed attempt followed by a `retry: 1` passed
attempt — the pass-on-retry signal `/tc:analyze-results` keys on.

## Evidence-policy categories

The `evidence/` subtree exercises the Phase 7 policy split that the
`tc-evidence` indexer enforces:

- `evidence/screenshots/` — **committed.** A screenshot stub for the failed case.
- `evidence/videos/` — **git-ignored by default** (documented `git-lfs` opt-in). A video stub for the failed case.
- `evidence/traces/` — **git-ignored by default** (documented `git-lfs` opt-in). Trace stubs for the failed case and the flaky retry.

JSON/HTML reports (here, `results.json`) are committed and referenced from the
quality report. The stub files carry placeholder text, not real binary payloads
— the indexer routes by artifact type, not by content.

## Linkage-tag convention

Each result links back to its scenario and requirement through machine-readable
provenance carried in both the report and the generated spec:

- `@req:REQ-NNN` — the requirement the result traces to.
- `@cs:CS-NNN-NNN` — the candidate scenario the result realizes.

`/tc:run` joins a report entry to its requirement through `automation-map.md`
(scenario title -> requirement / candidate / spec) and the `@req:`/`@cs:`
provenance, so a per-run record maps every result to a requirement.
