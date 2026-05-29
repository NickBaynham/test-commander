---
name: tc-test-data
description: Test-data generation for Test Commander. Use when the user runs /tc:generate-test-data, or asks about populating the workspace test-data directory from BDD scenarios and product-knowledge entities, producing declarative seed data, scenario data, and factories that generated fixtures reference, or keeping test data out of test code. Owns the single command that generates the test-data tree as Markdown specs, YAML manifests, and JSON fixtures that the generated automation reaches only through fixtures.
---

# tc-test-data

The test-data skill for Test Commander. Owns the one command that populates `<workspace>/test-data/` from the BDD scenarios and product-knowledge entities, so generated automation reaches its data only through fixtures and never inlines it (Decision D6).

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command page under `commands/` is the authoritative behavior spec — link the user there for full detail.

## Status

Phase 6 (Step 6.6). The command is end-to-end runnable:

- `/tc:generate-test-data` — **shipped (Step 6.6).** Populates `<workspace>/test-data/seed/<area>.json` and `test-data/scenarios/<area>.md` from the BDD scenarios so the per-area fixture `/tc:automate` generates reaches its data through a file (D6).

## Commands

### `/tc:generate-test-data`

Scans `<workspace>/bdd/features/*.feature` and, per `@area:`, writes `test-data/seed/<area>.json` (the JSON fixture the generated per-area fixture loads — one record per `@cs:` candidate) and `test-data/scenarios/<area>.md` (a Markdown spec of each scenario's declarative data requirement). Per Open Question Q11, declarative formats (JSON fixtures + Markdown specs) cover the universal case; hand-authored Python factories under `test-data/factories/` are the exception and are never written here. Overwrite mode for generated files (those carrying the generated marker); **skip-not-overwrite** for user-authored files (no marker), so hand-tuned data survives. Deterministic (byte-identical re-run). The shipped seed shape is universal (D19): generic records keyed by candidate id; Claude fleshes out realistic field values from `product-knowledge/`. This closes the D6 loop — the fixture's `test-data/seed/<area>.json` reference resolves to a real file, so no data is inlined in the spec.

**Run:**

```sh
python3 <plugin-root>/scripts/generate_test_data.py <project-root>
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2) and the absence of any `.feature` file (exit 2; the precondition error directs the user at `/tc:generate-bdd`).

Full spec: [commands/generate-test-data.md](commands/generate-test-data.md). Methodology: [methodology/test-data-strategy.md](methodology/test-data-strategy.md).

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-automate skill](../tc-automate/SKILL.md)
- [tc-knowledge skill](../tc-knowledge/SKILL.md)
