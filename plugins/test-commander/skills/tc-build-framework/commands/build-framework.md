# /tc:build-framework

Scaffold the project-root Playwright/TypeScript automation framework lazily
(Decision D8): the `tests/{e2e,pages,components,fixtures,utils}/` tree plus
`tests/playwright.config.ts` and `tests/package.json`. Built only when absent;
a re-run is a byte-stable no-op.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`). The framework
  itself lands at the project root `tests/` tree, outside the workspace.
- CLI: `<project-root>` (defaults to the current directory). No other flags.

## Outputs

- `tests/e2e/`, `tests/pages/`, `tests/components/`, `tests/fixtures/`,
  `tests/utils/` - the framework tree (each seeded with a `.gitkeep`).
- `tests/playwright.config.ts` - the Playwright config. Sets `testDir: './e2e'`
  and reads the target from the `PLAYWRIGHT_BASE_URL` environment variable.
- `tests/package.json` - declares `@playwright/test` and `typescript` dev
  dependencies and the `test` / `test:headed` / `report` scripts.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.

## Behavior

1. **Resolve** the workspace (refuse if `.test-commander/` is absent).
2. **Create each managed path only when absent.** Each subdirectory's
   `.gitkeep`, `playwright.config.ts`, and `package.json` is written only if it
   does not already exist; an existing path is reported skipped and left
   byte-for-byte untouched.
3. **Report** `created N, skipped M` and list each created path.

Idempotent and byte-stable: a re-run creates nothing (`created 0`); a partially
present tree converges without clobbering user edits. The
`tests/playwright.config.ts` sentinel is the lazy-init signal -
`ensure_framework(project_root)` short-circuits when it is present, so
`/tc:automate` can call it cheaply before every generation.

## Safety

- Writes only under the project-root `tests/` tree. Never writes
  `.test-commander/` (the workspace) and never overwrites an existing file.
- No network, no browser. The helper only writes TypeScript and JSON text - it
  never invokes `tsc` or `npx playwright test`. Execution is Phase 7's
  `/tc:run`.

## Implementation

- Helper: `plugins/test-commander/scripts/build_framework.py` (per D18).
- Run: `python3 <plugin-root>/scripts/build_framework.py <project-root>`.
- Exposes `ensure_framework(project_root)` - the lazy-init entry point the
  Phase 6.4 generator calls first. The four `.ts` object templates under
  [`templates/`](../templates/) are the v1 rendering contract `/tc:automate`
  consumes; `build_framework` itself renders `playwright.config.ts` and
  `package.json` inline.

## Definition of Done

- Framework builds lazily at the project-root `tests/` tree; uninitialized
  workspace refused (exit 2).
- Generated `playwright.config.ts` and the four object templates are
  structurally valid TypeScript; `package.json` is valid JSON declaring
  `@playwright/test`.
- Re-run is byte-stable (`created 0`).
- `tc-build-framework/SKILL.md` describes the shipped behavior.

## See also

- [Playwright standards](../methodology/playwright-standards.md) - framework layout, config conventions, the generate-and-structurally-validate discipline.
- [Locator strategy](../methodology/locator-strategy.md) - the locator priority order page objects follow.
- [Page object template](../templates/page-object-template.ts), [component object template](../templates/component-object-template.ts), [spec template](../templates/playwright-spec-template.ts), [fixture template](../templates/fixture-template.ts) - the v1 rendering contract for `/tc:automate`.
- [tc-build-framework skill](../SKILL.md)
- [tc-automate skill](../../tc-automate/SKILL.md) - the generator that calls `ensure_framework` first.
