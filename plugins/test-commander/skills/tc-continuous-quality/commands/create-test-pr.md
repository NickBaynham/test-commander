# /tc:create-test-pr

Open a clearly-labeled test pull request — gated by the autonomy mode.

## Inputs

- A gap feature (CLI: `--feature <name>`).
- `<workspace>/.test-commander/continuous/config.yaml` (autonomy mode + PR label).

## Outputs

- `<workspace>/.test-commander/continuous/pr.json` — the labeled PR bundle (title,
  label, feature, mode), when opened.

## Preconditions

- The workspace exists. Otherwise exit 2.

## Behavior

1. Load the autonomy mode and the PR label.
2. **Mode gate:** a below-threshold mode (0–2) cannot open a PR — returned held
   with a clear reason, no execution.
3. At mode 3+, run the code-write generation through the Phase-10.5 pipeline
   (auto-approved by the autonomy gate for the mode, recorded in the audit log).
   If the pipeline holds the action, the PR is not opened.
4. On success, write the labeled PR bundle.

The PR is **clearly labeled** (`pr_label`) so it is never mistaken for a human
change. Continuous mode never bypasses approvals: nothing above the configured
mode executes without explicit human approval.

## Safety

- Runs through the Phase-10.5 pipeline — permission policy, approval gate, output
  validation, audit. Mode is a ceiling; `destructive`/`admin` never auto-approve.
- Mode 0 cannot open a PR; a PR opened by the agent is labeled.

## Implementation

- Command: `plugins/test-commander/scripts/create_test_pr.py` (per D18).
- Run: `python3 <plugin-root>/scripts/create_test_pr.py <project-root> --feature <name>`.

## Definition of Done

- Gated by the autonomy mode (0–2 cannot open; 3+ opens a labeled PR through the
  pipeline with an audit entry); uninitialized refused (exit 2).
- `tc-continuous-quality/SKILL.md` describes the shipped command.

## See also

- [/tc:propose-tests](propose-tests.md)
- [Autonomy modes](../methodology/autonomy-modes.md)
- [tc-continuous-quality skill](../SKILL.md)
