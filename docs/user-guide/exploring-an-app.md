# Workflow — Exploring an App (Phase 4)

This guide walks you through Test Commander's four Phase 4 commands end to end against a consuming project. The examples use the deliberately-generic seeded fixture from `tests/fixtures/seeded-exploration-session/` (plus the Phase 2 `tests/fixtures/seeded-flawed-requirements/` fixture for the `/tc:test-ideas` step) so every output is reproducible.

## What's available in Phase 4

Phase 4 ships the `tc-explore` skill with four commands plus an internal exploration-review sub-mode that auto-runs at the end of every `/tc:explore` session:

| Command | Reads | Writes |
| --- | --- | --- |
| `/tc:create-charter` | `product-knowledge/{entities,user-journeys,system-model}.md` + `requirements/open-questions.md` + `risk-register/risk-register.md` (when present) | `<workspace>/charters/<CH-NNN>.md` |
| `/tc:explore` | `charters/<CH-ID>.md` + a recorded Playwright MCP session JSON at the configured path | `<workspace>/exploration-notes/<SESS-ID>.md`; appends `[exploration-review]` gap signals to `requirements/open-questions.md` (suppressible with `--no-review`) |
| `/tc:session-summary` | `exploration-notes/<SESS-ID>.md` + the cited charter | `<workspace>/sessions/<SESS-ID>.md` + `sessions/index.md` |
| `/tc:test-ideas` | `sessions/SESS-*.md` + `test-ideas/REQ-*.md` (Phase-2 seeds) | enriches `test-ideas/REQ-*.md` in place — preserves every Phase-2 frontmatter key byte-for-byte; flips `status: seed` → `status: enriched`; merges `phase_4_sessions:`; appends a `## Phase 4 enrichment` body section |

Phase 4 **reads broadly** but **writes only to its own directories** (charters/, exploration-notes/, sessions/, test-ideas/ enrichment, plus the `[exploration-review]` line in open-questions.md). `<workspace>/product-knowledge/` and `<workspace>/traceability/` are not touched — those are Phase 3 and Phase 5 territory.

Per Decision D19 ([planning/plan.md](../../planning/plan.md)) all four helpers ship universal-core detection patterns only. Domain-specific vocabulary enters through `<workspace>/config.yaml` extensions — see [customizing-for-your-project.md](customizing-for-your-project.md).

## Prerequisites

1. `<workspace>/.test-commander/` exists (`/tc:init` has run — see [workflow.md](workflow.md)).
2. Phase 3 has populated `<workspace>/product-knowledge/` (at minimum `entities.md`, `user-journeys.md`, `system-model.md`) — `/tc:create-charter` refuses an uninitialized product-knowledge state with a precondition error directing you at `/tc:learn-from-docs`. See [building-project-knowledge.md](building-project-knowledge.md).
3. The consuming project has uploaded a recorded Playwright MCP session at the configured path. The default is `<workspace>/documents/uploaded/recorded-sessions/<CH-ID>.json`; the path is overridable via `tc-explore.exploration.recorded-path` in `<workspace>/config.yaml`. The session JSON is a list of `{timestamp, event_type, page_url, ...}` entries; the seeded fixture at `tests/fixtures/seeded-exploration-session/recorded-session.json` documents the exact shape.
4. For the Phase-4 enrichment step (`/tc:test-ideas`) to enrich anything, Phase 2 must have already produced test-idea seeds at `<workspace>/test-ideas/REQ-*.md` via `/tc:requirements-to-tests`. See [reviewing-requirements.md](reviewing-requirements.md).

```
.test-commander/documents/uploaded/
  product-overview.md           # Phase 3 prerequisite
  ...                           # other Phase 3 ingestion sources
  recorded-sessions/
    CH-001.json                 # default path; override via tc-explore.exploration.recorded-path
```

5. The Phase 3 helpers do not need to have ALL run for Phase 4 to work — a minimum `entities.md`, `user-journeys.md`, and `system-model.md` is enough. Risk-register (`<workspace>/risk-register/risk-register.md`) is optional; absence is handled cleanly.

## Step 1: `/tc:create-charter`

