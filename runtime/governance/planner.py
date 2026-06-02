"""Command planner (Phase 10.5 Step 10.5.5).

Produces an explicit, displayable, deterministic plan for a routed command:
command, likely reads, likely writes, permission level, target environment,
expected artifacts, and whether approval is required. The plan is what the
approval gate (10.5.6) renders and the bounded executor (10.5.7) wraps.
"""

from __future__ import annotations

from dataclasses import dataclass

# Levels that require approval by default (the approval gate may widen this for
# safe-write via approvals.yaml; read-only/safe-write are exempt by default).
_APPROVAL_REQUIRED = {"code-write", "execute-tests", "external-network", "destructive", "admin"}


@dataclass(frozen=True)
class Plan:
    command: str
    level: str
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()
    expected_artifacts: tuple[str, ...] = ()
    target_environment: str | None = None
    requires_approval: bool = False
    summary: str = ""


# Per-command knowledge: command -> (level, reads, writes, target_environment).
_COMMAND_PLANS: dict[str, dict] = {
    "/tc:review-requirements": {
        "level": "safe-write",
        "reads": ("requirements/", "documents/uploaded/"),
        "writes": ("requirements/requirements-review.md", "requirements/open-questions.md"),
    },
    "/tc:generate-bdd": {
        "level": "safe-write",
        "reads": ("test-ideas/", "requirements/"),
        "writes": ("bdd/features/",),
    },
    "/tc:automate": {
        "level": "code-write",
        "reads": ("bdd/features/",),
        "writes": ("tests/e2e/", "tests/pages/", "traceability/automation-map.md"),
    },
    "/tc:run": {
        "level": "execute-tests",
        "reads": ("tests/",),
        "writes": ("runs/", "evidence/"),
    },
    "/tc:explore": {
        "level": "external-network",
        "reads": ("charters/", "product-knowledge/"),
        "writes": ("exploration-notes/", "sessions/"),
        "target_environment": "target site / staging",
    },
    "/tc:visualize": {
        "level": "safe-write",
        "reads": ("traceability/", "product-knowledge/", "risk-register/"),
        "writes": ("visuals/mermaid/",),
    },
    "/tc:report": {
        "level": "safe-write",
        "reads": ("runs/", "traceability/", "requirements/"),
        "writes": ("quality-report/",),
    },
    "/tc:create-charter": {
        "level": "safe-write",
        "reads": ("product-knowledge/", "requirements/", "risk-register/"),
        "writes": ("charters/",),
    },
}


def plan(command: str) -> Plan:
    """Build the deterministic plan for a routed command (or the read-only path)."""
    if command == "read-only" or command not in _COMMAND_PLANS:
        return Plan(
            command="read-only",
            level="read-only",
            reads=("the indexed workspace",),
            summary="Read-only Q&A from indexed artifacts; no writes, no approval.",
        )
    spec = _COMMAND_PLANS[command]
    level = spec["level"]
    writes = tuple(spec.get("writes", ()))
    return Plan(
        command=command,
        level=level,
        reads=tuple(spec.get("reads", ())),
        writes=writes,
        expected_artifacts=writes,
        target_environment=spec.get("target_environment"),
        requires_approval=level in _APPROVAL_REQUIRED,
        summary=f"{command} ({level})",
    )
