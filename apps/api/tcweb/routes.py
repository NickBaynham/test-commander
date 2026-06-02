"""Read-only API routes + SSE + proposal generation (Phase 10 Step 10.3).

Every route reads the index (or the workspace) or returns a proposal card. None
mutates the workspace or runs a command. The router resolves its served project
root from the app state set by `create_app`.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from tcweb import chat, config, indexer, proposals, queries, sse

router = APIRouter(prefix="/api")


def _project_root(request: Request) -> Path:
    return request.app.state.project_root


def _index_conn(project_root: Path) -> sqlite3.Connection:
    """Open the index, rebuilding it once if it does not yet exist (read path)."""
    db_path = config.index_db_path(project_root)
    if not db_path.is_file():
        indexer.rebuild(project_root)
    return indexer.connect(db_path)


@router.get("/requirements")
def get_requirements(request: Request) -> list[dict]:
    conn = _index_conn(_project_root(request))
    try:
        return queries.requirements(conn)
    finally:
        conn.close()


@router.get("/runs")
def get_runs(request: Request) -> list[dict]:
    conn = _index_conn(_project_root(request))
    try:
        return queries.runs(conn)
    finally:
        conn.close()


@router.get("/runs/results")
def get_run_results(request: Request) -> list[dict]:
    conn = _index_conn(_project_root(request))
    try:
        return queries.run_results(conn)
    finally:
        conn.close()


@router.get("/evidence")
def get_evidence(request: Request) -> list[dict]:
    conn = _index_conn(_project_root(request))
    try:
        return queries.evidence(conn)
    finally:
        conn.close()


@router.get("/journal")
def get_journal(request: Request) -> list[dict]:
    conn = _index_conn(_project_root(request))
    try:
        return queries.journal(conn)
    finally:
        conn.close()


@router.get("/traceability")
def get_traceability(request: Request) -> list[dict]:
    conn = _index_conn(_project_root(request))
    try:
        return queries.traceability(conn)
    finally:
        conn.close()


@router.get("/quality-report")
def get_quality_report(request: Request) -> dict:
    conn = _index_conn(_project_root(request))
    try:
        return queries.quality_report(conn)
    finally:
        conn.close()


@router.get("/dashboard")
def get_dashboard(request: Request) -> dict:
    conn = _index_conn(_project_root(request))
    try:
        return queries.dashboard(conn)
    finally:
        conn.close()


@router.get("/sessions")
def get_sessions(request: Request) -> list[dict]:
    """Sessions are read directly from the workspace (not indexed). Empty is OK."""
    sessions_dir = config.workspace_dir(_project_root(request)) / "sessions"
    if not sessions_dir.is_dir():
        return []
    return [
        {"session": p.stem, "source": f"sessions/{p.name}"}
        for p in sorted(sessions_dir.glob("*.md"))
        if p.name != "index.md"
    ]


@router.get("/events")
def get_events(request: Request, max_events: int | None = None) -> StreamingResponse:
    ws = config.workspace_dir(_project_root(request))
    return StreamingResponse(
        sse.event_stream(ws, max_events=max_events),
        media_type="text/event-stream",
    )


@router.post("/proposals")
def post_proposal(payload: dict) -> dict:
    """Return a command proposal card. Never executes."""
    return proposals.propose(payload.get("intent", "")).to_dict()


@router.post("/chat")
def post_chat(payload: dict, request: Request) -> dict:
    """Answer a question from the index; attach a proposal card. Never executes."""
    conn = _index_conn(_project_root(request))
    try:
        return chat.answer(payload.get("question", ""), conn)
    finally:
        conn.close()


@router.post("/execute")
def post_execute(payload: dict, request: Request) -> dict:
    """Run an approved request through the governance pipeline.

    The ONLY execution path in the console. Every action flows through
    intent -> plan -> policy -> approval -> bounded execution -> validation ->
    audit; nothing executes without it.
    """
    from governance import pipeline

    res = pipeline.handle_request(
        payload.get("request", ""),
        role=payload.get("role", "Viewer"),
        project_root=_project_root(request),
        adapter=request.app.state.governance_adapter,
        approve=bool(payload.get("approve", False)),
        approver=payload.get("approver"),
        user=payload.get("user", "anon"),
    )
    return {
        "blocked": res.blocked,
        "executed": res.executed,
        "requires_approval": res.requires_approval,
        "approved": res.approved,
        "level": res.level,
        "command": res.intent,
        "reason": res.reason,
    }
