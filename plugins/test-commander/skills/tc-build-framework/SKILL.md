---
name: tc-build-framework
description: Lazy Playwright/TypeScript framework scaffolding for Test Commander. Use when the user runs /tc:build-framework, or asks about creating the project-root tests/ tree (e2e, pages, components, fixtures, utils), playwright.config.ts, and package.json that Test Commander generates only when automation first needs them. Owns the single command that builds the automation framework idempotently and exposes the lazy-init entry point the other Phase 6 commands call before generating any TypeScript.
---

# tc-build-framework

The framework-bootstrap skill for Test Commander. Owns the one command that scaffolds the project-root Playwright/TypeScript framework lazily — built only when automation first needs it (Decision D8), and idempotent on re-run.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command page under `commands/` is the authoritative behavior spec — link the user there for full detail.

## Status

Phase 6 (Step 6.2). The command is end-to-end runnable:

- `/tc:build-framework` — **shipped (Step 6.2).** Scaffolds the project-root `tests/{e2e,pages,components,fixtures,utils}/` tree plus `playwright.config.ts` and `package.json`, creating each managed path only when absent so a re-run is a byte-stable no-op. Exposes `ensure_framework(project_root)` as the lazy-init entry point `/tc:automate` calls first.

## Commands

### `/tc:build-framework`

Scaffolds the project-root Playwright/TypeScript framework lazily (Decision D8): the `tests/{e2e,pages,components,fixtures,utils}/` tree, `tests/playwright.config.ts` (`testDir: './e2e'`, target from the `PLAYWRIGHT_BASE_URL` environment variable), and `tests/package.json` (declaring `@playwright/test` and `typescript`). Each path is created only when absent — a re-run reports `created 0` and leaves existing files byte-for-byte untouched, and a partial tree converges without clobbering user edits. The framework lands at the project root `tests/` tree, *outside* the `.test-commander/` workspace.

The helper only writes TypeScript and JSON text — it never invokes `tsc` or `npx playwright test` and never reaches a browser. Execution is Phase 7's `/tc:run`. The four `.ts` object templates under [`templates/`](templates/) are the v1 rendering contract `/tc:automate` consumes.

**Run:**

```sh
python3 <plugin-root>/scripts/build_framework.py <project-root>
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2). `ensure_framework(project_root)` is the lazy-init entry point importable by the Phase 6.4 generator.

Full spec: [commands/build-framework.md](commands/build-framework.md). Methodology: [methodology/playwright-standards.md](methodology/playwright-standards.md), [methodology/locator-strategy.md](methodology/locator-strategy.md).

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-automate skill](../tc-automate/SKILL.md)
- [tc-automation-plan skill](../tc-automation-plan/SKILL.md)
