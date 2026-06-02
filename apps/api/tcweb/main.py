"""FastAPI application factory for the Test Commander web console (Phase 10).

`create_app()` builds the read-only console API. Phase 10.1 ships the app shell
and the health route; later sub-steps mount the indexer, the read routes, the
SSE stream, and proposal generation.

Read-only and proposal-only by contract: no route mutates the workspace or runs
a command (execution is gated behind Phase 10.5).
"""

from __future__ import annotations

from fastapi import FastAPI

API_TITLE = "Test Commander Web Console"
API_VERSION = "0.10.0"


def create_app() -> FastAPI:
    app = FastAPI(title=API_TITLE, version=API_VERSION)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "tc-web", "version": API_VERSION}

    return app


# The ASGI entry point uvicorn/gunicorn import (`tcweb.main:app`).
app = create_app()
