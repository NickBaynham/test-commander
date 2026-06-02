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

Phase 9 (Step 9.6). All eleven commands are end-to-end runnable:

- `/tc:visualize` — **shipped (Step 9.2).** The umbrella that regenerates the full visual set. Runs every registered generator, skipping any whose source is a missing stub so one absent source never blocks the rest. Owns the shared render engine (`render_diagram`, `render_flowchart`, `render_diagram_doc`, `write_visual`, `read_source`, `mermaid_id`, `Node`/`Edge`) every `/tc:diagram-*` reuses. Writes only under `visuals/`. Full spec: [commands/visualize.md](commands/visualize.md).
- `/tc:diagram-flow` — **shipped (Step 9.2).** A user-journey flow `flowchart` built from `product-knowledge/user-journeys.md` (the journey index) and `system-model.md` (the entities): a `User` actor, one node per journey, and a `System` node, written to `visuals/mermaid/flow.md` with a `> Sources:` footer. Refuses a missing source (exit 2) pointing at `/tc:learn-from-docs`. Full spec: [commands/diagram-flow.md](commands/diagram-flow.md).
- `/tc:diagram-sequence` — **shipped (Step 9.3).** A `sequenceDiagram` of the journeys the user initiates against the system, from `user-journeys.md` + `system-model.md`, written to `visuals/mermaid/sequence.md`. Refuses a missing source pointing at `/tc:learn-from-docs`. Full spec: [commands/diagram-sequence.md](commands/diagram-sequence.md).
- `/tc:diagram-state` — **shipped (Step 9.3).** A `stateDiagram-v2` of the scenario result lifecycle (`[*] → Pending → Passed/Failed/Flaky`) drawn from `traceability/test-map.md`, written to `visuals/mermaid/state.md`. Only states present in the map appear. Refuses a missing source pointing at `/tc:traceability-map`. Full spec: [commands/diagram-state.md](commands/diagram-state.md).
- `/tc:diagram-architecture` — **shipped (Step 9.3).** A `flowchart` of the entities the product comprises, from `product-knowledge/system-model.md`, written to `visuals/mermaid/architecture.md`. Refuses a missing source pointing at `/tc:learn-from-docs`. Full spec: [commands/diagram-architecture.md](commands/diagram-architecture.md).
- `/tc:diagram-risk` — **shipped (Step 9.4).** A `flowchart` grouping the risk register's risks into severity subgraphs, from `risk-register/risk-register.md`, written to `visuals/mermaid/risk.md`. Refuses a missing source pointing at `/tc:review-requirements`. Full spec: [commands/diagram-risk.md](commands/diagram-risk.md).
- `/tc:diagram-coverage` — **shipped (Step 9.4).** A `flowchart` linking each requirement to the downstream artifact types it has, from `traceability/requirements-map.md`, written to `visuals/mermaid/coverage.md`. Refuses a missing source pointing at `/tc:requirements-coverage`. Full spec: [commands/diagram-coverage.md](commands/diagram-coverage.md).
- `/tc:diagram-traceability` — **shipped (Step 9.4).** A `flowchart` of the full chain (requirement → scenario → result, resolved or `pending`) from `traceability/test-map.md`, written to `visuals/mermaid/traceability.md`. Refuses a missing source pointing at `/tc:traceability-map`. Full spec: [commands/diagram-traceability.md](commands/diagram-traceability.md).
- `/tc:diagram-test-strategy` — **shipped (Step 9.4).** A `flowchart` of requirements feeding the automation decision buckets, from `requirements/requirements-inventory.md` + `automation-plan/*.md`, written to `visuals/mermaid/test-strategy.md`. Refuses a missing source pointing at `/tc:automation-plan`. Full spec: [commands/diagram-test-strategy.md](commands/diagram-test-strategy.md).
- `/tc:generate-infographic` — **shipped (Step 9.5).** Aggregates the quality report's headline facts into an infographic brief (`visuals/infographic/quality-brief.md`) and a structured spec (`quality-spec.md`), measured facts only, each citing the report. Refuses a missing report pointing at `/tc:report`. Full spec: [commands/generate-infographic.md](commands/generate-infographic.md).
- `/tc:render-visuals` — **shipped (Step 9.6).** Walks `visuals/mermaid/*.md`, extracts each Mermaid block, and renders it to `visuals/svg/<name>.svg` + `visuals/png/<name>.png` via the Mermaid CLI. The only command that shells out — refused under pytest, and graceful when the CLI is absent. Refuses (exit 2) only when there are no Mermaid sources, pointing at `/tc:visualize`. Full spec: [commands/render-visuals.md](commands/render-visuals.md).

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-traceability skill](../tc-traceability/SKILL.md)
- [tc-quality-report skill](../tc-quality-report/SKILL.md)