Reads Phase-3 product-knowledge plus Phase-2 open questions and writes a charter file scoping a single exploration session. Accepts either an explicit `--target <area>` / `--mission <text>` OR auto-suggests a target from the highest-mention-count entity in the product-knowledge artifacts (ties broken alphabetically for deterministic output).

**Run:**

```sh
python3 <plugin-root>/scripts/create_charter.py <project-root> [--target TEXT | --mission TEXT] [--new-id]
```

**What lands:**

- `<workspace>/charters/<CH-NNN>.md` — YAML frontmatter (`id`, `mission`, `target`, `time-box: 60min`, `risk-areas`, `acceptance-criteria`, `created_at`, `phase_3_sources`) plus a structured body (Mission / Target Area / Time-Box / Risk Areas / Acceptance Criteria / Out of Scope / Phase 3 Sources).
- The charter is **skip-not-overwrite** for downstream-enriched files: re-running with the same `--target` (case-insensitive) preserves any user edits to the existing charter byte-for-byte and reports `created: 0  skipped: 1`. The `--new-id` flag forces a fresh `CH-NNN` allocation even when the target matches.

**Sample output** (from the seeded fixture, supplying `--target "Sign-in flow plus workspace-detail asset upload (POST /workspaces/{id}/assets)."`):

```yaml
---
id: CH-001
mission: Discover whether the Sign-in flow plus workspace-detail asset upload (POST /workspaces/{id}/assets). behaves correctly under the documented risk conditions.
target: Sign-in flow plus workspace-detail asset upload (POST /workspaces/{id}/assets).
time-box: 60min
risk-areas:
  - Authentication / authorization boundaries
  - Session lifecycle and token leakage
  - Performance under documented load thresholds
  - Input validation on user-supplied data
acceptance-criteria:
  - Every flow under '...' completes the happy path with documented status codes.
  - Authentication is correctly enforced for every endpoint that should require it.
  - At least one anomaly per universal category is documented or explained away.
created_at: 2026-05-28T18:47:33Z
phase_3_sources:
  - product-knowledge/entities.md
  - product-knowledge/user-journeys.md
  - product-knowledge/system-model.md
  - requirements/open-questions.md
---
```

The risk areas and acceptance criteria are populated from universal-core templates. Edit the charter body afterwards to refine the scope — your edits are preserved on every subsequent re-run. Domain-specific risk vocabulary can be plumbed in via `tc-explore.charters.risk-keywords` extensions; see [customizing-for-your-project.md](customizing-for-your-project.md).

Full methodology with worked examples per dimension: [`tc-explore/methodology/charter-based-exploration.md`](../../plugins/test-commander/skills/tc-explore/methodology/charter-based-exploration.md).

## Step 2: `/tc:explore`

Reads the charter and replays a recorded Playwright MCP session against it. Classifies every event into the universal-core categories — Observations (six event types), Evidence (every screenshot), Anomalies (six categories times four severities). Computes a Charter-Coverage matrix marking each acceptance criterion `observed` / `partial` / `unobserved`. Runs the internal exploration-review sub-mode at end of session (suppressible with `--no-review`).

**Run:**

```sh
python3 <plugin-root>/scripts/explore.py <project-root> --charter CH-NNN [--no-review]
```

**Recorded vs live mode.** The default `recorded` mode reads the playback JSON file the consuming project supplies. The opt-in `live` mode (`tc-explore.exploration.mode: live`) is documented but **refused under pytest** — the helper detects pytest via the `PYTEST_CURRENT_TEST` environment variable and exits 2 before any MCP connection is constructed. Live mode is not implemented in v1; recorded playback is sufficient for every Phase-4 contract.

**What lands:**

