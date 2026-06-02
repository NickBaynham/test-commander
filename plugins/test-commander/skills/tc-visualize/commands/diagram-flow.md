# /tc:diagram-flow

Render a user-journey flow diagram from the project knowledge base — the first
concrete generator and a worked example of the generate-and-cite discipline.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- Sources: `product-knowledge/user-journeys.md` (the journey index) and
  `product-knowledge/system-model.md` (the entities).
- CLI: `<project-root>` (defaults to the current directory).

## Outputs

- `<workspace>/visuals/mermaid/flow.md` — a Mermaid `flowchart` with a `User`
  actor, one node per user journey, and a `System` node carrying the system
  entities, plus a `> Sources:` footer.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- Both sources are populated (not template stubs). A missing source is refused
  (exit 2) with a message directing the user at `/tc:learn-from-docs`.

## Behavior

1. **Resolve** the workspace and **read** both sources (refusing a stub).
2. **Parse** the journey titles (document order) and the system entities (sorted).
3. **Build** the graph: `User` → each journey → `System`. Every node traces to a
   source; nothing is invented.
4. **Render** via the shared engine and write `visuals/mermaid/flow.md`.

Deterministic: nodes and edges are sorted, so re-running over unchanged sources
yields byte-identical output.

## Safety

- Writes only `visuals/mermaid/flow.md`. Reads the two sources; never modifies them.
- No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/visualize.py` — `diagram_flow(project_root)`.
- Run: `python3 <plugin-root>/scripts/visualize.py <project-root>` (the umbrella
  runs every generator) or call `diagram_flow` directly.

## Definition of Done

- Renders a valid Mermaid flowchart whose every node traces to a source; cites
  both sources; byte-stable; a missing source refused pointing at the producer.
- `tc-visualize/SKILL.md` describes the shipped `/tc:diagram-flow`.

## See also

- [Diagram standards](../methodology/diagram-standards.md)
- [Flow diagram template](../templates/flow-diagram-template.md)
- [/tc:visualize](visualize.md)
- [tc-visualize skill](../SKILL.md)
