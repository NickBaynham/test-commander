# Web console architecture

The Phase 10 web console is the **viewer** runtime role (see the Runtime
Topology section of [planning/plan.md](../planning/plan.md)). It is local-first
(Pattern A, Decision D15): no cloud dependency, no Claude in the stack.

## Stack

```
apps/web/   Next.js app-router frontend (port 3100)
apps/api/   FastAPI backend (port 8100), package tcweb
runtime/    shared runtime notes
docker-compose.yml   api + web, brought up by `make run`
```

The backend reads one consuming-project `.test-commander/` workspace (located
via `TC_WORKSPACE`, mounted read-only in the container) and serves it.

## Invariants

1. **Read-only and proposal-only — no execution.** Every route reads the
   workspace/index or returns a proposal card. No route mutates the workspace or
   runs a command. Execution is Phase 10.5.
2. **The workspace is the source of truth; the DB is a derived index.** The
   SQLite index (`.test-commander/.web/index.db`) is a rebuildable derivative;
   `index_workspace` drops and repopulates every table. Every panel cites the
   artifact it rendered.
3. **`make run` brings up the whole stack on docker compose.**

## Components

| Module | Role |
| --- | --- |
| `tcweb.config` | workspace + index-path resolution (`TC_WORKSPACE`) |
| `tcweb.db` | SQLite schema + connection |
| `tcweb.indexer` | walk the workspace into the index (rebuildable) |
| `tcweb.queries` | read the index into page payloads (each cites its source) |
| `tcweb.routes` | the read-only API routes + SSE + proposals + chat |
| `tcweb.sse` | workspace-change detection + the event stream |
| `tcweb.proposals` | intent → command proposal card (never executes) |
| `tcweb.chat` | read-only Q&A over the index + proposal cards |
| `tcweb.exporter` | the deterministic static export bundle |

## Commands

The five `/tc:web-*` commands (plugin scripts, per D18) drive the stack:
`/tc:web-init`, `/tc:web-start`, `/tc:web-sync`, `/tc:web-index-artifacts`,
`/tc:web-export`. See the [command reference](command-reference.md).

## See also

- [Web console user guide](user-guide/web-console.md)
- [Runtime API reference](runtime-api.md)
- [tc-web skill](../plugins/test-commander/skills/tc-web/SKILL.md)