- `<workspace>/exploration-notes/<SESS-ID>.md` — title heading + Session metadata bullets + Observations table (`# / Timestamp / event_type / Page / Action / Result`) + Anomalies summary (six universal categories) + Evidence index (every screenshot with `evidence/screenshots/<id>.png` references) + Charter Coverage matrix (one row per AC with verdict). Byte-deterministic: re-running against the same recording produces identical bytes.
- Session ID follows `SESS-YYYYMMDD-NNN` where NNN is derived deterministically from the first recorded event's time-of-day so the same recording always produces the same SESS-ID.
- The internal exploration-review sub-mode appends `[exploration-review]` gap signals to `<workspace>/requirements/open-questions.md` for (a) every anomaly carrying `screenshot_id: null` AND no `screenshot` event within ±3 seconds, and (b) every acceptance criterion marked `unobserved`.

**Sample output** (from the seeded fixture):

```
exploration note written: SESS-20260528-600 (50 observations, 6 anomalies, 9 screenshots, 1 review findings)
```

The first table rows in the generated exploration note:

```markdown
| # | Timestamp | event_type | Page | Action | Result |
| --- | --- | --- | --- | --- | --- |
| 0 | 2026-05-28T10:00:00.000Z | page_load | /sign-in |  | ok |
| 1 | 2026-05-28T10:00:01.250Z | screenshot | /sign-in |  | Sign-in page rendered with account_id and code fields visible. |
| 2 | 2026-05-28T10:00:03.100Z | fill | /sign-in | fill input[name=account_id] = acc-*** |  |
| 3 | 2026-05-28T10:00:04.820Z | fill | /sign-in | fill input[name=code] = *** |  |
| 4 | 2026-05-28T10:00:06.500Z | click | /sign-in | submit sign-in form |  |
| 5 | 2026-05-28T10:00:06.812Z | network_request | /sign-in | POST /sessions -> 201 | 201 |
```

The Anomaly summary captures one anomaly per universal category (the seeded fixture is deliberately complete):

```markdown
## Anomalies

| Category | Severity | Page | Reproduction | Evidence |
| --- | --- | --- | --- | --- |
| auth-mismatch | high | /workspaces/ws-1 | Retry to GET /workspaces/{id}/assets without Authorization header got 401 | S-005 |
| broken-link | medium | /account/profile | Link to /account/profile returned 404 | S-004 |
| ... | ... | ... | ... | ... |
```

After the run, `<workspace>/requirements/open-questions.md` carries the one missing-evidence gap the seeded fixture deliberately triggers:

```markdown
- [tc-explore/explore-review] [exploration-review] missing-evidence: anomaly at 2026-05-28T10:00:48.100Z carries no screenshot_id and no screenshot event was captured within +/- 3 seconds of the anomaly timestamp.
```

Full methodology: [`tc-explore/methodology/session-based-test-management.md`](../../plugins/test-commander/skills/tc-explore/methodology/session-based-test-management.md). Methodology coverage includes the asymmetric `missing-evidence` rule (anomalies citing their own `screenshot_id` are not flagged even when no nearby screenshot event exists) and the trigger-word downgrade rule for coverage verdicts.

## Step 3: `/tc:session-summary`

Reads the exploration note and synthesizes a per-session summary. Aggregates observations by `event_type`, anomalies by `category` AND `severity`, and resolves coverage into a one-line verdict (`X observed, Y partial, Z unobserved` of total ACs). Computes session duration from first/last observation timestamps. Synthesizes structured candidate scenarios forward-compatible with Step 4's enrichment input.

**Run:**

```sh
python3 <plugin-root>/scripts/session_summary.py <project-root> --session SESS-YYYYMMDD-NNN
```

**What lands:**

- `<workspace>/sessions/<SESS-ID>.md` — 7 sections: Session metadata / Observation Summary / Anomaly Summary / Charter Coverage Summary / Evidence / Candidate Scenarios / Executive Narrative.
- `<workspace>/sessions/index.md` — rebuilt from scratch on every invocation by scanning every `sessions/SESS-*.md` file, sorted by SESS-ID. One row per session.
- Byte-deterministic: re-running against an unchanged exploration note produces identical bytes for both the summary and the index.

**Sample output** (from the seeded fixture):

```
session summary written: SESS-20260528-600 (12 candidate scenarios) at <workspace>/sessions/SESS-20260528-600.md
```

The summary excerpt (Observation Summary section):

