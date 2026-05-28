---
name: tc-explore
description: Charter-based exploratory testing commands for Test Commander. Use when the user runs /tc:create-charter, /tc:explore, /tc:session-summary, or /tc:test-ideas, or asks about exploratory testing, charters, session-based test management, anomaly detection, or enriching Phase-2 test-idea seeds with exploration-derived candidate scenarios. Owns the four commands that produce charters, drive Playwright MCP (or replay recorded sessions in tests), synthesize per-session summaries, and enrich the Phase-2 tc-test-idea/v1 seeds with refined scenarios drawn from exploration. Live mode is opt-in via tc-explore.mode: live and refused under pytest.
---

# tc-explore

The exploratory-testing skill for Test Commander. Owns the four commands that turn product-knowledge ingestion (Phase 3) and requirements review (Phase 2) into charter-based exploration of a running target application, capturing observations, evidence, anomalies, and refined candidate scenarios.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Status

Phase 4 is in progress. The skill scaffold and seeded-exploration-session fixture (Step 4.1) plus `/tc:create-charter` (Step 4.2) plus `/tc:explore` (Step 4.3) have shipped. Remaining command behavior arrives in subsequent sub-steps:

- `/tc:create-charter` — **shipped (Step 4.2).**
- `/tc:explore` — **shipped (Step 4.3).** Auto-runs the internal exploration-review sub-mode at end of every session (suppressible with `--no-review`).
- `/tc:session-summary` — behavior arrives in Step 4.4.
- `/tc:test-ideas` — behavior arrives in Step 4.5. Enriches the Phase-2 `tc-test-idea/v1` seeds; preserves every Phase-2 frontmatter key byte-for-byte; bumps `status: seed` → `status: enriched`.

Each sub-step ships the helper, methodology, template(s), and per-command page in a single commit, then updates this SKILL.md to describe the now-shipped behavior and remove the deferral wording for that command.

## Commands

### `/tc:create-charter`

Reads Phase-3 product-knowledge (`system-model.md`, `entities.md`, `user-journeys.md`) plus Phase-2 `requirements/open-questions.md` and the project's `risk-register/risk-register.md` to either accept an explicit `--target <area>` / `--mission <text>` charter scope OR auto-suggest one from the entity with the highest mention count (ties broken alphabetically for deterministic output). Writes a charter file under `<workspace>/charters/<CH-NNN>.md` with YAML frontmatter (`id`, `mission`, `target`, `time-box: 60min`, `risk-areas`, `acceptance-criteria`, `created_at`, `phase_3_sources`) and a structured body (Mission / Target Area / Time-Box / Risk Areas / Acceptance Criteria / Out of Scope / Phase 3 Sources). Idempotent: re-running with the same `--target` skips the existing charter byte-identically (`created: 0, skipped: 1`); `--new-id` forces a fresh `CH-NNN` allocation; user edits to charter bodies are preserved across re-runs.

**Run:**

