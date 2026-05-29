# Phase 5 — BDD Generation and Traceability (implementation summary)

Status: complete 2026-05-29, tagged `phase-5` on origin. Two skills shipped —
`tc-bdd` and `tc-traceability` — adding three commands. This document
summarizes what Phase 5 delivered, the user-facing capabilities it unlocked,
and the capabilities that already existed prior to Phase 5.

Authoritative sources: [CHANGELOG.md](../CHANGELOG.md) (per-sub-step shipping
log), [planning/plan.md](../planning/plan.md) (the Phase 5 section, Completed
entry, and lessons learned), and the user walkthrough
[docs/user-guide/generating-bdd.md](../docs/user-guide/generating-bdd.md).

## What existed prior to Phase 5 (Phases 0–4)

By the close of Phase 4, Test Commander was a Claude Code plugin plus a small
Python runtime that took a project from raw requirements through exploratory
testing, writing every artifact into a committed `.test-commander/` workspace.
The shipped surface:

| Phase | Skill | Commands | Capability |
| --- | --- | --- | --- |
| 0 | — | — | Repository foundation: marketplace + plugin manifest, `bootstrap.sh`, `make install`, the verify chain (`ruff`, `pytest`, `verify_skills.py`, `check_links.py`). |
| 1 | `tc-core` | `/tc:init`, `/tc:status`, `/tc:journal`, `/tc:next` | Initialize the committed `.test-commander/` workspace, summarize its state, append a journal, and recommend the next command. |
| 2 | `tc-requirements` | `/tc:review-requirements`, `/tc:review-user-stories`, `/tc:review-acceptance-criteria`, `/tc:requirements-coverage`, `/tc:requirements-to-tests` | Review requirements / stories / acceptance criteria against a universal rubric; build the requirements inventory; seed `test-ideas/REQ-*.md` files (the `tc-test-idea/v1` schema) and the first traceability map. |
| 3 | `tc-knowledge` | `/tc:learn-from-docs`, `/tc:learn-from-specs`, `/tc:learn-from-code`, `/tc:learn-from-api`, `/tc:learn-from-tests` | Ingest narrative docs, OpenAPI/Postman specs, Python source, recorded API responses, and existing tests into a structured `product-knowledge/` model (entities, journeys, business rules, system model). |
| 4 | `tc-explore` | `/tc:create-charter`, `/tc:explore`, `/tc:session-summary`, `/tc:test-ideas` | Charter-based exploratory testing: scope a session, replay a recorded Playwright MCP session (or drive a live one), synthesize per-session summaries, and **enrich** the Phase-2 test-idea seeds with exploration-derived candidate scenarios (`status: seed` → `enriched`, a `## Phase 4 enrichment` body section). |

What was missing at the end of Phase 4: the enriched test ideas were the
furthest-downstream artifact. There was no executable behavior specification
(no Gherkin), no review of such specs, and no single cross-cutting map tying a
requirement forward to the scenarios that exercise it. Phase 5 fills that gap.

## What Phase 5 delivered

Phase 5 turns the Phase-4-enriched test ideas into reviewable Gherkin feature
files with full traceability, via two new skills.

### `tc-bdd` — generation and review

- **`/tc:generate-bdd`** ([command page](../plugins/test-commander/skills/tc-bdd/commands/generate-bdd.md)).
  Reads each enriched `test-ideas/REQ-*.md` seed and renders one Gherkin
  `Scenario` per Phase-4 enrichment candidate (`CS-NNN-NNN`) into
  `.test-commander/bdd/features/<area>.feature`. Every scenario carries
  machine-readable provenance — `@req:REQ-NNN`, `@cs:CS-NNN-NNN`, plus
  `@anomaly:<category>` when anomaly-derived — a universal class tag mapped from
  the candidate type (`happy`/`positive` → `@smoke`; `edge`/`negative` →
  `@regression`), and an `@area:` namespace tag. It also writes a per-feature
  summary, rebuilds `bdd/index.md`, and auto-runs the review sub-mode
  (suppressible with `--no-review`). The helper produces a deterministic,
  byte-stable scaffold; Claude refines the Given/When/Then into domain language,
  promotes data-driven scenarios to `Scenario Outline`, and adds `@risk:` /
  `@persona:` values.
- **`/tc:review-bdd`** ([command page](../plugins/test-commander/skills/tc-bdd/commands/review-bdd.md)).
  Runs a deterministic six-category universal rubric over every feature —
  `ambiguous-step`, `missing-tag`, `untraceable`, `ui-coupled-step`,
  `missing-examples`, `conjunction-overload` — writes a verdict into each
  feature's summary (`pass` or `N finding(s)`), and routes failures to
  `requirements/open-questions.md` as deduplicated `[bdd-review]` gap signals.
  The shared `review_features()` implementation is exactly what
  `/tc:generate-bdd` auto-runs.

### `tc-traceability` — the cross-cutting map

- **`/tc:traceability-map`** ([command page](../plugins/test-commander/skills/tc-traceability/commands/traceability-map.md)).
  The authoritative regenerator of two maps under `.test-commander/traceability/`:
  - `requirements-map.md` — the shared four-column requirement → downstream view
    (REQ-ID / Test ideas / BDD features / Automation), rendered identically to
    `/tc:requirements-coverage` via the extracted `traceability_render.py`, so
    the file is byte-identical whichever command wrote it (no format drift).
  - `test-map.md` — the scenario-level chain: Requirement → Test idea (CS) → BDD
    scenario → Automated test → Test result → Quality report. The three
    downstream columns render `pending` (never invented) until Phases 6–7
    populate them.

