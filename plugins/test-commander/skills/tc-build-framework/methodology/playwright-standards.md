# Playwright framework standards

How Test Commander structures the Playwright/TypeScript automation framework it
generates, and why. These conventions are universal (Decision D19): they
describe a generic web-app automation layout, not any product's surface.

## Lazy by design (D8)

The framework is built only when automation first needs it. `/tc:build-framework`
scaffolds it on demand, and `/tc:automate` calls `ensure_framework` before
generating any TypeScript, so a project that never automates never carries a
`tests/` tree. The `tests/playwright.config.ts` file is the sentinel: its
presence means the framework exists.

## Layout

The framework lands at the project root `tests/` tree, outside the
`.test-commander/` workspace (the cross-phase write boundary):

| Path | Holds |
| --- | --- |
| `tests/e2e/` | Specs - one `<area>.spec.ts` per `@area:` feature, one `test()` per scenario. |
| `tests/pages/` | Page objects - one per `@area:` namespace. Locators live here, never in specs. |
| `tests/components/` | Component objects - shared UI fragments (nav, dialogs, tables). |
| `tests/fixtures/` | Fixtures - the only path test data reaches a spec (D6). |
| `tests/db/` | Optional database-layer assertion helpers ([database-assertions.md](database-assertions.md)). |
| `tests/utils/` | Shared helpers. |
| `tests/playwright.config.ts` | Config: `testDir: './e2e'`, `PLAYWRIGHT_BASE_URL` target. |
| `tests/package.json` | `@playwright/test` + `typescript` dev deps; `test` scripts. |

## Every spec pairs a page object with a fixture

This is the framework's core shape, not a suggestion. A spec imports its page
object (locators and behavior methods) and its fixture (data and state); the body
expresses intent only. No locators in specs (they live in `tests/pages/`), no
inlined test data (it comes through a fixture, D6). The generated spec template
already shows this pairing; hand-written specs follow it.

## Test isolation on a shared backend

When the target keeps a database that persists between tests, every test must
start from a known state or tests leak into each other. The generated fixture
carries an auto `resetState` fixture that POSTs to a configured reset endpoint
(`PLAYWRIGHT_RESET_PATH`) before each test - on by setting the env var, a no-op
otherwise. A suite that shares one backend also runs sequentially (per project,
`fullyParallel: false` / `--workers=1`), because a reset that regenerates ids
would invalidate another test's fetched ids mid-run.

## Verify persistence at the database layer

Confirming the API response is not the same as confirming the write landed. Where
persistence or relationships are the risk, assert against the store directly via a
`tests/db/` helper - see [database-assertions.md](database-assertions.md).

## Idempotent and byte-stable

Every managed path is created only when absent. A re-run reports `created 0` and
leaves existing files byte-for-byte untouched, so the framework converges from a
partial state without clobbering user edits. Generated specs and page objects
(`/tc:automate`) preserve a user-edits region per the object templates.

## Generate and structurally validate; never run under pytest

The Python helpers generate TypeScript text; the test suite asserts the
generated files' *structure* (well-formed scaffolding, correct imports,
page-object / spec / fixture shape, `@req:`/`@cs:` provenance) by parsing the
rendered text. The suite never invokes `tsc` or `npx playwright test` and never
reaches a browser - that keeps it hermetic even though the artifacts are
executable. Real execution is Phase 7's `/tc:run`; a manual smoke against a
tester-supplied local app is opt-in and refused under pytest.

## Configuration

The target URL is read from the `PLAYWRIGHT_BASE_URL` environment variable so
the shipped config carries no product-specific host. A consuming project sets
its own base URL at run time and may extend the config after generation; the
scaffold never overwrites an edited `playwright.config.ts`.

## See also

- [Locator strategy](locator-strategy.md) - the locator priority order.
- [Database assertions](database-assertions.md) - the DB-layer verification pattern.
- [/tc:build-framework](../commands/build-framework.md) - the command spec.
- [Object templates](../templates/) - the v1 rendering contract.
