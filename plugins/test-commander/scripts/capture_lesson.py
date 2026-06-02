#!/usr/bin/env python3
"""/tc:learn helper - Phase 8 Step 8.2.

The foundational capture command of the learning loop. Appends a candidate
lesson to ``<workspace>/learning/lessons-inbox.md`` from a freeform ``--note``
(or, for the ``/tc:learn-from-*`` commands, from a derived ``Lesson``), rendered
as a ``tc-lesson/v1`` block carrying ``path:line`` provenance and a stable
``LESSON-NNN`` id.

This module owns the **shared inbox engine** every capture command reuses:

- ``Lesson`` - the candidate dataclass (without an id; the engine allocates it).
- ``parse_inbox`` - parse the inbox into a list of frontmatter dicts.
- ``append_lessons(workspace, lessons, now)`` - allocate monotonic ids,
  deduplicate by ``(source, origin, summary)`` (the Phase-2 open-questions
  contract), and append the new blocks. Returns the count appended.

**Injected-clock determinism**: ``captured_at`` and (transitively) the inbox
bytes come from an injected ``now``; tests pass a fixed timestamp so the inbox
is byte-stable, and a re-run that adds no new lessons leaves it unchanged.

Per D18 the helper ships inside the plugin. Per D19 the category taxonomy is
universal.

Exit codes:
    0 - lesson captured (or nothing new to add).
    2 - precondition failure (uninitialized workspace).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

WORKSPACE_DIRNAME = ".test-commander"
STUB_MARKER = "_(empty until"

# The universal lesson taxonomy (D19).
CATEGORIES: tuple[str, ...] = (
    "product-defect-pattern",
    "flaky-pattern",
    "coverage-gap",
    "process",
    "heuristic",
    "anti-pattern",
)
SEVERITIES: tuple[str, ...] = ("low", "medium", "high")

INBOX_HEADER = (
    "# Lessons Inbox\n\n"
    "Newly captured candidate lessons awaiting review. Each block is a "
    "`tc-lesson/v1` record; `/tc:review-lessons` sorts them into accepted / "
    "rejected / needs-human-review.\n"
)

ID_RE = re.compile(r"^id:\s*LESSON-(\d+)\s*$", re.MULTILINE)
BLOCK_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL | re.MULTILINE)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class LearnError(Exception):
    pass


class UninitializedWorkspaceError(LearnError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Lesson:
    """A candidate lesson before it is assigned an id and rendered."""

    source: str
    origin: str
    category: str
    severity: str
    summary: str
    body: str

    def dedup_key(self) -> tuple[str, str, str]:
        return (self.source, self.origin, self.summary)


# ---------------------------------------------------------------------------
# Workspace IO
# ---------------------------------------------------------------------------


def workspace_dir(project_root: Path) -> Path:
    ws = project_root / WORKSPACE_DIRNAME
    if not ws.is_dir():
        raise UninitializedWorkspaceError(
            f"not a Test Commander workspace: {project_root} "
            f"(no {WORKSPACE_DIRNAME}/). Run /tc:init first."
        )
    return ws


def parse_inbox(text: str) -> list[dict]:
    """Parse the inbox into a list of lesson frontmatter mappings."""
    lessons: list[dict] = []
    for fm_text in BLOCK_RE.findall(text):
        data = yaml.safe_load(fm_text)
        if isinstance(data, dict) and data.get("schema") == "tc-lesson/v1":
            lessons.append(data)
    return lessons


def _next_id(existing_text: str) -> int:
    ids = [int(m) for m in ID_RE.findall(existing_text)]
    return (max(ids) + 1) if ids else 1


def _yaml_str(value: str) -> str:
    """Double-quote a free-text scalar so an embedded ``: `` or ``#`` cannot
    break the YAML frontmatter (the Phase 4 Step 4.8 embedded-key-value guard)."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _render_block(lesson: Lesson, lesson_id: str, now: datetime) -> str:
    return (
        "---\n"
        "schema: tc-lesson/v1\n"
        f"id: {lesson_id}\n"
        f"source: {lesson.source}\n"
        f"origin: {lesson.origin}\n"
        f"category: {lesson.category}\n"
        f"severity: {lesson.severity}\n"
        "status: candidate\n"
        f"captured_at: {now.isoformat()}\n"
        f"summary: {_yaml_str(lesson.summary)}\n"
        "---\n\n"
        f"{lesson.body.rstrip()}\n"
    )


# ---------------------------------------------------------------------------
# Shared engine
# ---------------------------------------------------------------------------


def append_lessons(workspace: Path, lessons: list[Lesson], now: datetime) -> int:
    """Allocate ids, dedup by (source, origin, summary), append new blocks.

    The shared engine every capture command reuses. Returns the count appended.
    """
    inbox = workspace / "learning" / "lessons-inbox.md"
    inbox.parent.mkdir(parents=True, exist_ok=True)
    existing = inbox.read_text(encoding="utf-8") if inbox.is_file() else ""
    if not existing.strip() or STUB_MARKER in existing:
        existing = INBOX_HEADER

    seen = {
        (d.get("source", ""), d.get("origin", ""), d.get("summary", ""))
        for d in parse_inbox(existing)
    }
    next_id = _next_id(existing)
    new_blocks: list[str] = []
    for lesson in lessons:
        if lesson.dedup_key() in seen:
            continue
        seen.add(lesson.dedup_key())
        new_blocks.append(_render_block(lesson, f"LESSON-{next_id:03d}", now))
        next_id += 1

    if not new_blocks:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        inbox.write_text(existing, encoding="utf-8")
        return 0
    body = existing.rstrip("\n") + "\n\n" + "\n".join(new_blocks)
    inbox.write_text(body.rstrip("\n") + "\n", encoding="utf-8")
    return len(new_blocks)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def learn(
    project_root: Path,
    *,
    note: str,
    origin: str = "manual",
    category: str = "process",
    severity: str = "medium",
    summary: str | None = None,
    now: datetime | None = None,
) -> int:
    project_root = Path(project_root)
    workspace = workspace_dir(project_root)
    now = now or datetime.now()  # injected in tests; wall clock in production
    if category not in CATEGORIES:
        category = "process"
    if severity not in SEVERITIES:
        severity = "medium"
    lesson = Lesson(
        source="/tc:learn",
        origin=origin,
        category=category,
        severity=severity,
        summary=summary or note.strip().splitlines()[0][:120],
        body=note,
    )
    return append_lessons(workspace, [lesson], now)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Append a candidate lesson (tc-lesson/v1) to "
            "learning/lessons-inbox.md from a freeform note."
        ),
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    parser.add_argument("--note", required=True, help="The lesson observation.")
    parser.add_argument(
        "--origin", default="manual", help="path:line provenance (default: manual)."
    )
    parser.add_argument(
        "--category", default="process", choices=CATEGORIES, help="Lesson category."
    )
    parser.add_argument(
        "--severity", default="medium", choices=SEVERITIES, help="Lesson severity."
    )
    parser.add_argument("--summary", default=None, help="One-line summary (default: first line).")
    parser.add_argument("--now", default=None, help="Injected clock (ISO 8601) for determinism.")
    args = parser.parse_args(argv if argv is not None else None)
    project_root = Path(args.project_root).resolve()
    now = datetime.fromisoformat(args.now) if args.now else None

    try:
        appended = learn(
            project_root, note=args.note, origin=args.origin, category=args.category,
            severity=args.severity, summary=args.summary, now=now,
        )
    except LearnError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"captured: {appended} new candidate lesson(s) into learning/lessons-inbox.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
