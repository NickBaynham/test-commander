#!/usr/bin/env python3
"""/tc:review-lessons helper - Phase 8 Step 8.6.

Reviews the candidate lessons in ``<workspace>/learning/lessons-inbox.md`` and
sorts each into one of three governance buckets, moving it to the matching
``learning/`` file with its ``status`` updated and clearing the inbox.

The universal review rubric (precedence, most specific first):

1. **needs-human-review** - ``severity: high``. A high-impact lesson's scope
   needs a human's judgment before it becomes guidance.
2. **rejected** - the candidate's ``summary`` already appears in
   ``accepted-lessons.md``; it duplicates an accepted lesson and adds nothing.
3. **accepted** - everything else: provenanced, not high-severity, novel.

The mechanical rubric decides the confident buckets; Claude adds the judgment
layer (is a `needs-human-review` lesson a one-off or systemic; is a near-duplicate
genuinely redundant). **Idempotent**: a re-run over an already-cleared inbox is a
no-op. A fresh workspace whose inbox is still the template stub is refused
(nothing has been captured).

Exit codes:
    0 - inbox reviewed (or already empty).
    2 - precondition failure (uninitialized workspace, inbox still the stub).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from capture_lesson import STUB_MARKER, UninitializedWorkspaceError, workspace_dir

BLOCK_RE = re.compile(
    r"^---\n(?P<fm>.*?)\n---\n(?P<body>.*?)(?=^---\n|\Z)", re.DOTALL | re.MULTILINE
)
FIELD_RE = re.compile(r"^(\w+):\s*(.*)$")
SUMMARY_RE = re.compile(r"^summary:\s*(.*)$", re.MULTILINE)

BUCKET_FILE = {
    "accepted": "accepted-lessons.md",
    "rejected": "rejected-lessons.md",
    "needs-human-review": "needs-human-review.md",
}
BUCKET_HEADER = {
    "accepted": "# Accepted Lessons\n\nReviewed lessons promoted into project guidance.\n",
    "rejected": "# Rejected Lessons\n\nReviewed lessons rejected, with reasons.\n",
    "needs-human-review": (
        "# Lessons Needing Human Review\n\n"
        "Lessons the automated review could not classify confidently.\n"
    ),
}
INBOX_EMPTY = (
    "# Lessons Inbox\n\nNewly captured candidate lessons awaiting review. Each block is a "
    "`tc-lesson/v1` record; `/tc:review-lessons` sorts them into accepted / rejected / "
    "needs-human-review.\n"
)
CANONICAL_KEYS = (
    "schema", "id", "source", "origin", "category", "severity", "status",
    "captured_at", "summary",
)


class ReviewError(Exception):
    pass


class NoCandidatesError(ReviewError):
    pass


@dataclass
class ReviewOutcome:
    reviewed: int = 0
    buckets: dict[str, int] = field(default_factory=lambda: {b: 0 for b in BUCKET_FILE})


def _parse_fields(fm_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in fm_text.splitlines():
        m = FIELD_RE.match(line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return value


def _accepted_summaries(text: str) -> set[str]:
    return {_unquote(m.strip()) for m in SUMMARY_RE.findall(text)}


def classify(fields: dict[str, str], accepted_summaries: set[str]) -> str:
    if fields.get("severity", "").lower() == "high":
        return "needs-human-review"
    if _unquote(fields.get("summary", "")) in accepted_summaries:
        return "rejected"
    return "accepted"


def _render_block(fields: dict[str, str], body: str) -> str:
    lines = ["---"]
    for key in CANONICAL_KEYS:
        if key in fields:
            lines.append(f"{key}: {fields[key]}")
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body.strip() + "\n"


def _append_block(path: Path, header: str, block: str) -> None:
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    if not existing.strip() or STUB_MARKER in existing:
        existing = header
    body = existing.rstrip("\n") + "\n\n" + block
    path.write_text(body.rstrip("\n") + "\n", encoding="utf-8")


def review_lessons(project_root: Path) -> ReviewOutcome:
    project_root = Path(project_root)
    workspace = workspace_dir(project_root)
    learning = workspace / "learning"
    inbox = learning / "lessons-inbox.md"
    text = inbox.read_text(encoding="utf-8") if inbox.is_file() else ""

    blocks = [(m.group("fm"), m.group("body")) for m in BLOCK_RE.finditer(text)]
    candidates = [(fm, body) for fm, body in blocks
                  if _parse_fields(fm).get("schema") == "tc-lesson/v1"]
    if not candidates:
        if not text.strip() or STUB_MARKER in text:
            raise NoCandidatesError(
                "no candidate lessons in learning/lessons-inbox.md. Run /tc:learn "
                "(or a /tc:learn-from-* command) first."
            )
        return ReviewOutcome()  # already-cleared inbox: idempotent no-op

    accepted_summaries = _accepted_summaries(
        (learning / "accepted-lessons.md").read_text(encoding="utf-8")
        if (learning / "accepted-lessons.md").is_file() else ""
    )

    outcome = ReviewOutcome()
    for fm_text, body in candidates:
        fields = _parse_fields(fm_text)
        bucket = classify(fields, accepted_summaries)
        fields["status"] = bucket
        if bucket == "accepted":
            accepted_summaries.add(_unquote(fields.get("summary", "")))
        _append_block(learning / BUCKET_FILE[bucket], BUCKET_HEADER[bucket],
                      _render_block(fields, body))
        outcome.reviewed += 1
        outcome.buckets[bucket] += 1

    inbox.write_text(INBOX_EMPTY, encoding="utf-8")
    return outcome


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Classify the candidate lessons in learning/lessons-inbox.md into "
            "accepted / rejected / needs-human-review and clear the inbox."
        ),
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    args = parser.parse_args(argv if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        outcome = review_lessons(project_root)
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except NoCandidatesError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"reviewed: {outcome.reviewed} candidate(s) - "
        f"accepted {outcome.buckets['accepted']}, rejected {outcome.buckets['rejected']}, "
        f"needs-human-review {outcome.buckets['needs-human-review']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
