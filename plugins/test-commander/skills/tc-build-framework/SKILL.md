---
name: tc-build-framework
description: Lazy Playwright/TypeScript framework scaffolding for Test Commander. Use when the user runs /tc:build-framework, or asks about creating the project-root tests/ tree (e2e, pages, components, fixtures, utils), playwright.config.ts, and package.json that Test Commander generates only when automation first needs them. Owns the single command that builds the automation framework idempotently and exposes the lazy-init entry point the other Phase 6 commands call before generating any TypeScript.
---

# tc-build-framework

The framework-bootstrap skill for Test Commander. Owns the one command that scaffolds the project-root Playwright/TypeScript framework lazily — built only when automation first needs it (Decision D8), and idempotent on re-run.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command page under `commands/` is the authoritative behavior spec — link the user there for full detail.

## Status

Phase 6 scaffold (Step 6.1). The command is registered but its behavior is not yet shipped:

- `/tc:build-framework` — behavior arrives in Step 6.2. It will scaffold the project-root `tests/{e2e,pages,components,fixtures,utils}/` tree plus `playwright.config.ts` and `package.json` from bundled TypeScript templates, only if `tests/playwright.config.ts` is absent, and re-run as a byte-stable no-op. Step 6.2 also exposes `ensure_framework(project_root)` as the lazy-init entry point `/tc:automate` calls first.

When Step 6.2 lands, this SKILL.md is updated to describe the shipped behavior and the deferral wording above is removed.

## Commands

### `/tc:build-framework`

Scaffolds the project-root automation framework lazily (only when absent) and idempotently. Full behavior is documented in the per-command page once Step 6.2 ships the helper.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-automate skill](../tc-automate/SKILL.md)
- [tc-automation-plan skill](../tc-automation-plan/SKILL.md)
