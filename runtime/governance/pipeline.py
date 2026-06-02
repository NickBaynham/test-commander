"""The governance pipeline orchestrator (Phase 10.5).

`handle_request` is the single entry point every request flows through:

    intent -> plan -> permission policy -> approval gate -> bounded execution
      -> output validation -> audit log

Default deny: an unsafe request is blocked before the agent; a privileged action
that is not approved is held (no execution, no change); an approved action is
executed in bounds, its diff validated against the plan, and the whole action is
written to the append-only audit journal. There is no execution path that
bypasses these gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from governance import approval, audit, executor, intent, planner, policy, validation


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


@dataclass
class Preview:
    """The pre-execution decision for a request: what it routes to, the level it
    classifies to, and whether the role is allowed. No execution, no audit."""

    intent: str
    level: str
    plan: Any
    allowed: bool


def preview(request: str, *, role: str, project_root: Path) -> Preview:
    """Route, plan, and classify a request without executing it.

    The single source of truth for the pre-execution decision: `handle_request`
    calls it before any gate, and the Runtime API's read-only `/plan` route
    surfaces it. Level matches the request's inherent risk even when the router
    falls back to read-only (a dangerous unrouted request still classifies high).
    """
    command = intent.route(request)
    the_plan = planner.plan(command)
    level = the_plan.level if command != "read-only" else policy.classify(request)
    return Preview(
        intent=command,
        level=level,
        plan=the_plan,
        allowed=policy.allows(role, level, project_root),
    )


def handle_request(
    request: str,
    *,
    role: str,
    project_root: Path,
    adapter: Any,
    approve: bool = False,
    approver: str | None = None,
    user: str = "anon",
    now: datetime | None = None,
) -> PipelineResult:
    now = now or datetime.now()

    # Route, plan, and classify (the shared pre-execution decision).
    pv = preview(request, role=role, project_root=project_root)
    command, the_plan, level = pv.intent, pv.plan, pv.level

    # Permission policy (default deny). The agent is never reached if denied.
    if not pv.allowed:
        return PipelineResult(
            blocked=True,
            reason=f"permission denied: {level} not allowed for {role} (default deny)",
            level=level, intent=command, plan=the_plan,
        )

    # Approval gate. A privileged action that is not approved is held.
    needs_approval = approval.requires_approval(the_plan, project_root)
    if needs_approval and not approve:
        return PipelineResult(
            reason="approval required", level=level, intent=command, plan=the_plan,
            requires_approval=True, approved=False, executed=False,
        )

    if needs_approval and approve and approver:
        approval.record(project_root, the_plan, approved=True, approver=approver, now=now)

    # A read-only request is answered without invoking the agent.
    if level == "read-only":
        return PipelineResult(
            level=level, intent=command, plan=the_plan, executed=False, reason="read-only",
        )

    # Bounded execution -> output validation -> audit.
    result = executor.run(the_plan, adapter, project_root)
    verdict = validation.validate(the_plan, result, project_root)
    if not verdict.ok:
        result.status = "failed"
    entry = audit.record(
        project_root,
        {
            "user": user,
            "request": request,
            "intent": command,
            "command": the_plan.command,
            "approval_status": "approved" if needs_approval else "not-required",
            "approver": approver,
            "level": level,
            "files_read": list(the_plan.reads),
            "files_changed": list(result.files_changed),
            "artifacts": list(result.artifacts_created),
            "tests_run": level == "execute-tests",
            "target_urls": [the_plan.target_environment] if the_plan.target_environment else [],
            "status": result.status,
            "summary": result.summary,
            "evidence": [],
        },
        now=now,
    )
    return PipelineResult(
        level=level, intent=command, plan=the_plan,
        requires_approval=needs_approval, approved=needs_approval, executed=True,
        result=result, validation=verdict, audit_entry=entry,
        reason="" if verdict.ok else "; ".join(verdict.violations),
    )
