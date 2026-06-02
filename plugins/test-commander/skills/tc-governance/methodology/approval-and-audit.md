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

`governance.audit` writes one line to the append-only
`<workspace>/audit/actions.jsonl` for every action the pipeline executes, with
the full field set: `user`, `timestamp`, `request`, `intent`, `command`,
`approval_status`, `approver`, `level`, `files_read`, `files_changed`,
`artifacts`, `tests_run`, `target_urls`, `status`, `summary`, `evidence`.
`read_entries(project)` parses the journal; a missing or empty journal returns
`[]`.

Because the only path to execution is the pipeline (and the adapter refuses an
unplanned call), an empty journal is proof that nothing executed outside the
gates: a direct adapter call with no plan is refused and writes no entry.

## See also

- [Permission policy](permission-policy.md)
- [tc-governance skill](../SKILL.md)
