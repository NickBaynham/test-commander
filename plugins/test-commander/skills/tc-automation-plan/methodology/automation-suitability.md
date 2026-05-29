# Automation suitability

How Test Commander decides which BDD scenarios are worth automating, and in what
order. `/tc:automation-plan` scores every scenario against seven mechanical,
universal factors (Decision D19), ranks it `automate` / `consider` / `manual`,
and writes a per-area plan. Two hard overrides bypass the score.

## The seven factors

Each factor is a signal read straight from a scenario's tags and steps. A
present signal contributes its weight; the total is thresholded into a rank.

| Factor | Signal | Default weight | Why it predicts automation value |
| --- | --- | --- | --- |
| `traceable` | has a `@req:`/`@cs:` linkage tag | 3 | An untraceable scenario cannot be mapped back to a requirement, so its automated result is meaningless. The strongest signal. |
| `regression-value` | has a `@smoke`/`@regression` class tag | 2 | Smoke and regression scenarios run repeatedly; automation pays back fastest there. |
| `risk-flagged` | has a `@risk:` tag | 2 | Risk-flagged behavior is where a regression hurts most; automate it first. |
| `deterministic` | NOT anomaly-derived (`@exploratory`/`@anomaly:`) | 2 | Exploratory and anomaly-derived scenarios are often non-deterministic or one-off; they automate poorly. |
| `right-sized` | step count within a healthy band (3-12) | 1 | Too few steps is trivial to automate (low value); too many is brittle. |
| `data-ready` | not a `Scenario Outline` missing its `Examples:` | 1 | A parameterized outline with no data table cannot be automated as written. |
| `persona-scoped` | has a `@persona:` tag | 1 | A concrete actor makes test setup unambiguous. |

Maximum total under the default weights is 12.

## Ranks

- **Hard override `@automated-candidate` -> `automate`.** A scenario explicitly
  marked an automation candidate (the shape `/tc:generate-bdd` emits from clean
  input) is always `automate`, regardless of score.
- **Hard override `@manual` -> `manual`.** A scenario explicitly marked manual
  always ranks `manual`, regardless of score.
- Otherwise, by total score: `>= 8` -> `automate`; `>= 5` -> `consider`;
  below -> `manual`.

## Worked examples

- **`@area:sign-in @req:REQ-001 @cs:CS-001-001 @smoke @automated-candidate`,
  4 behavior steps.** Hard override -> `automate`. (Score, were it computed:
  traceable 3 + regression 2 + deterministic 2 + right-sized 1 + data-ready 1 =
  9, also `automate`.)
- **`@area:search @req:REQ-009 @cs:CS-009-001`, 3 steps, no class/risk/persona
  tag.** traceable 3 + deterministic 2 + right-sized 1 + data-ready 1 = 7 ->
  `consider`. Boost matters: a project that raises `traceable` to 6 pushes this
  to 10 -> `automate`.
- **`@area:onboarding ... @exploratory @anomaly:layout-shift`, 2 steps.**
  traceable 3 + (deterministic 0, it is anomaly-derived) + (right-sized 0, only
  2 steps) + data-ready 1 = 4 -> `manual`. Exploratory anomaly follow-ups are
  better run by hand.

## Tuning the weights

Weights are tunable per project via `tc-automate.suitability.weights` in
`<workspace>/config.yaml`. Only the seven factor names above are recognized; an
unknown name keeps its default. See
[customizing-for-your-project.md](../../../../../docs/user-guide/customizing-for-your-project.md).

```yaml
tc-automate:
  suitability:
    weights:
      risk-flagged: 4   # a project that automates by risk first
```

## The Claude judgment layer

The score is a deterministic first pass, not the final word. After the plan is
written, Claude reads it alongside `product-knowledge/` and the scenario text to
sanity-check the ranking: a `consider` scenario covering a high-value flow may be
promoted, and an `automate` scenario that depends on an unstable third-party
surface may be held back with a note. The mechanical score makes the default
defensible and deterministic; Claude's judgment handles the cases a tag cannot
capture.

## See also

- [/tc:automation-plan](../commands/automation-plan.md) - the command spec.
- [Automation plan template](../templates/automation-plan-template.md) - the plan shape.
- [tc-automate skill](../../tc-automate/SKILL.md) - consumes the plan to generate TypeScript.
