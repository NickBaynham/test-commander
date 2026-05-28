# Session-based test management

The per-command methodology for `/tc:explore` (Phase 4 Step 4.3). Sits underneath the umbrella [`exploratory-testing.md`](exploratory-testing.md). Covers the Bach + Bolton session-based discipline, the observation / evidence / anomaly model, the universal anomaly categories, the charter-coverage rubric, the internal exploration-review sub-mode, and the Claude judgment layer that operates over the mechanical extraction.

## Session-based discipline (Bach + Bolton)

A session is a single time-boxed execution of a charter. It produces three artifacts:

1. An **exploration note** (`<workspace>/exploration-notes/<SESS-ID>.md`) — the mechanical record of every observation, every screenshot, every anomaly, plus a charter-coverage matrix. This is what `/tc:explore` writes.
2. A **session summary** (`<workspace>/sessions/<SESS-ID>.md`) — the synthesized view: duration, observation counts by event type, anomaly counts by category and severity, charter-coverage verdict, candidate scenarios extracted from the session. Step 4.4 (`/tc:session-summary`) writes this.
3. **Test-idea enrichment** (`<workspace>/test-ideas/<REQ-ID>.md` body sections) — refined candidate scenarios drawn from the session, mapped to Phase-2-seeded REQ-IDs via charter-coverage cross-reference. Step 4.5 (`/tc:test-ideas`) writes this.

The exploration note (1) is the contract for the per-session debrief; (2) and (3) are the outputs of the debrief itself.

`/tc:explore` operates in two modes:

- **Recorded mode** (default): reads a captured session JSON from the configured path. Pure data processing; no browser, no MCP. Pytest never reaches live mode (the `PYTEST_CURRENT_TEST` env var triggers refusal before any MCP connection is attempted — mirrors the Phase 3 Step 3.5 pattern verbatim).
- **Live mode** (`tc-explore.mode: live`): drives Playwright MCP at runtime against a real target URL. v1 documents the pattern but the live-mode plumbing is the next sub-phase's work; recorded mode is sufficient for every Phase-4 contract through to the `phase-4` tag.

## The observation / evidence / anomaly model

Every event in the recorded (or live) session classifies into one of three layers:

### Observations (every event)

Every event whose `event_type` is in the universal core surfaces as an `Observation` row in the exploration note's Observations table. The universal-core event types: `page_load`, `click`, `fill`, `screenshot`, `console_message`, `network_request`, plus the meta type `anomaly` (handled separately).

Each observation captures:

