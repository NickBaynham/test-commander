# seeded-web fixture

A populated `.test-commander/` workspace slice for the Phase 10 web-console
backend tests. Tests point the FastAPI app at this tree (via `TC_WORKSPACE`) and
assert the indexer and read routes render it faithfully.

Universal SaaS narrative (Decision D19): sign-in, dashboard, workspaces, file
upload — no product-specific domain vocabulary. The artifacts mirror the real
producer formats (`review_requirements`, `traceability_render`, `build_report`,
`run_tests`, `journal`) so the indexer parses fixture and live workspaces
identically.

Contents:

- `project.md` — project identity.
- `requirements/requirements-inventory.md` — the parsed requirement inventory.
- `traceability/test-map.md`, `requirements-map.md` — the traceability maps.
- `quality-report/current-quality-report.md` — the living quality report.
- `journal/2026-06-01.md` — an append-only journal day file.
- `runs/RUN-20260601-093000/` — one run (`run.md` + `results.json`).
- `evidence/` — the evidence index plus a screenshot reference.
