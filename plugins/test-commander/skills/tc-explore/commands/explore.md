# `/tc:explore`

The Phase 4 exploration-driver command. Reads a charter file plus a recorded Playwright MCP session (or drives MCP live; pytest never reaches live mode), classifies every event into Observations / Evidence / Anomalies, computes a Charter-Coverage matrix, runs an internal exploration-review sub-mode that emits `[exploration-review]` gap signals to `<workspace>/requirements/open-questions.md`, and writes `<workspace>/exploration-notes/<SESS-ID>.md` byte-deterministically against unchanged input.

## Inputs

- `--charter <CH-ID>` (required) — the charter to explore. The helper reads `<workspace>/charters/<CH-ID>.md` and refuses with a precondition error directing the user at `/tc:create-charter` when missing.
- `<workspace>/documents/uploaded/recorded-sessions/<CH-ID>.json` (default, configurable via `tc-explore.exploration.recorded-path`) — the recorded Playwright MCP session JSON. Each entry must declare `timestamp` and `event_type`; entries with `event_type: anomaly` must also carry an `anomaly: {category, severity, page_url, reproduction, screenshot_id}` payload.
- `<workspace>/config.yaml` (optional) — the `tc-explore.exploration:` block configures the helper. Recognized keys:
  - `mode: recorded` (default) or `mode: live` (refused under pytest).
  - `recorded-path: documents/uploaded/recorded-sessions` (workspace-relative).
  - `mcp-endpoint: http://localhost:9999` (live mode only; v1 reserved).
  - `target-url: http://localhost:8000` (live mode only; v1 reserved).

## Outputs

| Path | Mode | Owner |
| --- | --- | --- |
| `<workspace>/exploration-notes/<SESS-ID>.md` | overwrite (byte-deterministic against unchanged recording) | this command |
| `<workspace>/requirements/open-questions.md` | append, dedup by `(source-id, question-text)`; unless `--no-review` | this command |
| stdout | informational CLI report | this command |

`<workspace>/sessions/`, `<workspace>/test-ideas/`, `<workspace>/charters/` and `<workspace>/traceability/` are NOT touched — those are owned by Steps 4.4 / 4.5 / 4.2 / Phase 5 respectively. `<workspace>/product-knowledge/` is NOT touched (Phase 3 owns).

## Preconditions

- `<workspace>/.test-commander/` exists.
- `<workspace>/charters/<CH-ID>.md` exists with valid YAML frontmatter declaring at minimum `id`, `target`, and `acceptance-criteria` (the Step 4.1 cross-phase contract).
- A recorded session JSON exists at the configured path. The default is `<workspace>/documents/uploaded/recorded-sessions/<CH-ID>.json`.
- Pytest constraint: `mode: live` is refused before any MCP connection is attempted. The check inspects `os.environ.get("PYTEST_CURRENT_TEST")` — pytest sets this for every test, including in-process imports.

## Behavior

1. Resolve the workspace and load `tc-explore.exploration:` extensions from `<workspace>/config.yaml`.
2. If `mode: live`, refuse with exit 2:
   - If `PYTEST_CURRENT_TEST` is set, the error names pytest as the reason.
   - Otherwise, the error notes that live mode is not implemented in v1.
