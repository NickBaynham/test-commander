# Customizing Test Commander for Your Project

Test Commander is a **generic, product-domain-agnostic testing tool**. It ships with universal English and software-engineering defaults only — no e-commerce, healthcare, finance, research, or other product-domain vocabulary is baked into the shipped rubric, tags, methodology, fixtures, or examples. This is a deliberate design choice; see [Decision D19](../../planning/plan.md) in the phased plan.

This guide shows how a consuming project extends Test Commander for its own domain — what to add, where to add it, and what to leave alone.

## Why genericness, by default

Test Commander does not know in advance whether you are testing a banking app, a hospital information system, a research data platform, an online retailer, or an internal tool. The shipped rubric, tag taxonomy, and examples make no assumptions. Product-specific knowledge enters at runtime through hooks you control.

A direct consequence: out of the box, Test Commander will not flag PCI-, HIPAA-, or commerce-specific defects in your requirements. It catches universal quality problems (clarity, testability, dependencies, ambiguity, generic-security anti-patterns like `plain text`). To get domain-aware checks, extend the configuration as described below.

## Where domain knowledge enters

Four explicit hooks. None are required — Test Commander works without any of them on the universal defaults. Use as few or as many as your project needs.

| Hook | What you supply | When it ships |
| --- | --- | --- |
| 1 | `<workspace>/config.yaml` extensions to rubric keyword sets | Phase 2 (first surface), extended by later phases |
| 2 | Your project's documents under `.test-commander/documents/uploaded/` | Phase 2 |
| 3 | Phase 3 project knowledge ingestion (`/tc:learn-from-*`) | Phase 3 |
| 4 | Project-defined values inside shipped tag namespaces (`@area:`, `@risk:`, `@persona:`) | Phase 5 |

This guide is updated by every phase that adds an extensible surface. If a phase introduced a new hook or schema key, you will find a worked example here.

## Hook 1: `<workspace>/config.yaml` extensions

The workspace's `config.yaml` is the primary configuration surface. Test Commander reads it on every helper invocation and **unions** project-supplied lists with the shipped universal core. Extensions never replace defaults — only add to them.

### Phase 2 schema (`tc-requirements`)

Phase 2 ships three extensible rubric dimensions under `tc-requirements:` (read by `/tc:review-requirements` for `data-rules` and `risk`, and by `/tc:review-acceptance-criteria` for `roles-permissions`):

```yaml
tc-requirements:
  data-rules:
    sensitive-keywords:
      - PAN
      - primary account number
      - PHI
      - SSN
  risk:
    compliance-keywords:
      - PAN
      - primary account number
      - PHI
      - social security
  roles-permissions:
    permission-verbs:
      - issue
      - refund
      - dispense
      - prescribe
    role-qualifiers:
      - customer
      - store-manager
      - investigator
      - reviewer
```

Missing keys = no extension. The helper falls back to the universal core only. The shipped seeded fixture in `tests/fixtures/seeded-flawed-requirements/` does not rely on any extension; every seeded defect triggers via the universal core alone.

### Worked example — an e-commerce project

You are testing an online retail platform. Your requirements regularly mention `credit card`, `PAN`, `refund`, `customer`, `store manager`. Extend the configuration:

```yaml
tc-requirements:
  data-rules:
    sensitive-keywords: [PAN, primary account number, credit card, credit-card]
  risk:
    compliance-keywords: [PAN, primary account number, credit card, social security]
  roles-permissions:
    permission-verbs: [issue, refund, charge, dispute]
    role-qualifiers: [customer, store-manager, fulfillment-agent]
```

Effect: `/tc:review-requirements` now flags requirements that mention `refund` without naming the role authorized to issue it, and flags requirements that mention `credit card` storage without a constraint keyword (`encrypted`, `tokenized`).

### Worked example — a healthcare project

```yaml
tc-requirements:
  data-rules:
    sensitive-keywords: [PHI, medical record number, MRN, prescription history, diagnosis code]
  risk:
    compliance-keywords: [PHI, HIPAA, patient identifier, MRN]
  roles-permissions:
    permission-verbs: [dispense, prescribe, refer, transfer]
    role-qualifiers: [physician, nurse, pharmacist, technician, patient]
```

Effect: requirements mentioning `prescribe` without a clinician role qualifier are flagged; storage references to `PHI` without an encryption constraint are flagged for HIPAA risk.

