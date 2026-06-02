#!/usr/bin/env python3
"""/tc:learn-from-failures helper - Phase 8 Step 8.3.

Derives candidate lessons from the Phase-7 test-run triage. Reads every
``<workspace>/runs/<RUN-ID>/analysis.md`` (the ``/tc:analyze-results`` output),
turns each triaged non-passed row into a ``tc-lesson/v1`` candidate, and appends
them via the shared ``capture_lesson.append_lessons`` engine with
``runs/<RUN-ID>/analysis.md:<line>`` provenance.

Design reference: ``superpowers:systematic-debugging`` (root-cause learning).

Mechanical classification mapping (analysis category -> lesson category):

    product-defect -> product-defect-pattern
    flaky          -> flaky-pattern
    test-defect    -> anti-pattern
    environment    -> process

Deterministic via the injected clock (inherited from ``append_lessons``).

Exit codes:
    0 - lessons captured (or nothing new).
    2 - precondition failure (uninitialized workspace, no analysis).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from capture_lesson import (
    LearnError,
    Lesson,
    UninitializedWorkspaceError,
    append_lessons,
    workspace_dir,
)

CATEGORY_MAP: dict[str, str] = {
    "product-defect": "product-defect-pattern",
    "flaky": "flaky-pattern",
    "test-defect": "anti-pattern",
    "environment": "process",
}

# analysis.md triage row: | REQ-NNN | CS-NNN-NNN | scenario | result | classification |
ROW_RE = re.compile(
    r"^\|\s*(REQ-\d+)\s*\|\s*(CS-\d{3}-\d{3})\s*\|\s*([^|]+?)\s*\|\s*(\w+)\s*\|\s*([\w-]+)\s*\|"
)

MESSAGE: dict[str, str] = {
    "product-defect-pattern": (
        "recurring product-defect - confirm the expected behavior and add an explicit "
        "assertion to the regression set"
    ),
    "flaky-pattern": (
        "recurring flaky test - investigate the non-determinism (waits, ordering, state) "
        "before trusting the result"
    ),
    "anti-pattern": (
        "recurring test-defect - fix the test (locator/selector/strict-mode), not the product"
    ),
    "process": (
        "recurring environment failure - stabilize or document the target environment"
    ),
}


class AnalysisMissingError(LearnError):
    pass


def _analysis_files(workspace: Path, run_id: str | None) -> list[Path]:
    runs = workspace / "runs"
    if run_id:
        path = runs / run_id / "analysis.md"
        return [path] if path.is_file() else []
    return sorted(runs.glob("*/analysis.md")) if runs.is_dir() else []


def _lessons_from_analysis(path: Path, rel: str) -> list[Lesson]:
    lessons: list[Lesson] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        m = ROW_RE.match(line)
        if not m:
            continue
        req, cs, scenario, _result, classification = (g.strip() for g in m.groups())
        category = CATEGORY_MAP.get(classification)
        if category is None:
            continue
        lessons.append(
            Lesson(
                source="/tc:learn-from-failures",
                origin=f"{rel}:{lineno}",
                category=category,
                severity="medium",
                summary=f"{classification}: scenario '{scenario}' ({req}/{cs})",
                body=(
                    f"Scenario '{scenario}' ({req} / {cs}) is a {MESSAGE[category]}."
                ),
            )
        )
    return lessons


def learn_from_failures(
    project_root: Path, *, run_id: str | None = None, now: datetime | None = None
) -> int:
    project_root = Path(project_root)
    workspace = workspace_dir(project_root)
    now = now or datetime.now()
    analyses = _analysis_files(workspace, run_id)
    if not analyses:
        raise AnalysisMissingError(
            "no run analysis found under runs/<RUN-ID>/analysis.md. "
            "Run /tc:analyze-results first."
        )
    lessons: list[Lesson] = []
    for path in analyses:
        rel = str(path.relative_to(workspace))
        lessons.extend(_lessons_from_analysis(path, rel))
    return append_lessons(workspace, lessons, now)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Derive candidate lessons from runs/<RUN-ID>/analysis.md (the Phase-7 "
            "triage) into learning/lessons-inbox.md."
        ),
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    parser.add_argument("--run-id", default=None, help="A single RUN-ID (default: all runs).")
    parser.add_argument("--now", default=None, help="Injected clock (ISO 8601) for determinism.")
    args = parser.parse_args(argv if argv is not None else None)
    project_root = Path(args.project_root).resolve()
    now = datetime.fromisoformat(args.now) if args.now else None

    try:
        appended = learn_from_failures(project_root, run_id=args.run_id, now=now)
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except AnalysisMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"captured: {appended} new failure-derived lesson(s) into learning/lessons-inbox.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
