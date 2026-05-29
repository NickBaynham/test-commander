# /tc:traceability-map

Rebuild the cross-cutting traceability maps. The authoritative regenerator of
`traceability/requirements-map.md` (the shared 4-column requirement-to-downstream
view) and `traceability/test-map.md` (the scenario-level chain, with `pending`
downstream links).

## Inputs

- `<workspace>/requirements/requirements-inventory.md` - the requirement
  inventory (produced by `/tc:review-requirements`). Required and must be
  generated, not the template stub.
- `<workspace>/test-ideas/` - test-idea seeds (for the requirements map).
- `<workspace>/bdd/features/*.feature` - scenarios with `@req:`/`@cs:` linkage
  tags (for both maps).
- `<workspace>/traceability/automation-map.md` - scanned for the automation
  column (Phase 6 populates it).

## Outputs

- `<workspace>/traceability/requirements-map.md` - shared 4-column format,
  byte-identical to what `/tc:requirements-coverage` writes.
- `<workspace>/traceability/test-map.md` - Requirement -> Test idea -> BDD
  scenario -> Automated test -> Test result -> Quality report, downstream
  `pending`.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- A generated requirements inventory exists. Otherwise exit 2 with an error
  directing the user at `/tc:review-requirements`.
- No `.feature` files is not an error: the requirements map still lists every
  requirement (BDD-features cell `_(none)_`) and the test map carries the
  empty-note.

## Behavior

1. **Resolve** the workspace and parse the requirement inventory.
2. **Scan** test-ideas, feature files, and the automation map (reusing the
   Phase-2 `requirements_coverage` scanners) to build the requirement rows.
3. **Render** `requirements-map.md` via the shared
   `traceability_render.render_requirements_map`.
4. **Parse** every feature's scenarios (reusing `review_bdd.parse_feature_file`)
   and read their `@req:`/`@cs:` tags into scenario-level rows.
5. **Render** `test-map.md` with `pending` downstream columns.

Both files overwrite deterministically (rows sorted); re-running is
byte-identical. Downstream links are reported `pending`, never invented.

## Safety

- Reads broadly; writes only `traceability/requirements-map.md` and
  `traceability/test-map.md`. From Phase 5 onward this command is the
  authoritative writer of both; the Phase-2 `/tc:requirements-coverage` write is
  a compatible interim seed (shared renderer, no drift). No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/traceability_map.py` (per D18); shared
  renderer `traceability_render.py`.
- Run: `python3 <plugin-root>/scripts/traceability_map.py <project-root>`.
- Reuses `requirements_coverage` scanners and `review_bdd.parse_feature_file`.

## Definition of Done

- Both maps written; requirements-map byte-identical to the Phase-2 writer's
  format; test-map carries the scenario chain with `pending` downstream.
- Idempotent (byte-identical re-run).
- `tc-traceability/SKILL.md` describes the shipped behavior with no deferral
  wording.

## See also

- [Traceability methodology](../methodology/traceability.md) - the chain, the two maps, the linkage-tag join key, Claude judgment layer.
- [Traceability map template](../templates/traceability-map-template.md) - the file shapes.
- [tc-bdd generate-bdd](../../tc-bdd/commands/generate-bdd.md) - emits the `@req:`/`@cs:` tags this map consumes.
- [tc-traceability skill](../SKILL.md)
