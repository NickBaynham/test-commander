# Workflow — Building Project Knowledge (Phase 3)

This guide walks you through Test Commander's five Phase 3 commands end to end against a consuming project. The examples use the deliberately-generic seeded fixture from `tests/fixtures/seeded-sample-project/` so every output is reproducible.

## What's available in Phase 3

Phase 3 ships the `tc-knowledge` skill with five commands plus a shared synthesizer:

| Command | Reads | Writes |
| --- | --- | --- |
| `/tc:learn-from-docs` | non-requirements Markdown under `documents/uploaded/` | `documentation-model.md` + contributions to entities / journeys / business-rules / assumptions |
| `/tc:learn-from-specs` | `openapi.yaml`/`.yml`/`.openapi.json` + Postman v2.1 collections | `spec-derived-model.md` + contributions to entities + business-rules |
| `/tc:learn-from-code` | Python source under `documents/uploaded/code/` | `code-derived-model.md` + contributions to entities |
| `/tc:learn-from-api` | recorded responses at `documents/uploaded/recorded-api/responses.json` | `api-model.md` + contributions to entities + business-rules |
| `/tc:learn-from-tests` | `test_*.py`/`*_test.py` + `*.spec.ts` under `documents/uploaded/tests/` | `tests-coverage.md` + contributions to entities |

All five commands also call the shared `synthesize_system_model.py` helper, which rewrites `<workspace>/product-knowledge/system-model.md` from the current state of every per-source model and cross-cutting artifact. Running any subset of the five helpers in any order produces a valid partial synthesis; running all five produces the full picture.

Per Decision D19 ([planning/plan.md](../../planning/plan.md)) all five helpers ship universal-core detection patterns only. Domain-specific vocabulary enters through `<workspace>/config.yaml` extensions — see [customizing-for-your-project.md](customizing-for-your-project.md).

## Prerequisites

1. `<workspace>/.test-commander/` exists (`/tc:init` has run — see [workflow.md](workflow.md)).
2. The consuming project has uploaded the artifacts it wants ingested under `<workspace>/documents/uploaded/`. The exact layout per command:

```
.test-commander/documents/uploaded/
  product-overview.md         # narrative docs (NO REQ-NNN markers)
  glossary.md
  user-journey-*.md
  openapi.yaml                # OpenAPI 3 (or .yml / .openapi.json / *.postman_collection.json)
  code/                       # Python source tree
    app/
      api/
      models/
      utils/
  recorded-api/
    responses.json            # JSON list of {method, path, status, headers, body}
  tests/
    test_*.py                 # pytest-shaped
    *.spec.ts                 # Playwright (detected, not parsed in v1)
```

3. PyYAML is available in the Python environment that runs the helpers. The project's `pyproject.toml` lists `pyyaml>=6.0` under `[project.dependencies]`; with `pdm install` it is on the path. When invoking the bundled helpers from a consuming project without pdm, ensure `pyyaml` is installed in the active Python (`pip install pyyaml`).

## Step 1: `/tc:learn-from-docs`

