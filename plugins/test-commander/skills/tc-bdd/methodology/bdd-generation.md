# BDD generation (umbrella methodology)

This is the umbrella methodology for the `tc-bdd` skill. It documents how Test
Commander turns reviewed requirements and Phase-4-enriched test ideas into
Gherkin feature files with full traceability, and how Claude layers judgment on
top of the deterministic helper output.

## Workflow

```
requirements review (Phase 2)
  + exploration + enriched test ideas (Phase 4)
      -> /tc:generate-bdd   -> bdd/features/<area>.feature
                               bdd/summaries/<area>.md
                               bdd/index.md
      -> /tc:review-bdd      -> review verdict + [bdd-review] gap signals
      -> /tc:traceability-map-> traceability/requirements-map.md + test-map.md
```

`/tc:generate-bdd` reads each enriched `<workspace>/test-ideas/REQ-NNN.md` seed
and renders one Gherkin `Scenario` per Phase-4 enrichment candidate
(`CS-NNN-NNN`). The helper is deterministic scaffolding; Claude refines it. The
standalone `/tc:review-bdd` command (and the review sub-mode it shares) lands in
Step 5.3.

## What the helper does (deterministic)

- Parses the `## Phase 4 enrichment` candidate bullets into a `Scenario`
  record (`req_id`, `cs_id`, `type`, `title`, `source`, `linked_anomaly`) -
  the same field shape `enrich_test_ideas.py` and `session_summary.py` emit, so
  the contract is enforced at three layers (producer dataclass, producer tests,
  this consumer parser).
- Emits one Gherkin `Scenario` per candidate with concrete, behavior-level
  Given/When/Then steps that reference the candidate title.
- Tags every scenario for traceability and classification (see below).
- Writes a per-feature summary and rebuilds the feature index.

## What Claude does (judgment layer)

- Rewrites the scaffold Given/When/Then into precise, domain-grounded steps
  using the project's product-knowledge vocabulary.
- Promotes a `Scenario` to a `Scenario Outline` with an `Examples:` table when
  the candidate is data-driven (multiple inputs, same behavior).
- Decides which candidates are worth a scenario versus noise, and which
  scenarios should carry `@manual` (not automatable) versus
  `@automated-candidate`.
- Adds project namespace tag values (`@area:`, `@risk:`, `@persona:`) that the
  deterministic helper cannot infer.

## Gherkin authoring discipline

- **Behavior, not UI.** Steps describe what the system does, not how the user
  clicks. Avoid selectors, element IDs, raw URLs, and "clicks the button".
- **Atomic steps.** One behavior per step. A step that chains behaviors with
  `and` hides multiple assertions and is not independently verifiable.
- **Concrete, not vague.** Avoid "does something", "it works", "behaves
  correctly". Name the subject and the outcome.
- **Scenario Outline needs Examples.** Never ship an outline without its table.

These rules are exactly what `/tc:review-bdd` (Step 5.3) checks mechanically;
the universal rubric categories are `ambiguous-step`, `missing-tag`,
`untraceable`, `ui-coupled-step`, `missing-examples`, and
`conjunction-overload`.

## Linkage-tag convention

Every generated scenario carries machine-readable provenance so
`/tc:traceability-map` can rebuild the trace map mechanically:

- `@req:REQ-NNN` - the requirement the scenario traces to.
- `@cs:CS-NNN-NNN` - the candidate scenario the scenario realizes.
- `@anomaly:<category>` - present when the source candidate was anomaly-derived.

Universal class tags map from the candidate type: `happy`/`positive` -> `@smoke`;
`edge`/`negative` -> `@regression`; anomaly-derived candidates also carry
`@exploratory`. The remaining universal classes (`@manual`,
`@automated-candidate`) are applied by Claude during refinement.

## Tag namespaces (project-extensible, D19)

Test Commander ships the namespaces; the consuming project picks the values.

- `@area:<feature>` - feature area (the helper derives a slug from the
  requirement title; projects override during refinement).
- `@risk:<class>` - risk class (severity or category).
- `@persona:<role>` - persona.

Projects union additional class tags onto every generated scenario via
`tc-bdd.tags.extra-classes` in `<workspace>/config.yaml`.

## Cross-phase write boundary

`/tc:generate-bdd` reads `<workspace>/test-ideas/`, `<workspace>/sessions/`, and
`<workspace>/product-knowledge/`. It writes only under `<workspace>/bdd/`. It
does not write `test-ideas/` (Phase 4 owns enrichment) or `traceability/`
(Phase 5's `/tc:traceability-map` owns the maps).

## See also

- [generate-bdd command page](../commands/generate-bdd.md)
- [Feature template](../templates/feature-template.feature)
- [BDD summary template](../templates/bdd-summary-template.md)
- [tc-bdd skill](../SKILL.md)
- [Phased plan](../../../../../planning/plan.md)