3. Load and parse the charter. Refuse with precondition error if missing or unparseable.
4. Load and parse the recorded session JSON. Refuse with precondition error if missing or unparseable.
5. Extract Observations (every event whose `event_type` is in the universal core except `anomaly`), Evidence (every `screenshot` event with a `screenshot_id`), and Anomalies (every `anomaly` event whose payload carries a category from the universal core).
6. Build an observed-corpus (URLs + action text + result text + anomaly text + caption text) and assess each charter acceptance criterion against it, producing a `CoverageVerdict` of `observed` / `partial` / `unobserved`.
7. Allocate the session ID: `SESS-YYYYMMDD-NNN` where YYYYMMDD is the date of the recorded session's first event and NNN is `(hour*60 + minute) % 1000`. Deterministic per (date, hour, minute) so re-runs against the same recording produce the same SESS-ID.
8. If `--no-review` is NOT set, run the internal exploration-review sub-mode: emit a `missing-evidence` gap for every anomaly with `screenshot_id: null` AND no `screenshot` event within ±3s; emit a `charter-coverage-shortfall` gap for every acceptance criterion marked `unobserved`.
9. Render the exploration note (Session header + Observations table + Anomalies summary + Evidence index + Charter-Coverage matrix + optional Review findings) byte-deterministically against unchanged input. Write to `<workspace>/exploration-notes/<SESS-ID>.md` (overwrite).
10. Append `[exploration-review]` gap signals to `<workspace>/requirements/open-questions.md` with the Phase-2 `(source-id, question-text)` dedup contract (unless `--no-review`).
11. Exit 0 with a CLI summary line.

## Safety

- Live mode is refused under pytest before any HTTP / MCP connection is constructed. The refusal is asserted by `test_live_mode_refused_under_pytest`.
- Recorded mode reads only the configured playback file. No shell-out; no network; no browser launch.
- Per the Phase-3 Step-3.8 cross-phase-write-boundary discipline made operational in Phase 4: this helper writes only to `exploration-notes/` and `requirements/open-questions.md` (the open-questions append). It does NOT write to `traceability/`, `product-knowledge/`, `charters/`, `sessions/`, or `test-ideas/`.
- Re-running against unchanged input is byte-deterministic. The `open-questions.md` dedup prevents append drift.
- Per D19, the anomaly-category and event-type universal cores carry no domain vocabulary.

## Implementation

- Helper: `plugins/test-commander/scripts/explore.py` (~830 lines).
- Mirrors the Phase 4 helper-mirroring skeleton established in Step 4.2 (`create_charter.py`). Differences from 4.2: per-source extraction operates on JSON events instead of Markdown bodies; idempotency is overwrite (pure generated report) rather than skip-not-overwrite; session-ID allocation is deterministic from the recording's first-event timestamp rather than from filesystem-scanning + increment.
- Tests: `tests/test_explore.py` (17 cases - uninit refused, missing-charter refused with precondition error pointing at /tc:create-charter, missing-recording refused, session note generation with required sections + all 6 event types + all 6 anomaly categories + Evidence index + Charter-Coverage matrix, at least one AC marked partial for the seeded coverage shortfall, missing-evidence gap routes to open-questions, --no-review suppresses gap signals, live mode refused under pytest, idempotent re-run byte-identical, recorded-path extension applied, SESS-YYYYMMDD-NNN format).

## Definition of Done

- Helper passes all 17 test cases.
- Partition-table coverage assertion is part of the test suite (every event type AND every universal anomaly category surface).
- Methodology covers the session-based discipline + the partition table + the Claude judgment layer.
- Review sub-mode emits the expected gap signals; `--no-review` suppresses them.
- Templates authored: exploration-note + anomaly-record + exploration-review.
- Per-command page complete (this file).
- `tc-explore/SKILL.md` describes `/tc:explore`'s shipped behavior and the auto-running review sub-mode; no deferral wording for this command.
- `make verify` chain green.

## See also

- [Session-based-test-management methodology](../methodology/session-based-test-management.md) — observation/evidence/anomaly model, charter-coverage rubric, exploration-review rubric, Claude judgment layer.
- [Umbrella exploratory-testing methodology](../methodology/exploratory-testing.md) — cross-command workflow and cross-phase write boundaries.
- [Exploration-note template](../templates/exploration-note-template.md) — the render shape.
- [Anomaly-record template](../templates/anomaly-record-template.md) — recorded-session JSON anomaly entry contract.
- [Exploration-review template](../templates/exploration-review-template.md) — gap-signal entry shape and `--no-review` semantics.
- [Seeded recorded session](../../../../../tests/fixtures/seeded-exploration-session/recorded-session.json) — 55 events including one anomaly per universal category.
