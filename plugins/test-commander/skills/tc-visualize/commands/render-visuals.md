# /tc:render-visuals

Render every Mermaid source under `visuals/mermaid/` to SVG and PNG via the
Mermaid CLI — the only tc-visualize command that shells out.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- Sources: `visuals/mermaid/*.md` (produced by `/tc:visualize` and the
  `/tc:diagram-*` commands).
- The Mermaid CLI (`mmdc`), provisioned by `make install`.
- CLI: `<project-root>` (defaults to the current directory).

## Outputs

- `<workspace>/visuals/svg/<name>.svg` and `visuals/png/<name>.png` for each
  Mermaid source.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- At least one `visuals/mermaid/*.md` exists. Otherwise refused (exit 2),
  directing the user at `/tc:visualize`.

## Behavior

1. Resolve the workspace and plan `(source → svg, png)` for every Mermaid file.
2. If `mmdc` is not on PATH, report the missing CLI and exit 0 without rendering
   (graceful degradation — a missing CLI never breaks a workflow).
3. Otherwise render each source to SVG and PNG.

The real `mmdc` invocation is **refused under pytest** (`PYTEST_CURRENT_TEST`),
so the test suite asserts the Mermaid extraction and the planned paths, never a
rendered binary.

## Safety

- Writes only under `visuals/svg/` and `visuals/png/`. Reads Mermaid sources;
  never modifies them.
- The only command that shells out. No network; the Mermaid CLI runs locally.

## Implementation

- Helper: `plugins/test-commander/scripts/render_visuals.py` (per D18). Reuses
  `visualize.py` for workspace resolution and the error types.
- Run: `python3 <plugin-root>/scripts/render_visuals.py <project-root>`.
- Exposes `extract_mermaid`, `plan_visuals`, `mmdc_available`, and the guarded
  `_invoke_mmdc`.

## Definition of Done

- Extracts each Mermaid block and plans correct SVG/PNG paths; the real render is
  refused under pytest with a directing message; a missing CLI degrades
  gracefully; no Mermaid sources refused pointing at `/tc:visualize`.
- `tc-visualize/SKILL.md` describes the shipped command.

## See also

- [Visual documentation methodology](../methodology/visual-documentation.md)
- [/tc:visualize](visualize.md)
- [tc-visualize skill](../SKILL.md)