- `timestamp` (ISO-8601 from the recorded event).
- `event_type` (one of the universal core).
- `page_url` (the page the event occurred on; may be empty for non-page-bound events).
- `action` (synthesized — for clicks it's the selector + intent; for fills it's the selector + redacted value; for network_requests it's `METHOD path -> status`).
- `result` (synthesized — load duration for page_loads; status code for network_requests; caption for screenshots; raw message for console_messages).
- `source_index` (0-based index into the recorded events list; the provenance citation in the rendered note is `<recorded-session.json>:<source_index + 1>`).

### Evidence (every screenshot)

Every event of type `screenshot` captures a `screenshot_id`, `page_url`, and `caption`. The exploration note's Evidence index lists every screenshot with its file reference under `evidence/screenshots/<id>.png`. The seeded fixture's recording uses placeholder IDs (S-001 through S-009); live mode writes real PNG files captured by Playwright MCP.

### Anomalies (every flagged event)

Events with `event_type: anomaly` carry a structured `anomaly: {category, severity, page_url, reproduction, screenshot_id}` payload. Each anomaly classifies into the universal core:

| Category | Universal-core trigger | Worked example (from seeded fixture) |
| --- | --- | --- |
| `slow-response` | Network request exceeding documented latency threshold | GET /workspaces returned in 3812ms |
| `console-error` | Browser console message at error level | Uncaught TypeError on asset list render |
| `broken-link` | Click target returned 404 or stayed on the same page | Link to /account/profile returned 404 |
| `missing-evidence` | Anomaly without an adjacent screenshot event within ±3s AND with `screenshot_id: null` | Undocumented `last_login_at` field, no screenshot |
| `auth-mismatch` | Request lacking Authorization header OR response 401/403 | Retry to GET /workspaces/{id}/assets without auth got 401 |
| `unexpected-state` | UI element present when it should not be (or vice versa) | Residual workspace card on sign-in page after sign-out |

The `severity` field uses the universal core `{low, medium, high, critical}`.

## Charter-coverage rubric

The exploration note's Charter Coverage matrix marks each acceptance criterion with one of three verdicts:

- **observed** — at least half the URL paths AND distinctive keywords from the criterion appear in the observed events, AND every trigger word from the criterion is observed.
- **partial** — some URLs / keywords matched, OR a trigger word from the criterion is absent from observations. The criterion is touched but not fully exercised.
- **unobserved** — no URLs or keywords from the criterion match any observation.

The assessor extracts:

- URL paths via regex (`/[a-zA-Z][a-zA-Z0-9/{}_-]+`).
- Distinctive keywords (≥4 chars, after filtering stopwords like `with`, `from`, `valid`, `response`).
- Trigger words — a universal-core list of scenario triggers that, when present in the AC but absent from observations, downgrade the verdict: `{expiration, expired, expire, leak, leakage, concurrent, race, timeout, timed-out, rollback}`. If the AC says "session expiration" and the events never carry `expiration`, the verdict is at best `partial`.

**Worked example (CH-001, AC5):** "Session expiration during workspace navigation routes the user back to /sign-in".

- URL paths in AC: `{/sign-in}`. Observed: yes (the seeded recording reaches /sign-in after a sign-out attempt). One path matched.
- Trigger words in AC: `{expiration}`. Observed in events: no. Trigger gap → verdict downgraded to `partial`.

**Worked example (CH-001, AC1):** "Sign-in completes with a valid session token returned in the response body".

- URL paths in AC: `{}` (the AC names "Sign-in" descriptively but does not include the explicit path).
- Distinctive keywords: `{sign, session, token, completes, returned}`. Observed in actions / network paths: most match. Half-or-more matched.
- No trigger words. Verdict: `observed`.

## Internal exploration-review sub-mode

Auto-runs at the end of every `/tc:explore` session unless `--no-review` is set. Emits gap signals routed to `<workspace>/requirements/open-questions.md` with the `[exploration-review]` prefix and the Phase-2 `(source-id, question-text)` dedup contract (extended in Phase 3 with the `[<kind>]` inside-prefix).

Two universal-core checks ship in v1:

### `missing-evidence` review check

Fires when an anomaly carries `screenshot_id: null` AND no event of type `screenshot` exists within ±3 seconds of the anomaly timestamp. The seeded fixture's recorded `missing-evidence` anomaly is the worked example.

The check is asymmetric: an anomaly with a non-null `screenshot_id` field is treated as having explicit evidence even if the cited screenshot was captured before the anomaly was observed. The ±3-second window only applies when the anomaly does NOT name a screenshot itself.

### `charter-coverage-shortfall` review check

Fires for every acceptance criterion marked `unobserved` after the full session. Criteria marked `partial` do not trigger this gap (they are partially exercised; the human/Claude debrief decides whether to follow up). Criteria marked `observed` are silent.

The seeded fixture's CH-001 ends up with one `partial` AC (about session expiration) but zero `unobserved`, so the shortfall check does not fire for the seed. Tests that need to exercise the shortfall path synthesize a charter with deliberately-uncovered ACs.

## Session summary (Step 4.4)

`/tc:session-summary` reads the exploration note produced by `/tc:explore` and synthesizes a per-session summary at `<workspace>/sessions/<SESS-ID>.md` plus a one-line-per-session ledger at `<workspace>/sessions/index.md`. The summary aggregates the mechanical extraction the exploration note already carried, plus adds two pieces the note doesn't:

1. **Aggregate counts.** Observations grouped by `event_type`; anomalies grouped by `category` AND `severity` (the exploration note's Anomalies table is per-row, not aggregated); coverage matrix aggregated into a one-line verdict (`X observed, Y partial, Z unobserved` of total ACs).
2. **Candidate scenarios.** A structured list of test-idea seeds derived deterministically from the session, forward-compatible with Step 4.5's enrichment input.

### Candidate scenario synthesis rules

Three deterministic synthesis paths, run in this order so the resulting `CS-NNN-NNN` IDs are stable across re-runs:

1. **`negative` candidates from anomalies** — one per anomaly, sorted by category for deterministic ordering. Title: `Reproduce <category> on <page_url>`. Source: `<SESS-ID>:anomaly:<category>`. `linked_anomaly` set to the category.
2. **`edge` candidates from coverage gaps** — one per acceptance criterion marked `partial` OR `unobserved`, in source order. Title: `Follow-up exploration to fully cover acceptance criterion #N: '<criterion text>'`. Source: `<SESS-ID>:coverage:AC<N>:<verdict>`. `linked_anomaly` absent.
3. **`happy` candidates from successful flows** — up to three, drawn from `network_request` observations returning 2xx on distinct `(method, path)` pairs, sorted by `source_index`. Title: `Happy path: METHOD path returns NNN`. Source: `<SESS-ID>:obs:<source_index>`. `linked_anomaly` absent.

Each candidate carries four stable fields Step 4.5 reads: `id`, `title`, `type`, `source` (plus optional `linked_anomaly`). The shape is forward-compatible with Phase 2's `tc-test-idea/v1` candidates field — Step 4.5 (`/tc:test-ideas`) appends these to the existing Phase-2-seeded test-idea files under `<workspace>/test-ideas/<REQ-ID>.md` as a `## Phase 4 enrichment` body section.

### Session-summary idempotency contract

Re-running `/tc:session-summary --session <SESS-ID>` against an unchanged exploration note produces byte-identical bytes for both `sessions/<SESS-ID>.md` and `sessions/index.md`. Determinism factors:

- The exploration note (the input) is byte-deterministic against the recorded session (per Step 4.3).
- Candidate `CS-NNN-NNN` IDs are derived from the SESS-ID's last NNN segment plus a sequence ordinal across the deterministic candidate list.
- Aggregate counts are pure functions of the parsed input.
- The sessions index is rebuilt from scratch by scanning every `sessions/SESS-*.md` file and emitting one row per match sorted by SESS-ID (chronological by YYYYMMDD prefix).

### What lands in the index

The index row for each session lists the SESS-ID, the charter ID resolved from the title heading, the duration parsed from the Session bullet (when present), the anomaly count parsed from the Anomaly Summary header (when present), and the coverage verdict tuple `Xo/Yp/Zu` parsed from the Charter Coverage Summary header (when present). Older summaries written by manual edits or by previous helper versions surface with their available metadata; missing fields are simply omitted from the row.

## Claude judgment layer

The mechanical extraction handles every dimension above deterministically. The Claude judgment layer adds:

- **Anomaly severity calibration.** The mechanical category is universal; the severity is project-dependent. A `slow-response` at 4 seconds is low-priority for a batch analytics flow but critical for a payments endpoint. Claude reads the anomaly category + project context (from `<workspace>/product-knowledge/`) and recommends a severity adjustment.
- **Candidate scenario extraction.** Many observations are noise. Claude reads the Observations table + Anomalies summary and identifies which observations look like good seeds for `/tc:test-ideas` enrichment (Step 4.5). Typically: any observation paired with an anomaly, any observation hitting an endpoint the Phase-3 `/tc:learn-from-api` flagged with a `[gap]`, any observation completing an acceptance criterion that was previously `unobserved` in a prior session.
- **Partial-coverage follow-up decisions.** A criterion marked `partial` may warrant a follow-up charter (sufficiency depends on the gap). Claude reads the matched-paths + matched-keywords from the verdict and recommends either (a) accept the partial coverage as documented evidence of best-effort exploration, or (b) author a new charter targeting the specific gap.
- **Cross-source correlation.** Every observation has a `recorded-session.json:<index>` provenance citation. The judgment layer correlates these with the Phase-3 product-knowledge artifacts (`code-derived-model.md`, `api-model.md`, `tests-coverage.md`) to identify whether the observed behavior aligns with the documented system or surfaces a previously-undocumented case.

## Configurable extensions

```yaml
tc-explore:
  exploration:
    mode: recorded                                       # or: live (refused under pytest)
    recorded-path: documents/uploaded/recorded-sessions  # default; resolves relative to <workspace>
    mcp-endpoint: http://localhost:9999                  # live mode only
    target-url: http://localhost:8000                    # live mode only
```

Reserved for the v2 live-mode wiring; v1 implements only the `mode: recorded` path plus the live-mode refusal under pytest.

## See also

- [Umbrella methodology](exploratory-testing.md)
- [Charter-based-exploration methodology](charter-based-exploration.md)
- [Per-command page: /tc:explore](../commands/explore.md)
- [Exploration-note template](../templates/exploration-note-template.md)
- [Anomaly-record template](../templates/anomaly-record-template.md)
- [Exploration-review template](../templates/exploration-review-template.md)
- [Seeded recorded session](../../../../../tests/fixtures/seeded-exploration-session/recorded-session.json)