### Worked example — a research data platform

```yaml
tc-requirements:
  data-rules:
    sensitive-keywords: [participant identifier, IRB protocol, consent record]
  risk:
    compliance-keywords: [IRB, deidentification, re-identification risk]
  roles-permissions:
    permission-verbs: [enroll, terminate, deidentify, archive]
    role-qualifiers: [investigator, study-coordinator, IRB-reviewer, participant]
```

Effect: requirements that move participant data without naming the IRB-authorized role are flagged; storage references that lack `deidentification` constraints are flagged for compliance.

### Extension rules

- Extensions are **additive**. The helper unions defaults with your list. You cannot remove a universal-core keyword via configuration.
- Keyword matching is case-insensitive. Single-token keywords match at word boundaries; multi-token phrases (e.g. `credit card`) match literally.
- Add the same vocabulary in multiple sections if the same term carries meaning under multiple dimensions (e.g. `PAN` is both `sensitive-keywords` for data-rules and `compliance-keywords` for risk — that is correct and intentional).
- Document your additions in your project's `.test-commander/methodology.md` so the team uses a shared taxonomy.

### Phase 3 schema (`tc-knowledge`)

Phase 3 ships four extensible sub-blocks under `tc-knowledge:` (one per learn helper that has tunable detection; `/tc:learn-from-specs` has no `specs:` schema in v1 because the OpenAPI / Postman structural keys are themselves a universal vocabulary):

```yaml
tc-knowledge:
  documents:
    # Additive case-sensitive entity names. Surface anywhere they appear in
    # prose, even outside an entity-tokened heading.
    entity-keywords: [Patient, Provider, Claim]
    # Additive case-insensitive heading tokens. A heading containing any of
    # these substrings is treated as a journey heading.
    journey-headings: [story, flow]

  code:
    # Where to walk. Default: documents/uploaded/code. Resolves relative to
    # <workspace>. Use ../src to point at the consuming project's actual
    # source if it lives outside the workspace.
    source-root: src
    # v1 parses python only. Setting [] short-circuits the AST walk while
    # still flagging unsupported-language files.
    enabled-languages: [python]
    # Substring matches against the relative path; default includes
    # __pycache__, .git, .venv, node_modules.
    ignored-paths: [migrations, fixtures, .venv]
    # Reserved for the v2 spec-vs-decorator cross-check; v1 ignores.
    endpoint-decorator-patterns: ["@app.{method}", "@router.{method}"]

  api:
    # recorded (default) or live. Live mode is refused under pytest via the
    # PYTEST_CURRENT_TEST env var.
    mode: recorded
    # Default: documents/uploaded/recorded-api/responses.json. Resolves
    # relative to <workspace>.
    recorded-path: documents/uploaded/recorded-api/responses.json
    # Live-mode-only (v2). v1 ignores both keys when mode is recorded.
    base-url: http://localhost:8000
    auth-header: "Authorization: Bearer ${TC_API_TOKEN}"

  tests:
    # Default: documents/uploaded/tests. Resolves relative to <workspace>.
    source-root: tests
    # Substring matches against the relative path.
    ignored-paths: [fixtures, __pycache__]
```

Missing keys = no extension. The helpers fall back to documented defaults. The shipped seeded fixture in `tests/fixtures/seeded-sample-project/` does not rely on any extension; every seeded finding triggers via the universal cores plus the default paths.

#### Worked example — Python / FastAPI app

The consuming project's source lives at the repository root under `src/`; the OpenAPI spec lives at `openapi.yaml`; tests live under `tests/`.

```yaml
tc-knowledge:
  documents:
    entity-keywords: [Patient, Provider, Claim, EncounterRecord]
    journey-headings: [story]
  code:
    source-root: ../src
    enabled-languages: [python]
    ignored-paths: [migrations, alembic, .venv, __pycache__]
    endpoint-decorator-patterns: ["@app.{method}", "@router.{method}"]
  api:
    mode: recorded
    recorded-path: ../tests/recorded-api/responses.json
  tests:
    source-root: ../tests
    ignored-paths: [conftest.py, fixtures]
```

Effect: `/tc:learn-from-code` walks the consuming project's `src/` (not the workspace's local code directory); `/tc:learn-from-tests` reads the consuming project's `tests/`; `/tc:learn-from-api` plays back a recording the project's own test harness produced. `Patient`, `Provider`, `Claim`, `EncounterRecord` surface as entities anywhere they appear in prose.

