---
name: tc-knowledge
description: Project-knowledge ingestion commands for Test Commander. Use when the user runs /tc:learn-from-docs, /tc:learn-from-specs, /tc:learn-from-code, /tc:learn-from-api, or /tc:learn-from-tests, or asks about building project knowledge, extracting entities, journeys, endpoints, modules, or test coverage from uploaded artifacts. Owns the five commands that turn the consuming project's documents, OpenAPI/Postman specs, source code, recorded API responses, and existing tests into structured knowledge artifacts under .test-commander/product-knowledge/.
---

# tc-knowledge

The project-knowledge skill for Test Commander. Owns the five commands that read uploaded source artifacts and populate `<workspace>/product-knowledge/` with per-source models (`documentation-model.md`, `spec-derived-model.md`, `code-derived-model.md`, `api-model.md`, `tests-coverage.md`) plus the cumulative cross-cutting artifacts (`entities.md`, `user-journeys.md`, `business-rules.md`, `assumptions.md`) and the synthesized `system-model.md`.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Status

Phase 3 is in progress. The skill scaffold and seeded sample-project fixture (Step 3.1) have shipped. Steps 3.2-3.5 have shipped `/tc:learn-from-docs` (with the shared `synthesize_system_model.py` helper), `/tc:learn-from-specs`, `/tc:learn-from-code`, and `/tc:learn-from-api`. Command behavior arrives in subsequent sub-steps:

- `/tc:learn-from-docs` — **shipped (Step 3.2).**
- `/tc:learn-from-specs` — **shipped (Step 3.3).**
- `/tc:learn-from-code` — **shipped (Step 3.4).**
- `/tc:learn-from-api` — **shipped (Step 3.5).**
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

Auto-detects OpenAPI 3 specs (YAML or JSON) and Postman v2.1 collections under `<workspace>/documents/uploaded/` and extracts three positive rubric dimensions (endpoints, schemas, auth-schemes) with `<path>:<line>` provenance per the universal-core extractors in [`methodology/learning-from-specs.md`](methodology/learning-from-specs.md). OpenAPI extractor walks `paths.<path>.<method>`, `components.schemas`, and `components.securitySchemes`; Postman extractor walks `item.request` recursively, captures the URL path and method, derives schemas from `request.body.raw` JSON shapes, and surfaces distinct `request.auth.type` values. Detects two gap signals — `unspecified-status` (endpoint with no `responses` keys or only `default`) and `schema-without-type` (schema entry missing both `type` and `$ref`) — routed to `<workspace>/requirements/open-questions.md` deduplicated by `(source-id, question-text)`. Writes `<workspace>/product-knowledge/spec-derived-model.md` byte-deterministically. Contributes `## From specs` to `entities.md` (endpoints grouped by resource — the first non-templated URL segment becomes the resource name) and `business-rules.md` (auth schemes as rules); does NOT touch `user-journeys.md` or `assumptions.md`. Calls the shared synthesizer at the end.

**Run:**

```sh
python3 <plugin-root>/scripts/extract_knowledge_from_specs.py <project-root>
```

`<project-root>` defaults to the current working directory. The structural keys in OpenAPI and Postman are themselves a universal vocabulary; no `tc-knowledge.specs:` config extensions are required in v1.

Full spec: [commands/learn-from-specs.md](commands/learn-from-specs.md). Methodology: [methodology/learning-from-specs.md](methodology/learning-from-specs.md).

### `/tc:learn-from-code`

