# /tc:web-export

Export the console's current view as a shareable static bundle.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- CLI: `<project-root>` (defaults to the current directory); `--out <dir>` to
  override the output directory.

## Outputs

- `<workspace>/.test-commander/.web/export/data.json` — the structured bundle
  (quality facts, requirements, runs, run results, evidence, traceability,
  sources).
- `<workspace>/.test-commander/.web/export/index.html` — a self-contained,
  dependency-free rendering of the bundle.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.

## Behavior

1. Resolve the workspace; rebuild the index if absent.
2. Assemble the bundle from the index and write `data.json` + `index.html`.

Deterministic: sorted keys, no wall-clock timestamps, so the same workspace
yields byte-identical output. Read-only — writes only under `.web/export/`,
never a workspace artifact.

## Safety

- Writes only the export bundle. Reads the index/workspace; never modifies a
  workspace artifact. No network, no command execution.

## Implementation

- Command: `plugins/test-commander/scripts/web_export.py` (per D18) — delegates
  to the backend `tcweb.exporter.export`.
- Backend: `apps/api/tcweb/exporter.py`.
- Run: `python3 <plugin-root>/scripts/web_export.py <project-root> [--out <dir>]`.

## Definition of Done

- Produces a deterministic static bundle from a seeded workspace; uninitialized
  refused (exit 2); the workspace is not mutated.
- `tc-web/SKILL.md` describes the shipped command.

## See also

- [Web console architecture](../methodology/web-architecture.md)
- [tc-web skill](../SKILL.md)