### Cross-cutting concepts introduced

- **Linkage tags as the traceability contract.** `@req:`/`@cs:` tags emitted by
  the generator are the mechanical join key the mapper parses — the same field
  shape the Phase-4 enrichment produces, closing the requirement → test idea →
  scenario contract triangle.
- **The full traceability chain, with honest placeholders.** Phase 5 populates
  the first three links and reports everything downstream as `pending`.
- **Project extensibility (D19).** Universal cores ship by default; projects tune
  via `<workspace>/config.yaml`: `tc-bdd.tags.extra-classes` (extra class tags
  on every scenario) and `tc-bdd.review.rubric-extensions` (extra vague-word /
  UI-word tokens). See
  [customizing-for-your-project.md](../docs/user-guide/customizing-for-your-project.md).

## Key features available to the user after Phase 5

1. **Generate traceable BDD specs from enriched test ideas** — `/tc:generate-bdd`
   produces Gherkin `.feature` files where every scenario links back to its
   requirement and candidate test idea.
2. **Mechanical BDD quality review** — `/tc:review-bdd` (and the generate-time
   auto-run) flags ambiguous, untraceable, UI-coupled, or non-atomic scenarios
   and records the findings as deduplicated open questions.
3. **A single cross-cutting traceability map** — `/tc:traceability-map` rebuilds
   the requirement and scenario-level maps on demand, showing exactly which
   requirements have BDD coverage and which downstream links remain `pending`.
4. **End-to-end workflow** — the four prior phases plus Phase 5 now run as one
   chain: requirements → knowledge → exploration → enriched test ideas → BDD →
   traceability, all committed under `.test-commander/`. Walkthrough:
   [generating-bdd.md](../docs/user-guide/generating-bdd.md).
5. **Project-tunable tags and review rubric** without touching shipped defaults.

## Implementation breakdown (sub-steps 5.1–5.7)

| Sub-step | What landed |
| --- | --- |
| 5.1 | Scaffolded both skills + the `seeded-bdd` fixture (an enriched `REQ-001.md`, a session summary, and `flawed.feature` with one defect per review category); strict-PyYAML frontmatter assertion baked into both scaffold tests from the start. |
| 5.2 | `/tc:generate-bdd` (generation only) — `generate_bdd.py`, the `Scenario` dataclass, the umbrella `bdd-generation.md` methodology, the feature + summary templates, and the scan-and-index rebuild of `bdd/index.md`. |
| 5.3 | `/tc:review-bdd` + the shared `review_features()` + wiring the generate-time auto-run into `generate_bdd.py`; the six-category rubric and `bdd-quality-review.md`. |
| 5.4 | `/tc:traceability-map` — extracted the shared `traceability_render.py` from `requirements_coverage.py` (keeping Phase-2 output byte-identical), then the authoritative regenerator writing `requirements-map.md` + the new `test-map.md`. |
| 5.5 | Documentation pass — `generating-bdd.md`, command-reference, workspace-reference, the customization-guide Phase 5 schema with three project-shape examples, and six status-line locations. |
| 5.6 | Testing finalization — `DEFAULT_PHASE_CAP` 4 → 5 (both skills flip to `PRESENT`) and `test_phase_5_integration.py` (full Phase 2 → 3 → 4 → 5 sweep). |
| 5.7 | Sign-off — cold-user walkthrough from a clean `make install`, per-step DoD audit, plan + CHANGELOG closing, the test-first `test_phase_5_signoff.py`, and the annotated `phase-5` tag. |

Three deliberate plan refinements were made during implementation and recorded
as lessons: review wiring was deferred from 5.2 to 5.3 to avoid a forward
dependency; the scenario-level detail went into a new `test-map.md` rather than
a new column on the shared `requirements-map.md` (avoiding format drift); and
the integration-test assumption was corrected when the deliberately-flawed
requirements fixture correctly produced review-flagged BDD (the generate→review
pipeline working as designed, not a bug).

## Post-close fix relevant to the user experience

Immediately after Phase 5 closed, a long-standing `/tc:next` defect (flagged in
Phase 2 and latent until Phases 3–5 all shipped) was fixed: the next-step
heuristic had treated user-uploaded inputs and cross-phase writes as evidence
that a later phase had started, so after only Phase 2 it would skip straight to
recommending Phase 6. The phase status signal now keys only on directories each
phase uniquely produces, so the recommended sequence is correct end to end. See
[CHANGELOG.md](../CHANGELOG.md) `[Unreleased] → Fixes`.

## Quality state at Phase 5 close

- 518 tests passing (the `/tc:next` fix brought it to 519); `ruff` clean;
  `check_links.py` clean across 172 files.
- `verify_skills.py` reports all six shipped skills `PRESENT` (`tc-core`,
  `tc-requirements`, `tc-knowledge`, `tc-explore`, `tc-bdd`, `tc-traceability`)
  with `UNEXPECTED=0`.
- Both `tc-bdd` and `tc-traceability` describe every shipped command with no
  deferral wording; `claude plugin validate` passes on both manifests.

## What comes next (Phase 6)

Phase 6 (Playwright framework + strategic automation) consumes the Phase 5 BDD
output: it scores scenarios for automation suitability, generates a
Playwright/TypeScript suite, and resolves the `Automated test` column of
`test-map.md`. Phase 6 is broken into nine sub-steps in
[planning/plan.md](../planning/plan.md); implementation has not started.
