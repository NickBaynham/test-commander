# Workflow — The Learning Loop (Phase 8)

This guide walks you through Test Commander's six Phase 8 commands end to end:
capture (`/tc:learn` + the three `/tc:learn-from-*`) → review
(`/tc:review-lessons`) → promote (`/tc:promote-lessons --apply`). The examples
use the deliberately-generic seeded fixture from `tests/fixtures/seeded-learning/`
(a Phase-7 analysis, an exploration note, and resolved feedback), so every
output is reproducible.

## What's available in Phase 8

Phase 8 ships one skill, `tc-learning`, that turns signals from runs,
exploration, and feedback into reviewed, governed project guidance — and never
silently rewrites Test Commander itself.

| Command | Reads | Writes |
| --- | --- | --- |
| `/tc:learn` | a freeform `--note` | a `tc-lesson/v1` candidate in `learning/lessons-inbox.md` |
| `/tc:learn-from-failures` | `runs/<RUN-ID>/analysis.md` | `product-defect-pattern` / `flaky-pattern` / ... candidates |
| `/tc:learn-from-exploration` | `exploration-notes/`, `sessions/` | `anti-pattern` / `coverage-gap` candidates |
| `/tc:learn-from-feedback` | resolved `open-questions.md`, `documents/uploaded/feedback.md` | `process` / `heuristic` candidates |
| `/tc:review-lessons` | `learning/lessons-inbox.md` | sorts candidates into `accepted` / `rejected` / `needs-human-review`; clears the inbox |
| `/tc:promote-lessons` | `learning/accepted-lessons.md` | a proposal by default; `--apply` writes `learning/promoted-guidance.md` |

Per Decision D19 the lesson taxonomy and the review/promote rubrics are
universal. Phase 8 ships **no new `config.yaml` surface** — the governance gate
is a fixed `--apply` flag, not a tunable.

## The `tc-lesson/v1` schema

Every captured lesson is a Markdown block with YAML frontmatter carrying a stable
`LESSON-NNN` id, the `source` command, `path:line` `origin` provenance, a
universal `category`, a `severity`, a `status`, and a `summary` (the dedup key).
See [methodology/learning-loop.md](../../plugins/test-commander/skills/tc-learning/methodology/learning-loop.md).

## Step 1: capture

The four capture commands append candidates to one shared inbox through one
engine (monotonic ids, `(source, origin, summary)` dedup):

```console
$ python3 <plugin-root>/scripts/learn_from_failures.py . --now 2026-01-15T09:30:00
captured: 2 new failure-derived lesson(s) into learning/lessons-inbox.md

$ python3 <plugin-root>/scripts/learn_from_exploration.py . --now 2026-01-15T09:30:00
captured: 3 new exploration-derived lesson(s) into learning/lessons-inbox.md

$ python3 <plugin-root>/scripts/learn_from_feedback.py . --now 2026-01-15T09:30:00
captured: 1 new feedback-derived lesson(s) into learning/lessons-inbox.md

$ python3 <plugin-root>/scripts/capture_lesson.py . --note "Prefer role-based locators over CSS." --category heuristic --now 2026-01-15T09:30:00
captured: 1 new candidate lesson(s) into learning/lessons-inbox.md
```

## Step 2: review

`/tc:review-lessons` sorts the inbox into the three buckets — `severity: high` →
`needs-human-review`, a summary already accepted → `rejected`, otherwise →
`accepted` — and clears the inbox:

```console
$ python3 <plugin-root>/scripts/review_lessons.py .
reviewed: 7 candidate(s) - accepted 6, rejected 0, needs-human-review 1
```

## Step 3: promote (the human gate)

By default `/tc:promote-lessons` only **proposes** — it writes
`learning/promotion-proposal.md` and changes no guidance:

```console
$ python3 <plugin-root>/scripts/promote_lessons.py .
proposed: see .test-commander/learning/promotion-proposal.md (re-run with --apply to promote)
```

```markdown
# Promotion proposal

_Proposed by `/tc:promote-lessons`. Re-run with `--apply` to promote (the human-approval gate). No guidance changed yet._

| Lesson | Category | Scope | Summary |
| --- | --- | --- | --- |
| LESSON-001 | product-defect-pattern | project guidance | ... |
```

Only `--apply` — your explicit approval — moves accepted lessons into
`learning/promoted-guidance.md` (a visible `git diff`):

```console
$ python3 <plugin-root>/scripts/promote_lessons.py . --apply
promoted: 6 lesson(s) into learning/promoted-guidance.md; 0 core proposal(s)
```

A lesson flagged `core: true` renders a `learning/core-promotion-proposal.md`
entry instead — a proposal for a human to take upstream as a plugin PR. Test
Commander never edits its own shipped methodology, and never modifies
third-party skills (Open Question Q6).

## Never silently rewrites

The whole loop writes **only** under `learning/`. Capture is automatic, review is
mechanical-with-judgment, and promotion is always a deliberate, visible,
human-approved act — "learns continuously, improves deliberately."

## Customizing for your project

Phase 8 ships no new extensible `config.yaml` surface — the lesson taxonomy, the
review rubric, and the promotion gate are the universal governance contract. See
[customizing-for-your-project.md](customizing-for-your-project.md).

## Beyond Phase 8

Phase 9 generates visual quality artifacts (Mermaid diagrams and infographics)
from the workspace — see [visuals.md](visuals.md) for the walkthrough.

## See also

- [tc-learning skill](../../plugins/test-commander/skills/tc-learning/SKILL.md)
- [The learning loop methodology](../../plugins/test-commander/skills/tc-learning/methodology/learning-loop.md)
- [Improvement governance](../../plugins/test-commander/skills/tc-learning/methodology/improvement-governance.md)
- [Command reference](../command-reference.md)
- [Workspace reference](../workspace-reference.md)
- [Running tests (Phase 7)](running-tests.md) — produces the run triage `/tc:learn-from-failures` reads.
