# Workspace Reference

Each consuming project gets a `.test-commander/` workspace at its repo root. The workspace holds every quality artifact Test Commander produces — requirements reviews, exploration notes, BDD specs, automation plans, evidence, learning, quality reports, traceability, visuals, sessions, journal, and runs.

The full directory layout is in [../planning/plan.md](../planning/plan.md) under "Workspace Layout".

The workspace is created and populated by `/tc:init`, which ships in Phase 1. Phase 0 does not produce a workspace — the workspace is a property of consuming projects, not of this repo.

> This page is filled out in Phase 1 alongside `/tc:init`.
