"""Expanded Runtime API routes (Phase 11).

The Phase-10 console API is read-only + proposal-only. Phase 11 adds the Runtime
API: a self-describing `/api/runtime/info` route (Step 11.1 scaffold) and the
governed-execution routes (Step 11.2) that enter the Phase-10.5 pipeline. Every
mutating route is routed through `governance.pipeline.handle_request`; there is
no direct-execution backdoor.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from governance import pipeline
from governance.policy import LEVELS

runtime_router = APIRouter(prefix="/api/runtime")

SERVICE_NAME = "tc-runtime-api"
SERVICE_VERSION = "0.11.0"


def _project_root(request: Request) -> Path:
    return request.app.state.project_root


@runtime_router.get("/info")
def runtime_info() -> dict:
    """Self-description: service identity + the seven permission levels.

    A client reads this to learn the levels it will be gated against. Read-only;
    advertises the policy surface without exposing any workspace data.
    """
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "permission_levels": list(LEVELS),
    }


@runtime_router.post("/plan")
def runtime_plan(payload: dict, request: Request) -> dict:
    """A read-only dry run: route, plan, and classify a request without running it.

    Returns the routed command, the classified permission level, the plan's
    reads/writes/approval, and whether the caller's role is allowed. Never
    executes and never writes to the audit journal.
    """
    pv = pipeline.preview(
        payload.get("request", ""),
        role=payload.get("role", "Viewer"),
        project_root=_project_root(request),
    )
    return {
        "intent": pv.intent,
        "command": pv.plan.command,
        "level": pv.level,
        "allowed": pv.allowed,
        "reads": list(pv.plan.reads),
        "writes": list(pv.plan.writes),
        "requires_approval": pv.plan.requires_approval,
        "target_environment": pv.plan.target_environment,
        "summary": pv.plan.summary,
    }


@runtime_router.post("/execute")
def runtime_execute(payload: dict, request: Request) -> dict:
    """Run an approved request through the governance pipeline.

    A governed-execution route: it enters intent -> plan -> policy -> approval ->
    bounded execution -> validation -> audit. A request above read-only cannot
    execute without a plan and (where the level requires it) an approval. There
    is no direct-execution backdoor.
    """
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
