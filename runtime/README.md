# runtime/

Shared runtime configuration for the Test Commander local stack (Pattern A,
local-first — Decision D15).

The web console (Phase 10) runs two services brought up by `make run` via docker
compose:

- `api` — the FastAPI backend under [`apps/api/`](../apps/api/). Reads the
  consuming project's `.test-commander/` workspace and serves read-only data and
  command **proposals** (never execution — that is Phase 10.5).
- `web` — the Next.js frontend under [`apps/web/`](../apps/web/).

The backend's SQLite index is a rebuildable derivative of the workspace; the
committed `.test-commander/` files remain authoritative. The workspace path is
supplied to the stack through the `TC_WORKSPACE` environment variable.

No orchestrator (Claude) runs here — Docker hosts only the viewer and the test
runtime, never the orchestrator (see the Runtime Topology section of
[`../planning/plan.md`](../planning/plan.md)).
