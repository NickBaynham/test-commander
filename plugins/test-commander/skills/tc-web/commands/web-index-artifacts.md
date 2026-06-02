# /tc:web-index-artifacts

Rebuild the web console's SQLite index from the committed `.test-commander/`
workspace.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- CLI: `<project-root>` (defaults to the current directory).

## Outputs

- `<workspace>/.test-commander/.web/index.db` — the rebuilt SQLite index
  (requirements, runs, run results, evidence, journal, traceability, quality
  facts). Git-ignored and rebuildable; the workspace artifacts remain
  authoritative.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.

## Behavior

1. Locate the backend (`apps/api/`) and the workspace.
2. Drop and recreate every index table, then parse each artifact into it
   (mirroring the real producer formats).
3. Report per-table row counts.

Deterministic: the same workspace yields the same counts. Indexing never writes
a workspace artifact — only the derived index DB.

## Safety

- Writes only the derived index DB under `.web/`. Reads workspace artifacts;
  never modifies them. No network, no command execution.

## Implementation

- Command: `plugins/test-commander/scripts/web_index_artifacts.py` (per D18) —
  delegates to the backend `tcweb.indexer.rebuild`.
- Backend: `apps/api/tcweb/indexer.py`, `apps/api/tcweb/db.py`.
- Run: `python3 <plugin-root>/scripts/web_index_artifacts.py <project-root>`.

## Definition of Done

- Indexing a seeded workspace populates the expected rows; a changed artifact
  re-indexes; the index is rebuildable from scratch; uninitialized refused
  (exit 2); the workspace is not mutated.
- `tc-web/SKILL.md` describes the shipped command.

## See also

- [Web console architecture](../methodology/web-architecture.md)
- [tc-web skill](../SKILL.md)
