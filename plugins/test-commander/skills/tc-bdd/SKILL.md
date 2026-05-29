---
name: tc-bdd
description: BDD generation and review commands for Test Commander. Use when the user runs /tc:generate-bdd or /tc:review-bdd, or asks about turning reviewed requirements and Phase-4-enriched test ideas into Gherkin feature files, writing scenarios with behavior-not-UI steps, tagging scenarios with universal classes and project namespaces, or reviewing BDD specs for ambiguity and traceability. Owns the two commands that generate .feature files carrying machine-readable @req and @cs linkage tags and review them against a deterministic quality rubric, plus the internal review sub-mode that auto-runs at the end of generation.
---

# tc-bdd

The BDD-generation skill for Test Commander. Owns the two commands that turn Phase-2 reviewed requirements and Phase-4-enriched test-idea seeds into Gherkin `.feature` files with full traceability, then review those specs against a deterministic quality rubric.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Status

Phase 5 in progress. The commands ship sub-step by sub-step:

- `/tc:generate-bdd` — behavior ships in Step 5.2. Auto-runs the internal BDD review sub-mode at the end of generation (suppressible with `--no-review`).
- `/tc:review-bdd` — behavior ships in Step 5.3. Standalone, re-runnable review of already-written `.feature` files; shares one implementation with the generate-time review sub-mode.

Each sub-step ships the helper, methodology, template(s), and per-command page in a single commit, then updates this SKILL.md to describe the now-shipped behavior and remove the deferral wording for that command.

## Commands

### `/tc:generate-bdd`

Behavior arrives in Step 5.2. Will read the Phase-4-enriched test-idea seeds under `<workspace>/test-ideas/` plus the referenced session summaries under `<workspace>/sessions/` and Phase-3 product-knowledge for grounding, then write Gherkin `.feature` files under `<workspace>/bdd/features/`. Every scenario will carry machine-readable linkage tags (`@req:REQ-NNN`, `@cs:CS-NNN-NNN`) plus universal class tags and a project `@area:` tag, so `/tc:traceability-map` can rebuild the trace map mechanically. Also writes per-feature summaries under `<workspace>/bdd/summaries/`, rebuilds `<workspace>/bdd/index.md`, and auto-runs the review sub-mode.

### `/tc:review-bdd`

Behavior arrives in Step 5.3. Will read `<workspace>/bdd/features/*.feature` and run the six-category universal review rubric (`ambiguous-step`, `missing-tag`, `untraceable`, `ui-coupled-step`, `missing-examples`, `conjunction-overload`), writing a verdict into each feature's summary and routing failures to `<workspace>/requirements/open-questions.md` as `[bdd-review]` gap signals. The same implementation backs the review sub-mode that `/tc:generate-bdd` auto-runs.

## Finding the helpers

The helpers live at `scripts/<name>.py` relative to this plugin's root (the directory containing this SKILL.md is `<plugin-root>/skills/tc-bdd/`). In a development checkout that is `<repo>/plugins/test-commander/scripts/`. In the installed plugin cache it is `~/.claude/plugins/cache/test-commander-marketplace/test-commander/<version>/scripts/`. Either way, resolve the helper path relative to this SKILL.md's own location.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-traceability skill](../tc-traceability/SKILL.md)
- [tc-explore skill](../tc-explore/SKILL.md)
