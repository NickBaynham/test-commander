# Runtime Approval Flow

How an action moves from "proposed" to "executed" or "denied," and what gets recorded along the way.

## State machine

```
proposed
  -> awaiting-approval        (if required by policy)
  -> approved
  -> running
  -> validating               (output validation runs the diff)
  -> done
```

Side branches:

- `denied` from `awaiting-approval`.
- `violated_policy` from `validating` (e.g. an out-of-scope file write).
- `failed` from `running` (agent returned an error before validation).
- `bypassed` is never a state. There is no bypass.

## Roles in the flow

| Role | Can propose | Can approve | Approval scope |
| --- | --- | --- | --- |
| Viewer | `read-only` only | n/a | n/a |
| Tester | up to `safe-write`, propose `execute-tests` | n/a | n/a |
| Automation Engineer | up to `code-write` (with approval) | n/a | n/a |
| Maintainer | up to `code-write` | `code-write`, `execute-tests`, `safe-write` | actions inside scope |
| Admin | all | all | all |

A user cannot approve their own action above `safe-write` unless explicit deployment config allows self-approval for that level.

## The approval card

The card is the only surface a user sees before execution. It must show:

- The mapped command and its arguments.
- The plan: reads, writes, runtime, target environment.
- The permission level.
- The agent backend (Claude Code CLI, mock, API).
- A clear Approve / Deny / Edit action.
- A field for an optional approver note (recorded in the audit log).

The card is rendered server-side from the plan; the client cannot tamper with it. The Approve action posts to a signed endpoint that re-validates the plan against the stored proposal.

## Audit records

Two records per action:

1. The action itself in `.test-commander/audit/actions.jsonl` (see [security-and-permissions.md](security-and-permissions.md) for the schema).
2. A standalone approval record at `.test-commander/audit/approvals/<id>.json` containing the plan as approved, the approver identity, the timestamp, and any approver note. This is what PRs and the quality report cite.

Both records are append-only.

## Failure handling

- `denied`: no execution. Audit records the denial and the deny note.
- `violated_policy`: action stops. The runtime restores any partial state where safe (e.g. cannot un-run a destructive shell command, but can refuse to commit partial workspace writes). Admin review required before any related re-submission.
- `failed`: agent error before validation. The audit log captures the error and any partial outputs. The user may re-submit the same plan if they choose; no auto-retry.

## Re-approval rules

- A plan that has been approved is fingerprinted (command + arguments + plan scope + agent). If anything in that fingerprint changes, re-approval is required.
- An approval expires after a configurable window (default 15 minutes) if execution has not started.
- Continuous quality mode (Phase 13) pre-approves actions at or below the configured autonomy level. Anything above still routes to a human.

## See also

- [Controlled agent execution](controlled-agent-execution.md)
- [Security and permissions](security-and-permissions.md)
- [Chat command governance](chat-command-governance.md)
