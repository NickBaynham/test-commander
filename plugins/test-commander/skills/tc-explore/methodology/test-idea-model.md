# Test idea model

The per-command methodology for `/tc:test-ideas` (Phase 4 Step 4.5). Sits underneath the umbrella [`exploratory-testing.md`](exploratory-testing.md). Covers the Phase-2 `tc-test-idea/v1` schema contract, the Phase-4 enrichment additions, the charter-coverage → REQ-ID cross-reference logic, the idempotency contract, and the Claude judgment layer that operates over the mechanical mapping.

## The `tc-test-idea/v1` schema

Each `<workspace>/test-ideas/<REQ-ID>.md` file ships with YAML frontmatter declaring the schema version and a set of stable keys. The schema is **shared across phases**: Phase 2 (`/tc:requirements-to-tests`) authors the seed; Phase 4 (`/tc:test-ideas`) enriches it; Phase 5 (BDD generation) and Phase 6 (executable test generation) read it. The contract is therefore strict about what is preserved and what may change.

| Key | Owner | Mutability |
| --- | --- | --- |
| `schema` | Phase 2 | Immutable. Always `tc-test-idea/v1` for files this version generates. |
| `requirement_id` | Phase 2 | Immutable. The REQ-NNN identifier the file describes. |
| `requirement_title` | Phase 2 | Immutable. The first-12-word derivation from the requirement body. |
| `source` | Phase 2 | Immutable. The provenance path under `documents/uploaded/`. |
| `status` | Phase 2 | Mutable, controlled-transition. `seed` (Phase 2 author) → `enriched` (Phase 4 enrich). No other transitions are emitted by helpers. |
| `ac_review_present` | Phase 2 | Immutable. Whether the Step 2.4 review existed when the seed was authored. |
| `phase_2_findings` | Phase 2 | Immutable. The rubric dimensions Step 2.2 flagged for this requirement. |
| `candidates` | Phase 2 | Immutable. The happy/edge/negative candidate stubs Step 2.6 emitted. |
| `phase_4_sessions` | Phase 4 | Append-only sorted-deduplicated list of contributing SESS-IDs. Absent on un-enriched seeds. |
| `generated_by` | Phase 2 | Immutable. Always `/tc:requirements-to-tests` for files this version generates. |

The body section structure is similarly stable:

- `# Test ideas for <REQ-ID>` — title heading.
- `## Requirement` — verbatim requirement body, blockquoted.
- `## Candidate scenarios` — the Phase-2 candidate stubs.
- `## Related acceptance-criteria findings` — present iff `ac_review_present: true`.
- `## Phase 2 review findings` — present iff Phase 2 found rubric issues for this REQ.
- `## Notes` — Phase 2 prose pointer to Phase 4.
- `## Phase 4 enrichment` — Phase 4-authored. Contains one `### <SESS-ID>` sub-block per contributing session.
- (Any other section is treated as user-edited content and preserved on re-run.)

## Phase-4 enrichment additions

`/tc:test-ideas` enriches a seed when a session covers the seed's REQ-ID via charter-coverage cross-reference (see below). The mechanical additions per matched (session, seed) pair:

1. **Frontmatter — `status:` flip.** `status: seed` becomes `status: enriched`. Once a file is enriched, the status is sticky (a re-run against the same session leaves it as `enriched`).
2. **Frontmatter — `phase_4_sessions:` merge.** A new inline-list key `phase_4_sessions: [SESS-NNN, ...]` is inserted after `status:` on first enrichment. Subsequent enrichments by additional sessions merge the new SESS-ID into the sorted-deduplicated list. The pre-scan-then-update logic (see the [Step 4.5 lessons](../../../../../planning/plan.md)) prevents the duplicate-key emission bug a naive insert-after-status would produce.
3. **Body — `## Phase 4 enrichment` section.** Appended once. Contains one `### <SESS-ID>` sub-block per contributing session. Each sub-block carries the charter target + mission line plus a bullet list of candidate scenarios from that session, with each candidate's `id`, `type`, `title`, `source`, and optional `linked_anomaly`.
4. **Untouched bytes.** Every other line in the file — `schema:`, `requirement_id:`, `source:`, `ac_review_present:`, `phase_2_findings:`, `candidates:`, `generated_by:`, body sections outside `## Phase 4 enrichment` — survives the enrichment byte-for-byte. The unit tests assert this explicitly.

## Charter-coverage → REQ-ID cross-reference

The mechanical question this helper answers: **for a given session, which REQ-IDs in `<workspace>/test-ideas/` does the session cover?** The answer drives which seeds are enriched.

The matching algorithm:

1. **Session keyword set.** Tokenize the charter mission + charter target + each acceptance criterion + each candidate scenario's `title`, `source`, and `linked_anomaly`. Keep only lowercase alphanumeric runs of length ≥ 4 that are not in the universal English stopword list (`shall`, `system`, `user`, `with`, `from`, `into`, ..., per [D19](../../../../../planning/plan.md)). Reduce each token to its **five-character stem**.
2. **Requirement keyword set.** Tokenize the requirement body from the seed's `## Requirement` section the same way. Reduce to five-character stems.
3. **Match decision.** The session covers the requirement iff the two stem sets share at least one element.

The five-character stem is chosen so morphological variants match (`authentication` ↔ `authenticated` via `authe`; `session` ↔ `sessions` via `sessi`; `workspace` ↔ `workspaces` via `works`) without requiring a real stemmer dependency.

