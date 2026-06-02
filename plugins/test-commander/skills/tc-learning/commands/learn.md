# /tc:learn

Append a candidate lesson to the lessons inbox from a freeform observation — the
foundational capture command of the learning loop, and the home of the
`tc-lesson/v1` schema and the shared inbox engine every `/tc:learn-from-*`
command reuses.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- CLI: `<project-root>` (defaults to the current directory), plus:
  - `--note "<observation>"` (required) — the lesson.
  - `--origin <path:line>` — provenance (default `manual`).
  - `--category <name>` — one of the universal taxonomy (default `process`).
  - `--severity <low|medium|high>` — default `medium`.
  - `--summary "<line>"` — the dedup-key summary (default: the note's first line).
  - `--now <ISO-8601>` — injected clock for a deterministic `captured_at`.

## Outputs

- `<workspace>/learning/lessons-inbox.md` — the appended `tc-lesson/v1` block
  (`status: candidate`), with a monotonic `LESSON-NNN` id and `path:line`
  provenance.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.

## Behavior

1. **Resolve** the workspace.
2. **Build** a `Lesson` from the note (source `/tc:learn`).
3. **Append** via the shared `append_lessons` engine: allocate the next
   `LESSON-NNN` id (scanning the inbox), deduplicate by
   `(source, origin, summary)`, and append the block. A duplicate is not
   re-appended; the inbox stub is replaced with a real header on first capture.

Deterministic: the same note plus the same injected clock leave the inbox
byte-identical (a duplicate adds nothing).

## Safety

- Writes only `learning/lessons-inbox.md`. It captures *candidates* — nothing is
  reviewed or promoted here, and no guidance or methodology is changed.
- No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/capture_lesson.py` (per D18).
- Run: `python3 <plugin-root>/scripts/capture_lesson.py <project-root> --note "..." [--origin ...] [--category ...] [--severity ...] [--now ...]`.
- Exposes `Lesson`, `parse_inbox`, and `append_lessons(workspace, lessons, now)`
  — the shared engine the `/tc:learn-from-*` commands import.

## Definition of Done

- A note appends one valid `tc-lesson/v1` candidate with provenance; the id
  allocator is monotonic; the injected clock makes the inbox byte-stable; a
  duplicate is not re-appended; uninitialized workspace refused (exit 2).
- `tc-learning/SKILL.md` describes the shipped `/tc:learn` behavior.

## See also

- [The learning loop methodology](../methodology/learning-loop.md) - the three stages, the schema, the never-silently-rewrite principle.
- [Lesson taxonomy](../methodology/lesson-taxonomy.md) - the universal category catalog.
- [Lesson template](../templates/lesson-template.md) - the `tc-lesson/v1` block shape.
- [tc-learning skill](../SKILL.md)