```markdown
## Observation Summary

Total observations: **50**.

| event_type | Count |
| --- | --- |
| page_load | 10 |
| click | 13 |
| fill | 6 |
| screenshot | 9 |
| console_message | 2 |
| network_request | 10 |
```

The Candidate Scenarios section renders each candidate as an independently-citable sub-block with literal field labels (the producer/consumer contract Step 4 reads):

```markdown
### CS-600-001

- title: Reproduce auth-mismatch on /workspaces/ws-1
- type: negative
- source: `SESS-20260528-600:anomaly:auth-mismatch`
- linked_anomaly: auth-mismatch
```

The seeded session produces 12 candidates: 6 `negative` (one per anomaly, sorted by category), 3 `edge` (one per partial-coverage AC, in source order), 3 `happy` (top three successful network requests on distinct `(method, path)` pairs, sorted by `source_index`).

The sessions index gains one row per processed session:

```markdown
# Sessions index

Auto-generated by `/tc:session-summary`. Re-scans every `sessions/SESS-*.md` on each invocation. One row per session, sorted by SESS-ID (chronological by the YYYYMMDD prefix).

- `SESS-20260528-600` - charter `CH-001` - duration 1m 2s (62.5s total) - anomalies=6
```

The Executive Narrative section ships as a placeholder for the Claude judgment layer (anomaly severity calibration, candidate-scenario prioritization, partial-coverage follow-up recommendations, cross-source correlation). The mechanical synthesis above is complete and stable; the narrative is where the operator-led judgment happens.

Full methodology: [`tc-explore/methodology/session-based-test-management.md`](../../plugins/test-commander/skills/tc-explore/methodology/session-based-test-management.md) (Session summary subsection).

## Step 4: `/tc:test-ideas`

Reads one session summary (via `--session`) or every session under `<workspace>/sessions/SESS-*.md` (when omitted), and enriches each Phase-2-seeded `<workspace>/test-ideas/REQ-*.md` file whose REQ-ID is covered by a session via charter-coverage keyword cross-reference. Preserves every Phase-2 `tc-test-idea/v1` frontmatter key byte-for-byte.

**Run:**

```sh
python3 <plugin-root>/scripts/enrich_test_ideas.py <project-root> [--session SESS-YYYYMMDD-NNN]
```

**How a REQ-ID gets enriched.** The helper builds a keyword set from the charter mission + target + each acceptance criterion + every candidate scenario's title/source/linked_anomaly. Tokens are lowercase alphanumeric runs of length ≥ 4 outside a small universal-English stopword list, reduced to **five-character stems** so morphological variants match (`authentication` matches `authenticated` via `authe`; `session` matches `sessions` via `sessi`). The verbatim requirement body inside each test-idea seed's `## Requirement` section is tokenized the same way. A non-empty stem intersection means the session covers the requirement.

**What lands** (per matched (session, seed) pair):

- Frontmatter: `status: seed` flips to `status: enriched`; `phase_4_sessions: [SESS-A, SESS-B, ...]` is merged sorted-deduplicated. Every other Phase-2 key — `schema`, `requirement_id`, `requirement_title`, `source`, `ac_review_present`, `phase_2_findings`, `candidates`, `generated_by` — is preserved byte-for-byte.
- Body: a single `## Phase 4 enrichment` section is appended (once); under it, one `### <SESS-ID>` sub-block per contributing session, each listing the candidate scenarios from that session with `id`, `type`, `title`, `source`, and optional `linked_anomaly`.
- User edits or any body sections outside `## Phase 4 enrichment` are preserved byte-for-byte across re-runs. The helper is idempotent — re-running produces byte-identical files and zero duplicate enrichment sections.

**Sample output** (from running the helper against the seeded session plus the seeded Phase-2 flawed-requirements fixture, after `/tc:requirements-to-tests` has produced 17 seeds):

```
enriched: 10 (skipped: 0, untouched: 7)
  - .test-commander/test-ideas/REQ-004.md
  - .test-commander/test-ideas/REQ-005.md
  - .test-commander/test-ideas/REQ-006.md
  - .test-commander/test-ideas/REQ-007.md
  - .test-commander/test-ideas/REQ-008.md
  - .test-commander/test-ideas/REQ-009.md
  - .test-commander/test-ideas/REQ-012.md
  - .test-commander/test-ideas/REQ-014.md
  - .test-commander/test-ideas/REQ-015.md
  - .test-commander/test-ideas/REQ-016.md
```

