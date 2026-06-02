# Improvement governance

The governed lifecycle a lesson moves through — and the gate that ensures Test
Commander never silently rewrites itself.

## The four-bucket lifecycle

```
lessons-inbox.md
      |  /tc:review-lessons
      v
accepted-lessons.md | rejected-lessons.md | needs-human-review.md
      |  /tc:promote-lessons --apply
      v
promoted-guidance.md
```

A lesson is `candidate` in the inbox, becomes `accepted` / `rejected` /
`needs-human-review` after review, and `promoted` only after an explicit,
human-approved promotion.

## The review rubric

`/tc:review-lessons` classifies every inbox candidate, most-specific rule first:

| Bucket | Mechanical signal | Why |
| --- | --- | --- |
| `needs-human-review` | `severity: high` | a high-impact lesson's scope (one-off vs. systemic) needs a human's judgment before it shapes guidance. |
| `rejected` | the `summary` already appears in `accepted-lessons.md` | a duplicate that adds nothing to what is already accepted. |
| `accepted` | none of the above | provenanced, not high-severity, novel — safe to carry forward. |

Worked examples (from the seeded fixture):

- A `medium`-severity `product-defect-pattern` with `runs/.../analysis.md:8`
  provenance and a novel summary → **accepted**.
- A `low`-severity note whose summary duplicates an already-accepted lesson →
  **rejected**.
- A `high`-severity `anti-pattern` about a possible access-control gap →
  **needs-human-review** (the scope is ambiguous; a human decides).

The rubric is deliberately conservative: it only auto-accepts what is clearly
safe and routes anything high-impact or ambiguous to a human. Claude adds the
judgment the mechanics cannot — recognizing that three candidates are one
lesson, or that a "duplicate" actually sharpens an accepted one.

## The promotion gate (Q6)

`/tc:promote-lessons` is the only command that turns an accepted lesson into
project guidance, and it does so under a hard gate:

- **By default it proposes** — it writes `promotion-proposal.md` (what *would*
  be promoted) and changes no guidance.
- **Only `--apply`** (the human's approval) moves accepted lessons into
  `learning/promoted-guidance.md`. Every applied promotion is a visible
  `git diff`.
- It writes **only** under the workspace `learning/` tree. It never edits Test
  Commander's shipped methodology, commands, or templates, and never modifies
  third-party installed skills (Open Question Q6).
- A lesson that argues for a change to Test Commander's own shipped doctrine
  renders an `improvement-proposal` artifact — a proposal for a human to take
  upstream as a plugin PR — never an automatic edit.

This is what "learns continuously, improves deliberately" means in code: capture
is automatic, review is mechanical-with-judgment, and promotion is always a
deliberate, visible, human-approved act.
