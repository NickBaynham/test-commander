# /tc:generate-bdd

Turn Phase-4-enriched test-idea seeds into Gherkin feature files with full
traceability. One Gherkin `Scenario` per Phase-4 enrichment candidate
(`CS-NNN-NNN`), each carrying machine-readable `@req:`/`@cs:` linkage tags.

## Inputs

- `<workspace>/test-ideas/REQ-NNN.md` - **enriched** test-idea seeds (the
  `## Phase 4 enrichment` candidate bullets are the scenario source). Required:
  at least one seed with `status: enriched`.
- `<workspace>/sessions/SESS-*.md` - referenced for provenance (cited in the
  feature comment and summary).
- `<workspace>/product-knowledge/` - read by Claude for the judgment layer
  (refining steps into domain-grounded language).
- `<workspace>/config.yaml` - optional `tc-bdd.tags.extra-classes` extension.
- CLI: `--req REQ-NNN` to generate for a single requirement; omit for all
  enriched seeds.

## Outputs

- `<workspace>/bdd/features/<area>.feature` - one Gherkin feature per
  requirement, `<area>` derived as a slug of the requirement title.
- `<workspace>/bdd/summaries/<area>.md` - a per-feature summary.
- `<workspace>/bdd/index.md` - the feature index (rebuilt every run).

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- At least one enriched test-idea seed exists. Otherwise exit 2 with an error
  directing the user at `/tc:test-ideas` (after `/tc:requirements-to-tests`).

## Behavior

1. **Resolve** the workspace and discover enriched seeds (`--req` selects one).
2. **Parse** each seed's `## Phase 4 enrichment` candidate bullets into
   `Scenario` records (`req_id`, `cs_id`, `type`, `title`, `source`,
   `linked_anomaly`) - the same field shape `enrich_test_ideas.py` emits.
3. **Render** one Gherkin `Scenario` per candidate with concrete,
   behavior-level Given/When/Then steps and the linkage + class tags. The
   render shape is documented in
   [`templates/feature-template.feature`](../templates/feature-template.feature).
4. **Write** the per-feature summary
   ([`templates/bdd-summary-template.md`](../templates/bdd-summary-template.md)).
5. **Rebuild** `bdd/index.md` by scanning every `bdd/features/*.feature`.

Tagging: `@area:<slug>` + `@req:<REQ-ID>` + `@cs:<CS-ID>` on every scenario; a
class tag mapped from the candidate type (`happy`/`positive` -> `@smoke`,
`edge`/`negative` -> `@regression`); `@exploratory` + `@anomaly:<category>` when
the candidate is anomaly-derived; plus any `tc-bdd.tags.extra-classes`.

Output is deterministic: scenarios sort by `cs_id`, index rows by filename,
overwrite mode. Re-running against unchanged input is byte-identical.

The review sub-mode (auto-run after generation, suppressible with
`--no-review`) is wired in Step 5.3; until then, run `/tc:review-bdd`
separately once it ships.

## Safety

- Reads broadly but writes only under `<workspace>/bdd/`. Never writes
  `test-ideas/` (Phase 4 owns enrichment) or `traceability/` (Phase 5's
  `/tc:traceability-map`).
- No network, no browser, fully offline and deterministic.

## Implementation

- Helper: `plugins/test-commander/scripts/generate_bdd.py` (per D18).
- Run: `python3 <plugin-root>/scripts/generate_bdd.py <project-root> [--req REQ-NNN]`.
- Mirrors the Phase 4 `enrich_test_ideas.py` skeleton; unique work is the
  enrichment-candidate parser, the Gherkin renderer, and the index sweep.

## Definition of Done

- Generates valid Gherkin with resolvable `@req:`/`@cs:` tags and an `@area:`
  tag on every scenario.
- Writes the per-feature summary and rebuilds the index.
- Idempotent (byte-identical re-run).
- `tc-bdd/SKILL.md` describes the shipped generation behavior.

## See also

- [BDD generation methodology](../methodology/bdd-generation.md) - workflow, Gherkin discipline, linkage-tag convention, Claude judgment layer.
- [Feature template](../templates/feature-template.feature) - the render shape.
- [BDD summary template](../templates/bdd-summary-template.md) - the summary shape.
- [tc-bdd skill](../SKILL.md)
- [Seeded enriched test-idea (REQ-001)](../../../../../tests/fixtures/seeded-bdd/REQ-001.md) - worked example input.
