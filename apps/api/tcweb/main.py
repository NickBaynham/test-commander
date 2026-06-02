"""FastAPI application factory for the Test Commander web console (Phase 10).

`create_app()` builds the console API: read-only data routes, the SSE stream,
proposal generation, the read-only chat, and (Phase 10.5) the single
`/api/execute` route that runs an approved request through the governance
pipeline. The only execution path is `/api/execute` → governance; every other
route is read-only or proposal-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI

from tcweb import config
from tcweb.routes import router
from tcweb.runtime_api import runtime_router

API_TITLE = "Test Commander Web Console"
API_VERSION = "0.10.0"


def _default_adapter() -> Any:
    # The console MVP drives the governance pipeline with the deterministic mock
    # adapter; an operator selects the real ClaudeCodeCliAdapter explicitly.
    from agent_adapters.mock_agent import MockAgentAdapter

    return MockAgentAdapter()


def create_app(project_root: Path | None = None, governance_adapter: Any = None) -> FastAPI:
    app = FastAPI(title=API_TITLE, version=API_VERSION)
    app.state.project_root = Path(project_root) if project_root else config.project_root()
    app.state.governance_adapter = governance_adapter or _default_adapter()

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "tc-web", "version": API_VERSION}

    app.include_router(router)
    app.include_router(runtime_router)
    return app


# The ASGI entry point uvicorn/gunicorn import (`tcweb.main:app`).
app = create_app()
