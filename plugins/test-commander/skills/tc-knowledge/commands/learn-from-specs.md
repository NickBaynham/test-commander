# `/tc:learn-from-specs`

The Phase 3 spec-ingestion command. Auto-detects OpenAPI 3 specs (YAML or JSON) and Postman v2.1 collections under `<workspace>/documents/uploaded/`, extracts endpoints / schemas / auth-schemes with file:line provenance, routes gap signals (`unspecified-status`, `schema-without-type`) to `<workspace>/requirements/open-questions.md`, contributes a `## From specs` section to `entities.md` (resources) and `business-rules.md` (auth rules), and regenerates `system-model.md` via the shared `synthesize_system_model.py` helper.

## Inputs

- `<workspace>/documents/uploaded/openapi.yaml`, `openapi.yml`, `*.openapi.yaml`, `*.openapi.yml` - OpenAPI 3 in YAML.
- `<workspace>/documents/uploaded/openapi.json`, `*.openapi.json` - OpenAPI 3 in JSON.
- `<workspace>/documents/uploaded/*.postman_collection.json` - Postman v2.1 collections.

Recursive glob; any subdirectory under `documents/uploaded/` is searched. Multiple spec files are unioned. No spec files -> the helper writes a `_No spec found_` stub and exits 0.

## Outputs

| Path | Mode | Owner |
| --- | --- | --- |
| `<workspace>/product-knowledge/spec-derived-model.md` | overwrite | this command |
| `<workspace>/product-knowledge/entities.md` (`## From specs`) | section-overwrite | this command |
| `<workspace>/product-knowledge/business-rules.md` (`## From specs`) | section-overwrite | this command |
| `<workspace>/product-knowledge/system-model.md` | overwrite (synthesizer) | shared |
| `<workspace>/requirements/open-questions.md` | append, dedup by `(source-id, question)` | this command |

`user-journeys.md` and `assumptions.md` are NOT touched; specs declare no journeys and specs are confirmed facts (not inferences).

## Preconditions

- `<workspace>/.test-commander/` exists (run `/tc:init` first). The helper exits non-zero with a clear error if the workspace is uninitialized.

No upstream Phase 3 helper is required - `/tc:learn-from-specs` is independent of every other learn-from-* command. Running any subset in any order produces a valid partial synthesis.

## Behavior

1. Resolve the workspace under `<project-root>/.test-commander/`.
2. Walk `documents/uploaded/` recursively for files matching the OpenAPI YAML, OpenAPI JSON, or Postman v2.1 globs.
3. For each spec file, dispatch to the appropriate extractor (`extract_openapi` for OpenAPI YAML/JSON; `extract_postman` for Postman v2.1).
4. OpenAPI extractor: parse with PyYAML (or `json.loads` for `.json`). Walk `paths.<path>.<method>` triples for endpoints; walk `components.schemas` for schemas; walk `components.securitySchemes` for auth schemes. Run gap detection: `unspecified-status` if an endpoint has no `responses` keys or only `default`; `schema-without-type` if a schema entry has neither `type` nor `$ref`.
5. Postman extractor: parse with `json.loads`. Walk `item[*].request` (recursing into nested folders); capture endpoint method + URL path; capture body shape as `<request-label>Body` schemas; capture distinct `request.auth.type` values.
6. Resolve line-number provenance for every finding by string-scanning the source text for the relevant marker (`<path>:`, `<method>:`, `<schema-name>:`, etc.).
7. Render `spec-derived-model.md` (overwrite) with executive summary tables for sources / endpoints / schemas / auth schemes / gap signals.
8. Render the `## From specs` section body for `entities.md` (endpoints grouped by resource) and `business-rules.md` (auth schemes as rules); call `update_cross_cutting()` which preserves every other source's `## From <other-source>` section and writes the file deterministically.
9. Append open questions for each gap signal, deduplicated by `(source-id, question-text)`.
10. Call `synthesize_system_model.synthesize(project_root)` to regenerate `system-model.md`.
11. Exit 0.

## Safety

- The helper reads only from `<workspace>/documents/uploaded/`. No network calls; no shell-out; no writes outside `product-knowledge/` and `requirements/open-questions.md`.
- YAML parsing uses `yaml.safe_load` (no Python object construction).
- Re-running against unchanged input is byte-deterministic across every output. The `open-questions.md` dedup prevents append drift.
- Per the Phase-3 design decisions, `/tc:learn-from-specs` does not write to `<workspace>/traceability/`; spec-vs-code cross-checking is Phase 5's responsibility.
- Per D19, the extractors carry no domain vocabulary. The OpenAPI / Postman structural keys are themselves universal.

## Implementation

- Helper: `plugins/test-commander/scripts/extract_knowledge_from_specs.py` (~600 lines).
- Dependency: PyYAML (>= 6.0) added in this sub-step. Pure Python; canonical YAML library.
- Tests: `tests/test_learn_from_specs.py` (21 cases - uninitialized refused, no-spec stub, OpenAPI extracts 6 endpoints + 6 schemas + bearerAuth, both gap signals route to open-questions, idempotency across all outputs, Postman auto-detection, cross-cutting scope (entities + business-rules only; NOT user-journeys or assumptions), `## From documents` preservation when Step 3.2 ran first).

## Definition of Done

- Helper passes all 21 test cases.
- OpenAPI YAML/JSON and Postman v2.1 auto-detection both work.
- Methodology covers all 3 positive dimensions plus both gap signals with worked examples and Claude-judgment-layer paragraphs.
- Template authored.
- Per-command page complete (this file).
- `tc-knowledge/SKILL.md` describes `/tc:learn-from-specs`'s shipped behavior; no deferral wording for this command.
- `make verify` chain green.

## See also

- [Methodology](../methodology/learning-from-specs.md)
- [Umbrella methodology](../methodology/project-knowledge.md)
- [Spec-derived-model template](../templates/spec-derived-model-template.md)
