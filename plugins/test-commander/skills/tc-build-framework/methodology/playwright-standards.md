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
| `tests/utils/` | Shared helpers. |
| `tests/playwright.config.ts` | Config: `testDir: './e2e'`, `PLAYWRIGHT_BASE_URL` target. |
| `tests/package.json` | `@playwright/test` + `typescript` dev deps; `test` scripts. |

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
- [/tc:build-framework](../commands/build-framework.md) - the command spec.
- [Object templates](../templates/) - the v1 rendering contract.
