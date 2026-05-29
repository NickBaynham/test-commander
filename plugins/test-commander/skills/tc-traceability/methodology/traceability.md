# Traceability

Methodology for `/tc:traceability-map`. Test Commander maintains a single
cross-cutting traceability chain and regenerates it deterministically from the
artifacts each phase produces.

## The chain

```
Requirement -> Test Idea -> BDD Scenario -> Automation Candidate
            -> Automated Test -> Test Result -> Quality Report
```

Phase 5 populates the first three links (Requirement, Test Idea, BDD Scenario).
Automation Candidate is partial (Phase-4 enriched test ideas); Automated Test is
Phase 6; Test Result and Quality Report are Phase 7. Links a later phase owns
render `pending` and are **never invented** - the map reports honestly what
exists today.

## The two maps

`/tc:traceability-map` is the authoritative regenerator of both maps under
`<workspace>/traceability/`. Overwrite mode; byte-deterministic.

### `requirements-map.md` (shared format)

The requirement-to-downstream view: one row per requirement with the
test-idea, BDD-feature, and automation artifacts that trace back to it. This is
the **same 4-column format** `/tc:requirements-coverage` (Phase 2) writes -
both helpers call the shared `traceability_render.render_requirements_map`, so
the file is byte-identical whichever command wrote it. The Phase-2 write is a
compatible interim seed; from Phase 5 onward `/tc:traceability-map` is the
authoritative writer. There is no format drift to reconcile.

### `test-map.md` (scenario-level)

The scenario-level chain, one row per BDD scenario: Requirement -> Test idea
(the `CS-NNN-NNN` candidate) -> BDD scenario -> Automated test -> Test result
-> Quality report. The three downstream columns render `pending`. This is where
the scenario-grained "BDD-scenario" detail lives, so the requirements map stays
the drift-free shared 4-column shape.

## The linkage tags are the join key

`/tc:generate-bdd` emits machine-readable `@req:REQ-NNN` and `@cs:CS-NNN-NNN`
tags on every scenario. `/tc:traceability-map` parses those tags (reusing
`review_bdd.parse_feature_file`) to build the test-map mechanically - the tag is
the contract between the generator and the mapper. A scenario with no `@req:`
tag is invisible to the map; `/tc:review-bdd` flags it as `untraceable`.

## Claude judgment layer

The mechanical map records what traces to what; Claude reads it to:

- spot requirements with zero scenarios (coverage gaps);
- spot scenarios that span multiple requirements (candidate splits);
- prioritise which `pending` downstream links to close first by risk.

## See also

- [traceability-map command page](../commands/traceability-map.md)
- [Traceability map template](../templates/traceability-map-template.md)
- [tc-traceability skill](../SKILL.md)
- [tc-bdd generate-bdd](../../tc-bdd/commands/generate-bdd.md) - emits the linkage tags this map consumes.
- [Phased plan](../../../../../planning/plan.md)
