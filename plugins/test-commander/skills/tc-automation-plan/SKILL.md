---
name: tc-automation-plan
description: Automation suitability planning for Test Commander. Use when the user runs /tc:automation-plan, or asks about scoring BDD scenarios for automation, ranking scenarios as automate, consider, or manual against a universal seven-factor suitability rubric, or deciding which reviewed scenarios are worth automating first. Owns the single command that scans the BDD feature files and writes a per-area automation plan with per-factor scores and a recommended order.
---

# tc-automation-plan

The automation-planning skill for Test Commander. Owns the one command that scores each reviewed BDD scenario against a universal seven-factor suitability rubric and writes a ranked, ordered automation plan — the strategic gate before any TypeScript is generated.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command page under `commands/` is the authoritative behavior spec — link the user there for full detail.

## Status

Phase 6 (Step 6.3). The command is end-to-end runnable:

- `/tc:automation-plan` — **shipped (Step 6.3).** Scans `<workspace>/bdd/features/*.feature`, scores each scenario against the seven-factor rubric, and writes `<workspace>/automation-plan/<area>.md` ranking scenarios `automate` / `consider` / `manual`.

## Commands

### `/tc:automation-plan`

Scans `<workspace>/bdd/features/*.feature` and scores each scenario against a universal seven-factor suitability rubric (`traceable`, `regression-value`, `risk-flagged`, `deterministic`, `right-sized`, `data-ready`, `persona-scoped`), then writes `<workspace>/automation-plan/<area>.md` ranking every scenario `automate` / `consider` / `manual` with its per-factor scores and a recommended order. Two hard overrides bypass the score: `@automated-candidate` always ranks `automate`; `@manual` always ranks `manual`. Deterministic (byte-identical re-run). The mechanical score is a first pass — Claude then reviews the plan against `product-knowledge/` and may promote or hold back a scenario with a note (the judgment layer). Suitability weights are tunable under `tc-automate.suitability.weights` in `<workspace>/config.yaml`.

**Run:**

```sh
python3 <plugin-root>/scripts/automation_plan.py <project-root>
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2); the absence of any `.feature` file is not an error (it reports "no scenarios to plan" and exits 0, directing the user at `/tc:generate-bdd`).

Full spec: [commands/automation-plan.md](commands/automation-plan.md). Methodology: [methodology/automation-suitability.md](methodology/automation-suitability.md).

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-automate skill](../tc-automate/SKILL.md)
- [tc-bdd skill](../tc-bdd/SKILL.md)