#### Worked example — Node / Express app (v1 cannot parse JS yet)

The consuming project is a Node/Express service. v1 of `/tc:learn-from-code` parses Python only — but `enabled-languages: []` documents the project's intent and still flags every `.ts`/`.js` file as `language-unsupported-in-v1` so the gap signal is visible while a future phase adds the TS/JS parser.

```yaml
tc-knowledge:
  documents:
    entity-keywords: [Order, LineItem, Shipment, Refund]
  code:
    source-root: ../src
    # v1 cannot parse JS/TS. The empty list documents intent; the helper
    # still emits language-unsupported-in-v1 gaps for every detected file,
    # which keeps the surface visible until the parser ships.
    enabled-languages: []
    ignored-paths: [node_modules, dist, build]
  api:
    mode: recorded
    recorded-path: ../e2e/recorded.json
  tests:
    # Jest convention: __tests__/*.test.js or src/**/*.test.js. v1 detects
    # *.spec.ts and *_test.py but does NOT recognize .test.js yet; the
    # ignored-paths key is unused here, but documents the future intent.
    source-root: ../e2e
    ignored-paths: [node_modules, fixtures]
```

Effect: `/tc:learn-from-code` flags every `.js`/`.ts` file under `../src/` as a `language-unsupported-in-v1` gap; the consuming project knows what is uncovered in v1. The same code helper still runs cleanly for any Python files that happen to be in the tree (utility scripts, automation, etc.).

#### Worked example — Postman-only project (no OpenAPI)

The consuming project exposes its API through Postman collections rather than OpenAPI. `/tc:learn-from-specs` auto-detects Postman v2.1 by file extension; no `specs` config key is needed.

```yaml
tc-knowledge:
  documents:
    entity-keywords: [Subscription, Plan, Invoice]
  api:
    mode: recorded
    # Postman collection runs typically write a separate recording per
    # request. The consuming project concatenates them into a single
    # responses.json at this path.
    recorded-path: ../qa-artifacts/postman-recordings.json
  tests:
    source-root: ../qa
    ignored-paths: [fixtures]
```

The consuming project drops `their-api.postman_collection.json` under `documents/uploaded/` and runs `/tc:learn-from-specs`. The helper extracts endpoints (from `item.request`), schemas (from `request.body.raw` JSON top-level keys), and auth schemes (from distinct `request.auth.type` values across requests). The Postman URL is normalized — `{{base_url}}` prefixes are stripped via `_strip_postman_variables` so the captured path is just the API path. `/tc:learn-from-api`'s cross-check against the spec model works the same way it does for OpenAPI consumers.

### Phase 3 — what landed

- **Universal cores.** `/tc:learn-from-docs` detects entities, terms, journeys, business rules, and assumptions through universal English heading tokens (`entit`/`model`/`noun`/`glossary` for entities; `glossary`/`terminology` for terms; `journey`/`flow`/`walkthrough`/`scenario` for journeys) plus RFC-2119 modals (`must`/`shall`/`should`/`may`) and assumption markers (`assume`/`expected`/`presumed`/`likely`). `/tc:learn-from-specs` reads OpenAPI 3 / Postman v2.1 structural keys directly. `/tc:learn-from-code` uses stdlib `ast` for Python; non-Python extensions (`.ts`, `.tsx`, `.js`, `.jsx`, `.go`, `.java`, `.rb`) are flagged. `/tc:learn-from-api` reads recorded `{method, path, status, headers, body}` entries and classifies status family. `/tc:learn-from-tests` parses `test_*.py`/`*_test.py` via `ast` and counts `*.spec.ts` files via regex without parsing TypeScript.
- **Schema keys** (per the YAML block above): `tc-knowledge.documents.{entity-keywords, journey-headings}`, `tc-knowledge.code.{source-root, enabled-languages, ignored-paths, endpoint-decorator-patterns}`, `tc-knowledge.api.{mode, recorded-path, base-url, auth-header}`, `tc-knowledge.tests.{source-root, ignored-paths}`.
- **Tests that would fail if helpers ignored extensions.** `tests/test_learn_from_docs.py::test_entity_keywords_extension_applied` and `::test_journey_headings_extension_applied` assert that `tc-knowledge.documents.{entity-keywords, journey-headings}` extend the universal cores additively. `tests/test_learn_from_code.py::test_source_root_extension_applied` and `::test_ignored_paths_extension_excludes_matches` assert the same for code. `tests/test_learn_from_api.py::test_recorded_path_extension_applied` and `::test_live_mode_refused_under_pytest` assert recorded-path + live-mode refusal. `tests/test_learn_from_tests.py::test_source_root_extension_applied` asserts the tests source-root extension. Each test points the helper at a non-default path and asserts the helper found the content there; if the helpers ignored extensions, every one of these tests would fail with "no source found" or equivalent.

