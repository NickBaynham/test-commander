# Seeded BDD fixture

This directory is the shared fixture for Phase 5 (`tc-bdd` + `tc-traceability`).
It is a **deliberately generic, universal SaaS-dashboard narrative** (sign-in /
accounts / workspaces / assets), reusing the entity vocabulary of the Phase 3
`seeded-sample-project` and Phase 4 `seeded-exploration-session` fixtures so the
Phase 5 integration smoke composes without translation. Nothing here is a claim
about any real product's scope (per Decision D19).

## Files

| File | Role |
| --- | --- |
| `REQ-001.md` | A Phase-4-**enriched** test-idea seed (`status: enriched`, `tc-test-idea/v1` schema). The primary input to `/tc:generate-bdd`. Carries a `## Phase 4 enrichment` section whose `### SESS-...` sub-block lists candidate scenarios as `- **CS-NNN-NNN**` bullets — the real shape `enrich_test_ideas.py` emits. |
| `SESS-20260115-001.md` | A session summary (the second generator input). Carries `### CS-NNN-NNN` candidate blocks — the real shape `session_summary.py` emits. |
| `flawed.feature` | A Gherkin file seeding exactly one defect per universal BDD-review category, for the Step 5.3 review helper to catch. |
| `README.md` | This file. |

## Linkage-tag convention

Generated scenarios carry machine-readable provenance tags so `/tc:traceability-map`
can rebuild the trace map mechanically:

- `@req:REQ-NNN` — the requirement the scenario traces to.
- `@cs:CS-NNN-NNN` — the candidate scenario (from a session summary / enrichment) the scenario realizes.
- `@anomaly:<category>` — present when the source candidate was anomaly-derived.

Universal class tags (`@smoke`, `@regression`, `@manual`, `@exploratory`,
`@automated-candidate`) and project namespaces (`@area:<feature>`,
`@risk:<class>`, `@persona:<role>`) round out the tag set. Test Commander ships
the namespaces; the consuming project picks values under `tc-bdd.tags.*`.

## Universal BDD-review categories

The marker convention is the literal token `knowledge: <category>` carried in
each file's native comment syntax (Gherkin `#` comments here). The six universal
categories seeded in `flawed.feature`:

- `knowledge: ambiguous-step` — vague Given/When/Then with no concrete subject or outcome.
- `knowledge: missing-tag` — scenario lacking a required namespace tag (`@area:` or a linkage tag).
- `knowledge: untraceable` — scenario with no resolvable `@req:`/`@cs:` linkage tag.
- `knowledge: ui-coupled-step` — steps describing clicks/selectors/URLs instead of behavior.
- `knowledge: missing-examples` — a `Scenario Outline` with no `Examples:` table.
- `knowledge: conjunction-overload` — a step chaining multiple behaviors so it is not atomically assertable.
