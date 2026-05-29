---
name: tc-automate
description: Playwright/TypeScript test generation and review for Test Commander. Use when the user runs /tc:automate or /tc:review-automation, or asks about generating page objects and specs from reviewed BDD scenarios, carrying requirement and candidate provenance into the generated TypeScript, reaching test data only through fixtures, or reviewing generated automation against a universal quality rubric. Owns the two commands that turn automate-ranked scenarios into structurally-valid TypeScript with full traceability and review that TypeScript for quality and provenance.
---

# tc-automate

The automation-generation skill for Test Commander. Owns the two commands that turn `automate`-ranked BDD scenarios into structurally-valid Playwright/TypeScript page objects and specs carrying full requirement-and-candidate provenance, then review that generated TypeScript against a universal quality rubric.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Status

Phase 6 scaffold (Step 6.1). Both commands are registered but their behavior is not yet shipped:

- `/tc:automate` — behavior arrives in Step 6.4. It will read the automation plan plus `bdd/features/*.feature`, build the framework lazily via `ensure_framework` first, render TypeScript page objects and specs for `automate`-ranked and `@automated-candidate` scenarios (each carrying a `@req:`/`@cs:` provenance comment and reaching data only via a fixture), and write `traceability/automation-map.md` linking scenario to spec.
- `/tc:review-automation` — behavior arrives in Step 6.5. It will review generated specs and page objects against a universal rubric and route failures to `requirements/open-questions.md` as `[automation-review]` gap signals. Step 6.5 also wires the same review as an auto-run at the end of `/tc:automate` (suppressible with `--no-review`).

When Steps 6.4 and 6.5 land, this SKILL.md is updated per command to describe the shipped behavior and remove the deferral wording for that command.

## Commands

### `/tc:automate`

Generates structurally-valid Playwright/TypeScript page objects and specs from `automate`-ranked scenarios with `@req:`/`@cs:` provenance and fixture-mediated data. Full behavior is documented in the per-command page once Step 6.4 ships the helper.

### `/tc:review-automation`

Reviews generated automation against a universal quality rubric and routes failures to open questions. Full behavior is documented in the per-command page once Step 6.5 ships the helper.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-automation-plan skill](../tc-automation-plan/SKILL.md)
- [tc-build-framework skill](../tc-build-framework/SKILL.md)
- [tc-test-data skill](../tc-test-data/SKILL.md)
