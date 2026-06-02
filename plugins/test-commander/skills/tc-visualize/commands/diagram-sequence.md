# /tc:diagram-sequence

Render a sequence diagram of the journeys the user initiates against the system.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- Sources: `product-knowledge/user-journeys.md` and `product-knowledge/system-model.md`.
- CLI: `<project-root>` (defaults to the current directory).

## Outputs

- `<workspace>/visuals/mermaid/sequence.md` — a Mermaid `sequenceDiagram` with
  `User` and `System` participants, a `Note over System` listing the entities,
  and one `User->>System` message per journey, plus a `> Sources:` footer.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- Both sources are populated. A missing source is refused (exit 2) pointing at
  `/tc:learn-from-docs`.

## Behavior

1. Resolve the workspace and read both sources (refusing a stub).
2. Parse the journey titles (document order) and the entities (sorted).
3. Emit a sequence message per journey; annotate the system with its entities.
4. Render via the shared engine and write `visuals/mermaid/sequence.md`.

Deterministic: message order follows the journey document order; re-running over
unchanged sources is byte-identical.

## Safety

- Writes only `visuals/mermaid/sequence.md`. Reads sources; never modifies them.
- No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/visualize.py` — `diagram_sequence(project_root)`.
- Run: `python3 <plugin-root>/scripts/visualize.py <project-root>`.

## Definition of Done

- Valid `sequenceDiagram` whose messages trace to journeys; cites both sources;
  byte-stable; missing source refused pointing at the producer.
- `tc-visualize/SKILL.md` describes the shipped command.

## See also

- [Diagram standards](../methodology/diagram-standards.md)
- [Sequence diagram template](../templates/sequence-diagram-template.md)
- [tc-visualize skill](../SKILL.md)
