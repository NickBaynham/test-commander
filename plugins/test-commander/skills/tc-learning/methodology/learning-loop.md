# The learning loop methodology

How Test Commander "learns continuously, improves deliberately" — the governed
loop that turns signals from runs, exploration, and feedback into reviewed
project guidance, without ever silently rewriting itself.

## The three stages

```
capture  ->  review  ->  promote
```

1. **Capture** — `/tc:learn` and the three `/tc:learn-from-*` commands append
   candidate lessons to `learning/lessons-inbox.md`. Each candidate is a
   `tc-lesson/v1` record with `path:line` provenance and a stable `LESSON-NNN`
   id.
2. **Review** — `/tc:review-lessons` classifies every candidate into `accepted`,
   `rejected`, or `needs-human-review` and moves it to the matching `learning/`
   file, clearing the inbox.
3. **Promote** — `/tc:promote-lessons` proposes promotions by default and, only
   with `--apply` (the human-approval gate), moves accepted lessons into
   `learning/promoted-guidance.md`.

## The `tc-lesson/v1` schema

Every captured lesson is a Markdown block opened by YAML frontmatter:

| Field | Meaning |
| --- | --- |
| `schema` | always `tc-lesson/v1`. |
| `id` | a stable `LESSON-NNN` identifier; the engine allocates the next number by scanning the inbox (monotonic). |
| `source` | the command that captured it (`/tc:learn`, `/tc:learn-from-failures`, ...). |
| `origin` | `path:line` provenance pointing at the committed artifact it came from. |
| `category` | one of the universal taxonomy (see `lesson-taxonomy.md`). |
| `severity` | `low` / `medium` / `high`. |
| `status` | `candidate` → `accepted` / `rejected` / `needs-human-review` → `promoted`. |
| `captured_at` | an ISO timestamp from the injected clock. |
| `summary` | a one-line summary; the third element of the `(source, origin, summary)` dedup key. |

## The shared capture engine

`capture_lesson.append_lessons(workspace, lessons, now)` is the one engine all
four capture commands use. It allocates monotonic ids, deduplicates by
`(source, origin, summary)` (so re-running a capture never spams the inbox), and
appends new blocks — leaving the inbox byte-identical when there is nothing new.
The `/tc:learn-from-*` commands build `Lesson` objects from their respective
artifacts and call the same engine, so every candidate, whatever its source,
carries the same schema and the same provenance discipline.

## Never silently rewrites (Q6)

The loop writes **only** into the workspace `learning/` tree. It never edits
Test Commander's shipped methodology, commands, or templates, and never modifies
third-party installed skills. `/tc:promote-lessons` is the only command that
changes guidance, and only under the explicit `--apply` human gate — every
applied promotion is a visible `git diff`. A lesson that argues for a change to
Test Commander's own shipped doctrine renders an `improvement-proposal` artifact
(a proposal for a human to take upstream as a plugin PR), never an automatic
edit.

## The Claude judgment layer

The capture commands are mechanical: they extract candidates with provenance and
append them. Claude adds the judgment the mechanics cannot:

- writing a sharp, actionable lesson body from a terse signal;
- recognizing that three flaky-test candidates are one determinism problem;
- deciding which lessons are worth a human's review time;
- framing a promoted lesson as guidance the team will actually follow.
