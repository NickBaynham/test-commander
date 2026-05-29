---
name: tc-automate
description: Playwright/TypeScript test generation and review for Test Commander. Use when the user runs /tc:automate or /tc:review-automation, or asks about generating page objects and specs from reviewed BDD scenarios, carrying requirement and candidate provenance into the generated TypeScript, reaching test data only through fixtures, or reviewing generated automation against a universal quality rubric. Owns the two commands that turn automate-ranked scenarios into structurally-valid TypeScript with full traceability and review that TypeScript for quality and provenance.
---

# tc-automate

The automation-generation skill for Test Commander. Owns the two commands that turn `automate`-ranked BDD scenarios into structurally-valid Playwright/TypeScript page objects and specs carrying full requirement-and-candidate provenance, then review that generated TypeScript against a universal quality rubric.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Status

Phase 6 (Step 6.5). Both commands are end-to-end runnable:

- `/tc:automate` — **shipped (Step 6.4).** Reads the automation plan plus `bdd/features/*.feature`, builds the framework lazily via `ensure_framework`, and renders page objects, per-area fixtures, and specs for `automate`-ranked / `@automated-candidate` scenarios with `@req:`/`@cs:` provenance and fixture-mediated data. Writes `traceability/automation-map.md`, then auto-runs the automation review (suppressible with `--no-review`).
- `/tc:review-automation` — **shipped (Step 6.5).** Standalone, re-runnable review of the generated `tests/e2e/*.spec.ts` against the six-category universal rubric; shares one implementation (`review_automation()`) with the generate-time auto-run.

## Commands

### `/tc:automate`

Reads the automation plan and `bdd/features/*.feature`, builds the framework lazily via `ensure_framework`, and renders, for every `automate`-ranked / `@automated-candidate` scenario with a resolvable `@req:`/`@cs:` linkage: a page object (`tests/pages/<AreaName>Page.ts`, with a preserved user-edits region), a per-area fixture (`tests/fixtures/<area>.ts`, reaching data only via the `.test-commander/test-data/` tree per D6), and a spec (`tests/e2e/<area>.spec.ts`, one `test()` per scenario opened by a `// @req:REQ-NNN @cs:CS-NNN-NNN` provenance comment). Writes `traceability/automation-map.md` linking each scenario to its spec (the Phase-6-owned map). Deterministic: overwrite mode for specs and fixtures, the page object's user-edits region carried forward, so a re-run with no edits is byte-identical. Writes only the project-root `tests/` tree and `automation-map.md` — never `bdd/` or `product-knowledge/`. No `tsc` or browser; execution is Phase 7's `/tc:run`. After writing the map it auto-runs the automation review (the same `review_automation()` `/tc:review-automation` uses), updating the review summary and routing findings to `requirements/open-questions.md`; pass `--no-review` to suppress it.

**Run:**

```sh
python3 <plugin-root>/scripts/automate.py <project-root> [--area <slug>] [--scenario "<name>"]
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2) and the absence of any real automation plan (exit 2; the precondition error directs the user at `/tc:automation-plan`).

Full spec: [commands/automate.md](commands/automate.md). Methodology: [methodology/automation-generation.md](methodology/automation-generation.md).

### `/tc:review-automation`

Reads `tests/e2e/*.spec.ts` and runs the six-category universal rubric (`inline-test-data`, `hardcoded-wait`, `missing-provenance`, `weak-locator`, `untraceable-spec`, `assertion-free`), one finding per category per spec. Writes a per-spec verdict to `<workspace>/automation-plan/review-summary.md` (`pass` or `N finding(s) - categories: ...`) and routes failures to `<workspace>/requirements/open-questions.md` as `[automation-review]` gap signals (per-spec source-id `tc-automate/automation-review-<area>`, Phase-2 dedup contract). A clean generated spec passes with zero findings; re-running is idempotent. The shared `review_automation()` implementation is the same code path `/tc:automate` auto-runs. The `untraceable-spec` check uses `traceability/automation-map.md`.

**Run:**

```sh
python3 <plugin-root>/scripts/review_automation.py <project-root>
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2) and the absence of any `tests/e2e/*.spec.ts` (exit 2; the precondition error directs the user at `/tc:automate`).

Full spec: [commands/review-automation.md](commands/review-automation.md). Methodology: [methodology/automation-review.md](methodology/automation-review.md).

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-automation-plan skill](../tc-automation-plan/SKILL.md)
- [tc-build-framework skill](../tc-build-framework/SKILL.md)
- [tc-test-data skill](../tc-test-data/SKILL.md)
