# Autonomy levels

Continuous quality mode never has its own execution path — it runs through the
Phase-10.5 pipeline. The **autonomy mode** is a *ceiling*: it decides which
permission levels the continuous agent may auto-approve. Nothing above the
configured mode executes without explicit human approval.

## The five modes

| Mode | Name | Auto-approves (cumulative) | Can open PRs |
| --- | --- | --- | --- |
| 0 | read-only-advisor | nothing | no |
| 1 | assisted-testing | `safe-write` | no |
| 2 | approved-execution | `safe-write`, `execute-tests` | no |
| 3 | pull-request-automation | `safe-write`, `execute-tests`, `code-write` | yes (labeled) |
| 4 | governed-autonomy | `safe-write`, `execute-tests`, `code-write`, `external-network` | yes (labeled) |

`read-only` is always allowed; **`destructive` and `admin` are never
auto-approved at any mode**. The sets are cumulative along the autonomy
progression (advisor → safe-write → execute-tests → code-write →
external-network), which is *not* the policy level ordering — the modes are
explicit sets, not a ceiling on a linear order.

## How the gate works

For each action the continuous agent proposes, the policy engine classifies its
permission level and the autonomy gate (`auto_approves(mode, level)`) decides
whether the mode auto-approves it:

- **Auto-approved** → the Phase-10.5 pipeline runs the action with an autonomy
  approver recorded in the audit log.
- **Not auto-approved** → the action is *held* for a human to approve, exactly as
  the console holds a privileged action.

Opening a pull request additionally requires `can_open_pr(mode)` (mode 3+), and a
PR opened by the agent is clearly labeled (`pr_label`) so it is never mistaken
for a human change. Mode 0 auto-approves nothing and cannot open PRs — a pure
advisor.

## Configuring the mode

Set `autonomy_mode` in `<workspace>/.test-commander/continuous/config.yaml` — see
[customizing-for-your-project.md](user-guide/customizing-for-your-project.md).
The mode starts at 0 (advisor) and a team raises it deliberately.

## See also

- [Continuous quality agent](continuous-quality-agent.md)
- [Governed self-improvement](governed-self-improvement.md)
- [Security and permissions](security-and-permissions.md)
