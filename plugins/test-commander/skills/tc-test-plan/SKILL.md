---
name: tc-test-plan
description: Test-plan authoring and maintenance for Test Commander. Use when the user runs /tc:generate-test-plan or /tc:update-test-plan, or asks to create a test plan, draft a test strategy document, build a requirement-to-test coverage map, or keep a test plan up to date as requirements and tests change. Owns the two commands that seed a human-owned test plan from the requirements inventory and regenerate its coverage map deterministically.
---

# tc-test-plan

The test-planning skill for Test Commander. Owns the two commands that turn the requirements inventory (Phase 2) plus downstream traceability into a maintainable **test plan** and a **requirement → coverage map** — the document a QA lead reviews and keeps current as the suite grows.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Model: mechanical scaffold + judgment layer

The helper is deterministic and universal (D19). It does two things:

1. **Seeds `test-plan.md`** from the bundled template, populated with the requirement inventory and a mechanical coverage status. After creation the file is **human-owned** — the helper never overwrites it, so per-test tables, defects, risks, and narrative survive. Re-create with `--force`.
2. **Regenerates `coverage-map.md`** on every run — a pure generated requirement → coverage table. This is the "keep up to date" half: it always reflects the current inventory, test-ideas, and traceability map.

The **Claude judgment layer** then fills the per-test tables (ID / Name / Description / Test Data / Status), the defect register, and the risks — the parts a generic helper cannot know because the actual test files live in the consuming project, not the workspace. See [methodology/test-planning.md](methodology/test-planning.md).

## Commands

### `/tc:generate-test-plan`

Seeds `<workspace>/test-plan/test-plan.md` from the template (skip-not-overwrite: never clobbers an existing plan unless `--force`) and writes `<workspace>/test-plan/coverage-map.md`. Reads `<workspace>/requirements/requirements-inventory.md` (required) and `<workspace>/traceability/requirements-map.md` (optional, for coverage status).

**Run:**

```sh
python3 <plugin-root>/scripts/test_plan.py <project-root> [--force]
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces and a missing/empty inventory with exit 2 (directing the user at `/tc:init` and `/tc:review-requirements`).

Full spec: [commands/generate-test-plan.md](commands/generate-test-plan.md).

### `/tc:update-test-plan`

Regenerates `<workspace>/test-plan/coverage-map.md` from the current inventory and traceability map and **never touches** the human-owned `test-plan.md`. Run it after requirements, test-ideas, or automation change so the coverage map stays current.

**Run:**

```sh
python3 <plugin-root>/scripts/test_plan.py <project-root> --refresh
```

`<project-root>` defaults to the current working directory. Same preconditions as above.

Full spec: [commands/update-test-plan.md](commands/update-test-plan.md). Methodology: [methodology/test-planning.md](methodology/test-planning.md).

## See also

- [Plugin README](../../README.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-requirements skill](../tc-requirements/SKILL.md) — produces the inventory this skill reads.
- [tc-automation-plan skill](../tc-automation-plan/SKILL.md) — the automation-suitability gate.
- [tc-quality-report skill](../tc-quality-report/SKILL.md) — run-time quality reporting.
