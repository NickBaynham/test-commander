# seeded-visuals fixture

A populated `.test-commander/` workspace slice carrying one real source artifact
per `tc-visualize` diagram type, so the diagram generators can be exercised
against a deterministic input that mirrors the real producer formats. Tests copy
this tree into a tmp workspace and run the helpers against it.

The narrative is deliberately universal (Decision D19): a generic SaaS surface —
sign-in, dashboard, workspaces, file upload — with no product-specific domain
vocabulary. A consuming project's real artifacts replace these at runtime.

## Per-diagram source map

Each generator reads exactly the artifact(s) named here and cites them in a
`> Sources:` footer. It never invents a node, edge, or metric absent from the
source.

| Command | Source artifact(s) |
| --- | --- |
| `/tc:diagram-flow` | `product-knowledge/user-journeys.md`, `product-knowledge/system-model.md` |
| `/tc:diagram-sequence` | `product-knowledge/user-journeys.md`, `product-knowledge/system-model.md` |
| `/tc:diagram-state` | `traceability/test-map.md` (session-lifecycle scenarios) |
| `/tc:diagram-architecture` | `product-knowledge/system-model.md` |
| `/tc:diagram-risk` | `risk-register/risk-register.md` |
| `/tc:diagram-coverage` | `traceability/requirements-map.md` |
| `/tc:diagram-traceability` | `traceability/test-map.md` |
| `/tc:diagram-test-strategy` | `requirements/requirements-inventory.md`, `automation-plan/*.md` |
| `/tc:generate-infographic` | `quality-report/current-quality-report.md` |

## Format fidelity

Every artifact here is byte-for-byte in the shape its real producer emits:

- `requirements/requirements-inventory.md` — `review_requirements._render_inventory`.
- `traceability/requirements-map.md`, `traceability/test-map.md` — `traceability_render`.
- `quality-report/current-quality-report.md` — `build_report`.
- `product-knowledge/system-model.md` — `synthesize_system_model`.
- `product-knowledge/user-journeys.md` — `extract_knowledge_from_docs`.
- `automation-plan/sign-in.md` — `automation_plan.render_plan`.
- `risk-register/risk-register.md` — the human-authored register shape that
  `build_report` and `create_charter` already read (no shipped helper writes it).
