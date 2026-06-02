# /tc:promote-lessons

Turn accepted lessons into project guidance — under a human-approval gate. By
default it proposes; only `--apply` changes guidance. It writes only under
`learning/` and never rewrites Test Commander's shipped methodology (Q6).

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- `learning/accepted-lessons.md` (from `/tc:review-lessons`).
- CLI: `<project-root>` (defaults to the current directory), plus:
  - `--apply` — the human-approval gate. Without it, the command only proposes.

## Outputs

- Default: `learning/promotion-proposal.md` — what *would* be promoted. No
  guidance changed.
- `--apply`:
  - `learning/promoted-guidance.md` — each accepted non-core lesson, appended
    with `status: promoted`.
  - `learning/core-promotion-proposal.md` — each `core: true` lesson, as an
    upstream proposal (never applied to shipped files).
  - `learning/accepted-lessons.md` — promoted lessons marked `status: promoted`
    (so a re-apply skips them).

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- `accepted-lessons.md` carries accepted lessons (not still the template stub).
  Otherwise exit 2 (the error directs the user at `/tc:review-lessons`). An
  all-promoted accepted file is a no-op (exit 0).

## Behavior

1. **Resolve** the workspace and the accepted (not-yet-promoted) lessons.
2. **Default (propose):** write `promotion-proposal.md` listing the candidates
   and their scope (project guidance vs. core/upstream). Change no guidance.
3. **`--apply`:** append each non-core lesson to `promoted-guidance.md`
   (`status: promoted`), each `core: true` lesson to `core-promotion-proposal.md`,
   and mark the promoted lessons in `accepted-lessons.md`.

Idempotent: an already-promoted lesson is skipped on re-apply.

## Safety

- **Writes only under `learning/`.** It never edits Test Commander's shipped
  methodology, commands, or templates, and never modifies third-party installed
  skills (Q6). Every applied promotion is a visible `git diff`.
- The `--apply` gate is the human's approval; the default is non-destructive.
- No network, no browser.

## Implementation

- Helper: `plugins/test-commander/scripts/promote_lessons.py` (per D18).
- Run: `python3 <plugin-root>/scripts/promote_lessons.py <project-root> [--apply]`.
- Exposes `promote(project_root, *, apply=False)` returning a `PromoteOutcome`.

## Definition of Done

- Default proposes without changing guidance; `--apply` promotes into
  `promoted-guidance.md` (`status: promoted`); a `core: true` lesson renders a
  core-promotion proposal; promotion writes only under `learning/`; idempotent
  re-apply; uninitialized workspace refused (exit 2); no accepted lessons
  refused (exit 2) pointing at `/tc:review-lessons`.
- `tc-learning/SKILL.md` describes the shipped `/tc:promote-lessons` behavior.

## See also

- [Improvement governance](../methodology/improvement-governance.md) - the lifecycle and the promotion gate.
- [Commander doctrine](../methodology/commander-doctrine.md), [Anti-patterns](../methodology/anti-patterns.md), [Heuristics](../methodology/heuristics.md) - the shipped doctrine promoted guidance extends.
- [Core promotion template](../templates/core-promotion-template.md) - the upstream-proposal shape.
- [tc-learning skill](../SKILL.md)
- [/tc:review-lessons](review-lessons.md) - produces the accepted lessons this command promotes.
