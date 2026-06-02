# /tc:diagram-test-strategy

Render the test strategy from requirements and the automation plan.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- Source: `requirements/requirements-inventory.md` and `automation-plan/*.md`.
- CLI: `<project-root>` (defaults to the current directory).

## Outputs

- `<workspace>/visuals/mermaid/test-strategy.md` — a Mermaid `flowchart` of requirements feeding the automation decision buckets, plus a `> Sources:` footer.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- The source is populated. A missing source is refused (exit 2) pointing at `/tc:automation-plan`.

## Behavior

1. Resolve the workspace and read the source (refusing a stub).
2. Parse the structured rows and build the diagram, citing the source.
3. Render via the shared engine and write `visuals/mermaid/test-strategy.md`.

Deterministic: nodes and edges are sorted; re-running over unchanged sources is byte-identical. Never invents a node, edge, or metric absent from the source.

## Safety

- Writes only `visuals/mermaid/test-strategy.md`. Reads the source; never modifies it.
- No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/visualize.py` — `diagram-test-strategy` (underscored).
- Run: `python3 <plugin-root>/scripts/visualize.py <project-root>`.

## Definition of Done

- Valid Mermaid that traces to the source; cites the source; byte-stable; missing source refused pointing at the producer.
- `tc-visualize/SKILL.md` describes the shipped command.

## See also

- [Diagram standards](../methodology/diagram-standards.md)
- [tc-visualize skill](../SKILL.md)
