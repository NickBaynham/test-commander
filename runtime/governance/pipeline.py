"""The governance pipeline orchestrator (built across 10.5.3-10.5.10).

`handle_request` is the single entry point every request flows through:

    intent -> plan -> permission policy -> approval gate -> bounded execution
      -> output validation -> audit log

Built component-by-component. As of Step 10.5.6 the **policy** and **approval**
gates are live: an unsafe request is blocked before the agent, and a privileged
action that is not approved is held (no execution, no change). Bounded execution
(10.5.7), output validation (10.5.8), and audit (10.5.9) land next, so an
*approved* action is not yet executable and the later security tests stay xfail.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from governance import approval, executor, intent, planner, policy, validation


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
    # Route to a known command (or read-only); plan it deterministically.
    command = intent.route(request)
    the_plan = planner.plan(command)
    level = the_plan.level if command != "read-only" else policy.classify(request)

    # Permission policy (default deny). The agent is never reached if denied.
    if not policy.allows(role, level, project_root):
        return PipelineResult(
            blocked=True,
            reason=f"permission denied: {level} not allowed for {role} (default deny)",
            level=level,
            intent=command,
            plan=the_plan,
        )

    # Approval gate. A privileged action that is not approved is held: no
    # execution, no change.
    needs_approval = approval.requires_approval(the_plan, project_root)
    if needs_approval and not approve:
        return PipelineResult(
            blocked=False,
            reason="approval required",
            level=level,
            intent=command,
            plan=the_plan,
            requires_approval=True,
            approved=False,
            executed=False,
        )

    # Approved (or approval not required). Record the approval decision.
    if needs_approval and approve and approver:
        approval.record(project_root, the_plan, approved=True, approver=approver, now=_now())

    # A read-only request is answered without invoking the agent.
    if level == "read-only":
        return PipelineResult(
            level=level, intent=command, plan=the_plan, requires_approval=False,
            approved=False, executed=False, reason="read-only",
        )

    # Bounded execution through the adapter (output validation lands in 10.5.8;
    # the audit entry in 10.5.9 — until then validation is None and the
    # approve-diff-matches security test stays xfail).
    result = executor.run(the_plan, adapter, project_root)
    verdict = validation.validate(the_plan, result, project_root)
    if not verdict.ok:
        result.status = "failed"
    return PipelineResult(
        level=level, intent=command, plan=the_plan,
        requires_approval=needs_approval, approved=needs_approval, executed=True,
        result=result, validation=verdict,
        reason="" if verdict.ok else "; ".join(verdict.violations),
    )


def _now():  # pragma: no cover - replaced by an injected clock in 10.5.9
    from datetime import datetime

    return datetime.now()
