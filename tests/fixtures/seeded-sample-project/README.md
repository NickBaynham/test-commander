# Seeded-sample-project fixture

A deliberately-generic consuming-project corpus that exercises every knowledge-rubric dimension and every gap-signal the Phase 3 `tc-knowledge` commands extract. The Test Commander Phase 3 commands (`/tc:learn-from-docs`, `/tc:learn-from-specs`, `/tc:learn-from-code`, `/tc:learn-from-api`, `/tc:learn-from-tests`) are tested against this fixture: every command suite asserts that the corresponding extraction or gap-signal finding is produced for each seeded item.

This fixture is a **test asset, not part of the shipped plugin**. Its narrative is intentionally domain-neutral (a generic SaaS dashboard — sign-in, accounts, workspaces, assets) because Test Commander is a universal testing tool. At runtime it works against whatever sources the consuming project supplies, not against any pre-known product. Markers here use only universal English and software-engineering vocabulary; nothing in this fixture should be read as a claim about a specific product domain (e-commerce, banking, healthcare, etc.). Domain-specific vocabulary enters at runtime through `<workspace>/config.yaml` extensions under `tc-knowledge:`, not through this fixture.

## Sub-trees

- `documents/` — three narrative Markdown files: `product-overview.md` (system narrative), `glossary.md` (universal SaaS terms), `user-journey-sign-in.md` (an ordered journey with at least one untested branch).
- `specs/openapi.yaml` — small OpenAPI 3.0 spec. Six endpoints in scope. At least one endpoint declared in the spec but absent from `src/` (the `unimplemented-endpoint` seed).
- `src/` — Python application tree (`app/__init__.py`, `app/models/account.py`, `app/models/workspace.py`, `app/api/auth.py`, `app/api/files.py`, `app/utils/validation.py`) plus `web/app.ts` to seed the `language-unsupported-in-v1` gap. At least one public function deliberately lacks a docstring (the `undocumented-function` seed).
- `tests/` — pytest-shaped Python files covering a subset of `src/`. At least one public function in `src/` deliberately has no test (the `untested-function` seed). At least one `.spec.ts` file seeds the `unsupported-test-runner` gap.
- `recorded-api/responses.json` — playback fixture for `/tc:learn-from-api`'s `recorded` mode. Covers every endpoint in `specs/openapi.yaml` plus one undocumented endpoint (the `unspecified-endpoint` seed). At least one response carries a status not declared by the spec (the `mismatched-status` seed).

## Marker convention

Every seeded gap signal is marked with a universal token in the file's native comment syntax:

- Markdown: `<!-- knowledge: <dimension> -->`
- YAML: `# knowledge: <dimension>`
- Python: `# knowledge: <dimension>`
- TypeScript / JavaScript: `// knowledge: <dimension>`
- JSON (no native comments): an inline `"_knowledge": "knowledge: <dimension>"` key on the affected entry. The value carries the literal `knowledge: <dimension>` marker so the same regex matches across all file types.

The scaffold test (`tests/test_tc_knowledge_scaffold.py`) walks every file under this directory and matches the regex `knowledge:\s*([a-z][a-z0-9-]*)` to verify gap-signal coverage. Per-command tests (3.2 onward) assert the specific helper surfaces the expected finding for each tagged seed.

Positive rubric dimensions (entities, terms, journeys, business-rules, assumptions, endpoints, schemas, auth-schemes, modules / classes / functions, docstrings, test-coverage) are structurally present in the fixture by design (a glossary file exists, the OpenAPI spec declares paths, Python classes are defined, etc.) and asserted with shape checks rather than markers.

## Gap signals (used across all sub-trees)

`undefined-term`, `contradictory-rule`, `unspecified-status`, `schema-without-type`, `unimplemented-endpoint`, `undocumented-function`, `language-unsupported-in-v1`, `unspecified-endpoint`, `mismatched-status`, `untested-function`, `unsupported-test-runner`.

## Adding a new seed

1. Pick a dimension key (kebab-case, lowercase).
2. Add the dimension to the `GAP_SIGNALS` list in `tests/test_tc_knowledge_scaffold.py` (for gap signals) or extend the structural assertions (for positive dimensions).
3. Add the seed in the appropriate fixture file, marked with the inline `knowledge: <dimension>` token in the file's native comment syntax. Keep wording domain-neutral.
4. Add a test case in the relevant command test (`test_learn_from_docs.py`, etc.) that asserts the command surfaces the corresponding finding using the helper's universal-core extraction logic.

## Domain-specific seeds

Domain vocabulary (PCI: PAN; HIPAA: PHI; commerce: refund, gift card; research: investigator) does **not** belong in this fixture. Domain-specific extractions are exercised by consuming projects via their own uploaded sources and their own `<workspace>/config.yaml` extensions; they are not part of Test Commander's universal contract (per Decision D19).
