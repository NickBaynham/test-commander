# /tc:diagram-state

Render the scenario result lifecycle as a state machine, drawn from the test map.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- Source: `traceability/test-map.md`.
- CLI: `<project-root>` (defaults to the current directory).

## Outputs

- `<workspace>/visuals/mermaid/state.md` — a Mermaid `stateDiagram-v2` with an
  initial transition into `Pending` and a transition into each terminal result
  state (`Passed`, `Failed`, `Flaky`) present in the map, plus a `> Sources:`
  footer.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- The test map is populated. A missing source is refused (exit 2) pointing at
  `/tc:traceability-map`.

## Behavior

1. Resolve the workspace and read the test map (refusing a stub).
2. Parse the distinct Test-result values present.
3. Build `[*] --> Pending` plus `Pending --> <Result>` for each terminal result.
4. Render via the shared engine and write `visuals/mermaid/state.md`.

Deterministic: transitions are sorted; only states present in the map appear.

## Safety

- Writes only `visuals/mermaid/state.md`. Reads the test map; never modifies it.
- No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/visualize.py` — `diagram_state(project_root)`.
- Run: `python3 <plugin-root>/scripts/visualize.py <project-root>`.

## Definition of Done

- Valid `stateDiagram-v2` whose states are present in the map; cites the test
  map; byte-stable; missing source refused pointing at the producer.
- `tc-visualize/SKILL.md` describes the shipped command.

## See also

- [Diagram standards](../methodology/diagram-standards.md)
- [State diagram template](../templates/state-diagram-template.md)
- [tc-visualize skill](../SKILL.md)
