# /tc:diagram-traceability

Render the full traceability chain from the test map.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- Source: `traceability/test-map.md`.
- CLI: `<project-root>` (defaults to the current directory).

## Outputs

- `<workspace>/visuals/mermaid/traceability.md` — a Mermaid `flowchart` of requirement to scenario to test result (resolved or `pending`), plus a `> Sources:` footer.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- The source is populated. A missing source is refused (exit 2) pointing at `/tc:traceability-map`.

## Behavior

1. Resolve the workspace and read the source (refusing a stub).
2. Parse the structured rows and build the diagram, citing the source.
3. Render via the shared engine and write `visuals/mermaid/traceability.md`.

Deterministic: nodes and edges are sorted; re-running over unchanged sources is byte-identical. Never invents a node, edge, or metric absent from the source.

## Safety

- Writes only `visuals/mermaid/traceability.md`. Reads the source; never modifies it.
- No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/visualize.py` — `diagram-traceability` (underscored).
- Run: `python3 <plugin-root>/scripts/visualize.py <project-root>`.

## Definition of Done

- Valid Mermaid that traces to the source; cites the source; byte-stable; missing source refused pointing at the producer.
- `tc-visualize/SKILL.md` describes the shipped command.

## See also

- [Diagram standards](../methodology/diagram-standards.md)
- [tc-visualize skill](../SKILL.md)
