# Seeded automation fixture

This directory is the shared fixture for Phase 6 (`tc-build-framework`,
`tc-automation-plan`, `tc-automate`, `tc-test-data`). Unlike the Phase 5
`seeded-bdd` fixture (which seeds one defect per review category), this one
carries a **clean, automatable** feature — the shape `/tc:generate-bdd`
emits when its input is clean. It is a **deliberately generic, universal
SaaS narrative** (sign-in / accounts / sessions / workspaces / assets),
reusing the entity vocabulary of the Phase 3 `seeded-sample-project`, Phase 4
`seeded-exploration-session`, and Phase 5 `seeded-bdd` fixtures so the Phase 6
integration smoke composes without translation. Nothing here is a claim about
any real product's scope (per Decision D19).

## Files

| File | Role |
| --- | --- |
| `sign-in.feature` | A clean Gherkin feature whose every scenario is an `@automated-candidate` carrying resolvable `@req:`/`@cs:` linkage tags, behavior-level steps, and an `@area:` namespace. The input to `/tc:automation-plan` and `/tc:automate`. |
| `README.md` | This file. |

## Linkage-tag convention

Each automatable scenario carries machine-readable provenance tags so
`/tc:automate` can stamp the generated TypeScript with its origin and
`/tc:traceability-map` can resolve the trace map mechanically:

- `@req:REQ-NNN` — the requirement the scenario traces to.
- `@cs:CS-NNN-NNN` — the candidate scenario (from a session summary / enrichment) the scenario realizes.
- `@automated-candidate` — the scenario is suitable for automation; `/tc:automation-plan` always ranks it `automate`.

Universal class tags (`@smoke`, `@regression`) and project namespaces
(`@area:<feature>`) round out the tag set. Test Commander ships the
namespaces; the consuming project picks values under `tc-bdd.tags.*`.
