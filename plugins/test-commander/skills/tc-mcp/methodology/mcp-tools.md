# MCP tools methodology

The MCP server (`apps/mcp/`) is a lightweight, schema-first Model Context
Protocol server. It does not depend on a heavy MCP SDK: it is a small tool
registry that an MCP transport (stdio) wraps, and that tests exercise in-process
through a sample client.

## Schema-first tools

Every tool ships an explicit JSON schema for its arguments. A tool definition is
a name, a one-line description, an `inputSchema` (JSON Schema for arguments), and
a handler. The registry validates arguments against the schema before dispatch:
a missing required argument or an unknown argument returns an MCP error rather
than reaching a handler.

The shipped tools (`apps/mcp/tcmcp/server.py`):

- `tc_status` — read-only server identity and the seven permission levels.
- `tc_plan` — read-only dry run: route, plan, and classify a request via
  `pipeline.preview`, with no execution and no audit entry.
- `tc_run_command` — governed execution via `pipeline.handle_request`.

`dispatch()` handles the `initialize` / `tools/list` / `tools/call` protocol
messages and is wrapped by the stdio entry point (`__main__.py`).

## Dispatch into the pipeline

A tool that does anything above `read-only` dispatches into
`governance.pipeline.handle_request` — the same pipeline the console and the
Runtime API use. There is no direct-execution backdoor: the tool cannot reach an
adapter without passing intent routing, planning, permission policy, the
approval gate, output validation, and audit.

## Permission gating

Each tool declares the maximum permission level it can reach. The pipeline
classifies the actual request and resolves it against the caller's role; a tool
above `read-only` is refused for a role that lacks the level (default deny), and
a destructive tool is refused without an admin-level approval.

Shipped in Step 11.3 (`tests/test_mcp_server.py`). The per-level gate matrix and
the destructive-tool security tests are in Step 11.4
(`tests/test_permission_gates.py`), which also hardened the approval gate so an
approval with no approver is not an approval.
