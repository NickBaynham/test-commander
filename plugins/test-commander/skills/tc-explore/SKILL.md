---
name: tc-explore
description: Charter-based exploratory testing commands for Test Commander. Use when the user runs /tc:create-charter, /tc:explore, /tc:session-summary, or /tc:test-ideas, or asks about exploratory testing, charters, session-based test management, anomaly detection, or enriching Phase-2 test-idea seeds with exploration-derived candidate scenarios. Owns the four commands that produce charters, drive Playwright MCP (or replay recorded sessions in tests), synthesize per-session summaries, and enrich the Phase-2 tc-test-idea/v1 seeds with refined scenarios drawn from exploration. Live mode is opt-in via tc-explore.mode: live and refused under pytest.
---

# tc-explore

The exploratory-testing skill for Test Commander. Owns the four commands that turn product-knowledge ingestion (Phase 3) and requirements review (Phase 2) into charter-based exploration of a running target application, capturing observations, evidence, anomalies, and refined candidate scenarios.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Status

Phase 4 is in progress. The skill scaffold and seeded-exploration-session fixture (Step 4.1) have shipped. Command behavior arrives in subsequent sub-steps:

- `/tc:create-charter` — behavior arrives in Step 4.2.
- `/tc:explore` — behavior arrives in Step 4.3. Auto-runs the internal exploration-review sub-mode at end of every session (suppressible with `--no-review`).
- `/tc:session-summary` — behavior arrives in Step 4.4.
- `/tc:test-ideas` — behavior arrives in Step 4.5. Enriches the Phase-2 `tc-test-idea/v1` seeds; preserves every Phase-2 frontmatter key byte-for-byte; bumps `status: seed` → `status: enriched`.

Each sub-step ships the helper, methodology, template(s), and per-command page in a single commit, then updates this SKILL.md to describe the now-shipped behavior and remove the deferral wording for that command.

## Commands

### `/tc:create-charter`

Behavior arrives in Step 4.2. Will read `<workspace>/product-knowledge/` (system-model, entities, journeys) plus `<workspace>/requirements/open-questions.md` and `<workspace>/risk-register/risk-register.md` to suggest a charter target, or accept an explicit `--target <area>` / `--mission <text>`. Writes a charter file under `<workspace>/charters/<CH-NNN>.md` with YAML frontmatter (`id`, `mission`, `target`, `time-box`, `risk-areas`, `acceptance-criteria`, `created_at`, `phase_3_sources`).

### `/tc:explore`

Behavior arrives in Step 4.3. Will drive Playwright MCP in `live` mode against a target URL OR replay a recorded session in `recorded` mode (default; pytest never reaches `live`). Captures observations + evidence + anomalies into `<workspace>/exploration-notes/<SESS-ID>.md`. Runs the internal exploration-review sub-mode at end of session — emits `[exploration-review]` gap signals to `<workspace>/requirements/open-questions.md` when the charter coverage shortfalls or evidence gaps are detected. The `--no-review` flag suppresses the review sub-mode for advanced users who chain commands manually.

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
