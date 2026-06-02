# /tc:web-sync

Reconcile the web console's SQLite index with the committed `.test-commander/`
workspace.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- CLI: `<project-root>` (defaults to the current directory).

## Outputs

- An up-to-date `<workspace>/.test-commander/.web/index.db`.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.

## Behavior

1. Locate the backend and the workspace.
2. Reconcile the index with the workspace. Because the index is a full
   rebuildable derivative, a sync is a clean rebuild — the workspace stays
   authoritative.
3. Report the reconciled row count.

The console's open pages also refresh automatically via the SSE `changed` event
when the workspace changes; `/tc:web-sync` is the explicit, on-demand reconcile.

## Safety

- Writes only the derived index DB. Reads workspace artifacts; never modifies
  them. No network, no command execution.

## Implementation

- Command: `plugins/test-commander/scripts/web_sync.py` (per D18) — delegates to
  the backend `tcweb.indexer.rebuild`.
- Backend read routes: `apps/api/tcweb/routes.py`; SSE: `apps/api/tcweb/sse.py`;
  proposals: `apps/api/tcweb/proposals.py`.
- Run: `python3 <plugin-root>/scripts/web_sync.py <project-root>`.

## Definition of Done

- Reconciles the index; uninitialized refused (exit 2); the workspace is not
  mutated.
- `tc-web/SKILL.md` describes the shipped command.

## See also

- [Web console architecture](../methodology/web-architecture.md)
- [/tc:web-index-artifacts](web-index-artifacts.md)
- [tc-web skill](../SKILL.md)
