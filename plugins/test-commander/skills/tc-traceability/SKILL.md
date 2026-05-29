---
name: tc-traceability
description: Cross-cutting traceability mapping for Test Commander. Use when the user runs /tc:traceability-map, or asks about linking requirements to test ideas and BDD scenarios, rebuilding the requirements map, building a test map, or understanding which requirements have downstream coverage. Owns the command that scans the workspace, parses the @req and @cs linkage tags emitted into Gherkin feature files, and rebuilds the traceability maps with downstream links reported as pending until later phases populate them.
---

# tc-traceability

The cross-cutting traceability skill for Test Commander. Owns the command that ties every requirement to its test ideas and BDD scenarios, rebuilding the maps under `<workspace>/traceability/`.

The command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command page under `commands/` is the authoritative behavior spec — link the user there for full detail.

## Status

Phase 5 in progress. The command ships in Step 5.4:

- `/tc:traceability-map` — behavior ships in Step 5.4.

## Commands

### `/tc:traceability-map`

Behavior arrives in Step 5.4. Will scan `<workspace>/requirements/` (the requirement inventory), `<workspace>/test-ideas/` (Phase-4-enriched seeds), and `<workspace>/bdd/features/*.feature` (parsing the `@req:`/`@cs:` linkage tags), then rebuild `<workspace>/traceability/requirements-map.md` (enriched with a BDD-scenario column) and write `<workspace>/traceability/test-map.md` (test idea to BDD scenario, with downstream links reported `pending`). It is the authoritative regenerator of those two maps from Phase 5 onward; the Phase-2 `requirements_coverage.py` write is reconciled via a shared render module so both callers produce byte-identical output. Downstream chain links (Automated Test, Test Result, Quality Report) render `pending` and are never invented.

The full traceability chain is: Requirement to Test Idea to BDD Scenario to Automation Candidate to Automated Test to Test Result to Quality Report. Phase 5 populates the first three links.

## Finding the helper

The helper lives at `scripts/<name>.py` relative to this plugin's root (the directory containing this SKILL.md is `<plugin-root>/skills/tc-traceability/`). In a development checkout that is `<repo>/plugins/test-commander/scripts/`. In the installed plugin cache it is `~/.claude/plugins/cache/test-commander-marketplace/test-commander/<version>/scripts/`. Either way, resolve the helper path relative to this SKILL.md's own location.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-bdd skill](../tc-bdd/SKILL.md)
