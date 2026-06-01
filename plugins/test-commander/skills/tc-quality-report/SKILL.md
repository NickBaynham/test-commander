---
name: tc-quality-report
description: Quality reporting and release gating for Test Commander. Use when the user runs /tc:report or /tc:quality-gate, or asks about aggregating the workspace into a living quality report with a committed history, separating facts from interpretation, resolving the downstream traceability columns, or evaluating release readiness against project-defined thresholds. Owns the two commands that produce the quality report plus its history snapshots and return a PASS, WARN, or FAIL gate verdict.
---

# tc-quality-report

The quality-reporting skill for Test Commander. Owns the two commands that aggregate the whole workspace into a living quality report — keeping facts, interpretation, and human-review items clearly separated — snapshot every report into a committed history, and evaluate release readiness against project-defined thresholds.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Status

Phase 7 (Step 7.5). `/tc:report` is end-to-end runnable; `/tc:quality-gate` is registered but not yet shipped:

- `/tc:report` — **shipped (Step 7.5).** Aggregates the workspace into `<workspace>/quality-report/current-quality-report.md` with all fifteen spec'd sections (keeping `[fact]` / `[interpretation]` / `[review]` content separated), snapshots a byte-identical full copy to `quality-report/history/<YYYY-MM-DD-HHmm>.md` (kept forever; filename from an injected clock for determinism), and rebuilds the traceability maps so the `Test result` and `Quality report` columns of `traceability/test-map.md` resolve from `pending`.
- `/tc:quality-gate` — behavior arrives in Step 7.6. It will evaluate the report and latest run against project-defined thresholds (`tc-quality-report.gate.thresholds`) and return PASS / WARN / FAIL with a per-criterion breakdown, reading only measured values (never inventing metrics).

When Step 7.6 lands, this SKILL.md is updated to describe the shipped `/tc:quality-gate` behavior and the deferral wording above is removed.

## Commands

### `/tc:report`

Aggregates the workspace into `<workspace>/quality-report/current-quality-report.md` with all fifteen sections (executive summary, coverage, requirements readiness, exploratory findings, automated regression status, known risks, known defects, open questions, automation health, flaky tests, evidence summary, traceability summary, recommendations, release readiness, recent changes), keeping `[fact]` (measured), `[interpretation]` (synthesis), and `[review]` (needs human review) content clearly separated and never inventing a metric. Snapshots a byte-identical full copy to `quality-report/history/<YYYY-MM-DD-HHmm>.md`, then rebuilds the traceability maps so `test-map.md`'s `Test result` (from `runs/`) and `Quality report` (from this report) columns resolve from `pending`. Deterministic via an injected clock (`--now`).

**Run:**

```sh
python3 <plugin-root>/scripts/build_report.py <project-root> [--now <ISO-8601>]
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2). A report can be built before any test has run (run-derived sections read "no run yet").

Full spec: [commands/report.md](commands/report.md). Methodology: [methodology/quality-reporting.md](methodology/quality-reporting.md).

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