```sh
python3 <plugin-root>/scripts/create_charter.py <project-root> [--target TEXT | --mission TEXT] [--new-id]
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces and empty Phase-3 product-knowledge with exit 2; the precondition error directs the user at `/tc:learn-from-docs` (Phase 3). Configurable via `tc-explore.charters.{risk-keywords, area-keywords}` in `<workspace>/config.yaml` — both extensions union with the universal core additively per D19.

Full spec: [commands/create-charter.md](commands/create-charter.md). Methodology: [methodology/charter-based-exploration.md](methodology/charter-based-exploration.md). Umbrella: [methodology/exploratory-testing.md](methodology/exploratory-testing.md).

### `/tc:explore`

Reads a charter file at `<workspace>/charters/<CH-ID>.md` (required, refused with precondition error pointing at `/tc:create-charter` when missing) plus a recorded Playwright MCP session at the configured path (default `<workspace>/documents/uploaded/recorded-sessions/<CH-ID>.json`, overridable via `tc-explore.exploration.recorded-path`). Classifies every event into Observations (`page_load`, `click`, `fill`, `screenshot`, `console_message`, `network_request`), Evidence (every screenshot with its `screenshot_id` + caption), and Anomalies (the six universal-core categories `slow-response`, `console-error`, `broken-link`, `missing-evidence`, `auth-mismatch`, `unexpected-state` with severities from `{low, medium, high, critical}`). Computes a Charter-Coverage matrix marking each acceptance criterion `observed` / `partial` / `unobserved` based on URL-path + distinctive-keyword + trigger-word matching against the observed corpus. Runs the internal exploration-review sub-mode at end of session (suppressible with `--no-review`): emits `missing-evidence` gap signals for anomalies carrying `screenshot_id: null` AND no `screenshot` event within ±3s; emits `charter-coverage-shortfall` gap signals for every acceptance criterion marked `unobserved`. All gap signals route to `<workspace>/requirements/open-questions.md` with the `[exploration-review]` kind prefix and the Phase-2 `(source-id, question-text)` dedup contract. Writes `<workspace>/exploration-notes/<SESS-ID>.md` byte-deterministically — re-running against unchanged input produces identical bytes. Session IDs follow `SESS-YYYYMMDD-NNN` where NNN is derived deterministically from the first event's time-of-day so the same recording always produces the same SESS-ID. Live mode (`tc-explore.exploration.mode: live`) is documented for future use and **refused under pytest** via the `PYTEST_CURRENT_TEST` env-var check before any MCP connection is constructed (mirrors Phase 3 Step 3.5 verbatim).

**Run:**

```sh
python3 <plugin-root>/scripts/explore.py <project-root> --charter CH-NNN [--no-review]
```

`<project-root>` defaults to the current working directory. The `--charter` flag is required. The `--no-review` flag suppresses the internal review sub-mode for advanced users who chain commands manually.

Full spec: [commands/explore.md](commands/explore.md). Methodology: [methodology/session-based-test-management.md](methodology/session-based-test-management.md).

### `/tc:session-summary`

Behavior arrives in Step 4.4. Will read `<workspace>/exploration-notes/<SESS-ID>.md` and synthesize a per-session summary at `<workspace>/sessions/<SESS-ID>.md`: charter resolved, duration, observation counts by event type, anomaly counts by category and severity, charter-coverage verdict, candidate scenarios extracted from the session (forward-compatible with Step 4.5's enrichment input). Also maintains `<workspace>/sessions/index.md` as the one-line-per-session ledger.

### `/tc:test-ideas`

Behavior arrives in Step 4.5. Will enrich the Phase-2-seeded `<workspace>/test-ideas/<REQ-ID>.md` files with refined candidate scenarios drawn from exploration sessions. **Preserves every Phase-2 `tc-test-idea/v1` frontmatter key byte-for-byte**, bumps `status: seed` → `status: enriched`, adds `phase_4_sessions: [SESS-ID, ...]` to frontmatter (sorted, deduplicated; updated never duplicated on re-runs), and appends a `## Phase 4 enrichment` body section listing each contributing session's candidate scenarios mapped to this REQ-ID via charter-coverage cross-reference. User edits + prior Phase-4 enrichments are preserved.

## Finding the helpers

The helpers will live at `scripts/<name>.py` relative to this plugin's root (the directory containing this SKILL.md is `<plugin-root>/skills/tc-explore/`). In a development checkout that is `<repo>/plugins/test-commander/scripts/`. In the installed plugin cache it is `~/.claude/plugins/cache/test-commander-marketplace/test-commander/<version>/scripts/`. Either way, resolve the helper path relative to this SKILL.md's own location.

## What to do when a slash command fires

Until the per-command sub-steps land, invoking any `/tc:create-charter`, `/tc:explore`, `/tc:session-summary`, or `/tc:test-ideas` command should produce a clear notice that the behavior arrives in the named sub-step and point the user at the phased plan. From Step 4.2 onward, this section will be replaced with per-command invocation guidance mirroring `tc-requirements/SKILL.md` and `tc-knowledge/SKILL.md`: resolve the helper path, run via `Bash` against the project root, report the helper's output, and layer the relevant methodology's judgment narrative on top.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-core skill](../tc-core/SKILL.md)
- [tc-requirements skill](../tc-requirements/SKILL.md)
- [tc-knowledge skill](../tc-knowledge/SKILL.md)
