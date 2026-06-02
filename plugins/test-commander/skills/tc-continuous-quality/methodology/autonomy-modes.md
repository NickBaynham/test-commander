# Autonomy modes methodology

Continuous mode never has its own execution path — it runs through the Phase-10.5
pipeline. The autonomy mode is a **ceiling**: it decides which permission levels
the continuous agent may *auto-approve*, and nothing above the mode executes
without explicit human approval.

## The five modes

| Mode | Name | Auto-approves up to | Can open PRs |
| --- | --- | --- | --- |
| 0 | read-only-advisor | nothing | no |
| 1 | assisted-testing | safe-write | no |
| 2 | approved-execution | execute-tests | no |
| 3 | pull-request-automation | code-write | yes (labeled) |
| 4 | governed-autonomy | external-network | yes (labeled) |

`destructive` and `admin` are never auto-approved at any mode.

## How the gate works

For each proposed action, the agent classifies it (via the policy engine) and
asks the autonomy gate whether the mode auto-approves that level. If yes, the
pipeline runs with an autonomy approver recorded in the audit log. If no, the
action is **held** — surfaced for a human to approve, exactly as the console
holds a privileged action. Mode 0 auto-approves nothing, so it is a pure advisor.

Opening a pull request requires both a sufficient mode (3+) and that the mode
auto-approves the PR's level; a PR opened by the agent is clearly labeled so it is
never mistaken for a human change.

Shipped in `continuous/autonomy.py` (`auto_approves`, `can_open_pr`, `mode_name`),
exercised end to end by the orchestrator (`tests/test_cq_check_gates.py`).
