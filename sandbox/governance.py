"""Governance travels with the sandbox (Phase 12 Step 12.4).

The Phase-10.5 controlled execution pipeline runs inside the sandbox exactly as
it does locally. `run_in_sandbox` is the single entry point a sandboxed job uses
to act — it is `governance.pipeline.handle_request`, so a sandbox cannot execute
above its approved permission level, nothing bypasses the approval gate, and
every action is audited. Sandboxing never relaxes governance.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from governance import pipeline


def run_in_sandbox(
    request: str,
    *,
    role: str,
    project_root: Path,
    adapter: Any,
    approve: bool = False,
    approver: str | None = None,
    user: str = "sandbox",
):
    """Run a request through the governance pipeline from inside the sandbox."""
    return pipeline.handle_request(
        request,
        role=role,
        project_root=Path(project_root),
        adapter=adapter,
        approve=approve,
        approver=approver,
        user=user,
    )
