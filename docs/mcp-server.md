# MCP server reference

The Test Commander MCP server (`apps/mcp/tcmcp`) exposes the workspace to MCP
clients (Claude, an IDE, another agent) as a small set of schema-first tools. It
is a lightweight registry — not a heavy SDK — and every tool above `read-only`
dispatches into the same [controlled execution pipeline](controlled-agent-execution.md)
the web console and the [Runtime API](runtime-api.md) use. There is no
direct-execution backdoor.

## Transport

The server speaks the MCP protocol over **stdio**. The entry point is
`python -m tcmcp` (the image's default command). It reads one JSON message per
line and writes one JSON response per line. The protocol core is
`tcmcp.server.dispatch(message)`, which handles:

| Method | Purpose |
| --- | --- |
| `initialize` | Handshake: returns `protocolVersion`, `serverInfo {name, version}`, `capabilities`. |
| `tools/list` | The schema-first tool catalog (`name`, `description`, `inputSchema`). |
| `tools/call` | `params: {name, arguments}` → `{result}` or `{isError: true, error}`. |

Arguments are validated against each tool's JSON schema before dispatch: a
missing required argument, an unknown argument, or an unknown tool name returns
an MCP error rather than reaching a handler.

## Tools

| Tool | Max level | Arguments | Returns |
| --- | --- | --- | --- |
| `tc_status` | `read-only` | — | `{server, version, permission_levels, workspace_present}` |
| `tc_plan` | `read-only` | `{request, role?}` | a dry run: `{intent, command, level, allowed, requires_approval}` — no execution, no audit entry |
| `tc_run_command` | `admin` | `{request, role?, approve?, approver?, user?}` | governed execution: `{blocked, executed, requires_approval, approved, level, command, reason}` |

`tc_run_command` is gated by the seven permission levels exactly as the Runtime
API is: a denied request is blocked before the agent, a privileged request is
held without an `approver`, and neither writes an audit entry. Use `tc_plan` to
preview a request (and check `allowed`) before calling `tc_run_command`.

## Example session

```
-> {"id": 1, "method": "initialize"}
<- {"id": 1, "protocolVersion": "2024-11-05", "serverInfo": {"name": "test-commander", "version": "0.11.0"}, "capabilities": {"tools": {}}}

-> {"id": 2, "method": "tools/list"}
<- {"id": 2, "tools": [ {"name": "tc_status", ...}, {"name": "tc_plan", ...}, {"name": "tc_run_command", ...} ]}

-> {"id": 3, "method": "tools/call", "params": {"name": "tc_plan", "arguments": {"request": "generate playwright tests for sign-in", "role": "Automation Engineer"}}}
<- {"id": 3, "result": {"intent": "/tc:automate", "command": "/tc:automate", "level": "code-write", "allowed": true, "requires_approval": true}}

-> {"id": 4, "method": "tools/call", "params": {"name": "tc_run_command", "arguments": {"request": "generate playwright tests for sign-in", "role": "Automation Engineer", "approve": true, "approver": "maintainer"}}}
<- {"id": 4, "result": {"blocked": false, "executed": true, "level": "code-write", "command": "/tc:automate", ...}}
```

## Workspace

The served workspace is the project root that holds `.test-commander/`, taken
from the `TC_WORKSPACE` environment variable (default: the current directory).
In the container it is mounted at `/workspace`.

## See also

- [Runtime API reference](runtime-api.md)
- [Integrating with Test Commander](user-guide/integrating.md)
- [Security and permissions](security-and-permissions.md)
- [Controlled agent execution](controlled-agent-execution.md)
