# Lesson taxonomy

The universal `category` values a `tc-lesson/v1` record can carry. Per Decision
D19 the taxonomy is universal English / software-engineering vocabulary; a
project does not add domain categories — domain specifics live in the lesson
`body` and `origin`, not in new category names.

| Category | What it captures | Typical source |
| --- | --- | --- |
| `product-defect-pattern` | a recurring way the product misbehaves | `/tc:learn-from-failures` (a `product-defect` triage) |
| `flaky-pattern` | a recurring source of test non-determinism | `/tc:learn-from-failures` (a `flaky` triage) |
| `coverage-gap` | a behavior or flow no scenario exercises | `/tc:learn-from-exploration` (an unreached flow) |
| `process` | a workflow / methodology improvement | `/tc:learn`, `/tc:learn-from-feedback` |
| `heuristic` | a rule of thumb worth following next time | `/tc:learn`, `/tc:learn-from-feedback` |
| `anti-pattern` | a recurring mistake to avoid | `/tc:learn-from-exploration`, `/tc:learn` |

## Choosing a category

- A capture command picks the category mechanically from its source (e.g.
  `learn-from-failures` maps a `product-defect` triage to `product-defect-pattern`).
- `/tc:learn` defaults to `process` for a freeform note unless `--category` is
  given; an unknown value falls back to `process` (never corrupts the record).
- The category drives nothing automatic — it is a human-readable grouping the
  review and promote stages use to organize the guidance corpus.

## Severity

`severity` is `low` / `medium` / `high`. It is advisory for the review stage:
a `high`-severity candidate with an ambiguous scope is a natural
`needs-human-review` (a human decides whether it is a one-off or a systemic
issue), while a `low`-severity well-provenanced candidate in a known category is
a natural `accepted`. The mechanical rubric in `improvement-governance.md` keys
on these signals; Claude adds the judgment.
