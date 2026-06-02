"""Approval gate (Phase 10.5 Step 10.5.6).

Decides whether a plan needs human approval, renders the approval card the UI
shows, and records the decision under `<workspace>/audit/approvals/`. The
privileged levels (`code-write`, `execute-tests`, `external-network`,
`destructive`, `admin`) always require approval; `safe-write` is configurable per
deployment via `policy/approvals.yaml`.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import yaml

from governance.planner import Plan

WORKSPACE_DIRNAME = ".test-commander"
_ALWAYS_REQUIRE = {"code-write", "execute-tests", "external-network", "destructive", "admin"}


def _approval_config(project_root: Path | None) -> set[str] | None:
    if project_root is None:
        return None
    path = Path(project_root) / WORKSPACE_DIRNAME / "policy" / "approvals.yaml"
    if not path.is_file():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("require_approval"), list):
        return set(data["require_approval"])
    return None


def requires_approval(plan: Plan, project_root: Path | None = None) -> bool:
    """Whether the plan needs approval before execution."""
    configured = _approval_config(project_root)
    if configured is not None:
        return plan.level in configured
    return plan.level in _ALWAYS_REQUIRE


def render_card(plan: Plan) -> str:
    """The approval card the UI shows before execution."""
    lines = [f"Command:\n  {plan.command}", "This will:"]
    for r in plan.reads:
        lines.append(f"  - read {r}")
    for w in plan.writes:
        lines.append(f"  - create or modify {w}")
    if plan.target_environment:
        lines.append(f"  - target {plan.target_environment}")
    lines.append(f"Permission level:\n  {plan.level}")
    lines.append("Approve?")
    return "\n".join(lines)


def _next_id(approvals_dir: Path) -> int:
    existing = [p for p in approvals_dir.glob("approval-*.json")] if approvals_dir.is_dir() else []
    return len(existing) + 1


def record(
    project_root: Path,
    plan: Plan,
    *,
    approved: bool,
    approver: str,
    now: datetime,
) -> Path:
    """Write an approval decision record under audit/approvals/."""
    approvals_dir = Path(project_root) / WORKSPACE_DIRNAME / "audit" / "approvals"
    approvals_dir.mkdir(parents=True, exist_ok=True)
    record_path = approvals_dir / f"approval-{_next_id(approvals_dir):03d}.json"
    record_path.write_text(
        json.dumps(
            {
                "command": plan.command,
                "level": plan.level,
                "approved": approved,
                "approver": approver,
                "timestamp": now.isoformat(),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return record_path
