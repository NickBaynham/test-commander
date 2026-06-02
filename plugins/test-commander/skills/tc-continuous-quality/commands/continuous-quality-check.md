# /tc:continuous-quality-check

Run the full continuous-quality loop under the configured autonomy mode.

## Inputs

- A PR/push diff (CLI: `--diff <path>`).
- `<workspace>/.test-commander/continuous/config.yaml` (autonomy mode + PR label),
  the impact map, and the coverage map.

## Outputs

- The analysis artifacts (`changes.json`, `impact-analysis.md`,
  `coverage-gap-analysis.md`, `proposals/`), and — at mode 3+ — a labeled PR
  bundle per gap (`pr.json`).

## Preconditions

- The workspace exists. Otherwise exit 2.

## Behavior

1. **Read-only analysis (always runs):** watch → impact → coverage-gap → propose.
2. **Gated execution:** for each gap, open a clearly-labeled PR — *only when the
   configured autonomy mode allows it*. Modes 0–2 produce advice only (no PR);
   modes 3–4 open labeled PRs through the Phase-10.5 pipeline (auto-approved by
   the autonomy gate, audited).

The mode is a ceiling: nothing above it executes without explicit human approval.
`destructive`/`admin` never auto-approve at any mode.

## Safety

- The read-only analysis never changes the application. Any generated change
  arrives only as a gated, labeled PR — never a direct push.
- Every gated execution goes through the Phase-10.5 pipeline (policy, approval,
  validation, audit).

## Implementation

- Command: `plugins/test-commander/scripts/continuous_quality_check.py` (per D18).
- Run: `python3 <plugin-root>/scripts/continuous_quality_check.py <project-root> --diff <path>`.

## Definition of Done

- Runs the read-only analysis, opens PRs only at the allowed mode (mode 0 opens
  none, no audit entry; mode 3+ opens a labeled PR with an audit entry);
  uninitialized refused (exit 2).
- `tc-continuous-quality/SKILL.md` describes the shipped command.

## See also

- [/tc:propose-tests](propose-tests.md)
- [/tc:create-test-pr](create-test-pr.md)
- [Autonomy modes](../methodology/autonomy-modes.md)
- [tc-continuous-quality skill](../SKILL.md)
