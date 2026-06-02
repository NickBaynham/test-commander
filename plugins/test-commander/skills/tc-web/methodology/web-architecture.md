# Web console architecture

How the Test Commander web console is built and the invariants that keep it
trustworthy.

## Two services, one workspace

- **`api`** — a FastAPI backend (`apps/api/tcweb/`) that reads one consuming
  project's `.test-commander/` workspace (located via `TC_WORKSPACE`) and serves
  read-only data and command **proposals**.
- **`web`** — a Next.js frontend (`apps/web/`) that renders the API.

`make run` brings both up on docker compose (Pattern A, local-first — Decision
D15). No orchestrator (Claude) runs in the stack.

## The three invariants

1. **Read-only and proposal-only — no execution.** Every route either reads the
   workspace/index or returns a *proposal card* (a suggested `/tc:*` command the
   user can review). No route mutates the workspace or runs a command. Execution
   is gated behind Phase 10.5 (the governance phase).
2. **The workspace is the source of truth; the DB is a derived index.** The
   SQLite index (`.test-commander/.web/index.db`) is a rebuildable derivative of
   the committed artifacts. `index_workspace` drops and repopulates every table,
   so the index never holds state the workspace lacks. Every panel cites or
   links the artifact it rendered.
3. **`make run` brings up the whole stack on docker compose.** No cloud
   dependency for the MVP.

## The index schema

The indexer (`tcweb.indexer`) parses the real producer formats into tables:

| Table | Source artifact |
| --- | --- |
| `requirements` | `requirements/requirements-inventory.md` |
| `runs`, `run_results` | `runs/<RUN-ID>/results.json` |
| `evidence` | `evidence/evidence-index.md` |
| `journal` | `journal/<day>.md` (one row per timestamped entry) |
| `traceability` | `traceability/test-map.md` |
| `quality_facts` | `quality-report/current-quality-report.md` (measured facts) |

A rebuild is deterministic: the same workspace yields the same row counts. The
indexer never writes a workspace artifact — only the derived DB.

## See also

- [tc-web skill](../SKILL.md)
