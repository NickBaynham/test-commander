# Exploratory testing (umbrella methodology)

The umbrella methodology for `tc-explore`. Read this once at the start of any Phase 4 exploration; the per-command methodologies ([`charter-based-exploration.md`](charter-based-exploration.md), [`session-based-test-management.md`](session-based-test-management.md), [`test-idea-model.md`](test-idea-model.md)) sit underneath it and reference back here for the cross-command workflow and the cross-phase write boundaries.

## The four-step workflow

```
/tc:create-charter       (Step 4.2; shipped)
        |
        v
/tc:explore              (Step 4.3; shipped)
        |
        +------>  internal exploration-review sub-mode auto-runs at end of session
        |
        v
/tc:session-summary      (Step 4.4; shipped)
        |
        v
/tc:test-ideas           (Step 4.5; shipped)
```

Each step writes to its own directory under `<workspace>/`. Re-running any step is idempotent — re-running with the same `--target` or against the same recorded session produces byte-identical artifacts (the same discipline Phase 2 and Phase 3 helpers honor).

## Session-based test management (Bach + Bolton)

`tc-explore` follows James Bach's and Michael Bolton's session-based test management discipline:

- A **charter** is a written mission for a time-boxed exploration. It states the mission, the target area, the time-box, the risk areas the exploration prioritizes, and the acceptance criteria that confirm charter completion. The Phase 4 helper writes charters under `<workspace>/charters/CH-NNN.md`.
- A **session** is a single time-boxed execution of a charter. It produces a structured note (every observation, every screenshot, every anomaly) plus a session summary (charter-coverage verdict, anomaly counts, candidate scenarios). Phase 4 sessions live under `<workspace>/exploration-notes/SESS-YYYYMMDD-NNN.md` and `<workspace>/sessions/SESS-YYYYMMDD-NNN.md`.
- A **debrief** synthesizes the session into actionable artifacts. In Phase 4, the debrief is partially automated: the internal exploration-review sub-mode auto-runs at the end of every `/tc:explore` session and routes review-failure gap signals to `<workspace>/requirements/open-questions.md`; the human / Claude debrief layers on top of the mechanical review.

The seeded fixture's [`charter.md`](../../../../../tests/fixtures/seeded-exploration-session/charter.md) is a worked example of a charter; the seeded `recorded-session.json` is a worked example of a session.

## Cross-phase write boundaries

Phase 4 reads broadly but writes narrowly. Inputs:

- `<workspace>/product-knowledge/` — Phase 3 outputs. `entities.md`, `user-journeys.md`, `system-model.md` drive the auto-suggestion logic in `/tc:create-charter`.
- `<workspace>/requirements/` — Phase 2 outputs. `open-questions.md` carries the gap-signal backlog from Phase 2 + Phase 3 that Phase 4 charters address; `requirements-inventory.md` carries the REQ-ID space that Phase 4 enrichment cross-references.
- `<workspace>/risk-register/risk-register.md` — project-supplied risk inventory; the helper extracts risk-areas matching universal-core OR project-extended risk keywords.
- `<workspace>/learning/accepted-lessons.md` — Phase 8 feedback loop. v1 reads this when present (often empty in early projects).

Outputs:

- `<workspace>/charters/CH-NNN.md` — Step 4.2 writes; user edits preserved across re-runs.
- `<workspace>/exploration-notes/SESS-ID.md` — Step 4.3 writes; pure generated report, byte-deterministic against unchanged recorded input.
- `<workspace>/sessions/SESS-ID.md` + `<workspace>/sessions/index.md` — Step 4.4 writes; pure generated reports.
- `<workspace>/test-ideas/REQ-ID.md` — Step 4.5 enriches; preserves every Phase-2 frontmatter key byte-for-byte; appends a `## Phase 4 enrichment` section.
- `<workspace>/evidence/screenshots/<screenshot-id>.png` — Step 4.3 places screenshot references (the seeded recording bundles placeholders; live mode produces real screenshots).
- `<workspace>/requirements/open-questions.md` — appended with `[exploration-review]` gap signals from the review sub-mode.

