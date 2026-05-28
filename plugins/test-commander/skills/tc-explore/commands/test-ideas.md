# `/tc:test-ideas`

The Phase 4 test-idea enrichment command. Reads session summaries produced by `/tc:session-summary` and the Phase-2 test-idea seeds produced by `/tc:requirements-to-tests`, then enriches each seed whose REQ-ID is covered by a session with the session's candidate scenarios. Preserves every Phase-2 frontmatter key byte-for-byte, flips `status: seed` to `status: enriched`, merges `phase_4_sessions:` (sorted, deduplicated), and appends a `## Phase 4 enrichment` body section with one `### <SESS-ID>` sub-block per contributing session.

## Inputs

- `--session <SESS-ID>` (optional) — restrict enrichment to a single session. When omitted, every `<workspace>/sessions/SESS-*.md` is processed in sorted order.
- `<workspace>/sessions/<SESS-ID>.md` — the session summary written by `/tc:session-summary`. Refused with a precondition error pointing at `/tc:session-summary` when no session summaries exist (or the requested SESS-ID is missing).
- `<workspace>/test-ideas/REQ-*.md` — the Phase-2 seeds written by `/tc:requirements-to-tests`. Refused with a precondition error pointing at `/tc:requirements-to-tests` when none exist.

## Outputs

| Path | Mode | Owner |
| --- | --- | --- |
| `<workspace>/test-ideas/REQ-NNN.md` | in-place merge (frontmatter-preserving; body-appending) | this command |
| stdout | informational CLI report listing every enriched path | this command |

The helper never touches `<workspace>/sessions/`, `<workspace>/exploration-notes/`, `<workspace>/charters/`, `<workspace>/requirements/`, `<workspace>/product-knowledge/`, or `<workspace>/traceability/`. Those are owned by Step 4.4, Step 4.3, Step 4.2, Phase 2, Phase 3, and Phase 5 respectively.

## Preconditions

- `<workspace>/.test-commander/` exists (`/tc:init` has run).
- `<workspace>/sessions/` contains at least one `SESS-*.md` (write one with `/tc:session-summary --session <SESS-ID>` first).
- `<workspace>/test-ideas/` contains at least one `REQ-*.md` seed (write them with `/tc:requirements-to-tests` after `/tc:review-requirements`).

## Behavior

1. Resolve the workspace.
2. Discover the session summary set: when `--session` is given, the single named summary; otherwise every `sessions/SESS-*.md`. Refuse with precondition error if the set is empty.
3. Discover the test-idea seed set (`test-ideas/REQ-*.md`). Refuse with precondition error if the set is empty.
4. Parse each session summary: extract the SESS-ID + CH-ID from the title heading, the charter target + mission from the Session bullets, the acceptance criteria from the Charter Coverage Summary table, and the candidate scenarios from the per-candidate `### CS-NNN-NNN` sub-blocks (each candidate carries `id`, `title`, `type`, `source`, and optional `linked_anomaly`).
5. For every (session, seed) pair, decide whether the session covers the seed's REQ-ID via charter-coverage keyword cross-reference:
   - Build the session's keyword set as the union of significant tokens (length ≥ 4, lowercase, excluding a small universal-English stopword list per [D19](../../../../../planning/plan.md)) from the charter mission, charter target, each acceptance criterion, and each candidate's title + source + linked anomaly.
   - Build the seed's keyword set from the verbatim requirement body inside its `## Requirement` section.
   - Match by **five-character stem** so `authentication` (requirement) and `authenticated` (charter) match, and `session` and `sessions` match. A non-empty stem intersection means the session covers the requirement.
6. For each matched (session, seed):
   - Re-render the frontmatter in place, preserving every existing line byte-for-byte except: flip `status: seed` to `status: enriched`; merge `phase_4_sessions:` to the sorted-deduplicated union of existing IDs plus the new SESS-ID.
   - Append a `## Phase 4 enrichment` body section if absent; under it, append a `### <SESS-ID>` sub-block listing each candidate with its id, type, title, source, and linked anomaly.
