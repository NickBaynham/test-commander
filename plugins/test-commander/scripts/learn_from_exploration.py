#!/usr/bin/env python3
"""/tc:learn-from-exploration helper - Phase 8 Step 8.4.

Derives candidate lessons from the Phase-4 exploration record. Reads every
``<workspace>/exploration-notes/*.md`` (and ``sessions/*.md``), turns each
recorded **anomaly** into an ``anti-pattern`` candidate and each **coverage
gap** into a ``coverage-gap`` candidate, and appends them via the shared
``capture_lesson.append_lessons`` engine with
``exploration-notes/<file>:<line>`` provenance.

Deterministic via the injected clock (inherited from ``append_lessons``).

Exit codes:
    0 - lessons captured (or nothing new).
    2 - precondition failure (uninitialized workspace, no exploration notes).
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

SECTION_RE = re.compile(r"^##\s+(.+?)\s*$")
# Anomaly row: | <category> | <severity> | <page> | <evidence> |
ANOMALY_RE = re.compile(
    r"^\|\s*([\w-]+)\s*\|\s*(low|medium|high|critical)\s*\|\s*(\S+)\s*\|\s*(\S+)\s*\|",
    re.I,
)
BULLET_RE = re.compile(r"^-\s+(.+?)\s*$")


class ExplorationMissingError(LearnError):
    pass


def _note_files(workspace: Path) -> list[Path]:
    files: list[Path] = []
    for sub in ("exploration-notes", "sessions"):
        d = workspace / sub
        if d.is_dir():
            files.extend(p for p in sorted(d.glob("*.md")) if p.name != "README.md")
    return files


def _lessons_from_note(path: Path, rel: str) -> list[Lesson]:
    lessons: list[Lesson] = []
    section = ""
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        header = SECTION_RE.match(line)
        if header:
            section = header.group(1).lower()
            continue
        if "anomal" in section:
            m = ANOMALY_RE.match(line)
            if m:
                category, severity, page, _ev = (g.strip() for g in m.groups())
                lessons.append(
                    Lesson(
                        source="/tc:learn-from-exploration",
                        origin=f"{rel}:{lineno}",
                        category="anti-pattern",
                        severity=severity.lower(),
                        summary=f"anomaly {category} on {page}",
                        body=(
                            f"A {severity.lower()}-severity {category} anomaly was observed on "
                            f"{page}. Recurring anti-pattern: add a guard or a scenario that "
                            f"catches it."
                        ),
                    )
                )
        elif "coverage" in section:
            m = BULLET_RE.match(line)
            if m:
                gap = m.group(1)
                lessons.append(
                    Lesson(
                        source="/tc:learn-from-exploration",
                        origin=f"{rel}:{lineno}",
                        category="coverage-gap",
                        severity="medium",
                        summary=f"coverage gap: {gap[:80]}",
                        body=f"Coverage gap from exploration: {gap}",
                    )
                )
    return lessons


def learn_from_exploration(project_root: Path, *, now: datetime | None = None) -> int:
    project_root = Path(project_root)
    workspace = workspace_dir(project_root)
    now = now or datetime.now()
    notes = _note_files(workspace)
    if not notes:
        raise ExplorationMissingError(
            "no exploration notes found under exploration-notes/. Run /tc:explore first."
        )
    lessons: list[Lesson] = []
    for path in notes:
        rel = str(path.relative_to(workspace))
        lessons.extend(_lessons_from_note(path, rel))
    return append_lessons(workspace, lessons, now)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Derive candidate lessons from exploration-notes/ (anomalies and "
            "coverage gaps) into learning/lessons-inbox.md."
        ),
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    parser.add_argument("--now", default=None, help="Injected clock (ISO 8601) for determinism.")
    args = parser.parse_args(argv if argv is not None else None)
    project_root = Path(args.project_root).resolve()
    now = datetime.fromisoformat(args.now) if args.now else None

    try:
        appended = learn_from_exploration(project_root, now=now)
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ExplorationMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"captured: {appended} new exploration-derived lesson(s) into learning/lessons-inbox.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
