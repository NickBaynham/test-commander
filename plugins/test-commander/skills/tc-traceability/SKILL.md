---
name: tc-traceability
description: Cross-cutting traceability mapping for Test Commander. Use when the user runs /tc:traceability-map, or asks about linking requirements to test ideas and BDD scenarios, rebuilding the requirements map, building a test map, or understanding which requirements have downstream coverage. Owns the command that scans the workspace, parses the @req and @cs linkage tags emitted into Gherkin feature files, and rebuilds the traceability maps with downstream links reported as pending until later phases populate them.
---

# tc-traceability

The cross-cutting traceability skill for Test Commander. Owns the command that ties every requirement to its test ideas and BDD scenarios, rebuilding the maps under `<workspace>/traceability/`.

The command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command page under `commands/` is the authoritative behavior spec — link the user there for full detail.

## Status

Phase 5 in progress. The command is end-to-end runnable:

- `/tc:traceability-map` — **shipped (Step 5.4).**

## Commands

### `/tc:traceability-map`

Scans `<workspace>/requirements/` (the requirement inventory), `<workspace>/test-ideas/` (Phase-4-enriched seeds), and `<workspace>/bdd/features/*.feature` (parsing the `@req:`/`@cs:` linkage tags `/tc:generate-bdd` emits), then rebuilds two maps under `<workspace>/traceability/`. `requirements-map.md` is the shared 4-column requirement-to-downstream view (REQ-ID / Test ideas / BDD features / Automation) rendered by the same `traceability_render.render_requirements_map` `/tc:requirements-coverage` uses — byte-identical whichever command wrote it, so there is no format drift. `test-map.md` is the new scenario-level chain (Requirement → Test idea (CS) → BDD scenario → Automated test → Test result → Quality report); the three downstream columns render `pending` and are never invented. From Phase 5 onward this command is the authoritative writer of both maps; the Phase-2 `/tc:requirements-coverage` write is a compatible interim seed. Overwrite mode, byte-deterministic. Reuses the Phase-2 `requirements_coverage` scanners and `review_bdd.parse_feature_file` for DRY.

**Run:**

```sh
python3 <plugin-root>/scripts/traceability_map.py <project-root>
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2) and a missing/ungenerated requirements inventory (exit 2; the precondition error directs the user at `/tc:review-requirements`). No `.feature` files is not an error — the requirements map still lists every requirement and the test map carries the empty-note.

The full traceability chain is: Requirement → Test Idea → BDD Scenario → Automation Candidate → Automated Test → Test Result → Quality Report. Phase 5 populates the first three links.

Full spec: [commands/traceability-map.md](commands/traceability-map.md). Methodology: [methodology/traceability.md](methodology/traceability.md).

## Finding the helper

The helper lives at `scripts/<name>.py` relative to this plugin's root (the directory containing this SKILL.md is `<plugin-root>/skills/tc-traceability/`). In a development checkout that is `<repo>/plugins/test-commander/scripts/`. In the installed plugin cache it is `~/.claude/plugins/cache/test-commander-marketplace/test-commander/<version>/scripts/`. Either way, resolve the helper path relative to this SKILL.md's own location.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-bdd skill](../tc-bdd/SKILL.md)
