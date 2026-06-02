# /tc:learn-from-exploration

Derive candidate lessons from the Phase-4 exploration record. Turns recorded
anomalies into `anti-pattern` candidates and coverage gaps into `coverage-gap`
candidates in the lessons inbox.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- One or more `exploration-notes/*.md` (and `sessions/*.md`) from `/tc:explore`.
- CLI: `<project-root>` (defaults to the current directory), plus `--now <ISO-8601>`.

## Outputs

- `<workspace>/learning/lessons-inbox.md` — one `tc-lesson/v1` candidate per
  recorded anomaly (`anti-pattern`) and per coverage gap (`coverage-gap`), with
  `exploration-notes/<file>:<line>` provenance.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- At least one exploration note exists. Otherwise exit 2 (the error directs the
  user at `/tc:explore`).

## Behavior

1. **Resolve** the workspace and the exploration notes.
2. **Parse** each note's `## Anomalies` table (each row → an `anti-pattern`
   candidate, carrying the recorded severity) and `## Coverage gaps` bullets
   (each → a `coverage-gap` candidate).
3. **Append** the candidates via the shared `append_lessons` engine (monotonic
   ids, `(source, origin, summary)` dedup, byte-stable inbox).

Deterministic: re-running over unchanged notes adds nothing.

## Safety

- Reads the exploration notes and writes only `learning/lessons-inbox.md`. It
  captures *candidates* — nothing is reviewed, promoted, or changed in guidance.
- No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/learn_from_exploration.py` (per D18).
- Run: `python3 <plugin-root>/scripts/learn_from_exploration.py <project-root> [--now <ISO-8601>]`.
- Imports `Lesson` + `append_lessons` from `capture_lesson` (the shared engine).

## Definition of Done

- Anomalies and coverage gaps become candidates with provenance; dedup holds on
  re-run; uninitialized workspace refused (exit 2); no exploration notes refused
  (exit 2) pointing at `/tc:explore`.
- `tc-learning/SKILL.md` describes the shipped `/tc:learn-from-exploration` behavior.

## See also

- [The learning loop methodology](../methodology/learning-loop.md) - the three stages and the shared engine.
- [Lesson taxonomy](../methodology/lesson-taxonomy.md) - the category catalog.
- [tc-learning skill](../SKILL.md)
- [/tc:explore](../../tc-explore/commands/explore.md) - the exploration this command reads.