Walks Python source under the configured root (default `<workspace>/documents/uploaded/code/`, configurable via `tc-knowledge.code.source-root`) using the stdlib `ast` module and extracts five positive rubric dimensions (modules, classes, functions, docstrings, decorators) with `<path>:<line>` provenance per the universal-core extractors in [`methodology/learning-from-code.md`](methodology/learning-from-code.md). Non-Python files in the unsupported-extension set (`.ts`, `.tsx`, `.js`, `.jsx`, `.go`, `.java`, `.rb`) are detected by extension and flagged as `language-unsupported-in-v1` gaps — never silently ignored. Public functions without docstrings emit `undocumented-function` gaps. When `spec-derived-model.md` has been generated by `/tc:learn-from-specs`, the helper parses its endpoints table and cross-checks each endpoint's `operationId` against the parsed function-name set; mismatches emit `unimplemented-endpoint` gaps. All gap kinds route to `<workspace>/requirements/open-questions.md` with the gap kind as a prefix (`[undocumented-function] ...`) so grep-by-kind works uniformly. Writes `<workspace>/product-knowledge/code-derived-model.md` byte-deterministically. Contributes `## From code` to `entities.md` (classes as domain entities with their docstring summaries); reserves the `## From code` section in `business-rules.md` for module-level constants with explicit rule docstrings (empty in v1). Does NOT touch `user-journeys.md` or `assumptions.md`. Calls the shared synthesizer at the end.

**Run:**

```sh
python3 <plugin-root>/scripts/extract_knowledge_from_code.py <project-root>
```

`<project-root>` defaults to the current working directory. Configurable via `tc-knowledge.code.{source-root,enabled-languages,ignored-paths,endpoint-decorator-patterns}` in `<workspace>/config.yaml`. v1 parses Python only; the `enabled-languages` extension hook is reserved for future-phase language additions.

Full spec: [commands/learn-from-code.md](commands/learn-from-code.md). Methodology: [methodology/learning-from-code.md](methodology/learning-from-code.md).

### `/tc:learn-from-api`

Reads a recorded-response playback file (default `<workspace>/documents/uploaded/recorded-api/responses.json`, configurable via `tc-knowledge.api.recorded-path`) and extracts three positive rubric dimensions (live-endpoints, response-shapes, auth-required) per the universal-core extractors in [`methodology/learning-from-api.md`](methodology/learning-from-api.md). Each playback entry `{method, path, status, headers, body}` becomes a `Recording` with status-family classification (`2xx` / `3xx` / `4xx` / `5xx`), top-level response-body keys (JSON objects, or the first element's keys for arrays), and auth-required inference (request carried an `Authorization` header OR response is 401/403 without one). When `spec-derived-model.md` has been generated by `/tc:learn-from-specs`, the helper imports Step 3.3's parser (`extract_knowledge_from_specs.aggregate`) and cross-checks every recorded `(method, path, status)` triple against the spec: `unspecified-endpoint` fires when the spec does not declare the endpoint; `mismatched-status` fires when the spec declares some statuses for the endpoint but the recorded status isn't in them (the check is silent when the spec declares no statuses to avoid emitting redundant gaps alongside the spec-side `unspecified-status`). Both gaps route to `<workspace>/requirements/open-questions.md` with the `[<kind>]` prefix. Live mode (`tc-knowledge.api.mode: live`) is opt-in and **refused under pytest**: the helper detects `PYTEST_CURRENT_TEST` in the environment and exits 2 before issuing any network call. Writes `<workspace>/product-knowledge/api-model.md` byte-deterministically. Contributes `## From api` to `entities.md` (resources confirmed reachable, grouped by URL-path resource segment) and `business-rules.md` (one rule per auth-required endpoint). Does NOT touch `user-journeys.md` or `assumptions.md`. Calls the shared synthesizer at the end.

**Run:**

```sh
python3 <plugin-root>/scripts/extract_knowledge_from_api.py <project-root>
```

`<project-root>` defaults to the current working directory. Configurable via `tc-knowledge.api.{mode,recorded-path,base-url,auth-header}`. v1 only reaches the recorded path; live mode is documented for future-phase implementation and refused under pytest.

Full spec: [commands/learn-from-api.md](commands/learn-from-api.md). Methodology: [methodology/learning-from-api.md](methodology/learning-from-api.md).

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
