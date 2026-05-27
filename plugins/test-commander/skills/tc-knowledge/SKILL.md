---
name: tc-knowledge
description: Project-knowledge ingestion commands for Test Commander. Use when the user runs /tc:learn-from-docs, /tc:learn-from-specs, /tc:learn-from-code, /tc:learn-from-api, or /tc:learn-from-tests, or asks about building project knowledge, extracting entities, journeys, endpoints, modules, or test coverage from uploaded artifacts. Owns the five commands that turn the consuming project's documents, OpenAPI/Postman specs, source code, recorded API responses, and existing tests into structured knowledge artifacts under .test-commander/product-knowledge/.
---

# tc-knowledge

The project-knowledge skill for Test Commander. Owns the five commands that read uploaded source artifacts and populate `<workspace>/product-knowledge/` with per-source models (`documentation-model.md`, `spec-derived-model.md`, `code-derived-model.md`, `api-model.md`, `tests-coverage.md`) plus the cumulative cross-cutting artifacts (`entities.md`, `user-journeys.md`, `business-rules.md`, `assumptions.md`) and the synthesized `system-model.md`.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Status

Phase 3 is in progress. The skill scaffold and seeded sample-project fixture (Step 3.1) have shipped. Step 3.2 has shipped `/tc:learn-from-docs` plus the shared `synthesize_system_model.py` helper. Command behavior arrives in subsequent sub-steps:

- `/tc:learn-from-docs` — **shipped (Step 3.2).**
- `/tc:learn-from-specs` — behavior arrives in Step 3.3.
- `/tc:learn-from-code` — behavior arrives in Step 3.4.
- `/tc:learn-from-api` — behavior arrives in Step 3.5.
- `/tc:learn-from-tests` — behavior arrives in Step 3.6.

Each sub-step ships the helper, methodology, template(s), and per-command page in a single commit, then updates this SKILL.md to describe the now-shipped behavior and remove the deferral wording for that command.

## Commands

### `/tc:learn-from-docs`

Reads every `*.md` under `<workspace>/documents/uploaded/` that does **not** contain a `REQ-\d+` token (requirements-source files are handled by `/tc:review-requirements` instead). Extracts five positive rubric dimensions (entities, glossary terms, user journeys, business rules, assumptions) with `<path>:<line>` provenance against the universal-core extractors documented in [`methodology/learning-from-documents.md`](methodology/learning-from-documents.md). Detects two gap signals — `undefined-term` (capitalized phrase in >=2 docs or bolded in prose, never defined in any glossary) and `contradictory-rule` (same subject anchor, opposing negation) — and routes them to `<workspace>/requirements/open-questions.md` deduplicated by `(source-id, question-text)`. Writes `<workspace>/product-knowledge/documentation-model.md` byte-deterministically. Contributes the `## From documents` section to the four cross-cutting artifacts (`entities.md`, `user-journeys.md`, `business-rules.md`, `assumptions.md`) while preserving every other source's `## From <other-source>` section. Calls `synthesize_system_model.py` at end to regenerate `<workspace>/product-knowledge/system-model.md` byte-deterministically from the current state of every per-source model plus every cross-cutting artifact.

**Run:**

```sh
python3 <plugin-root>/scripts/extract_knowledge_from_docs.py <project-root>
```

`<project-root>` defaults to the current working directory. The universal-core extractors carry no domain vocabulary; consuming projects extend via `<workspace>/config.yaml` under `tc-knowledge.documents:` (`entity-keywords`, `journey-headings`). See [customizing for your project](../../../../docs/user-guide/customizing-for-your-project.md).

Full spec: [commands/learn-from-docs.md](commands/learn-from-docs.md). Methodology: [methodology/learning-from-documents.md](methodology/learning-from-documents.md). Umbrella synthesis model: [methodology/project-knowledge.md](methodology/project-knowledge.md).

### Shared synthesizer

`synthesize_system_model.py` regenerates `<workspace>/product-knowledge/system-model.md` from the current state of every per-source model file (`documentation-model.md`, `spec-derived-model.md`, etc.) plus every cross-cutting artifact (`entities.md`, `user-journeys.md`, `business-rules.md`, `assumptions.md`). Invoked at the end of every `/tc:learn-from-*` helper; can also be run directly:

```sh
python3 <plugin-root>/scripts/synthesize_system_model.py <project-root>
```

Sources whose per-source model still carries the workspace-template stub marker, or any "no <source> found" empty-run sentinel, count as not-yet-ingested. Running any subset of the five learn helpers in any order produces a valid partial synthesis; running all five produces the full picture.

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

For each shipped command (currently `/tc:learn-from-docs`): resolve `<plugin-root>` relative to this SKILL.md, determine `<project-root>` (the user's current working directory unless specified otherwise), run the bundled helper via `Bash`, and report the helper's CLI output. Then add the narrative judgment layer described in [`methodology/learning-from-documents.md`](methodology/learning-from-documents.md):

- Decide whether each extracted entity is a domain entity or an attribute of an existing one.
- Identify synonyms across sources (the document's `Account` is the spec's `account_id`).
- Translate business rules into testable predicates where possible.
- Rank journeys by surface coverage; flag missing journeys for critical surfaces.
- Surface useful assumptions (those that constrain design) and elevate them to either requirements or confirmed facts when supporting evidence appears.
- Explain *why* each gap signal matters in product context before the user resolves the corresponding open question.

For commands that have not yet shipped (`/tc:learn-from-specs` etc.), produce a clear notice that the behavior arrives in the named sub-step and point the user at the phased plan.

If a helper exits non-zero, surface its stderr and the relevant per-command page.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-core skill](../tc-core/SKILL.md)
- [tc-requirements skill](../tc-requirements/SKILL.md)
