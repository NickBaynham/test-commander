# /tc:review-lessons

Classify the candidate lessons in the inbox into `accepted`, `rejected`, or
`needs-human-review`, move each to the matching `learning/` file with its
`status` updated, and clear the inbox.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- `learning/lessons-inbox.md` with `tc-lesson/v1` candidates (from the capture
  commands), and the existing `learning/accepted-lessons.md` corpus.
- CLI: `<project-root>` (defaults to the current directory). No other flags.

## Outputs

- `learning/accepted-lessons.md`, `learning/rejected-lessons.md`,
  `learning/needs-human-review.md` — each reviewed candidate appended with its
  `status` updated.
- `learning/lessons-inbox.md` — cleared of the reviewed candidates.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- The inbox carries candidates (it is not still the template stub). Otherwise
  exit 2 (the error directs the user at `/tc:learn`). An already-cleared inbox
  (reviewed, not the stub) is a no-op (exit 0).

## Behavior

1. **Resolve** the workspace and parse the inbox candidates.
2. **Classify** each, most-specific rule first: `severity: high` →
   `needs-human-review`; a `summary` already in `accepted-lessons.md` →
   `rejected` (a duplicate); otherwise → `accepted`.
3. **Move** each candidate to the matching `learning/` file with its `status`
   updated, and **clear** the inbox.

Idempotent: a re-run over an already-cleared inbox changes nothing.

## Safety

- Writes only under `learning/`. It moves *candidates* into review buckets — it
  promotes nothing into guidance and changes no methodology (that is
  `/tc:promote-lessons --apply`, under the human gate).
- No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/review_lessons.py` (per D18).
- Run: `python3 <plugin-root>/scripts/review_lessons.py <project-root>`.
- Exposes `review_lessons(project_root)` returning a `ReviewOutcome` (per-bucket
  counts). Reuses the `capture_lesson` stub/workspace helpers.

## Definition of Done

- Candidates classified into the three buckets with `status` updated; the inbox
  cleared; idempotent re-run; uninitialized workspace refused (exit 2); a stub
  inbox refused (exit 2) pointing at `/tc:learn`.
- `tc-learning/SKILL.md` describes the shipped `/tc:review-lessons` behavior.

## See also

- [Improvement governance](../methodology/improvement-governance.md) - the four-bucket lifecycle, the rubric, the promotion gate.
- [Improvement proposal template](../templates/improvement-proposal-template.md) - what `/tc:promote-lessons` writes from accepted lessons.
- [tc-learning skill](../SKILL.md)
- [/tc:learn](learn.md) - captures the candidates this command reviews.
