# Test-planning methodology

How Test Commander generates a test plan and keeps it current — the division of
labor between the deterministic helper and the Claude judgment layer.

## Why a test plan is two artifacts

A test plan answers two different questions that change at different rates:

- **What must we verify, and how?** — scope, approach, environment, the
  requirement list, risks. This is narrative and human-owned. It changes slowly.
- **What is covered right now?** — which requirements have test ideas, BDD,
  automation. This is mechanical and changes on every requirements or test edit.

So the skill splits them:

- `test-plan.md` — the narrative document. Seeded once from the template, then
  **never overwritten** by the helper. Per-test tables, defects, and risks live
  here and survive re-runs.
- `coverage-map.md` — the mechanical map. **Regenerated every run** from the
  inventory and traceability. This is the part that "keeps up to date."

This mirrors the rest of Test Commander: a deterministic first pass plus a Claude
judgment layer.

## Mechanical layer (the helper)

`test_plan.py` reads `requirements/requirements-inventory.md` and
`traceability/requirements-map.md` and derives, per requirement, a coverage
status:

- `automated` — the traceability map links an automation artifact.
- `planned` — there is a test-idea or BDD link but no automation yet.
- `uncovered` — no downstream artifact references the requirement.

It writes the coverage map and, on first run, the plan scaffold. Everything it
writes is byte-deterministic so re-runs and diffs are clean.

## Judgment layer (Claude)

The helper cannot know the consuming project's real test files — they live
outside the workspace (e.g. a Playwright or PyTest suite in another repo). After
the helper runs, Claude maintains the parts of `test-plan.md` that require
judgment:

- **Per-test tables** (sections 8.x): ID, Name, Description, Test Data, Status —
  one row per real automated test, cross-referenced to the requirement it covers.
- **Defect register** (section 9): confirmed defects and their regression tests.
- **Environment, scope, risks** (sections 3, 6, 10): including shared-state and
  data-isolation constraints discovered while building the suite.
- **Status accuracy**: the per-test `Status` column is a point-in-time snapshot.
  Re-run the suite and refresh it; a fixed defect flips a regression row from
  `Fail (by design)` to `Pass`.

A useful discipline: the mechanical `coverage-map.md` status is a *signal*, not
the truth. A requirement can show `planned` (a seed exists) while a real
automated test already covers it — reconcile the two when you update the plan,
and prefer the evidence of an actual passing test over a seed link.

## Keeping it current

1. When requirements change → `/tc:review-requirements`, then `/tc:update-test-plan`.
2. When test ideas / BDD / automation change → `/tc:update-test-plan` to refresh
   the coverage map.
3. After a test run → update the per-test `Status` columns in `test-plan.md`.

The plan is a living document: the helper keeps the coverage map honest; the
judgment layer keeps the narrative and the per-test status honest.
