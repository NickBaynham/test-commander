---
name: tc-visualize
description: Visual documentation and infographics for Test Commander. Use when the user runs /tc:visualize, /tc:diagram-flow, /tc:diagram-sequence, /tc:diagram-state, /tc:diagram-risk, /tc:diagram-coverage, /tc:diagram-traceability, /tc:diagram-test-strategy, /tc:diagram-architecture, /tc:generate-infographic, or /tc:render-visuals, or asks to draw a diagram, flow, state machine, risk heat map, coverage map, traceability chain, or infographic of the project's quality posture. Every visual is generated only from committed workspace artifacts, cites its sources, and never invents a node, edge, or metric.
---

# tc-visualize

The visual-documentation skill for Test Commander. Owns the eleven commands that turn committed workspace artifacts into diffable Mermaid diagrams and infographic specs, then render them to SVG/PNG.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

Two disciplines govern every command in this skill:

- **Generate-and-cite, never invent.** Every diagram is rendered *only* from committed workspace artifacts (the traceability maps, the requirements inventory, the risk register, the quality report, the system model, the user-journey index), and every generated Mermaid file carries a `> Sources:` line listing the path of each artifact it drew from. A diagram never fabricates a node, edge, or metric that is not present in a source.
- **Mermaid text is the source of truth; rendering is a separate step.** The `/tc:diagram-*` commands and `/tc:generate-infographic` emit deterministic, byte-stable Mermaid/Markdown only — no binaries. `/tc:render-visuals` is the only command that shells out (to the Mermaid CLI to produce SVG/PNG); it is refused under pytest so the suite asserts the Mermaid source, never a rendered binary.

Generated Mermaid sources land under `<workspace>/visuals/mermaid/<name>.md`; rendered output under `visuals/svg/` and `visuals/png/`; infographics under `visuals/infographic/`. Nothing outside `visuals/` is ever written.

## Status

Phase 9 (Step 9.2). The remaining commands ship across Steps 9.3-9.6; until each lands, its behavior is documented in the per-command page once that step ships:

- `/tc:visualize` — **shipped (Step 9.2).** The umbrella that regenerates the full visual set. Runs every registered generator, skipping any whose source is a missing stub so one absent source never blocks the rest. Owns the shared render engine (`render_diagram`, `render_flowchart`, `render_diagram_doc`, `write_visual`, `read_source`, `mermaid_id`, `Node`/`Edge`) every `/tc:diagram-*` reuses. Writes only under `visuals/`. Full spec: [commands/visualize.md](commands/visualize.md).
- `/tc:diagram-flow` — **shipped (Step 9.2).** A user-journey flow `flowchart` built from `product-knowledge/user-journeys.md` (the journey index) and `system-model.md` (the entities): a `User` actor, one node per journey, and a `System` node, written to `visuals/mermaid/flow.md` with a `> Sources:` footer. Refuses a missing source (exit 2) pointing at `/tc:learn-from-docs`. Full spec: [commands/diagram-flow.md](commands/diagram-flow.md).
- `/tc:diagram-sequence` — a sequence diagram from a user journey. Behavior arrives in Phase 9 Step 9.3.
- `/tc:diagram-state` — a state diagram from the session lifecycle. Behavior arrives in Phase 9 Step 9.3.
- `/tc:diagram-architecture` — an architecture diagram from `product-knowledge/system-model.md`. Behavior arrives in Phase 9 Step 9.3.
- `/tc:diagram-risk` — a risk diagram from `risk-register.md`. Behavior arrives in Phase 9 Step 9.4.
- `/tc:diagram-coverage` — a coverage diagram from `traceability/requirements-map.md`. Behavior arrives in Phase 9 Step 9.4.
- `/tc:diagram-traceability` — the full traceability chain from `traceability/test-map.md`. Behavior arrives in Phase 9 Step 9.4.
- `/tc:diagram-test-strategy` — a test-strategy diagram from requirements and the automation plan. Behavior arrives in Phase 9 Step 9.4.
- `/tc:generate-infographic` — an infographic brief and spec from the quality report. Behavior arrives in Phase 9 Step 9.5.
- `/tc:render-visuals` — renders every `visuals/mermaid/*.md` to SVG/PNG via the Mermaid CLI. Behavior arrives in Phase 9 Step 9.6.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-traceability skill](../tc-traceability/SKILL.md)
- [tc-quality-report skill](../tc-quality-report/SKILL.md)
