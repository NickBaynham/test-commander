# Diagram standards

The Mermaid conventions every `/tc:diagram-*` command follows so the generated
sources are valid, consistent, and byte-stable.

## Mermaid kind per diagram

| Command | Mermaid kind | Drawn from |
| --- | --- | --- |
| `/tc:diagram-flow` | `flowchart` | user journeys + system entities |
| `/tc:diagram-sequence` | `sequenceDiagram` | a user journey's actor/system exchange |
| `/tc:diagram-state` | `stateDiagram-v2` | session-lifecycle scenarios |
| `/tc:diagram-architecture` | `flowchart` | system-model entities |
| `/tc:diagram-risk` | `flowchart` (severity subgraphs) | the risk register |
| `/tc:diagram-coverage` | `flowchart` | the requirements map |
| `/tc:diagram-traceability` | `flowchart` | the test map (full chain) |
| `/tc:diagram-test-strategy` | `flowchart` | requirements + automation plan |

## Determinism

- **Identifiers** are derived from labels by `mermaid_id(prefix, label)` — a
  lowercase, underscore-collapsed slug with a kind prefix (`j_…`, `req_…`,
  `risk_…`). The prefix prevents collisions across kinds; the slug is stable.
- **Nodes and edges are sorted** by the shared `render_flowchart` engine
  (nodes by id, edges by `(src, dst, label)`), so re-running over unchanged
  sources yields byte-identical output regardless of source ordering.
- **No timestamps** leak into a diagram body. The only time-bearing artifact a
  generator reads (the quality report) contributes facts, not its clock.

## Labels and escaping

Node labels are wrapped in `["…"]`. The shared engine escapes embedded quotes
and newlines so a label drawn from a source can never break the Mermaid syntax.

## The Sources footer

Every generated `visuals/mermaid/<name>.md` ends with:

```
> Sources: `<workspace-relative-path>`, `<workspace-relative-path>`
```

listing each artifact the generator read. This is the cited-sources contract.

## Structural diagrams (per-kind derivation)

- **`/tc:diagram-sequence`** — `sequenceDiagram`. Participants are `User` and
  `System`; a `Note over System` lists the entities from the system model; one
  `User->>System` message is emitted per user journey, in document order. The
  journeys are named in `user-journeys.md`; nothing about message timing is
  invented beyond the order the journeys are listed.
- **`/tc:diagram-state`** — `stateDiagram-v2`. Models the *scenario result
  lifecycle* drawn from the test map: `[*] --> Pending`, then `Pending -->`
  each terminal result (`Passed`, `Failed`, `Flaky`) that actually appears in
  the map. A result state absent from the map never appears. (The plan's "session
  lifecycle" phrasing was a guess; the test map's result column is the real,
  derivable lifecycle source.)
- **`/tc:diagram-architecture`** — `flowchart`. A `System` node with a
  `comprises` edge to each entity in the system model's Entities section. Entities
  are sorted; no relationship the model does not state is drawn.

## Quality diagrams (per-kind derivation)

- **`/tc:diagram-risk`** — `flowchart` with one subgraph per severity level
  (`critical` → `high` → `medium` → `low`, only levels present). Each node is a
  recorded risk (`RISK-NNN: <area>`) from the register. No severity or risk is
  invented.
- **`/tc:diagram-coverage`** — `flowchart`. Each requirement links to the
  downstream artifact-type nodes (`Test ideas`, `BDD`, `Automation`) it actually
  has in the requirements map; a `_(none)_` cell yields no edge, so an uncovered
  requirement stands alone.
- **`/tc:diagram-traceability`** — `flowchart` (`LR`). The full chain per test-map
  row: `requirement → candidate scenario → result`, where result nodes
  (`Passed`/`Failed`/`Flaky`/`Pending`) are shared across rows. Resolved results
  are shown; an unresolved row renders `Pending` — never an invented outcome.
- **`/tc:diagram-test-strategy`** — `flowchart`. A `Requirements (N)` node (the
  inventory total) feeds the automation decision buckets (`Automate`/`Consider`/
  `Manual`, only those present in the plan), each linking to its ranked
  scenarios.

## See also

- [Visual documentation methodology](visual-documentation.md)
- [tc-visualize skill](../SKILL.md)
