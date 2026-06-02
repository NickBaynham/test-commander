# /tc:visualize

Regenerate the full Test Commander visual set from the current workspace state —
the umbrella command that runs every available `/tc:diagram-*` generator and
home of the shared render engine they reuse.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- CLI: `<project-root>` (defaults to the current directory).

## Outputs

- One `<workspace>/visuals/mermaid/<name>.md` per diagram whose source is
  present (Mermaid in a fenced block + a `> Sources:` footer). Diagrams whose
  source is missing or still a stub are skipped, not failed.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.

## Behavior

1. **Resolve** the workspace (refuse if uninitialized).
2. **Run** each registered generator. A generator whose source is missing raises
   `MissingSourceError`; the umbrella catches it and skips that diagram so one
   absent source never blocks the rest of the set.
3. **Report** the files written.

Deterministic: each generator is byte-stable, so re-running `/tc:visualize` over
unchanged sources leaves every `visuals/mermaid/*.md` byte-identical.

## Safety

- Writes only under `visuals/`. Reads workspace artifacts; never modifies them.
- No network, no browser. Rendering to SVG/PNG is `/tc:render-visuals`' job.

## Implementation

- Helper: `plugins/test-commander/scripts/visualize.py` (per D18).
- Run: `python3 <plugin-root>/scripts/visualize.py <project-root>`.
- Exposes the shared engine every generator reuses: `render_diagram`,
  `render_flowchart`, `render_diagram_doc`, `write_visual`, `read_source`,
  `mermaid_id`, and the `Node`/`Edge` dataclasses.

## Definition of Done

- Regenerates every available diagram from real sources; skips missing sources;
  byte-stable on re-run; writes only under `visuals/`; uninitialized refused.
- `tc-visualize/SKILL.md` describes the shipped behavior.

## See also

- [Visual documentation methodology](../methodology/visual-documentation.md)
- [Diagram standards](../methodology/diagram-standards.md)
- [/tc:diagram-flow](diagram-flow.md)
- [tc-visualize skill](../SKILL.md)
