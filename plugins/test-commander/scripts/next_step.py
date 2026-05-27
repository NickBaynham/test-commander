#!/usr/bin/env python3
"""`/tc:next` heuristics engine.

Reads a `WorkspaceSnapshot` from `workspace_state.snapshot()` and returns a
ranked list of `Recommendation`s. Rules are documented in
`plugins/test-commander/skills/tc-core/methodology/next-step-inference.md` —
this file is the executable counterpart.

The top recommendation is what `/tc:next` surfaces as the `next:` line; the
remaining matches follow as `followups`.
"""

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import workspace_state
from workspace_state import WorkspaceSnapshot

WORKSPACE_DIRNAME = workspace_state.WORKSPACE_DIRNAME


@dataclass(frozen=True)
class Recommendation:
    command: str
    explanation: str
    phase: str
    priority: int


# Each entry: (id, predicate, command, explanation, owning_phase, priority).
# Drift between this list and next-step-inference.md is caught by code
# review; every rule documented there must have an entry here.
_RULES: list[tuple[str, Callable[[WorkspaceSnapshot], bool], str, str, str, int]] = [
    (
        "R1",
        lambda s: not s.exists,
        "/tc:init",
        "Initialize the Test Commander workspace inside this project.",
        "1",
        1,
    ),
    (
        "R2",
        lambda s: s.exists and s.phase_status.get("1") == "not_started",
        "edit .test-commander/project.md (and config.yaml, methodology.md)",
        (
            "Fill in project-specific metadata in `.test-commander/project.md`, "
            "`config.yaml`, and `methodology.md`. /tc:init copies the template "
            "verbatim; these three files are how you tell Test Commander about "
            "your project."
        ),
        "1",
        2,
    ),
    (
        "R3",
        lambda s: s.exists and s.phase_status.get("2") == "not_started",
        "/tc:review-requirements",
        (
            "Review the project's requirements: testability, clarity, completeness. "
            "Surfaces gaps and ambiguity before any test work begins."
        ),
        "2",
        3,
    ),
    (
        "R4",
        lambda s: s.exists and s.phase_status.get("3") == "not_started",
        "/tc:learn-from-docs",
        (
            "Build the project knowledge base by ingesting docs, specs, code, and "
            "APIs. Subsequent commands rely on this knowledge."
        ),
        "3",
        4,
    ),
    (
        "R5",
        lambda s: s.exists and s.phase_status.get("4") == "not_started",
        "/tc:create-charter",
        (
            "Start a session-based exploratory testing charter to capture "
            "observations, test ideas, and risks."
        ),
        "4",
        5,
    ),
    (
        "R6",
        lambda s: s.exists and s.phase_status.get("5") == "not_started",
        "/tc:generate-bdd",
        (
            "Generate BDD scenarios from requirements and exploration. Maintain "
            "traceability from requirement to scenario to automation."
        ),
        "5",
        6,
    ),
    (
        "R7",
        lambda s: s.exists and s.phase_status.get("6") == "not_started",
        "/tc:automation-plan",
        (
            "Plan which BDD scenarios to automate. Apply the suitability rubric: "
            "business criticality, repeatability, determinism, maintenance cost, "
            "bug detection value."
        ),
        "6",
        7,
    ),
    (
        "R8",
        lambda s: s.exists and s.phase_status.get("7") == "not_started",
        "/tc:run",
        (
            "Run the automated test suite and collect evidence: screenshots, "
            "traces, logs. Failures feed the next quality report."
        ),
        "7",
        8,
    ),
    (
        "R9",
        lambda s: s.exists and s.phase_status.get("8") == "not_started",
        "/tc:learn",
        (
            "Capture lessons learned from this round of work. Candidates land in "
            "`learning/lessons-inbox.md` for human review before promotion."
        ),
        "8",
        9,
    ),
    (
        "R10",
        lambda s: s.exists and all(
            s.phase_status.get(p) == "in_progress"
            for p in ("1", "2", "3", "4", "5", "6", "7", "8")
        ),
        "/tc:report",
        (
            "All MVP phases have content. Keep the live quality report fresh and "
            "assess release readiness with /tc:quality-gate."
        ),
        "7",
        10,
    ),
]


def recommendations(snapshot: WorkspaceSnapshot) -> list[Recommendation]:
    """Return all matching recommendations, sorted by priority (most urgent first)."""
    matches = [
        Recommendation(cmd, expl, phase, prio)
        for _rid, pred, cmd, expl, phase, prio in _RULES
        if pred(snapshot)
    ]
    matches.sort(key=lambda r: r.priority)
    return matches


def next_step(snapshot: WorkspaceSnapshot) -> Recommendation | None:
    """Return only the top recommendation, or None when no rule matched."""
    matches = recommendations(snapshot)
    return matches[0] if matches else None


def recommendations_for(project_root: Path) -> list[Recommendation]:
    snap = workspace_state.snapshot(project_root)
    return recommendations(snap)


def next_step_for(project_root: Path) -> Recommendation | None:
    snap = workspace_state.snapshot(project_root)
    return next_step(snap)


def format_recommendations(recs: list[Recommendation]) -> str:
    """Render a grep-friendly report. First line is always `next: ...`."""
    if not recs:
        return "next: (no recommendations — workspace state could not be classified)"
    lines = []
    top = recs[0]
    lines.append(f"next: {top.command}  (Phase {top.phase})")
    lines.append(f"  {top.explanation}")
    if len(recs) > 1:
        lines.append("")
        lines.append("followups:")
        for r in recs[1:]:
            lines.append(f"  {r.command}  (Phase {r.phase})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recommend the next Test Commander command for a workspace state.",
    )
    parser.add_argument(
        "target",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Project root (default: current directory).",
    )
    args = parser.parse_args(argv)
    recs = recommendations_for(args.target)
    print(format_recommendations(recs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
