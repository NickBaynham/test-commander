---
name: tc-quality-report
description: Quality reporting and release gating for Test Commander. Use when the user runs /tc:report or /tc:quality-gate, or asks about aggregating the workspace into a living quality report with a committed history, separating facts from interpretation, resolving the downstream traceability columns, or evaluating release readiness against project-defined thresholds. Owns the two commands that produce the quality report plus its history snapshots and return a PASS, WARN, or FAIL gate verdict.
---

# tc-quality-report

The quality-reporting skill for Test Commander. Owns the two commands that aggregate the whole workspace into a living quality report — keeping facts, interpretation, and human-review items clearly separated — snapshot every report into a committed history, and evaluate release readiness against project-defined thresholds.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Status

Phase 7 scaffold (Step 7.1). The two commands are registered but their behavior is not yet shipped:

- `/tc:report` — behavior arrives in Step 7.5. It will aggregate the workspace into `<workspace>/quality-report/current-quality-report.md` with every spec'd section, snapshot a full copy to `quality-report/history/<YYYY-MM-DD-HHmm>.md` (full snapshot, kept forever; filename from an injected clock for determinism), and resolve the `Test result` and `Quality report` columns of `traceability/test-map.md` that Phase 6 left `pending`.
- `/tc:quality-gate` — behavior arrives in Step 7.6. It will evaluate the report and latest run against project-defined thresholds (`tc-quality-report.gate.thresholds`) and return PASS / WARN / FAIL with a per-criterion breakdown, reading only measured values (never inventing metrics).

When Steps 7.5 and 7.6 land, this SKILL.md is updated to describe the shipped behavior and the deferral wording above is removed.

## Commands

### `/tc:report`

Aggregates the workspace into the current quality report and snapshots it into the committed history. Full behavior is documented in the per-command page once Step 7.5 ships the helper.

### `/tc:quality-gate`

Evaluates release readiness against project-defined thresholds and returns PASS / WARN / FAIL. Full behavior is documented in the per-command page once Step 7.6 ships the helper.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-run skill](../tc-run/SKILL.md)
- [tc-evidence skill](../tc-evidence/SKILL.md)
- [tc-traceability skill](../tc-traceability/SKILL.md)
