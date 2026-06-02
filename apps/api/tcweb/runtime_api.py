"""Expanded Runtime API routes (Phase 11).

The Phase-10 console API is read-only + proposal-only. Phase 11 adds the Runtime
API: a self-describing `/api/runtime/info` route (Step 11.1 scaffold) and the
governed-execution routes (Step 11.2) that enter the Phase-10.5 pipeline. Every
mutating route is routed through `governance.pipeline.handle_request`; there is
no direct-execution backdoor.
"""

from __future__ import annotations

from fastapi import APIRouter
from governance.policy import LEVELS

runtime_router = APIRouter(prefix="/api/runtime")

SERVICE_NAME = "tc-runtime-api"
SERVICE_VERSION = "0.11.0"


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
