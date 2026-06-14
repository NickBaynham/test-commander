# /tc:generate-test-plan

Seed a human-owned test plan from the requirements inventory and write its
requirement → coverage map.

## Inputs

- `<workspace>/requirements/requirements-inventory.md` — the parsed REQ-ID list
  (required; produced by `/tc:review-requirements`).
- `<workspace>/traceability/requirements-map.md` — per-requirement downstream
  links (test ideas / BDD / automation), when present. Used to derive each
  requirement's mechanical coverage status.
- `skills/tc-test-plan/templates/test-plan-template.md` — the plan template.

## Outputs

- `<workspace>/test-plan/test-plan.md` — the plan document. Written from the
  template **only if it does not already exist** (or `--force`); otherwise the
  existing file is preserved untouched.
- `<workspace>/test-plan/coverage-map.md` — pure generated requirement →
  coverage table; overwritten byte-deterministically.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- The requirements inventory exists and has REQ rows. Otherwise exit 2,
  directing the user at `/tc:review-requirements`.

## Behavior

1. Resolve the workspace; refuse if uninitialized.
2. Parse the inventory into `(REQ-ID, body)` rows in document order.
3. Parse the traceability map (if present) into per-requirement downstream links.
4. Derive each requirement's coverage status: `automated` (has an automation
   link), `planned` (has a test-idea or BDD link), or `uncovered`.
5. Write `coverage-map.md` (always) and `test-plan.md` (skip-not-overwrite).

## Safety

- Writes only under `test-plan/`. Never modifies requirements, test-ideas, or
  traceability artifacts.
- No network, no browser; fully offline and deterministic.
- `test-plan.md` is never overwritten once it exists (unless `--force`), so the
  judgment layer's per-test tables and narrative survive re-runs.

## Implementation

- Helper: `plugins/test-commander/scripts/test_plan.py` (per D18).
- Run: `python3 <plugin-root>/scripts/test_plan.py <project-root> [--force]`.

## Judgment layer

After the helper runs, fill in the per-test tables (ID / Name / Description /
Test Data / Status), the defect register, the environment, and the risks — the
parts that depend on the actual suite in the consuming project. See
[methodology/test-planning.md](../methodology/test-planning.md).

## See also

- [Test-planning methodology](../methodology/test-planning.md)
- [Test-plan template](../templates/test-plan-template.md)
- [/tc:update-test-plan](update-test-plan.md)
