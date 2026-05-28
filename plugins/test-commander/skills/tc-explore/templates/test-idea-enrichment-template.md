# Test-idea enrichment template

Documents the `## Phase 4 enrichment` body section that `/tc:test-ideas` appends to a Phase-2-seeded `<workspace>/test-ideas/<REQ-ID>.md` file. The frontmatter additions are documented in [`test-idea-model.md`](../methodology/test-idea-model.md); this template captures the body-section structure so authors and downstream consumers (Phase 5 BDD generation, Phase 6 executable test generation) agree on the shape.

## Frontmatter changes (reference)

`/tc:test-ideas` modifies exactly two frontmatter keys; everything else is preserved byte-for-byte.

```yaml
status: enriched              # was: status: seed
phase_4_sessions: [SESS-NNN]  # inserted on first enrichment; merged-sorted-dedup on subsequent runs
```

## Body section

The `## Phase 4 enrichment` header appears exactly once per file, regardless of how many sessions have enriched the seed. Each contributing session contributes a `### <SESS-ID>` sub-block underneath the header.

```markdown
## Phase 4 enrichment

### SESS-YYYYMMDD-NNN

Charter `CH-NNN` - _target area resolved from the session summary_

This session contributed **N** candidate scenario(s) mapped to this requirement via charter-coverage keyword cross-reference. Refine these into BDD scenarios (Phase 5) or executable tests (Phase 6) once the candidate selection has been validated against project-specific risk.

- **CS-NNN-001** (happy) - Happy path: METHOD path returns NNN
  - source: `SESS-YYYYMMDD-NNN:obs:<source_index>`
- **CS-NNN-002** (edge) - Follow-up exploration to fully cover acceptance criterion #N: '...'
  - source: `SESS-YYYYMMDD-NNN:coverage:AC<N>:<verdict>`
- **CS-NNN-003** (negative) - Reproduce <category> on <page_url>
  - source: `SESS-YYYYMMDD-NNN:anomaly:<category>`
  - linked_anomaly: `<category>`
```

When the session covers the requirement via charter overlap but synthesized no candidate scenarios (no anomalies, no coverage gaps, no successful flows), the sub-block records the coverage without per-candidate bullets:

```markdown
### SESS-YYYYMMDD-NNN

Charter `CH-NNN` - _target area_

_This session covered the requirement via charter overlap but produced no candidate scenarios (no anomalies, no coverage gaps, no successful flows)._
```

## Multi-session example

When two sessions enrich the same REQ, the file ends up with one header and two sub-blocks (and `phase_4_sessions:` carries both SESS-IDs sorted):

```markdown
## Phase 4 enrichment

### SESS-20260528-600

Charter `CH-001` - Sign-in flow plus workspace-detail asset upload.

This session contributed **6** candidate scenarios mapped to this requirement via charter-coverage keyword cross-reference. ...

- **CS-600-001** (negative) - ...
- ...

### SESS-20260528-900

Charter `CH-001` - Sign-in flow plus workspace-detail asset upload.

This session contributed **6** candidate scenarios mapped to this requirement via charter-coverage keyword cross-reference. ...

- **CS-900-001** (negative) - ...
- ...
```

## What downstream phases read

- **Phase 5 (BDD generation)** parses each `### <SESS-ID>` sub-block as a candidate-scenario source. The candidate `id` becomes the scenario trace reference; the candidate `title` seeds the `Scenario:` heading; the candidate `type` informs whether to emit a happy / edge / negative outline; the candidate `source` becomes the scenario tag (`@source:SESS-YYYYMMDD-NNN:anomaly:...`).
- **Phase 6 (executable test generation)** consumes the BDD output, not this file directly.

## Idempotency contract

Re-running `/tc:test-ideas --session <SESS-ID>` against an unchanged workspace leaves the section byte-identical. The sub-block for an already-cited SESS-ID is never duplicated; the `## Phase 4 enrichment` header is never duplicated. See [`test-idea-model.md`](../methodology/test-idea-model.md) for the full determinism factors.

## See also

- [Test-idea-model methodology](../methodology/test-idea-model.md) — the schema contract, charter-coverage cross-reference, and Claude judgment layer.
- [Per-command page: /tc:test-ideas](../commands/test-ideas.md)
- [Session-summary template](session-summary-template.md) — the producer side of the candidate-shape contract.
