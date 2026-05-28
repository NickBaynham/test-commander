# Seeded-exploration-session fixture

A deliberately-generic recorded Playwright MCP exploration session that drives the Phase 4 `tc-explore` commands in tests. Every Phase 4 sub-step's test suite (4.2-4.5 + the 4.7 integration smoke) consumes this fixture so the rubric is the contract — adding a new universal anomaly category means adding a seeded entry here.

This fixture is a **test asset, not part of the shipped plugin**. The session narrative is intentionally domain-neutral — the same generic SaaS-dashboard narrative ([target-app.md](target-app.md)) the Phase 3 sample-project fixture uses (Account / Session / Workspace / Asset / Permission). Per D19, no e-commerce, healthcare, finance, or research vocabulary appears anywhere. Domain-specific exploration scenarios are exercised by consuming projects via their own recorded sessions and `tc-explore:` config extensions, not through this fixture.

## Files

- [`charter.md`](charter.md) — a `CH-001` worked example with mission, target area, time-box, risk areas, and acceptance criteria. Used as the `--charter` input for `/tc:explore` in 4.3's tests and as the charter argument in the 4.7 integration smoke.
- [`target-app.md`](target-app.md) — describes the seeded target (a generic SaaS dashboard, mirroring the Phase 3 sample-project narrative).
- [`recorded-session.json`](recorded-session.json) — a JSON list of 50-80 timestamped events (`page_load`, `click`, `fill`, `screenshot`, `console_message`, `network_request`, `anomaly`) representing what Playwright MCP would have produced during a real exploration of the target. The `/tc:explore` helper's `recorded` mode reads this file directly; pytest never enters `live` mode (refused via the `PYTEST_CURRENT_TEST` env-var check from Phase 3 Step 3.5).

## Marker convention

Every seeded anomaly is marked with the universal `knowledge: <category>` token in the file's native comment syntax:

- Markdown: `<!-- knowledge: <category> -->`
- JSON (no native comments): an `"_knowledge": "knowledge: <category>"` value string on the affected entry. The literal `knowledge: <category>` phrase travels with the value so one regex matches uniformly across HTML, YAML, Python, TypeScript, and JSON (the Phase 3 Step 3.1 marker-uniformity lesson made operational here).

The scaffold test (`tests/test_tc_explore_scaffold.py`) walks every file under this directory and matches the regex `knowledge:\s*([a-z][a-z0-9-]*)` to verify category coverage.

## Universal anomaly categories

`slow-response`, `console-error`, `broken-link`, `missing-evidence`, `auth-mismatch`, `unexpected-state`.

Each category has at least one seeded anomaly entry in `recorded-session.json` carrying:

```json
{
  "timestamp": "2026-05-28T10:15:42.123Z",
  "event_type": "anomaly",
  "anomaly": {
    "category": "slow-response",
    "severity": "medium",
    "page_url": "/workspaces",
    "reproduction": "Loaded /workspaces; first response took 3.8s (acceptable threshold 1s).",
    "screenshot_id": "S-007"
  },
  "_knowledge": "knowledge: slow-response"
}
```

The `_knowledge` value string carries the literal marker phrase so the scaffold test regex finds it; the `anomaly.category` field is the structured value the 4.3 helper consumes.

## Charter shape

The seeded `charter.md` has a YAML frontmatter block plus a structured body. Required frontmatter fields (asserted by the scaffold test):

- `id` — stable `CH-NNN` identifier; seeded as `CH-001`.
- `mission` — one-sentence statement of what the charter intends to discover.
- `target` — what part of the application the charter covers.
- `time-box` — duration in human-readable form (e.g. `60min`).
- `risk-areas` — list of risk dimensions the exploration prioritizes.
- `acceptance-criteria` — list of testable predicates that confirm charter completion.

The charter explicitly disclaims scope ("test asset, not a claim about scope") per the D19 fixture-discipline lesson from Phase 2 Step 2.1.

## Adding a new seed

1. Pick a new anomaly category key (kebab-case, lowercase). Update the `ANOMALY_CATEGORIES` list in `tests/test_tc_explore_scaffold.py` and the universal-core list in the Phase 4 partition table (`planning/plan.md` Step 4.3 deliverables).
2. Add at least one `event_type: anomaly` entry in `recorded-session.json` carrying the new category in its `anomaly.category` field, with `"_knowledge": "knowledge: <category>"` for the scaffold-test regex to find.
3. Update the universal-core list in `methodology/exploratory-testing.md` (the umbrella) and in `methodology/session-based-test-management.md` (Step 4.3 owns the anomaly methodology).
4. Add a per-command test case in `tests/test_explore.py` that asserts `/tc:explore` surfaces the new category in the exploration note's anomaly summary.

## Domain-specific seeds

Domain vocabulary (PCI: PAN; HIPAA: PHI; commerce: refund, gift card; research: investigator) does **not** belong in this fixture. Domain-specific exploration is exercised by consuming projects via their own recorded sessions and `tc-explore:` extensions in `<workspace>/config.yaml`; it is not part of Test Commander's universal contract (per Decision D19).
