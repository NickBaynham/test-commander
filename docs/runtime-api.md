# Runtime API reference

The FastAPI backend (`apps/api/tcweb`) serves the web console and the Runtime API.
Base URL defaults to `http://localhost:8100`. The routes fall into three classes:

- **Read routes** (Phase 10) answer from the SQLite index or the workspace.
- **Proposal/chat routes** (Phase 10) return a command proposal card; they never
  execute.
- **Governed-execution routes** (Phase 10.5 `/api/execute`, Phase 11
  `/api/runtime/*`) run an approved request through the controlled execution
  pipeline. This is the only way the API can change the workspace or run a
  command, and there is no direct-execution backdoor.

For integration walkthroughs (client snippets, the dry-run-then-execute flow),
see [integrating](user-guide/integrating.md); for the MCP front-end see
[mcp-server](mcp-server.md).

## Health

| Method | Path | Returns |
| --- | --- | --- |
| GET | `/api/health` | `{status, service, version}` |

## Read routes

Each opens the SQLite index read-only (rebuilding it once if absent) and returns
JSON. Page payloads name the artifact(s) they were rendered from.

| Method | Path | Returns |
| --- | --- | --- |
| GET | `/api/dashboard` | requirement/risk/open-question counts, latest run, `source` |
| GET | `/api/requirements` | the requirement inventory rows |
| GET | `/api/runs` | per-run pass/fail/flaky |
| GET | `/api/runs/results` | per-scenario results |
| GET | `/api/journal` | journal entries (day, timestamp, title) |
| GET | `/api/evidence` | indexed evidence rows |
| GET | `/api/traceability` | the requirement → scenario → result chain |
| GET | `/api/quality-report` | `{facts, source}` |
| GET | `/api/sessions` | exploration sessions (read from the workspace) |

## Events (SSE)

| Method | Path | Returns |
| --- | --- | --- |
| GET | `/api/events?max_events=N` | `text/event-stream`: a `connected` frame, then a `changed` frame on every workspace change |

The console pages subscribe to this to refresh on a workspace change. `max_events`
bounds the stream (omit it in production; the client disconnects to stop).

## Proposals and chat (read-only, never execute)

| Method | Path | Body | Returns |
| --- | --- | --- | --- |
| POST | `/api/proposals` | `{intent}` | a proposal card `{kind, command, rationale, executed: false}` |
| POST | `/api/chat` | `{question}` | `{kind, answer, proposal, executed: false}` |

`/api/proposals` maps an intent to a suggested `/tc:*` command. `/api/chat`
answers from the index and attaches a proposal card for action requests. Neither
executes anything; both always return `executed: false`. An execute attempt is
answered with a proposal plus a note that the console cannot run commands.

## Governed execution (through the pipeline)

These routes enter the [controlled execution pipeline](controlled-agent-execution.md)
— intent → plan → permission policy → approval gate → bounded execution → output
validation → audit. A request above `read-only` cannot execute without a plan
and (where the level requires it) an approval; an approval with no `approver` is
held, not executed.

| Method | Path | Body | Returns |
| --- | --- | --- | --- |
| GET | `/api/runtime/info` | — | `{service, version, permission_levels}` (the seven levels) |
| POST | `/api/runtime/plan` | `{request, role}` | a **read-only dry run**: `{intent, command, level, allowed, reads, writes, requires_approval, target_environment, summary}` — no execution, no audit entry |
| POST | `/api/runtime/execute` | `{request, role, approve, approver, user}` | `{blocked, executed, requires_approval, approved, level, command, reason}` |
| POST | `/api/execute` | `{request, role, approve, approver, user}` | the console's governed-execution route (same pipeline) |

The permission level is **classified server-side** from the request; a client
cannot raise its own privilege by supplying a `level`. Use `POST /api/runtime/plan`
to preview what an execute call would do (and whether the role is allowed)
before sending it. See [security and permissions](security-and-permissions.md)
for the role/level/approval matrix.

## The contract

Read and proposal/chat routes never mutate the workspace; the test suite asserts
this as a property (every read route and chat turn leaves the workspace
byte-identical). The governed-execution routes are the only mutating path, and
every one of them is gated by the pipeline and recorded in the audit journal.

## See also

- [MCP server reference](mcp-server.md)
- [Integrating with Test Commander](user-guide/integrating.md)
- [Security and permissions](security-and-permissions.md)
- [Web console architecture](web-console.md)
- [Web console user guide](user-guide/web-console.md)