## Hook 2: project documents under `documents/uploaded/`

The Phase 2 helpers read every Markdown file in `.test-commander/documents/uploaded/` that matches their convention — `REQ-\d+` markers for requirements, `US-\d+` for stories, `AC-\d+` for acceptance criteria. Drop your real product requirements there as Markdown files. No tool configuration is needed; the helpers find and parse them.

This is the single most important customization: the requirements Test Commander reviews are *your* requirements. The shipped fixture exists only so Test Commander can be tested against itself.

## Hook 3: project knowledge ingestion (Phase 3, shipped)

Phase 3 ships the `tc-knowledge` skill with five commands plus a shared synthesizer: `/tc:learn-from-docs`, `/tc:learn-from-specs`, `/tc:learn-from-code`, `/tc:learn-from-api`, `/tc:learn-from-tests`. They scan your narrative documents, OpenAPI/Postman specs, Python source, recorded API responses, and existing tests to build a structured knowledge model under `.test-commander/product-knowledge/` (10 artifacts: 5 per-source models, 4 cross-cutting indexes, plus `system-model.md` regenerated by every run). Downstream Phase 4, 5, 6, and 7 commands read this knowledge to make their findings product-aware without you hand-curating keyword lists. End-to-end walkthrough: [building-project-knowledge.md](building-project-knowledge.md).

The schema for tuning the five helpers is the `tc-knowledge:` block documented above under "Phase 3 schema (`tc-knowledge`)". Worked extension examples cover Python/FastAPI, Node/Express (where v1 cannot parse JS yet), and Postman-only projects.

This is the **preferred long-term path** for domain awareness. `config.yaml` extensions to `tc-requirements` are a useful Phase 2 bootstrap; Phase 3 ingestion is how Test Commander learns your product without manual taxonomy work.

## Hook 4: project-defined tag namespaces

Test Commander (Phase 5+) ships three project-defined namespaces:

| Namespace | Purpose | Example values your project picks |
| --- | --- | --- |
| `@area:<feature>` | Feature area your project tests | `@area:sign-in`, `@area:reports`, `@area:billing` |
| `@risk:<class>` | Risk classification | severity: `@risk:high`/`medium`/`low`; category: `@risk:data-loss`/`availability`/`integrity`; domain: `@risk:compliance`/`fraud`/`safety` |
| `@persona:<role>` | User persona | `@persona:admin`, `@persona:customer`, `@persona:investigator` |

Test Commander ships the namespaces; you pick the values. Document your values in your project's `.test-commander/methodology.md`. Tag-driven gates (e.g. "block release if any `@risk:high` test is failing") are configured per-project.

## What NOT to do

- **Do not fork Test Commander.** The universal core is a contract — extending via `config.yaml` is the supported path. Forking divorces you from upstream improvements.
- **Do not put product-specific vocabulary in the shipped fixtures** (`tests/fixtures/`). Those test Test Commander itself; your domain belongs in your project's `documents/uploaded/` and `config.yaml`.
- **Do not expect overrides to remove defaults.** Extensions add to defaults, never replace them. If a universal keyword (e.g. `plain text` for risk) is not relevant to your product, your finding still includes it — you simply ignore the suggestion in your team's review.
- **Do not encode product knowledge inline in helpers or methodology docs.** Phase 3's knowledge ingestion is the canonical place for that information; `config.yaml` is the canonical place for vocabulary extensions.

## See also

- [Workspace reference](../workspace-reference.md) — where each artifact lives, including `config.yaml`.
- [Phased plan, Decision D19](../../planning/plan.md) — the genericness principle.
- [Workflow walkthrough](workflow.md) — first end-to-end run.
- [Command reference](../command-reference.md) — every command, by phase.
- [Getting started](getting-started.md) — install and verify.
