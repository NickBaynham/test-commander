# /tc:automation-plan

Score every reviewed BDD scenario against the universal seven-factor suitability
rubric and write a per-area plan ranking each scenario `automate` / `consider` /
`manual` with its per-factor scores and a recommended order. The strategic gate
before any TypeScript is generated.

## Inputs

- `<workspace>/bdd/features/*.feature` - the reviewed Gherkin features. Each
  scenario's tags (`@req:`/`@cs:`, `@smoke`/`@regression`, `@risk:`,
  `@exploratory`/`@anomaly:`, `@persona:`, `@automated-candidate`, `@manual`)
  and step count are the scoring signals.
- `<workspace>/config.yaml` - optional `tc-automate.suitability.weights` to tune
  the per-factor weights.
- `<workspace>/product-knowledge/` - read by Claude for the judgment layer
  (promoting or holding back a scenario the score alone cannot judge).

## Outputs

- `<workspace>/automation-plan/<area>.md` - one plan per feature: the ranking
  table (per-factor scores) and the recommended order. The `automation-plan/`
  README placeholder is preserved.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- No feature files is **not** an error: the run reports "no scenarios to plan"
  (exit 0), directing the user at `/tc:generate-bdd`.

## Behavior

1. **Resolve** the workspace and load the per-factor weights (defaults merged
   with `tc-automate.suitability.weights`).
2. **Scan** every `bdd/features/*.feature` and parse each scenario (reusing the
   `/tc:review-bdd` feature parser).
3. **Score** each scenario across the seven factors (`traceable`,
   `regression-value`, `risk-flagged`, `deterministic`, `right-sized`,
   `data-ready`, `persona-scoped`); sum the present-signal weights.
4. **Rank** by score (`>= 8` automate, `>= 5` consider, else manual), with two
   hard overrides: `@automated-candidate` always `automate`; `@manual` always
   `manual`.
5. **Write** `automation-plan/<area>.md` with the ranking table and the
   recommended order (automate-then-consider, score descending then name).

Output is deterministic: scenarios sort by name in the table and by
`(rank, -score, name)` in the order; overwrite mode; byte-identical re-run.

The score is a deterministic first pass; Claude then reviews the plan against
`product-knowledge/` and may promote or hold back individual scenarios with a
note (the judgment layer, per the methodology).

## Safety

- Reads `bdd/features/`; writes only `automation-plan/<area>.md`. Never writes
  `bdd/` (Phase 5) or `product-knowledge/` (Phase 3).
- No network, no browser, fully offline and deterministic.

## Implementation

- Helper: `plugins/test-commander/scripts/automation_plan.py` (per D18).
- Run: `python3 <plugin-root>/scripts/automation_plan.py <project-root>`.
- Mirrors `review_bdd.py`; reuses its `parse_feature_file`. Unique work is the
  seven-factor rubric, the rank thresholds, and the plan renderer.

## Definition of Done

- A plan is written per feature with every scenario scored across all seven
  factors and a recommended order.
- `@automated-candidate` always ranks `automate`; `@manual` always `manual`.
- Deterministic (byte-identical re-run); config-tunable via
  `tc-automate.suitability.weights`.
- `tc-automation-plan/SKILL.md` describes the shipped behavior.

## See also

- [Automation suitability methodology](../methodology/automation-suitability.md) - the seven factors, ranks, worked examples, and the Claude judgment layer.
- [Automation plan template](../templates/automation-plan-template.md) - the plan shape.
- [Customizing for your project](../../../../../docs/user-guide/customizing-for-your-project.md) - `tc-automate.suitability.weights`.
- [tc-automation-plan skill](../SKILL.md)
- [tc-automate skill](../../tc-automate/SKILL.md) - consumes the plan.
