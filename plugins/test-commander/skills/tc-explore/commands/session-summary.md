# `/tc:session-summary`

The Phase 4 session-synthesis command. Reads the exploration note `/tc:explore` produced and emits a per-session summary at `<workspace>/sessions/<SESS-ID>.md` plus a one-line-per-session ledger at `<workspace>/sessions/index.md`. Aggregates observations / anomalies / coverage into counts, synthesizes structured candidate scenarios forward-compatible with Step 4.5's enrichment input, and leaves a section header for the Claude judgment layer.

## Inputs

- `--session <SESS-ID>` (required) — the session to summarize. The helper reads `<workspace>/exploration-notes/<SESS-ID>.md` and refuses with a precondition error directing the user at `/tc:explore` when missing.
- `<workspace>/charters/<CH-ID>.md` (cited by the exploration note; refused-tolerantly if not present) — the charter file. The helper parses the frontmatter to surface `target` and `mission` in the Session section of the summary.

## Outputs

| Path | Mode | Owner |
| --- | --- | --- |
| `<workspace>/sessions/<SESS-ID>.md` | overwrite (byte-deterministic against unchanged exploration note) | this command |
| `<workspace>/sessions/index.md` | overwrite (rebuilt from scratch by scanning every `sessions/SESS-*.md` file) | this command |
| stdout | informational CLI report | this command |

`<workspace>/exploration-notes/`, `<workspace>/charters/`, `<workspace>/test-ideas/`, `<workspace>/requirements/`, `<workspace>/product-knowledge/`, and `<workspace>/traceability/` are NOT touched — those are owned by Step 4.3 (exploration notes), Step 4.2 (charters), Step 4.5 (test-ideas), Phase 2 (requirements), Phase 3 (product-knowledge), Phase 5 (traceability) respectively.

## Preconditions

- `<workspace>/.test-commander/` exists (`/tc:init` has run).
- `<workspace>/exploration-notes/<SESS-ID>.md` exists. The helper accepts both Step-4.3-generated notes and notes written by manual edits (the parser tolerates missing optional sections).

## Behavior

1. Resolve the workspace.
2. Locate `<workspace>/exploration-notes/<SESS-ID>.md`. Refuse with precondition error if missing.
3. Parse the exploration note:
   - Title heading (extracts the SESS-ID and CH-ID).
   - Session metadata bullets (started_at, source recording path).
   - Observations table (extracts every row with a numeric source-index).
   - Anomalies table (extracts every row whose first cell is a universal-core anomaly category).
   - Evidence table.
   - Charter Coverage matrix (extracts every row whose third cell is a universal-core verdict).
4. Load the charter file (best-effort; returns a stub when missing so the helper still emits the summary).
5. Compute the duration from the first and last observation timestamps.
6. Synthesize candidate scenarios deterministically (see [Session summary methodology section](../methodology/session-based-test-management.md#session-summary-step-44)):
   - One `negative` candidate per anomaly (sorted by category).
   - One `edge` candidate per partial/unobserved coverage verdict (in source order).
   - Up to three `happy` candidates from successful network requests on distinct `(method, path)` pairs (sorted by `source_index`).
7. Render the summary with sections Session / Observation Summary / Anomaly Summary / Charter Coverage Summary / Evidence / Candidate Scenarios / Executive Narrative.
8. Write to `<workspace>/sessions/<SESS-ID>.md` (overwrite).
9. Rebuild `<workspace>/sessions/index.md` by scanning every `sessions/SESS-*.md` and emitting one row per match sorted by SESS-ID.
10. Exit 0 with a CLI summary line naming the SESS-ID and the candidate count.

## Safety

- No network; no shell-out; no writes outside `<workspace>/sessions/`.
- Re-running against an unchanged exploration note is byte-deterministic for both the summary AND the index (per the Phase 4 helper idempotency contract).
- Charter loading is tolerant: when the charter file is missing or its frontmatter is unparseable, the helper emits a summary with `(charter file not found)` or `(charter frontmatter unparseable)` instead of crashing. The session synthesis itself does not depend on the charter content; only the display of target + mission does.
- Per the Phase 4 cross-phase write-boundary discipline, this helper does not write to `<workspace>/test-ideas/` (Step 4.5 owns enrichment), `<workspace>/traceability/` (Phase 5 owns), or `<workspace>/product-knowledge/` (Phase 3 owns).

## Implementation

- Helper: `plugins/test-commander/scripts/session_summary.py` (~620 lines).
- Mirrors the Phase 4 helper-mirroring skeleton from Steps 4.2 + 4.3. Differences from 4.3: single input source (the exploration note markdown) instead of charter + recording JSON; no anomaly extraction (the note already carries them as table rows); no live-mode plumbing (recorded mode is the only mode that makes sense for a synthesizer reading another helper's output).
- Tests: `tests/test_session_summary.py` (15 cases — uninit refused, missing exploration note refused with precondition pointing at /tc:explore, summary has required sections, charter resolved, observation counts by event_type, anomaly counts by category + severity, coverage summary aggregates correctly, candidate scenarios extracted with stable shape including the literal field names `title`/`type`/`source`, candidate types include the universal core happy/edge/negative, sessions index updated, multiple sessions in index, idempotent re-run byte-identical).

## Definition of Done

- Helper passes all 15 test cases.
- Summary shape matches the methodology's documented session-summary subsection.
- Candidate scenarios shape compatible with Step 4.5's enrichment input.
- Sessions index rebuilds idempotently when 1 or more sessions exist.
- `tc-explore/SKILL.md` describes `/tc:session-summary`'s shipped behavior with no deferral wording for this command.
- `make verify` chain green.

## See also

- [Session-based-test-management methodology](../methodology/session-based-test-management.md) — the session-summary subsection covers the synthesis rules + idempotency contract + the Claude judgment layer.
- [Session-summary template](../templates/session-summary-template.md) — the render shape.
- [Exploration-note template](../templates/exploration-note-template.md) — the Step 4.3 input shape.
- [Per-command page: /tc:explore](explore.md) — the input source.
