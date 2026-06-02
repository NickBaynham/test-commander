# Approval gate and audit journal

## Approval gate

`governance.approval` decides whether a plan needs human approval, renders the
approval card the UI shows, and records the decision under
`<workspace>/audit/approvals/`.

- `requires_approval(plan, project_root)` — the privileged levels (`code-write`,
  `execute-tests`, `external-network`, `destructive`, `admin`) always require
  approval; `safe-write` is configurable per deployment via
  `policy/approvals.yaml` (`require_approval: [<level>, …]`).
- `render_card(plan)` — the card: command, what it will read / create or modify,
  target environment, permission level, and `Approve?`.
- `record(project_root, plan, approved, approver, now)` — an approval record
  (`approval-NNN.json`) with command, level, approved, approver, timestamp.

In the pipeline, a privileged action that is **not approved is held**: no
bounded instruction is built, the adapter is never called, and nothing changes
(the deny-no-change security property). Only an approved plan proceeds to
bounded execution.

## Audit journal

(Shipped in Step 10.5.9.) The append-only `audit/actions.jsonl` records every
action end to end.

## See also

- [Permission policy](permission-policy.md)
- [tc-governance skill](../SKILL.md)
