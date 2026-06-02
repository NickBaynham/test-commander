"""The governance pipeline orchestrator (built across 10.5.3-10.5.10).

`handle_request` is the single entry point every request flows through:

    intent -> plan -> permission policy -> approval gate -> bounded execution
      -> output validation -> audit log

Built component-by-component. As of Step 10.5.3 the **permission policy** gate is
live (default deny blocks before the agent); the downstream stages raise
NotImplementedError until their sub-steps land, so an allowed action is not yet
executable and the later security tests stay xfail.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from governance import policy


@dataclass
class PipelineResult:
    blocked: bool = False
    reason: str = ""
    level: str = ""
    intent: str = ""
    plan: Any = None
    requires_approval: bool = False
    approved: bool = False
    executed: bool = False
    result: Any = None
    validation: Any = None
    audit_entry: dict | None = None


def handle_request(
    request: str,
    *,
    role: str,
    project_root: Path,
    adapter: Any,
    approve: bool = False,
    approver: str | None = None,
    user: str = "anon",
) -> PipelineResult:
    # Permission policy (default deny). The agent is never reached if denied.
    decision = policy.decide(request, role, project_root)
    if not decision.allowed:
        return PipelineResult(blocked=True, reason=decision.reason, level=decision.level)

    # Allowed actions are not yet executable: approval (10.5.6), bounded
    # execution (10.5.7), validation (10.5.8), and audit (10.5.9) land next.
    raise NotImplementedError(
        "permitted actions become executable across Steps 10.5.4-10.5.9"
    )
