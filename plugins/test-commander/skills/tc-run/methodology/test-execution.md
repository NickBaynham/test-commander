# Test execution methodology

How `/tc:run` turns the generated Playwright suite into a captured, traceable
per-run record - and why the test suite that defends it never launches a
browser.

## The hermetic boundary

`/tc:run` has two responsibilities separated by a hard boundary:

- **Execution** (the operator's environment) shells out to `npx playwright
  test` - and, for the API path, the `postman` CLI - to produce a Playwright
  JSON report.
- **Ingestion** (always hermetic) reads a JSON report and writes the per-run
  record.

The execution path is **refused under pytest** via the `PYTEST_CURRENT_TEST`
environment variable (the same guard Phase 3's `/tc:learn-from-api` and Phase
4's `/tc:explore` use for live mode). This keeps the project's "no executable
runtime in tests" property intact even now that the *artifacts* are runnable:
the unit suite exercises only the ingestion logic, against a **recorded report
fixture** passed with `--report`. A real run is the operator's job, in the
operator's environment.

## Run modes

A run mode selects which results are captured into the record:

| Mode | Selects |
| --- | --- |
| `all` (default) | every result. |
| `smoke` | scenarios tagged `@smoke`. |
| `regression` | scenarios tagged `@regression`. |
| `feature` | scenarios tagged `@area:<slug>` (requires `--area`). |
| `failed-only` | results whose status is `failed` (re-run the failures). |
| `tagged` | scenarios carrying an arbitrary `--tag`. |

The class tags (`@smoke`, `@regression`), the `@area:` namespace, and the
`@req:`/`@cs:` provenance all originate upstream - `/tc:generate-bdd` stamps
them onto the scenarios and `/tc:automate` carries them into the generated
specs and the automation map. `/tc:run` reads them; it never invents them.

## The result schema

The helper reads the standard Playwright JSON reporter shape - `suites[] ->
specs[] -> tests[] -> results[]` - and normalizes each test to a universal
result class:

- test status `expected` -> `passed`; `unexpected` -> `failed`; `flaky` stays
  `flaky` (a `retry: 0` failure followed by a `retry: 1` pass).
- the retry count is the highest `retry` index across the test's attempts.
- `@req:`/`@cs:` come from the spec's `tags`; the spec path comes from the
  Phase-6 `automation-map.md` (`@cs:` -> spec), falling back to the report's
  own file.

The per-run record is two files under `runs/<RUN-ID>/`: `run.md` (the
human-readable summary table) and `results.json` (the structured record that
`/tc:analyze-results` and the `tc-evidence` indexer consume).

## Injected-clock determinism

`RUN-ID` is `RUN-<YYYYMMDD>-<HHMMSS>`. A timestamp in a filename would break the
byte-determinism every prior phase relies on, so `run` takes an **injected
clock**: tests pass a fixed `--now`, so the record is byte-stable; production
defaults to the wall clock. The helper never calls `datetime.now()` at import
or inline - only as the default inside `run` when `now` is omitted. Re-running
with the same report and the same clock overwrites the record byte-for-byte.

## Read-only upstream

`/tc:run` writes only under `runs/<RUN-ID>/`. It never mutates
`automation-map.md`, the generated specs, or any other upstream artifact - the
run is an observation, not an edit.

## The Claude judgment layer

The helper is mechanical: it ingests, classifies, filters, and records. Claude
adds the judgment the mechanics cannot:

- deciding *which* run mode answers the question at hand (a smoke gate before a
  merge vs. a full regression before a release vs. `failed-only` to confirm a
  fix);
- reading a `flaky` result as a signal to investigate determinism rather than a
  pass to celebrate;
- noticing when a requirement has automated scenarios that never appear in any
  run record (a coverage gap the raw numbers hide).

Evidence routing (screenshots, videos, traces) is the `tc-evidence` indexer's
job, wired into `/tc:run` from Step 7.3; failure triage and flaky analysis are
`/tc:analyze-results` (Step 7.4).
