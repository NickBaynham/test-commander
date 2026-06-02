# Runtime API methodology

The Runtime API (`apps/api/`) is the Phase-10 read-only console API expanded with
governed-execution routes. It is one of two front-ends to the Phase-10.5
governance pipeline (the other is the MCP server).

## Route classes

- **Read routes** answer from the SQLite index or the workspace; they never
  mutate and never run a command (`GET /api/requirements`, `/api/runs`,
  `/api/quality-report`, and the rest of the Phase-10 surface).
- **Proposal routes** return a command proposal card without executing
  (`POST /api/proposals`).
- **Governed-execution routes** run an approved request through the pipeline
  (`POST /api/runtime/execute`, and the console's `POST /api/execute`). This is
  the only path that can change the workspace or run a command, and it enters
  `governance.pipeline.handle_request` — intent -> plan -> permission policy ->
  approval gate -> bounded execution -> output validation -> audit.

The Runtime API also exposes `POST /api/runtime/plan`, a **read-only dry run**:
it routes, plans, and classifies a request (via `governance.pipeline.preview`)
and reports the level and whether the caller's role is allowed, without executing
and without writing to the audit journal. A client uses it to preview what an
execute call would do.

## The no-bypass rule

A route above `read-only` cannot execute without a plan and (where the level
requires it) an approval. The permission level is classified server-side from
the request; the client cannot raise its own privileges. A contract test asserts
that an execute request without approval for a privileged level is held — no
execution, no change, the audit log records nothing.

Shipped in Step 11.2 (`tests/test_runtime_api.py`).
