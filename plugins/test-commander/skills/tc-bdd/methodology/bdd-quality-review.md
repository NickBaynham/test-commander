# BDD quality review

Methodology for `/tc:review-bdd` and the generate-time review sub-mode it
shares. The review runs a deterministic six-category rubric over every
`<workspace>/bdd/features/*.feature` file, writes a verdict into each feature's
summary, and routes failures to `<workspace>/requirements/open-questions.md` as
`[bdd-review]` gap signals.

`/tc:generate-bdd` auto-runs this review after generation (suppressible with
`--no-review`); `/tc:review-bdd` runs it standalone over already-written
features. Both call the same `review_features()` implementation.

## The six universal categories

Each is a mechanical check applied per scenario. A scenario contributes at most
one finding per category.

| Category | Fires when | Worked example (from `flawed.feature`) |
| --- | --- | --- |
| `ambiguous-step` | a step uses a vague word (`something`, `stuff`, `somehow`, `works`, `appropriately`, `properly`, `correctly`) | `When the user does something` / `Then it works` |
| `missing-tag` | the scenario has no `@area:` namespace tag | a scenario tagged only `@req:REQ-001 @cs:CS-001-003` |
| `untraceable` | the scenario has no `@req:`/`@cs:` linkage tag | a scenario tagged only `@area:sign-in @smoke` |
| `ui-coupled-step` | a step names clicks / selectors / URLs (`click`, `button`, `navigate`, `url`, `selector`, `xpath`, `css`) | `When the user clicks the "#submit" button` |
| `missing-examples` | a `Scenario Outline` has no `Examples:` table | `Scenario Outline: Sign-in with various emails` with no table |
| `conjunction-overload` | one step chains multiple behaviors (two or more ` and `) | `When the account signs in and creates a workspace and uploads an asset and signs out and the session expires` |

The rubric is the inverse of the Gherkin authoring discipline in
[bdd-generation.md](bdd-generation.md): a clean generated feature (concrete
behavior-not-UI steps, `@area:`/`@req:`/`@cs:` on every scenario, no bare
`Scenario Outline`, atomic steps) produces zero findings and a `pass` verdict.

## Outputs

- **Verdict** in `bdd/summaries/<area>.md`: the `- Review verdict:` line becomes
  `pass` or `N finding(s) - categories: ...`.
- **Gap signals** in `requirements/open-questions.md`, one line per finding:
  `- [tc-bdd/bdd-review-<area>] [bdd-review] <category>: scenario '<name>' <message>.`
  Deduplicated by `(source-id, question)` so re-runs never duplicate a signal
  (the Phase-2 dedup contract; the per-area source-id keeps two features'
  identical findings distinct).

## Claude judgment layer

The mechanical rubric flags shape problems; Claude calibrates them:

- Rank severity beyond the flat category (a `ui-coupled-step` in a smoke test
  matters more than in an exploratory note).
- Decide which `ambiguous-step` flags are acceptable shorthand for a known
  domain term versus genuine vagueness.
- Recommend the concrete rewrite for each finding, drawing on
  `product-knowledge/` vocabulary.

## Project extensions (D19)

Add project-specific vague or UI tokens via `<workspace>/config.yaml`:

```yaml
tc-bdd:
  review:
    rubric-extensions:
      vague-words: ["tbd", "wip"]
      ui-words: ["tap", "swipe"]
```

The extensions union with the universal cores additively.

## See also

- [review-bdd command page](../commands/review-bdd.md)
- [BDD review template](../templates/bdd-review-template.md)
- [BDD generation methodology](bdd-generation.md) - the authoring discipline this rubric enforces.
- [tc-bdd skill](../SKILL.md)
- [Phased plan](../../../../../planning/plan.md)
