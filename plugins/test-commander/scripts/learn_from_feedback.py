#!/usr/bin/env python3
"""/tc:learn-from-feedback helper - Phase 8 Step 8.5.

Derives candidate lessons from resolved human feedback. Reads
``<workspace>/requirements/open-questions.md`` entries carrying a ``_Resolved:``
marker, plus an optional ``<workspace>/documents/uploaded/feedback.md``, and
turns each into a ``process`` ``tc-lesson/v1`` candidate via the shared
``capture_lesson.append_lessons`` engine with ``path:line`` provenance.

Design reference: ``superpowers:receiving-code-review`` (lesson intake).

Unlike the other capture commands, **no feedback is not an error** — open
questions exist throughout a project and may simply have none resolved yet — so
the helper is a no-op (exit 0, nothing appended) when there is nothing resolved.

Deterministic via the injected clock (inherited from ``append_lessons``).

Exit codes:
    0 - lessons captured (or nothing to capture).
    2 - precondition failure (uninitialized workspace).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from capture_lesson import (
    Lesson,
    UninitializedWorkspaceError,
    append_lessons,
    workspace_dir,
)

# A resolved open question: a `- [...]` line carrying a `_Resolved: ...` marker.
RESOLVED_RE = re.compile(r"^-\s+\[([^\]]+)\].*?_Resolved:\s*(.+?)_?\s*$", re.I)
BULLET_RE = re.compile(r"^-\s+(.+?)\s*$")
STUB_MARKER = "_(empty until"


def _resolved_open_questions(workspace: Path) -> list[Lesson]:
    path = workspace / "requirements" / "open-questions.md"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    if STUB_MARKER in text:
        return []
    rel = "requirements/open-questions.md"
    lessons: list[Lesson] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        m = RESOLVED_RE.match(line)
        if not m:
            continue
        source_id, resolution = m.group(1).strip(), m.group(2).strip().rstrip("_").strip()
        lessons.append(
            Lesson(
                source="/tc:learn-from-feedback",
                origin=f"{rel}:{lineno}",
                category="process",
                severity="low",
                summary=f"resolved feedback on {source_id}",
                body=f"Resolved open question ({source_id}): {resolution}",
            )
        )
    return lessons


def _uploaded_feedback(workspace: Path) -> list[Lesson]:
    path = workspace / "documents" / "uploaded" / "feedback.md"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    if STUB_MARKER in text:
        return []
    rel = "documents/uploaded/feedback.md"
    lessons: list[Lesson] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        m = BULLET_RE.match(line)
        if not m:
            continue
        note = m.group(1)
        lessons.append(
            Lesson(
                source="/tc:learn-from-feedback",
                origin=f"{rel}:{lineno}",
                category="heuristic",
                severity="low",
                summary=f"feedback: {note[:80]}",
                body=f"Human feedback: {note}",
            )
        )
    return lessons


def learn_from_feedback(project_root: Path, *, now: datetime | None = None) -> int:
    project_root = Path(project_root)
    workspace = workspace_dir(project_root)
    now = now or datetime.now()
    lessons = _resolved_open_questions(workspace) + _uploaded_feedback(workspace)
    if not lessons:
        return 0  # no feedback is not an error
    return append_lessons(workspace, lessons, now)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Derive candidate lessons from resolved feedback (open-questions.md "
            "and documents/uploaded/feedback.md) into learning/lessons-inbox.md."
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
        appended = learn_from_feedback(project_root, now=now)
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"captured: {appended} new feedback-derived lesson(s) into learning/lessons-inbox.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
