# Governance: how the console runs commands safely (Phase 10.5)

The web console never runs a command directly. Every request — a chat message, a
proposal card you approve, a button — flows through a **policy-governed
pipeline** before anything touches Claude or your workspace. This guide explains
what you see as a tester and why.

## What you can do depends on your role

| Role | Can do |
| --- | --- |
| Viewer | view reports and evidence, ask read-only questions |
| Tester | + review requirements, generate test ideas / BDD, approved test runs |
| Automation Engineer | + generate Playwright tests (with approval), update fixtures |
| Maintainer | + approve code-write actions, manage settings |
| Admin | everything, including secrets and permission rules |

Roles map to permission levels in `<workspace>/policy/permissions.yaml`. The
default is **deny**: if your role isn't granted a level, the action is blocked.

## The flow

1. You ask for something (chat or a proposal card).
2. The console maps it to a known `/tc:*` workflow (or answers read-only).
3. It builds a **plan** and checks your role's permission.
4. If the action is privileged, it shows an **approval card**.
5. Only after approval does it run — in a bounded scope — and then it validates
   the result and writes an audit entry.

### Blocked before the agent

An unsafe request from a low role never reaches the agent:

```
> delete all evidence   (as Viewer)
blocked: permission denied: destructive not allowed for Viewer (default deny)
```

### The approval card

A privileged action shows exactly what it will do before you approve:

```
Command:
  /tc:automate
This will:
  - read bdd/features/
  - create or modify tests/e2e/
  - create or modify tests/pages/
  - create or modify traceability/automation-map.md
Permission level:
  code-write
Approve?
```

Deny it and **nothing changes**. Approve it and it runs in bounds.

### After approval — bounded, validated, audited

The agent receives a *structured instruction* (the plan), never your raw text,
so a prompt injection can't escape the scope. After it runs, the console checks
the diff matches the plan (no out-of-scope writes, no secret files) and writes
an append-only entry to `<workspace>/audit/actions.jsonl`:

```json
{
  "user": "alice",
  "timestamp": "2026-06-01T09:30:00",
  "intent": "/tc:automate",
  "command": "/tc:automate",
  "level": "code-write",
  "approval_status": "approved",
  "approver": "maintainer",
  "files_changed": ["tests/e2e/", "tests/pages/", "traceability/automation-map.md"],
  "status": "succeeded"
}
```

## What the console never does

- Send your raw message to the agent.
- Run anything above `read-only` without an approval record.
- Show you provider secrets, or let a command print environment variables.
- Execute anything outside this pipeline — there is no bypass.

## Tuning it for your project

Edit `<workspace>/policy/permissions.yaml` (role → levels) and
`approvals.yaml` (which levels require approval). See
[customizing-for-your-project.md](customizing-for-your-project.md).

## See also

- [Controlled agent execution](../controlled-agent-execution.md)
- [Security and permissions](../security-and-permissions.md)
- [Runtime approval flow](../runtime-approval-flow.md)
