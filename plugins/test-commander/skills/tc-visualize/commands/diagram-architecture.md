# /tc:diagram-architecture

Render a system architecture diagram of the entities the product comprises.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- Source: `product-knowledge/system-model.md`.
- CLI: `<project-root>` (defaults to the current directory).

## Outputs

- `<workspace>/visuals/mermaid/architecture.md` — a Mermaid `flowchart` with a
  `System` node and one `comprises` edge to each entity, plus a `> Sources:`
  footer.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- The system model is populated. A missing source is refused (exit 2) pointing
  at `/tc:learn-from-docs`.

## Behavior

1. Resolve the workspace and read the system model (refusing a stub).
2. Parse the entities from the model's Entities section (sorted).
3. Build `System --> entity` (labelled `comprises`) per entity.
4. Render via the shared engine and write `visuals/mermaid/architecture.md`.

Deterministic: nodes and edges are sorted; re-running is byte-identical.

## Safety

- Writes only `visuals/mermaid/architecture.md`. Reads the model; never modifies it.
- No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/visualize.py` — `diagram_architecture(project_root)`.
- Run: `python3 <plugin-root>/scripts/visualize.py <project-root>`.

## Definition of Done

- Valid `flowchart` whose entities trace to the model; cites the system model;
  byte-stable; missing source refused pointing at the producer.
- `tc-visualize/SKILL.md` describes the shipped command.

## See also

- [Diagram standards](../methodology/diagram-standards.md)
- [Architecture diagram template](../templates/architecture-diagram-template.md)
- [tc-visualize skill](../SKILL.md)
