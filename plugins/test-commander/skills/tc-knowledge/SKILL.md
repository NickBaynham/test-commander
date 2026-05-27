---
name: tc-knowledge
description: Project-knowledge ingestion commands for Test Commander. Use when the user runs /tc:learn-from-docs, /tc:learn-from-specs, /tc:learn-from-code, /tc:learn-from-api, or /tc:learn-from-tests, or asks about building project knowledge, extracting entities, journeys, endpoints, modules, or test coverage from uploaded artifacts. Owns the five commands that turn the consuming project's documents, OpenAPI/Postman specs, source code, recorded API responses, and existing tests into structured knowledge artifacts under .test-commander/product-knowledge/.
---

# tc-knowledge

The project-knowledge skill for Test Commander. Owns the five commands that read uploaded source artifacts and populate `<workspace>/product-knowledge/` with per-source models (`documentation-model.md`, `spec-derived-model.md`, `code-derived-model.md`, `api-model.md`, `tests-coverage.md`) plus the cumulative cross-cutting artifacts (`entities.md`, `user-journeys.md`, `business-rules.md`, `assumptions.md`) and the synthesized `system-model.md`.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Status

Phase 3 is in progress. The skill scaffold and seeded sample-project fixture (Step 3.1) have shipped. Command behavior arrives in subsequent sub-steps:

- `/tc:learn-from-docs` — behavior arrives in Step 3.2.
- `/tc:learn-from-specs` — behavior arrives in Step 3.3.
- `/tc:learn-from-code` — behavior arrives in Step 3.4.
- `/tc:learn-from-api` — behavior arrives in Step 3.5.
- `/tc:learn-from-tests` — behavior arrives in Step 3.6.

Each sub-step ships the helper, methodology, template(s), and per-command page in a single commit, then updates this SKILL.md to describe the now-shipped behavior and remove the deferral wording for that command.

## Commands

### `/tc:learn-from-docs`

Behavior arrives in Step 3.2. Will extract entities, glossary terms, user journeys, business rules, and assumptions from non-requirements Markdown documents under `<workspace>/documents/uploaded/`, write `<workspace>/product-knowledge/documentation-model.md`, contribute `## From documents` sections to the cross-cutting artifacts, route knowledge gaps to `<workspace>/requirements/open-questions.md`, and regenerate `system-model.md`.

### `/tc:learn-from-specs`

Behavior arrives in Step 3.3. Will auto-detect OpenAPI 3 or Postman v2.1 collections under `<workspace>/documents/uploaded/`, extract endpoints, schemas, and auth schemes, write `<workspace>/product-knowledge/spec-derived-model.md`, contribute `## From specs` sections, append gap-signal questions for unspecified statuses and untyped schemas, and regenerate `system-model.md`.

### `/tc:learn-from-code`

Behavior arrives in Step 3.4. Will walk Python source under the configured code root using the stdlib `ast` module, extract modules / classes / functions / decorators / docstrings, write `<workspace>/product-knowledge/code-derived-model.md`, cross-check against `spec-derived-model.md` for unimplemented endpoints, count non-Python files as `language-unsupported-in-v1` gaps, contribute `## From code` sections, and regenerate `system-model.md`.

### `/tc:learn-from-api`

Behavior arrives in Step 3.5. Will probe a live or recorded API surface (default `recorded` mode reads `<workspace>/documents/uploaded/recorded-api/responses.json`; opt-in `live` mode probes a configured base URL — `live` is refused under the test harness), extract live endpoints / response shapes / auth-required signals, write `<workspace>/product-knowledge/api-model.md`, cross-check against `spec-derived-model.md` for unspecified endpoints and mismatched statuses, contribute `## From api` sections, and regenerate `system-model.md`.

### `/tc:learn-from-tests`

Behavior arrives in Step 3.6. Will walk pytest-style Python tests and Playwright spec files under the configured tests root, count test files and functions, cross-reference covered symbols against `code-derived-model.md`, write `<workspace>/product-knowledge/tests-coverage.md`, append `untested-function` gaps, contribute `## From tests` sections, and regenerate `system-model.md`.

## Finding the helpers

The helpers will live at `scripts/<name>.py` relative to this plugin's root (the directory containing this SKILL.md is `<plugin-root>/skills/tc-knowledge/`). In a development checkout that is `<repo>/plugins/test-commander/scripts/`. In the installed plugin cache it is `~/.claude/plugins/cache/test-commander-marketplace/test-commander/<version>/scripts/`. Either way, resolve the helper path relative to this SKILL.md's own location.

## What to do when a slash command fires

Until the per-command sub-steps land, invoking any `/tc:learn-from-*` command should produce a clear notice that the behavior arrives in the named sub-step and point the user at the phased plan. From Step 3.2 onward, this section will be replaced with per-command invocation guidance mirroring `tc-requirements/SKILL.md`'s shape: resolve the helper path, run via `Bash` against the project root, report the helper's output, and layer the relevant methodology's judgment narrative on top.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-core skill](../tc-core/SKILL.md)
- [tc-requirements skill](../tc-requirements/SKILL.md)
