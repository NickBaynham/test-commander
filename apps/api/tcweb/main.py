"""FastAPI application factory for the Test Commander web console (Phase 10).

`create_app()` builds the read-only console API. Phase 10.1 ships the app shell
and the health route; later sub-steps mount the indexer, the read routes, the
SSE stream, and proposal generation.

Read-only and proposal-only by contract: no route mutates the workspace or runs
a command (execution is gated behind Phase 10.5).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from tcweb import config
from tcweb.routes import router

API_TITLE = "Test Commander Web Console"
API_VERSION = "0.10.0"


def create_app(project_root: Path | None = None) -> FastAPI:
    app = FastAPI(title=API_TITLE, version=API_VERSION)
    app.state.project_root = Path(project_root) if project_root else config.project_root()

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "tc-web", "version": API_VERSION}

    app.include_router(router)
    return app


# The ASGI entry point uvicorn/gunicorn import (`tcweb.main:app`).
app = create_app()