Phase 4 does **NOT** write to:

- `<workspace>/traceability/` — Phase 5 owns. Phase 4 supplies the inputs Phase 5 will compose into the traceability map; writing here would bump Phase 5 to `in_progress` in `workspace_state.py` and skew `/tc:next`'s recommendations (the Phase 3 Step 3.8 lesson, made operational here too).
- `<workspace>/product-knowledge/` — Phase 3 owns. Phase 4 reads but never modifies; the Step 4.7 integration smoke asserts byte-identical product-knowledge state before and after Phase 4 runs.

## Test-idea enrichment contract

`/tc:test-ideas` (Step 4.5) enriches the Phase-2-seeded `<workspace>/test-ideas/<REQ-ID>.md` files. The contract is strict: **every Phase-2 frontmatter key is preserved byte-for-byte**. The Phase-2 `tc-test-idea/v1` schema documented in `commands/requirements-to-tests.md` (`schema`, `requirement_id`, `requirement_title`, `source`, `status`, `phase_2_findings`, `candidates`, `generated_by`) stays intact. Phase 4 adds:

- `status: seed` → `status: enriched` (one-character flip).
- `phase_4_sessions: [SESS-ID, ...]` — sorted, deduplicated; updated never duplicated on re-runs.
- A new `## Phase 4 enrichment` body section listing each contributing session's candidate scenarios mapped to this REQ-ID via charter-coverage cross-reference.

User edits + prior Phase-4 enrichments are preserved. The 4.5 test suite explicitly asserts byte-identical preservation of every key the Phase-2 seed shipped with. The integration smoke in 4.7 verifies the contract end-to-end.

## Anomaly categories (universal core)

Six universal-core anomaly categories ship in v1. Project-specific anomalies route through `tc-explore.charters.risk-keywords` extensions; the categories themselves are D19-compliant universal English.

| Category | What it catches | Worked example (from seeded fixture) |
| --- | --- | --- |
| `slow-response` | Network requests exceeding documented latency thresholds | GET /workspaces returned in 3812ms; threshold 1000ms |
| `console-error` | Browser console messages at error level | Uncaught TypeError on asset list render |
| `broken-link` | Anchor target returns 404 or stays on the same page | Link to /account/profile returned 404 |
| `missing-evidence` | Observed behavior with no adjacent screenshot (±3s window) | Undocumented `last_login_at` field with no screenshot |
| `auth-mismatch` | Authentication header absent on request that should require it (or 401/403 returned) | Retry to GET /workspaces/{id}/assets without Authorization got 401 |
| `unexpected-state` | UI element present when it should not be (or vice versa) | Residual workspace card on sign-in page after sign-out |

The seeded recording at [`tests/fixtures/seeded-exploration-session/recorded-session.json`](../../../../../tests/fixtures/seeded-exploration-session/recorded-session.json) carries one anomaly per category. The Step 4.3 helper extracts each one as a structured `Anomaly(category, severity, page_url, reproduction, screenshot_id)` finding.

## Per-command methodology

- [`charter-based-exploration.md`](charter-based-exploration.md) — Step 4.2. Charter rubric (mission specificity, target scope, time-box discipline, risk-area enumeration, acceptance-criteria testability), with worked examples per dimension drawn from the seeded `CH-001` and a Claude-judgment-layer paragraph.
- `session-based-test-management.md` — Step 4.3. Observation / evidence / anomaly model, charter-coverage rubric, exploration-review rubric.
- `test-idea-model.md` — Step 4.5. Phase-2 `tc-test-idea/v1` schema preservation, Phase-4 enrichment additions, charter-coverage → REQ-ID cross-reference logic.

## See also

- [Plugin README](../../../README.md)
- [Phased plan](../../../../../planning/plan.md)
- [tc-knowledge methodology umbrella](../../tc-knowledge/methodology/project-knowledge.md) — the Phase 3 equivalent of this umbrella; same shape, different cross-source domain.
- [Per-command page: /tc:create-charter](../commands/create-charter.md)
