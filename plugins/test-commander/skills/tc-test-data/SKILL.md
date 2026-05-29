---
name: tc-test-data
description: Test-data generation for Test Commander. Use when the user runs /tc:generate-test-data, or asks about populating the workspace test-data directory from BDD scenarios and product-knowledge entities, producing declarative seed data, scenario data, and factories that generated fixtures reference, or keeping test data out of test code. Owns the single command that generates the test-data tree as Markdown specs, YAML manifests, and JSON fixtures that the generated automation reaches only through fixtures.
---

# tc-test-data

The test-data skill for Test Commander. Owns the one command that populates `<workspace>/test-data/` from the BDD scenarios and product-knowledge entities, so generated automation reaches its data only through fixtures and never inlines it (Decision D6).

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command page under `commands/` is the authoritative behavior spec — link the user there for full detail.

## Status

Phase 6 scaffold (Step 6.1). The command is registered but its behavior is not yet shipped:

- `/tc:generate-test-data` — behavior arrives in Step 6.6. It will populate `<workspace>/test-data/{seed,scenarios,factories}/` from the BDD scenarios and product-knowledge entities (Markdown specs plus YAML manifests plus JSON fixtures per Open Question Q11; Python factories only where declarative is insufficient), overwriting generated data and preserving user-authored data.

When Step 6.6 lands, this SKILL.md is updated to describe the shipped behavior and the deferral wording above is removed.

## Commands

### `/tc:generate-test-data`

Populates the workspace test-data tree from BDD scenarios and product-knowledge entities, reached via fixtures. Full behavior is documented in the per-command page once Step 6.6 ships the helper.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-automate skill](../tc-automate/SKILL.md)
- [tc-knowledge skill](../tc-knowledge/SKILL.md)
