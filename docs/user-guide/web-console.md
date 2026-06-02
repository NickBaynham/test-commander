# Web console (Phase 10)

The web console is a team-facing, **read-only** viewer over a consuming
project's `.test-commander/` workspace — a Next.js frontend and a FastAPI
backend brought up together by `make run` on docker compose. It renders the
committed artifacts and never invents data; it is **read-only and proposal-only**
— it never changes the workspace or runs a command. Execution lands in Phase
10.5 (the governance phase).

## Bring it up

```
$ /tc:web-init                       # provision the console config (once)
web console config provisioned: .test-commander/.web/console.json

$ /tc:web-index-artifacts            # build the SQLite index from the workspace
indexed: 23 row(s) across 7 tables
  requirements   3
  runs           1
  run_results    3
  evidence       1
  journal        2
  traceability   4
  quality_facts  9

$ make run                           # bring up api (8100) + web (3100) on docker
```

`make run` mounts your project (set `TC_WORKSPACE` to its root, default the
current directory) and starts both services. The console reads your artifacts
and writes only its derived index under `.test-commander/.web/` — it never
changes a workspace artifact. `/tc:web-start` is the
scriptable equivalent — by default it prints the command without running it:

```
$ /tc:web-start
TC_WORKSPACE=/path/to/project docker compose up --build
(dry run — pass --up to bring the stack up; or run `make run`.)
```

Open `http://localhost:3100`.

## The pages

| Page | Reads | Shows |
| --- | --- | --- |
| Dashboard | `/api/dashboard` | requirement / risk / open-question counts, latest run, live badge |
| Quality Report | `/api/quality-report` | the measured quality facts |
| Journal | `/api/journal` | the append-only journal, with a live badge |
| Sessions | `/api/sessions` | exploration sessions |
| Requirements | `/api/requirements` | the requirement inventory |
| Test Runs | `/api/runs` | per-run pass/fail/flaky |
| Evidence | `/api/evidence` | the indexed evidence |
| Settings | — | the API base + the read-only notice |

The dashboard and journal carry a **live badge**: the backend pushes an SSE
`changed` event whenever the workspace changes (e.g. a journal append), and the
page refreshes. Run `/tc:web-sync` to reconcile the index on demand.

## Chat

The Chat page answers questions from the indexed workspace and suggests
commands as **proposal cards**:

- "How many requirements are there?" → an answer from the index.
- "Generate BDD for sign-in" → a proposal card for `/tc:generate-bdd`.
- "Run the tests now" → a proposal card plus a note that the console cannot run
  commands; you review and run it yourself.

The chat never changes the workspace or runs a command.

## Export

`/tc:web-export` writes a shareable static bundle (`data.json` + a
self-contained `index.html`) under `.test-commander/.web/export/`:

```
$ /tc:web-export
exported: 2 file(s)
  .test-commander/.web/export/data.json
  .test-commander/.web/export/index.html
```

## The read-only contract

Every backend route is read-only or proposal-generating. No UI or API path
mutates the workspace or runs a command — the project's test suite asserts this
as a property (hitting every route, and every chat turn, leaves the workspace
byte-identical). Execution arrives in Phase 10.5 behind the controlled execution
pipeline.

## See also

- [Web console architecture](../web-console.md)
- [Runtime API reference](../runtime-api.md)
- [Workspace reference](../workspace-reference.md)
