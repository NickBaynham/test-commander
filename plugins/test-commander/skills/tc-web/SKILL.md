---
name: tc-web
description: Read-only web console for Test Commander. Use when the user runs /tc:web-init, /tc:web-start, /tc:web-sync, /tc:web-index-artifacts, or /tc:web-export, or asks to open the dashboard, browse the quality report, journal, sessions, requirements, test runs, or evidence in a browser, or to chat with the workspace. The console renders the committed .test-commander workspace, never invents data, and is read-only and proposal-only - it never changes the workspace or runs a command (execution is gated behind Phase 10.5).
---

# tc-web

The web-console skill for Test Commander. Owns the five commands that bring up a team-facing, read-only viewer over a consuming project's `.test-commander/` workspace — a Next.js frontend (`apps/web/`) and a FastAPI backend (`apps/api/`), brought up together by `make run` on docker compose.

Each command is a Python helper bundled inside the plugin (per Decision D18) that drives the stack under `apps/`. The per-command pages under `commands/` are the authoritative behavior spec.

Three disciplines govern this skill:

- **Read-only and proposal-only — no execution.** The console answers from indexed artifacts and *suggests* `/tc:*` commands as proposal cards; it never changes the workspace or runs a command. Every backend route is read-only or proposal-generating. The execution pipeline is Phase 10.5 (the governance phase).
- **The workspace is the source of truth; the DB is a derived index.** The backend's SQLite index is a rebuildable derivative of the committed `.test-commander/` artifacts; the workspace files remain authoritative, and every panel cites or links the artifact it rendered.
- **`make run` brings up the whole stack on docker compose.** Frontend + backend run locally via `make run`; no cloud dependency for the MVP (Pattern A, Decision D15).

## Status

Phase 10 (Step 10.1 — scaffold). The five commands ship across Steps 10.2-10.6; until each lands, its behavior is documented in the per-command page once that step ships:

- `/tc:web-init` — **shipped (Step 10.4).** Provisions `.test-commander/.web/console.json` (api base, web port); idempotent; refuses an uninitialized workspace (exit 2). Full spec: [commands/web-init.md](commands/web-init.md).
- `/tc:web-start` — **shipped (Step 10.4).** Prints the `docker compose up` command and the workspace by default (a dry run); `--up` brings the stack up (refused under pytest). Ships alongside the MVP frontend pages (Dashboard, Quality Report, Journal, Sessions, Requirements, Test Runs, Evidence, Settings) with SSE live-update on the dashboard and journal. Full spec: [commands/web-start.md](commands/web-start.md).
- `/tc:web-sync` — **shipped (Step 10.3).** Reconciles the SQLite index with the workspace (a clean rebuild). Ships alongside the read-only API routes (one per page), the SSE `/api/events` stream (a `changed` frame on any workspace change), and `/api/proposals` (returns a command proposal card, never executes). Refuses an uninitialized workspace (exit 2). Full spec: [commands/web-sync.md](commands/web-sync.md).
- `/tc:web-index-artifacts` — **shipped (Step 10.2).** Rebuilds the SQLite index (requirements, runs, run results, evidence, journal, traceability, quality facts) from the workspace into `.test-commander/.web/index.db`. Drops and repopulates every table, so the index is always reconstructible; never mutates a workspace artifact. Refuses an uninitialized workspace (exit 2). Full spec: [commands/web-index-artifacts.md](commands/web-index-artifacts.md).
- `/tc:web-export` — export the current view as a shareable static bundle. Behavior arrives in Phase 10 Step 10.6.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-quality-report skill](../tc-quality-report/SKILL.md)
- [tc-visualize skill](../tc-visualize/SKILL.md)