7. Skip writes whose merge would be a no-op (the session was already present in `phase_4_sessions:` AND already had a sub-block in the body); the helper is byte-deterministic on re-run.
8. Exit 0 with a CLI summary line naming the enriched count and listing every touched path.

## Safety

- No network; no shell-out; no writes outside `<workspace>/test-ideas/`.
- Frontmatter contract preservation is asserted at the unit-test level — every Phase-2 key the seed shipped with is present and unchanged after enrichment (except `status:`).
- User-edited body sections survive re-run: the helper only appends to `## Phase 4 enrichment`; sections outside that header are left untouched.
- Idempotent: re-running produces byte-identical files for already-enriched seeds and zero duplicate enrichment sections.
- Per the Phase 4 cross-phase write-boundary discipline, this helper writes only to `<workspace>/test-ideas/`. The traceability map (`<workspace>/traceability/`) is owned by Phase 2 (which refreshes it during `/tc:requirements-to-tests`) and Phase 5; Phase 4 reads but does not write.

## Implementation

- Helper: `plugins/test-commander/scripts/enrich_test_ideas.py` (~510 lines).
- Mirrors the Phase 4 helper-mirroring skeleton from Steps 4.2-4.4. The unique work concentrates in (a) session-summary parsing — `### CS-NNN-NNN` block regex + per-field bullet regex per the Step 4.4 contract note, (b) the charter-coverage keyword cross-reference using five-character stem matching, (c) the frontmatter-preserving merge that pre-scans for existing `phase_4_sessions:` before deciding insert-vs-update (preventing the duplicate-key bug; see Phase 4 Lessons learned), and (d) the body merge that appends per-SESS-ID sub-blocks idempotently under a single `## Phase 4 enrichment` header.
- The consumer-side `CandidateScenario` dataclass mirrors `session_summary.CandidateScenario` field-for-field per the Step 4.4 lesson on three-layer cross-phase contracts; the producer and consumer share the same shape.
- Tests: `tests/test_enrich_test_ideas.py` (17 cases — uninitialized workspace refused; missing sessions refused with `/tc:session-summary` pointer; missing test-idea seeds refused with `/tc:requirements-to-tests` pointer; at-least-3 enrichments against the seeded fixture; enriched files carry the Phase 4 section and cite the SESS-ID; unenriched files byte-identical to pre-enrich snapshot; Phase-2 frontmatter keys preserved byte-for-byte; `status:` flips only on enriched files; `phase_4_sessions:` populated, sorted, deduplicated; idempotent re-run byte-identical; idempotent re-run produces zero duplicate enrichment sections; user-edited body section preserved; multi-session merge into `phase_4_sessions:`; default-no-flag enrich-against-all; CLI surfaces enriched count; consumer/producer `CandidateScenario` dataclass agreement).

## Definition of Done

- Helper passes all 17 test cases.
- Phase-2 frontmatter contract preserved byte-for-byte on every enriched file.
- `phase_4_sessions:` is sorted and deduplicated under all multi-session permutations exercised by the tests.
- Body merge is idempotent (single header; per-SESS-ID sub-block at most once).
- Step 4.5 enrichment contract forward-compatible with Phase 5 BDD generation (the BDD helper reads enriched test-ideas as charter-grounded scenario seeds).
- `tc-explore/SKILL.md` describes `/tc:test-ideas`'s shipped behavior with no deferral wording for this command.
- `make verify` chain green.

## See also

- [Test-idea-model methodology](../methodology/test-idea-model.md) — the schema contract, the Phase-2 → Phase-4 enrichment additions, the charter-coverage cross-reference logic, and the Claude judgment layer.
- [Test-idea enrichment template](../templates/test-idea-enrichment-template.md) — the body-section structure.
- [Per-command page: /tc:session-summary](session-summary.md) — the input source.
- [Per-command page: /tc:requirements-to-tests (Phase 2)](../../tc-requirements/commands/requirements-to-tests.md) — the seed generator.
