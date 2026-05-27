---
name: tc-requirements
description: Requirements quality, user-story, acceptance-criteria, coverage, and test-seed commands for Test Commander. Use when the user runs /tc:review-requirements, /tc:review-user-stories, /tc:review-acceptance-criteria, /tc:requirements-coverage, or /tc:requirements-to-tests, or asks about requirements quality, INVEST, acceptance criteria, or requirements traceability. Owns the five commands that turn uploaded requirements documents into reviewed artifacts and traceable test-idea seeds under .test-commander/requirements/ and .test-commander/test-ideas/.
---

# tc-requirements

The requirements-intelligence skill for Test Commander. Owns the five commands that review requirements, user stories, and acceptance criteria, compute coverage, and seed test ideas — before any automation exists.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). When the user invokes one of these slash commands, run the corresponding helper with `Bash` and report the output. The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Finding the helpers

The helpers live at `scripts/<name>.py` relative to this plugin's root (the directory containing this SKILL.md is `<plugin-root>/skills/tc-requirements/`). In a development checkout that is `<repo>/plugins/test-commander/scripts/`. In the installed plugin cache it is `~/.claude/plugins/cache/test-commander-marketplace/test-commander/<version>/scripts/`. Either way, resolve the helper path relative to this SKILL.md's own location.

## Commands

### `/tc:review-requirements`

Review uploaded requirements documents against the Test Commander rubric (clarity, testability, completeness, consistency, atomicity, measurability, dependencies, ambiguity, risk, NFRs, roles/permissions, data rules, automation suitability) and write a structured review.

Behavior arrives in Phase 2 Step 2.2. Until then, this command paragraph is a placeholder.

### `/tc:review-user-stories`

Review user stories against the INVEST rubric (Independent, Negotiable, Valuable, Estimable, Small, Testable) and the role-action-benefit shape.

Behavior arrives in Phase 2 Step 2.3. Until then, this command paragraph is a placeholder.

### `/tc:review-acceptance-criteria`

Review acceptance criteria for testability, edge-case coverage, negative-case coverage, data-rule clarity, and role/permission context.

Behavior arrives in Phase 2 Step 2.4. Until then, this command paragraph is a placeholder.

### `/tc:requirements-coverage`

Cross-reference requirement IDs with downstream artifacts (test ideas, BDD scenarios, automation candidates) and write a coverage matrix plus traceability updates.

Behavior arrives in Phase 2 Step 2.5. Until then, this command paragraph is a placeholder.

### `/tc:requirements-to-tests`

For every reviewed requirement, generate a seed test-idea file under `.test-commander/test-ideas/` with a schema Phase 4 will enrich.

Behavior arrives in Phase 2 Step 2.6. Until then, this command paragraph is a placeholder.

## What to do when a slash command fires

Until each command lands in its own Phase 2 sub-step, point the user at the planning entry in `planning/plan.md` (Phase 2 — Requirements and User Story Intelligence) and at the per-command page for the command they invoked, if it exists. Do not improvise behavior — the helpers are the source of truth and they arrive incrementally.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-core skill](../tc-core/SKILL.md)
