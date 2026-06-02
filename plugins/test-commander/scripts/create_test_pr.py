#!/usr/bin/env python3
"""/tc:create-test-pr - Phase 13 Step 13.4.

Open a clearly-labeled test pull request through the Phase-10.5 pipeline, gated
by the configured autonomy mode. A below-threshold mode (0-2) cannot open a PR.
At mode 3+, the code-write generation runs through the pipeline (auto-approved by
the autonomy gate, recorded in the audit log); the PR bundle is labeled so it is
never mistaken for a human change. Continuous mode never bypasses approvals.

Self-contained (D18).

Exit codes:
    0 - PR opened, or held/refused with a clear reason.
    2 - precondition failure (uninitialized workspace).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cq_support import cq_dir, load_config, require_workspace, resolve_repo_root, write_json


def create_pr(
    project_root: Path,
    *,
    gap_feature: str,
    mode: int | None = None,
    role: str = "Automation Engineer",
    approve: bool = False,
    approver: str | None = None,
    adapter=None,
) -> dict:
    require_workspace(project_root)
    config = load_config(project_root)
    mode = config["autonomy_mode"] if mode is None else mode
    label = config["pr_label"]

    resolve_repo_root()
    from agent_adapters.mock_agent import MockAgentAdapter
    from governance import pipeline

    from continuous.autonomy import auto_approves, can_open_pr, mode_name

    name = mode_name(mode)
    if not can_open_pr(mode):
        return {"opened": False, "label": label,
                "reason": f"mode {mode} ({name}) cannot open pull requests"}

    auto = auto_approves(mode, "code-write")
    res = pipeline.handle_request(
        f"generate playwright tests for {gap_feature}",
        role=role,
        project_root=Path(project_root),
        adapter=adapter or MockAgentAdapter(),
        approve=approve or auto,
        approver=approver or (f"autonomy:{name}" if auto else None),
        user="continuous-agent",
    )
    if not res.executed:
        return {"opened": False, "label": label,
                "requires_approval": res.requires_approval,
                "reason": res.reason or "held for human approval"}

    pr = {
        "opened": True,
        "label": label,
        "feature": gap_feature,
        "title": f"[{label}] Add tests for {gap_feature}",
        "mode": name,
        "approver": res.approved and (approver or f"autonomy:{name}") or approver,
    }
    write_json(cq_dir(project_root) / "pr.json", pr)
    return pr


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Open a labeled test PR (gated by autonomy mode).")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root.")
    parser.add_argument("--feature", required=True, help="The gap feature to add tests for.")
    parser.add_argument("--mode", type=int, default=None, help="Override the autonomy mode.")
    args = parser.parse_args(argv if argv is not None else None)
    try:
        result = create_pr(
            Path(args.project_root).resolve(), gap_feature=args.feature, mode=args.mode
        )
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if result["opened"]:
        print(f"create-test-pr: opened {result['title']}")
    else:
        print(f"create-test-pr: not opened ({result['reason']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
