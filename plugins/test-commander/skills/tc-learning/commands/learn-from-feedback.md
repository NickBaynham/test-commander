# /tc:learn-from-feedback

Derive candidate lessons from resolved human feedback — resolved open questions
and an optional uploaded feedback file — into the lessons inbox.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- `requirements/open-questions.md` entries carrying a `_Resolved:` marker, and
  an optional `documents/uploaded/feedback.md`.
- CLI: `<project-root>` (defaults to the current directory), plus `--now <ISO-8601>`.

## Outputs

- `<workspace>/learning/lessons-inbox.md` — one `tc-lesson/v1` candidate per
  resolved open question (`process`) and per uploaded feedback bullet
  (`heuristic`), with `path:line` provenance.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- **No feedback is not an error** — open questions exist throughout a project
  and may have none resolved yet, so the command is a no-op (exit 0, nothing
  appended) when there is nothing resolved.

## Behavior

1. **Resolve** the workspace.
2. **Read** `requirements/open-questions.md` for `_Resolved:` entries (→
   `process` candidates) and `documents/uploaded/feedback.md` bullets (→
   `heuristic` candidates). The template stub is treated as empty.
3. **Append** any candidates via the shared `append_lessons` engine (monotonic
   ids, `(source, origin, summary)` dedup, byte-stable inbox).

Deterministic: re-running over unchanged feedback adds nothing.

## Safety

- Reads the feedback artifacts and writes only `learning/lessons-inbox.md`. It
  captures *candidates* — nothing is reviewed, promoted, or changed in guidance.
- No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/learn_from_feedback.py` (per D18).
- Run: `python3 <plugin-root>/scripts/learn_from_feedback.py <project-root> [--now <ISO-8601>]`.
- Imports `Lesson` + `append_lessons` from `capture_lesson` (the shared engine).
- Design reference: `superpowers:receiving-code-review` (lesson intake).

## Definition of Done

- Resolved feedback becomes candidates with provenance; no feedback is a no-op
  (exit 0, not an error); dedup holds on re-run; uninitialized workspace refused
  (exit 2).
- `tc-learning/SKILL.md` describes the shipped `/tc:learn-from-feedback` behavior.

## See also

- [The learning loop methodology](../methodology/learning-loop.md) - the three stages and the shared engine.
- [Lesson taxonomy](../methodology/lesson-taxonomy.md) - the category catalog.
- [tc-learning skill](../SKILL.md)
