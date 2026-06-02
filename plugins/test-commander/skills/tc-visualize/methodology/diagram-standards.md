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

## See also

- [Visual documentation methodology](visual-documentation.md)
- [tc-visualize skill](../SKILL.md)