Ten of the 17 requirements share a stem with the charter's keyword set; the other seven (REQ-001 "robust and seamless user experience", REQ-013 "shall be available for use", etc.) carry no stem overlap and remain `status: seed`.

The frontmatter delta on `REQ-005.md` (the requirement "All API access requires an authenticated user account"):

```yaml
status: enriched              # was: status: seed
phase_4_sessions: [SESS-20260528-600]   # inserted after status:
```

Every other key in the frontmatter is preserved byte-for-byte. The body gains:

```markdown
## Phase 4 enrichment

### SESS-20260528-600

Charter `CH-001` - Sign-in flow plus workspace-detail asset upload (POST /workspaces/{id}/assets).

This session contributed **12** candidate scenario(s) mapped to this requirement via charter-coverage keyword cross-reference. Refine these into BDD scenarios (Phase 5) or executable tests (Phase 6) once the candidate selection has been validated against project-specific risk.

- **CS-600-001** (negative) - Reproduce auth-mismatch on /workspaces/ws-1
  - source: `SESS-20260528-600:anomaly:auth-mismatch`
  - linked_anomaly: `auth-mismatch`
- **CS-600-002** (negative) - Reproduce broken-link on /account/profile
  - source: `SESS-20260528-600:anomaly:broken-link`
  - linked_anomaly: `broken-link`
- ...
- **CS-600-010** (happy) - Happy path: POST /sessions returns 201
  - source: `SESS-20260528-600:obs:5`
- ...
```

Full methodology: [`tc-explore/methodology/test-idea-model.md`](../../plugins/test-commander/skills/tc-explore/methodology/test-idea-model.md). The methodology covers the schema contract per-key mutability, the charter-coverage cross-reference logic, the idempotency contract, the multi-session resolution rules, and the Claude judgment layer (candidate prioritization within a REQ, cross-REQ scenario identification, stale-enrichment detection).

## What changed on disk

After running all four helpers in order against the seeded fixture (with the Phase 2 fixture pre-seeded for Step 4), your `<workspace>/` carries:

```
charters/
  CH-001.md                       # populated by /tc:create-charter
exploration-notes/
  SESS-20260528-600.md            # populated by /tc:explore
sessions/
  SESS-20260528-600.md            # populated by /tc:session-summary
  index.md                        # rebuilt by /tc:session-summary on every run
test-ideas/
  REQ-001.md                      # Phase 2 seed; not enriched (no stem overlap)
  REQ-002.md                      # Phase 2 seed; not enriched
  ...
  REQ-005.md                      # Phase 2 seed; enriched (status: enriched, phase_4_sessions: [SESS-...])
  ...
requirements/open-questions.md    # gains one [exploration-review] line per session
```

`<workspace>/product-knowledge/` is **not** touched by Phase 4 (Phase 3's responsibility). `<workspace>/traceability/` is **not** touched by Phase 4 (Phase 5's responsibility). Phase 4 reads broadly but writes narrowly to its own directories plus the `[exploration-review]` line in `open-questions.md`.

## Re-running

Every helper is idempotent. Re-running against unchanged input produces:

