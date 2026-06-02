# /tc:learn-from-failures

Derive candidate lessons from the Phase-7 test-run triage. Reads the
`/tc:analyze-results` output and turns recurring failure classifications into
`tc-lesson/v1` candidates in the lessons inbox.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- One or more `runs/<RUN-ID>/analysis.md` triage files (from `/tc:analyze-results`).
- CLI: `<project-root>` (defaults to the current directory), plus:
  - `--run-id <RUN-ID>` — a single run (default: every run's analysis).
  - `--now <ISO-8601>` — injected clock for a deterministic `captured_at`.

## Outputs

- `<workspace>/learning/lessons-inbox.md` — one `tc-lesson/v1` candidate per
  triaged non-passed row, with `runs/<RUN-ID>/analysis.md:<line>` provenance.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- At least one `runs/<RUN-ID>/analysis.md` exists. Otherwise exit 2 (the error
  directs the user at `/tc:analyze-results`).

## Behavior

1. **Resolve** the workspace and the analysis files (the named `--run-id`, or all).
2. **Map** each triaged row's classification to a lesson category:
   `product-defect` → `product-defect-pattern`, `flaky` → `flaky-pattern`,
   `test-defect` → `anti-pattern`, `environment` → `process`.
3. **Append** the candidates via the shared `append_lessons` engine — monotonic
   ids, `(source, origin, summary)` dedup, byte-stable inbox.

Deterministic: re-running over unchanged analysis adds nothing.

## Safety

- Reads the analysis triage and writes only `learning/lessons-inbox.md`. It
  captures *candidates* — nothing is reviewed, promoted, or changed in guidance.
- No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/learn_from_failures.py` (per D18).
- Run: `python3 <plugin-root>/scripts/learn_from_failures.py <project-root> [--run-id <RUN-ID>] [--now <ISO-8601>]`.
- Imports `Lesson` + `append_lessons` from `capture_lesson` (the shared engine).
- Design reference: `superpowers:systematic-debugging` (root-cause learning).

## Definition of Done

- Triaged `product-defect` and `flaky` rows become candidates with provenance;
  dedup holds on re-run; uninitialized workspace refused (exit 2); no analysis
  refused (exit 2) pointing at `/tc:analyze-results`.
- `tc-learning/SKILL.md` describes the shipped `/tc:learn-from-failures` behavior.

## See also

- [The learning loop methodology](../methodology/learning-loop.md) - the three stages and the shared engine.
- [Lesson taxonomy](../methodology/lesson-taxonomy.md) - the category catalog.
- [tc-learning skill](../SKILL.md)
- [/tc:analyze-results](../../tc-run/commands/analyze-results.md) - the triage this command reads.
