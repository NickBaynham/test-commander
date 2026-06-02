# Runtime API reference (Phase 10)

The FastAPI backend (`apps/api/tcweb`) serves the web console. Every route is
**read-only or proposal-generating** — none mutates the workspace or runs a
command. Base URL defaults to `http://localhost:8100`.

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

## The read-only contract

There is no mutating route. The test suite asserts this as a property: hitting
every read route — and every chat turn — leaves the workspace byte-identical.
Execution arrives in Phase 10.5 behind the controlled execution pipeline.

## See also

- [Web console architecture](web-console.md)
- [Web console user guide](user-guide/web-console.md)
