---
name: tc-automation-plan
description: Automation suitability planning for Test Commander. Use when the user runs /tc:automation-plan, or asks about scoring BDD scenarios for automation, ranking scenarios as automate, consider, or manual against a universal seven-factor suitability rubric, or deciding which reviewed scenarios are worth automating first. Owns the single command that scans the BDD feature files and writes a per-area automation plan with per-factor scores and a recommended order.
---

# tc-automation-plan

The automation-planning skill for Test Commander. Owns the one command that scores each reviewed BDD scenario against a universal seven-factor suitability rubric and writes a ranked, ordered automation plan — the strategic gate before any TypeScript is generated.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command page under `commands/` is the authoritative behavior spec — link the user there for full detail.

## Status

Phase 6 scaffold (Step 6.1). The command is registered but its behavior is not yet shipped:

- `/tc:automation-plan` — behavior arrives in Step 6.3. It will scan `<workspace>/bdd/features/*.feature`, score each scenario against the seven-factor rubric (mechanical signals plus a Claude judgment layer), and write `<workspace>/automation-plan/<area>.md` ranking scenarios `automate` / `consider` / `manual`. Scenarios tagged `@automated-candidate` are always `automate`. Suitability weights are tunable under `tc-automate.suitability.weights` in `<workspace>/config.yaml`.

When Step 6.3 lands, this SKILL.md is updated to describe the shipped behavior and the deferral wording above is removed.

## Commands

### `/tc:automation-plan`

Scores and ranks BDD scenarios for automation suitability and writes a per-area plan. Full behavior is documented in the per-command page once Step 6.3 ships the helper.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-automate skill](../tc-automate/SKILL.md)
- [tc-bdd skill](../tc-bdd/SKILL.md)
