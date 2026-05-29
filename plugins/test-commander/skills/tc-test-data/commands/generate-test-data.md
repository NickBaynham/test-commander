# /tc:generate-test-data

Populate `<workspace>/test-data/` from the BDD scenarios so the per-area fixture
`/tc:automate` generates reaches its data through a file, never inlining it
(Decision D6).

## Inputs

- `<workspace>/bdd/features/*.feature` - the scenarios. Each scenario's `@req:`
  and `@cs:` tags key the generated records. Required: at least one feature.
- `<workspace>/product-knowledge/` - read by Claude for the judgment layer
  (fleshing out realistic field values).

## Outputs

- `<workspace>/test-data/seed/<area>.json` - the JSON fixture the generated
  per-area fixture loads. One record per `@cs:` candidate.
- `<workspace>/test-data/scenarios/<area>.md` - a Markdown spec of each
  scenario's declarative data requirement.
- `<workspace>/test-data/factories/` - left for hand-authored Python factories
  where declarative data is insufficient (never written here).

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- At least one BDD feature exists. Otherwise exit 2 with an error directing the
  user at `/tc:generate-bdd`.

## Behavior

1. **Resolve** the workspace and scan `bdd/features/*.feature`.
2. **Extract** one record per scenario with a resolvable `@req:`/`@cs:` linkage,
   sorted by candidate id.
3. **Write** `test-data/seed/<area>.json` (the fixture's data) and
   `test-data/scenarios/<area>.md` (the data spec).

Overwrite mode for *generated* files (those carrying the generated marker);
**skip-not-overwrite** for user-authored files (no marker), so hand-tuned data
survives. Deterministic: records sort by `@cs:` id; byte-stable re-run.

The generated seed is a universal scaffold (generic records keyed by candidate
id); Claude fleshes out realistic, scenario-appropriate field values from
`product-knowledge/`.

## Safety

- Writes only under `<workspace>/test-data/seed/` and
  `<workspace>/test-data/scenarios/`. Never writes `bdd/` (Phase 5),
  `product-knowledge/` (Phase 3), or `test-data/factories/` (hand-authored).
- Never overwrites a user-authored (marker-less) file.
- No network, no browser, fully offline and deterministic.

## Implementation

- Helper: `plugins/test-commander/scripts/generate_test_data.py` (per D18).
- Run: `python3 <plugin-root>/scripts/generate_test_data.py <project-root>`.
- Mirrors `enrich_test_ideas.py`; reuses `review_bdd.parse_feature_file`. Unique
  work is the per-scenario record extraction, the JSON/Markdown renderers, and
  the skip-not-overwrite marker logic.

## Definition of Done

- Test data populated under `.test-commander/test-data/`, reached via a fixture,
  nothing inline (D6).
- Seed JSON is valid and carries the generated marker; user-authored data
  preserved.
- Idempotent (byte-identical re-run).
- `tc-test-data/SKILL.md` describes the shipped behavior.

## See also

- [Test data strategy](../methodology/test-data-strategy.md) - the three surfaces, overwrite vs preserve, and the judgment layer.
- [Test data template](../templates/test-data-template.json) - the seed JSON shape.
- [tc-test-data skill](../SKILL.md)
- [tc-automate skill](../../tc-automate/SKILL.md) - the fixtures that read this data.