Reads non-requirements Markdown (files NOT containing any `REQ-\d+` token; the inverse of Phase 2's filter) and extracts five positive dimensions plus two gap signals.

**Run:**

```sh
python3 <plugin-root>/scripts/extract_knowledge_from_docs.py <project-root>
```

**What lands:**

- `<workspace>/product-knowledge/documentation-model.md` — sources table, entities, terms (glossary definitions), user journeys (numbered/bulleted steps under journey/flow/walkthrough/scenario headings), business rules (RFC-2119 modal sentences outside journey ranges), assumptions (with "no direct citation" flag), gap signals.
- `## From documents` section in `entities.md`, `user-journeys.md`, `business-rules.md`, `assumptions.md`.
- Open questions in `<workspace>/requirements/open-questions.md` (deduplicated by `(source-id, question-text)`) for `undefined-term` and `contradictory-rule` gaps.
- `<workspace>/product-knowledge/system-model.md` regenerated.

**Sample output** (from the seeded fixture):

```markdown
## Entities

| Entity | Source |
| --- | --- |
| Account | documents/uploaded/product-overview.md:13 |
| Asset | documents/uploaded/product-overview.md:16 |
| Permission | documents/uploaded/product-overview.md:17 |
| Session | documents/uploaded/product-overview.md:14 |
| Workspace | documents/uploaded/product-overview.md:15 |

## Terms

| Term | Definition | Source |
| --- | --- | --- |
| Account | A registered user of the platform. ... | documents/uploaded/glossary.md:5 |
...
```

The seeded fixture's `Telemetry` (bolded in `product-overview.md` but never defined) surfaces as an `undefined-term` open question. The seeded "admin may delete any workspace" vs "admin must not delete a workspace they did not create" pair surfaces as a `contradictory-rule` open question.

Full methodology with worked examples per dimension: [`tc-knowledge/methodology/learning-from-documents.md`](../../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-documents.md).

## Step 2: `/tc:learn-from-specs`

Auto-detects OpenAPI 3 (YAML or JSON) and Postman v2.1 collections under `documents/uploaded/`. Extracts endpoints, schemas, auth schemes.

**Run:**

```sh
python3 <plugin-root>/scripts/extract_knowledge_from_specs.py <project-root>
```

**What lands:**

- `<workspace>/product-knowledge/spec-derived-model.md` — sources table, endpoints table (`METHOD /path` cells), schemas table with `type` and `$ref` columns, auth-schemes table, gap signals.
- `## From specs` section in `entities.md` (endpoints grouped by HTTP-path resource — the first non-templated URL segment) and `business-rules.md` (one rule per security scheme).
- Open questions for `unspecified-status` (endpoint declares no responses) and `schema-without-type` (schema entry missing both `type` and `$ref`).
- `system-model.md` regenerated.

**Sample output** (seeded fixture):

```markdown
## Endpoints

| Endpoint | Operation | Source |
| --- | --- | --- |
| DELETE /sessions/{id} | sign_out | documents/uploaded/openapi.yaml:33 |
| GET /accounts/{id} | get_account | documents/uploaded/openapi.yaml:46 |
| GET /workspaces | list_workspaces | documents/uploaded/openapi.yaml:65 |
| GET /workspaces/{id}/assets | list_assets | documents/uploaded/openapi.yaml:99 |
| POST /sessions | sign_in | documents/uploaded/openapi.yaml:15 |
| POST /workspaces/{id}/assets | upload_file | documents/uploaded/openapi.yaml:81 |
```

The seeded fixture's `POST /workspaces/{id}/assets` (no `responses:` block) and `AssetUpload` schema (no `type` or `$ref`) both surface as open questions.

Full methodology: [`tc-knowledge/methodology/learning-from-specs.md`](../../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-specs.md).

## Step 3: `/tc:learn-from-code`

Walks Python source under the configured root using stdlib `ast`. Detects non-Python files (`.ts`, `.tsx`, `.js`, `.jsx`, `.go`, `.java`, `.rb`) and flags them as `language-unsupported-in-v1` gaps.

**Run:**

```sh
python3 <plugin-root>/scripts/extract_knowledge_from_code.py <project-root>
```

**What lands:**

- `<workspace>/product-knowledge/code-derived-model.md` — source-modules table, classes (with attributes column and per-class docstring summary bullets), functions (with decorators column and per-function docstring summary bullets), languages-detected-but-not-parsed table, gap signals.
- `## From code` section in `entities.md` (classes as domain-entity candidates with `(path:line) - docstring` bullets).
- Open questions for `undocumented-function` (public function without docstring), `language-unsupported-in-v1` (non-Python file), and (when `spec-derived-model.md` has been generated) `unimplemented-endpoint` (spec endpoint whose `operationId` does not match any function name).
- `system-model.md` regenerated.

The cross-check against the spec model fires only after `/tc:learn-from-specs` has run. Order-independent: code-before-specs produces no `unimplemented-endpoint` gaps; running specs later then re-running code lands them.

Configurable via `tc-knowledge.code.{source-root, enabled-languages, ignored-paths, endpoint-decorator-patterns}` — see [customizing-for-your-project.md](customizing-for-your-project.md). v1 parses Python only; `enabled-languages: [python]` is the default and `[]` short-circuits the AST walk while still flagging unsupported-language files.

Full methodology: [`tc-knowledge/methodology/learning-from-code.md`](../../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-code.md).

## Step 4: `/tc:learn-from-api`

Reads recorded API responses from `documents/uploaded/recorded-api/responses.json` (or the configured path). Classifies by status family, extracts response-body shapes, infers auth-required endpoints, cross-checks against the spec model.

**Run:**

```sh
python3 <plugin-root>/scripts/extract_knowledge_from_api.py <project-root>
```

**Recorded vs live mode.** The default `recorded` mode reads a JSON playback file the consuming project supplies. The opt-in `live` mode (`tc-knowledge.api.mode: live`) is documented but **refused under pytest** — the helper detects pytest via the `PYTEST_CURRENT_TEST` environment variable and exits 2 before issuing any network call. Live mode is not implemented in v1; recorded playback is sufficient for every Phase-3 contract.

**What lands:**

- `<workspace>/product-knowledge/api-model.md` — source recordings table, live-endpoints table with status family, response-shapes table (top-level JSON keys per endpoint), auth-required list, gap signals.
- `## From api` section in `entities.md` (resources confirmed reachable, grouped by URL-path resource segment) and `business-rules.md` (one rule per auth-required endpoint).
- Open questions for `unspecified-endpoint` (recorded request not in spec) and `mismatched-status` (recorded status outside the spec's declared response codes for that endpoint).
- `system-model.md` regenerated.

The cross-check fires only when `spec-derived-model.md` is generated. When the spec declares no responses for an endpoint, the spec-side `unspecified-status` gap already covers it and the api-side `mismatched-status` check stays silent (no double-counting).

Full methodology: [`tc-knowledge/methodology/learning-from-api.md`](../../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-api.md).

## Step 5: `/tc:learn-from-tests`

Walks pytest-style Python (`test_*.py`, `*_test.py`) and Playwright spec files (`*.spec.ts`). Pytest files parse with stdlib `ast`; Playwright files are detected by extension and counted by regex without parsing TypeScript.

**Run:**

```sh
python3 <plugin-root>/scripts/extract_knowledge_from_tests.py <project-root>
```

**What lands:**

- `<workspace>/product-knowledge/tests-coverage.md` — source-files table by runner, test-functions table with `<path>:<line>` provenance, covered-symbols aggregate (the union of `ast.Name.id` + `ast.Attribute.attr` references across every pytest test body), class-coverage breakdown vs `code-derived-model.md`, gap signals.
- `## From tests` section in `entities.md` — each class from `code-derived-model.md` annotated `(confidence: covered)` if its name appears in the covered-symbols aggregate, `(confidence: uncovered)` otherwise.
- Open questions for `unsupported-test-runner` (always, for every `*.spec.ts` file) and `untested-function` (after `/tc:learn-from-code` has run; emitted for every public function whose plain name does not appear in the covered-symbols aggregate).
- `system-model.md` regenerated.

The `untested-function` cross-check requires `code-derived-model.md` to be generated; without it, the helper emits only the always-on `unsupported-test-runner` gaps.

Full methodology: [`tc-knowledge/methodology/learning-from-tests.md`](../../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-tests.md).

## What changed on disk

After running all five helpers in any order against the seeded fixture, your `<workspace>/product-knowledge/` directory contains 10 populated artifacts:

```
product-knowledge/
  system-model.md             # synthesized cross-source overview (regenerated by every helper)
  documentation-model.md      # populated by /tc:learn-from-docs
  spec-derived-model.md       # populated by /tc:learn-from-specs
  code-derived-model.md       # populated by /tc:learn-from-code
  api-model.md                # populated by /tc:learn-from-api
  tests-coverage.md           # populated by /tc:learn-from-tests
  entities.md                 # 1+ "## From <source>" sections (all five helpers contribute)
  user-journeys.md            # ## From documents only
  business-rules.md           # ## From documents + ## From specs + ## From api
  assumptions.md              # ## From documents only
```

Plus appended open questions in `<workspace>/requirements/open-questions.md`.

`<workspace>/traceability/` is **not** touched by Phase 3. Cross-source traceability is Phase 5's responsibility; Phase 3 supplies the inputs.

## Re-running

Every helper is idempotent. Re-running against unchanged input produces:

- byte-identical per-source model files (`documentation-model.md`, `spec-derived-model.md`, etc.);
- byte-identical `## From <source>` section bodies in the cross-cutting artifacts (other sources' sections are preserved verbatim);
- line-stable `open-questions.md` (dedup by `(source-id, question-text)` with the `[<kind>]` prefix for tc-knowledge entries);
- byte-identical `system-model.md` regenerated by the shared synthesizer.

Add new uploaded files and re-run any subset of helpers; only the affected sections change.

## Customizing for your project

The shipped detectors carry no domain-specific vocabulary. Per D19, consuming projects extend the universal cores through `<workspace>/config.yaml`. The four extensible Phase-3 sub-blocks are:

| Block | Keys |
| --- | --- |
| `tc-knowledge.documents` | `entity-keywords`, `journey-headings` |
| `tc-knowledge.code` | `source-root`, `enabled-languages`, `ignored-paths`, `endpoint-decorator-patterns` |
| `tc-knowledge.api` | `mode`, `recorded-path`, `base-url`, `auth-header` |
| `tc-knowledge.tests` | `source-root`, `ignored-paths` |

`/tc:learn-from-specs` has no `tc-knowledge.specs:` schema in v1 — OpenAPI and Postman structural keys are themselves a universal vocabulary.

See [`customizing-for-your-project.md`](customizing-for-your-project.md) for the full schema and worked examples (Python/FastAPI app, Node/Express where v1 cannot parse JS yet, Postman-only project).

## Beyond Phase 3

After all five `/tc:learn-from-*` commands have run, the consuming project has structured knowledge artifacts under `<workspace>/product-knowledge/` plus a populated `<workspace>/requirements/open-questions.md`. Downstream phases consume this knowledge:

- **Phase 4** (`tc-explore`, charter-based exploration) **is shipped** and reads `system-model.md`, the per-source models, and `requirements/open-questions.md` to seed charter targets and risk areas. Follow [exploring-an-app.md](exploring-an-app.md) for the Phase 4 end-to-end walkthrough.
- **Phase 5** (`tc-bdd`, BDD generation) consumes the entity index, journey list, business rules, and Phase 4 enriched test-ideas to scaffold `.feature` files. Phase 5 also populates `<workspace>/traceability/` linking requirements, entities, endpoints, and tests.
- **Phase 6** (`tc-build-framework`, automation) uses the code model + spec model + test coverage signal to scaffold a Playwright framework.
- **Phase 7** (`tc-run`, execution + quality report) reads the cross-source knowledge to score risk and prioritize.

The Phase 1 `/tc:next` heuristic recommends the next command based on the workspace state; after Phase 3 finishes it advances past `/tc:learn-from-*` toward `/tc:create-charter` (Phase 4).

## See also

- [Phased plan](../../planning/plan.md) — full roadmap, decisions D1–D19, per-phase deliverables
- [Customizing for your project](customizing-for-your-project.md) — `tc-knowledge:` config schema and worked extension examples
- [Workspace reference](../workspace-reference.md) — per-file ownership of every `.test-commander/` artifact
- [Command reference](../command-reference.md) — every shipped `/tc:*` command with per-command-page links
- [Phase 1 walkthrough](workflow.md) — `/tc:init`, `/tc:status`, `/tc:journal`, `/tc:next`
- [Phase 2 walkthrough](reviewing-requirements.md) — requirements / user-stories / acceptance-criteria review chain
- Per-command pages inside the plugin:
  - [`commands/learn-from-docs.md`](../../plugins/test-commander/skills/tc-knowledge/commands/learn-from-docs.md)
  - [`commands/learn-from-specs.md`](../../plugins/test-commander/skills/tc-knowledge/commands/learn-from-specs.md)
  - [`commands/learn-from-code.md`](../../plugins/test-commander/skills/tc-knowledge/commands/learn-from-code.md)
  - [`commands/learn-from-api.md`](../../plugins/test-commander/skills/tc-knowledge/commands/learn-from-api.md)
  - [`commands/learn-from-tests.md`](../../plugins/test-commander/skills/tc-knowledge/commands/learn-from-tests.md)
- Per-command methodology docs:
  - [`learning-from-documents.md`](../../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-documents.md)
  - [`learning-from-specs.md`](../../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-specs.md)
  - [`learning-from-code.md`](../../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-code.md)
  - [`learning-from-api.md`](../../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-api.md)
  - [`learning-from-tests.md`](../../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-tests.md)
- [Umbrella methodology](../../plugins/test-commander/skills/tc-knowledge/methodology/project-knowledge.md) — three-tier synthesis model, provenance contract, assumptions-vs-facts rule, gap-signal routing, workspace boundaries