**Worked example (CH-001 against the seeded flawed-requirements fixture):** the seeded charter mentions `sign-in`, `workspace`, `asset`, `session`, `authenticated`, `account`, `expiration`. Against the 17 seeded REQs, ten REQs share a stem with the charter set — including REQ-004 (`authentication`), REQ-005 (`authenticated user account`), REQ-015 (`user session shall persist`), REQ-016 (`authentication credentials`). These ten enrich; the remaining seven (e.g. REQ-013 "The system shall be available for use") share no stem and stay `status: seed`.

The universal English stopword list and the stem length are both designed to err toward **inclusion**: a requirement that shares a single substantive token with the charter is enriched. Over-enrichment is preferable to under-enrichment because the Claude judgment layer (below) prunes irrelevant enrichments; under-enrichment hides session-derived candidates from a REQ that needed them.

## Idempotency contract

Re-running `/tc:test-ideas --session <SESS-ID>` against an unchanged workspace produces **byte-identical** files for every previously-enriched seed, and zero-newly-enriched count. Determinism factors:

- The match decision is a pure function of the session summary content + the seed body content.
- The frontmatter merge is order-stable: existing keys keep their position; `phase_4_sessions:` keeps its position after `status:` once inserted; the sessions list is always sorted-deduplicated.
- The body merge inserts each `### <SESS-ID>` sub-block under a single `## Phase 4 enrichment` header; the per-session sub-block is byte-deterministic against the session summary's candidate list.

When two sessions enrich the same REQ in two separate `/tc:test-ideas` invocations, the second invocation:

- Replaces `phase_4_sessions: [SESS-A]` with `phase_4_sessions: [SESS-A, SESS-B]` (sorted).
- Appends a new `### <SESS-B>` sub-block after the existing `### <SESS-A>` sub-block under the same header.
- Leaves `status: enriched` unchanged.

A third invocation against the same SESS-A leaves the file byte-identical.

## Multi-session resolution rules

When `/tc:test-ideas` runs with no `--session` flag, every session under `<workspace>/sessions/SESS-*.md` is processed in **sorted order** (chronological by the YYYYMMDD prefix, then by the NNN suffix). The sorted-order discipline keeps the resulting `phase_4_sessions:` and `### <SESS-ID>` sub-block ordering stable across re-runs, regardless of filesystem enumeration order.

A session that does not cover any REQ-IDs (the rare case where the charter shares no stems with any requirement) is silently skipped at the (session, seed) loop level; the helper reports an `untouched` count for it.

## Claude judgment layer

The mechanical mapping above is deliberately permissive — it errs toward enriching seeds rather than filtering them. The Claude judgment layer adds:

- **Candidate prioritization within a REQ.** A session may contribute six candidate scenarios to REQ-005 (one per anomaly + three happy-path + edge-case follow-ups). Not all six warrant elevation into a real test. Claude reads the enriched seed plus the consuming project's Phase-3 product-knowledge artifacts and recommends which candidates to elevate, ranked by (a) anomaly severity calibration, (b) coverage gap criticality against the consuming project's risk register, (c) duplication checks against existing automation under `<workspace>/automation-plan/`.
- **Cross-REQ scenario identification.** A single session-derived candidate may span multiple REQs (a `negative` candidate reproducing `auth-mismatch` on `/workspaces/{id}/assets` touches REQ-004 + REQ-005 + REQ-016 simultaneously). Claude reads the enriched files across multiple REQs and identifies these spanning candidates so Phase 5's BDD generation can produce a single feature file that satisfies all three.
- **Stale-enrichment detection.** A seed enriched against a session whose charter target has drifted (the consuming project has migrated the endpoint, or the Phase-3 sources the charter cited have been re-extracted) may carry candidates that no longer reflect the system under test. Claude reads the `phase_4_sessions:` list + the `created_at` of each cited charter + the latest Phase-3 product-knowledge mtimes and flags enrichments that are likely out of date.
- **Acceptance of un-enriched REQs.** A REQ that shares no stems with any charter is a signal: either (a) no exploration has targeted that REQ's feature area yet (author a new charter), or (b) the REQ is too abstract for exploration to reach (e.g. REQ-013 "shall be available for use"). Claude reads the un-enriched REQs and recommends which to follow up on with a new `/tc:create-charter` invocation versus which to mark as acceptable as Phase-2 seeds without Phase-4 enrichment.

## Configurable extensions

The Step 4.5 v1 ships no new `<workspace>/config.yaml` schema keys — the enrichment behavior reuses the universal stopword list and five-character stem matching with no project-tuning surface. Project-specific keyword tuning is deferred to a hypothetical v2 surface (`tc-explore.test-ideas.stopwords-extend:`, `tc-explore.test-ideas.stem-length:`) once cross-project usage data shows the universal defaults are insufficient.

Project-specific extension paths that DO exist already and shape this helper's input:

- `tc-explore.charters.risk-keywords` and `tc-explore.charters.area-keywords` (Step 4.2) tune which charters get authored, which in turn tunes the session keyword set this helper builds.
- The consuming project's uploaded requirements (`<workspace>/documents/uploaded/`) define the REQ-NNN seeds the helper enriches; project-domain vocabulary enters here per [D19](../../../../../planning/plan.md).

## See also

- [Umbrella methodology](exploratory-testing.md)
- [Session-based-test-management methodology](session-based-test-management.md) — the producer side of the candidate-shape contract.
- [Charter-based-exploration methodology](charter-based-exploration.md) — the upstream charter the cross-reference reads.
- [Per-command page: /tc:test-ideas](../commands/test-ideas.md)
- [Test-idea enrichment template](../templates/test-idea-enrichment-template.md)
- [Per-command page: /tc:requirements-to-tests (Phase 2)](../../tc-requirements/commands/requirements-to-tests.md) — the seed generator.
