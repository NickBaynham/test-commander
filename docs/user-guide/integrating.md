# Integrating with Test Commander

Test Commander exposes the workspace to other tools and agents two ways, both of
which run through the same governed pipeline the web console uses:

- the **Runtime API** — an HTTP API (`apps/api`), for scripts and services;
- the **MCP server** — a Model Context Protocol server (`apps/mcp`), for MCP
  clients (Claude, an IDE, another agent).

Neither can bypass governance. Every call above `read-only` is routed, planned,
permission-checked, approved where required, validated, and audited server-side.
The level is classified from the request — a client cannot raise its own
privilege.

## The dry-run-then-execute flow

The safe pattern for any privileged action is two steps: **plan**, then
**execute**.

1. **Plan (read-only).** Ask what a request would do and whether your role is
   allowed. This never executes and never writes to the audit journal.
2. **Execute (governed).** If the plan reports `requires_approval`, supply
   `approve: true` and an `approver`. An approval with no approver is held, not
   executed.

### Over the Runtime API

```bash
# 1. Preview
curl -s localhost:8100/api/runtime/plan \
  -H 'content-type: application/json' \
  -d '{"request": "generate playwright tests for sign-in", "role": "Automation Engineer"}'
# -> {"command": "/tc:automate", "level": "code-write", "allowed": true, "requires_approval": true, ...}

# 2. Execute (with approval, because code-write requires it)
curl -s localhost:8100/api/runtime/execute \
  -H 'content-type: application/json' \
  -d '{"request": "generate playwright tests for sign-in", "role": "Automation Engineer", "approve": true, "approver": "maintainer", "user": "alice"}'
# -> {"executed": true, "command": "/tc:automate", "level": "code-write", ...}
```

A denied request comes back `{"blocked": true, "executed": false}` — for example
a `Viewer` asking to "delete all evidence" (a `destructive` action). The agent is
never reached.

### Over the MCP server

Point your MCP client at `python -m tcmcp` (stdio), with `TC_WORKSPACE` set to
the project root that holds `.test-commander/`. List the tools, then call
`tc_plan` and `tc_run_command`:

```
tools/call tc_plan          {"request": "review these requirements", "role": "Tester"}
tools/call tc_run_command   {"request": "review these requirements", "role": "Tester"}
```

`safe-write` actions (like reviewing requirements) do not require approval by
default; `code-write` and above do. See the [MCP server reference](../mcp-server.md)
for the full tool list and a sample session.

## Roles and levels

Which role may do what is defined in `<workspace>/policy/permissions.yaml`, and
which levels require approval in `<workspace>/policy/approvals.yaml` — the same
files the console uses. Customizing those files customizes the API and the MCP
server at the same time. See [security and permissions](../security-and-permissions.md)
and [customizing for your project](customizing-for-your-project.md).

## Choosing a backend

Both front-ends drive a governance **adapter**. The default is the deterministic
mock adapter (safe for local development and CI); an operator selects the real
Claude Code adapter explicitly. The adapter is a server-side choice — it is never
exposed to a caller, and provider secrets stay server-side.

## See also

- [Runtime API reference](../runtime-api.md)
- [MCP server reference](../mcp-server.md)
- [Security and permissions](../security-and-permissions.md)
- [Governance user guide](governance.md)