- **`/tc:create-charter`** — same `--target` (case-insensitive) preserves the existing charter byte-for-byte; user edits to the body are preserved. `--new-id` forces a fresh allocation.
- **`/tc:explore`** — byte-identical exploration note (the SESS-ID is derived deterministically from the recording's first-event timestamp). `open-questions.md` deduplicates by `(source-id, question-text)`, so the `[exploration-review]` line lands only once.
- **`/tc:session-summary`** — byte-identical session summary AND byte-identical sessions index.
- **`/tc:test-ideas`** — byte-identical enriched test-idea files. The helper pre-scans for an existing `phase_4_sessions:` line and only inserts when absent, so re-runs never duplicate the frontmatter key; `## Phase 4 enrichment` sub-blocks for already-cited SESS-IDs are skipped.

Add a new recording at the configured path and re-run Steps 2–4 to land a second session. The sessions index gains a second row; `phase_4_sessions:` merges across sessions sorted-deduplicated; each enriched test-idea grows a second `### <SESS-ID>` sub-block under the same `## Phase 4 enrichment` header.

## Customizing for your project

The shipped helpers carry no domain-specific vocabulary. Per D19, consuming projects extend the universal cores through `<workspace>/config.yaml`. The three extensible Phase-4 sub-blocks are:

| Block | Keys |
| --- | --- |
| `tc-explore.charters` | `risk-keywords`, `area-keywords` |
| `tc-explore.exploration` | `mode`, `recorded-path`, `mcp-endpoint`, `target-url` |
| `tc-explore.review` | `rubric-extensions` |

Missing keys = no extension; the helpers fall back to the universal cores. See [`customizing-for-your-project.md`](customizing-for-your-project.md) for the full schema and worked examples (Python web app + Playwright; mobile app with a non-Playwright MCP; API-only project where exploration falls back to spec-derived journeys).

## Beyond Phase 4

After the four Phase 4 commands have run, the consuming project has charters + exploration notes + session summaries + enriched test-idea seeds. Downstream phases consume this:

- **Phase 5** (`tc-bdd` + `tc-traceability`, **shipped**) reads enriched test-ideas as scenario seeds and emits traceable `.feature` files, reviews them, and rebuilds `<workspace>/traceability/` linking requirements to test ideas and BDD scenarios. Follow [generating-bdd.md](generating-bdd.md) for the Phase 5 walkthrough.
- **Phase 6** (`tc-build-framework`, automation) consumes the BDD output (not enriched test-ideas directly) to scaffold a Playwright framework.
- **Phase 7** (`tc-run`, execution + quality report) uses the cross-source knowledge to score risk and prioritize.

The Phase 1 `/tc:next` heuristic recommends the next command based on the workspace state; after Phase 4 finishes it advances past `/tc:create-charter` toward `/tc:generate-bdd` (Phase 5).

## See also

- [Phased plan](../../planning/plan.md) — full roadmap, decisions D1–D19, per-phase deliverables
- [Customizing for your project](customizing-for-your-project.md) — `tc-explore:` config schema and worked extension examples
- [Workspace reference](../workspace-reference.md) — per-file ownership of every `.test-commander/` artifact
- [Command reference](../command-reference.md) — every shipped `/tc:*` command with per-command-page links
- [Phase 1 walkthrough](workflow.md) — `/tc:init`, `/tc:status`, `/tc:journal`, `/tc:next`
- [Phase 2 walkthrough](reviewing-requirements.md) — requirements / user-stories / acceptance-criteria review chain plus the `/tc:requirements-to-tests` seed step Phase 4 enriches
- [Phase 3 walkthrough](building-project-knowledge.md) — the project-knowledge ingestion Phase 4 reads
- Per-command pages inside the plugin:
  - [`commands/create-charter.md`](../../plugins/test-commander/skills/tc-explore/commands/create-charter.md)
  - [`commands/explore.md`](../../plugins/test-commander/skills/tc-explore/commands/explore.md)
  - [`commands/session-summary.md`](../../plugins/test-commander/skills/tc-explore/commands/session-summary.md)
  - [`commands/test-ideas.md`](../../plugins/test-commander/skills/tc-explore/commands/test-ideas.md)
- Per-command methodology docs:
  - [`charter-based-exploration.md`](../../plugins/test-commander/skills/tc-explore/methodology/charter-based-exploration.md)
  - [`session-based-test-management.md`](../../plugins/test-commander/skills/tc-explore/methodology/session-based-test-management.md)
  - [`test-idea-model.md`](../../plugins/test-commander/skills/tc-explore/methodology/test-idea-model.md)
- [Umbrella methodology](../../plugins/test-commander/skills/tc-explore/methodology/exploratory-testing.md) — the four-step Phase-4 workflow, Bach + Bolton session-based discipline, cross-phase write boundaries, universal anomaly categories, the test-idea enrichment contract
