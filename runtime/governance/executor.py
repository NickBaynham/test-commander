"""Bounded executor (Phase 10.5 Step 10.5.7).

Wraps an approved `Plan` into a `BoundedInstruction` — a structured instruction
the adapter runs — and executes it. The instruction-critical fields (command,
scope, allowed/disallowed paths and actions, expected outputs, safety rules) are
derived **only from the plan**, never from the raw user request, so a prompt
injection in the original text cannot reach the agent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_adapters.base import BoundedInstruction, ExecutionResult

from governance.planner import Plan

# Paths no command may touch (secret safety). Always disallowed.
SECRET_PATHS = (".env", "secrets", "credentials", ".git", "deploy")

# Allowed/disallowed actions per permission level.
_ACTIONS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "read-only": (("read",), ("write", "run", "network", "delete")),
    "safe-write": (("read", "write"), ("run", "network", "delete")),
    "code-write": (("read", "write"), ("run", "network", "delete")),
    "execute-tests": (("read", "write", "run"), ("network", "delete")),
    "external-network": (("read", "write", "run", "network"), ("delete",)),
    "destructive": (("read", "write", "run", "network", "delete"), ()),
    "admin": (("read", "write", "run", "network", "delete", "admin"), ()),
}

_SAFETY_RULES = (
    "Do not read or print secret files or environment variables.",
    "Stay within the allowed paths; do not touch disallowed paths.",
    "Write an audit/journal entry for this action.",
)


def build_instruction(plan: Plan, project_root: Path) -> BoundedInstruction:
    """Build the bounded instruction from an approved plan (no raw user text)."""
    allowed_actions, disallowed_actions = _ACTIONS.get(plan.level, _ACTIONS["read-only"])
    return BoundedInstruction(
        command=plan.command,
        scope=plan.level,
        project_root=Path(project_root),
        allowed_paths=tuple(plan.reads) + tuple(plan.writes),
        disallowed_paths=SECRET_PATHS,
        allowed_actions=allowed_actions,
        disallowed_actions=disallowed_actions,
        expected_outputs=tuple(plan.expected_artifacts),
        safety_rules=_SAFETY_RULES,
        journal_required=True,
        approved=True,
    )


def run(plan: Plan, adapter: Any, project_root: Path) -> ExecutionResult:
    """Wrap the approved plan and execute it through the adapter."""
    instruction = build_instruction(plan, project_root)
    return adapter.execute_command(instruction)
