#!/usr/bin/env python3
"""/tc:promote-lessons helper - Phase 8 Step 8.7.

The one command that turns accepted lessons into project guidance — under a
human-approval gate. Reads ``<workspace>/learning/accepted-lessons.md`` and:

- **By default, proposes only**: writes ``learning/promotion-proposal.md`` (what
  *would* be promoted) and changes no guidance.
- **With ``--apply`` (the human's approval)**: moves each accepted non-core
  lesson into ``learning/promoted-guidance.md`` with ``status: promoted``, marks
  it promoted in ``accepted-lessons.md`` (so it is not re-promoted), and renders
  a ``learning/core-promotion-proposal.md`` entry for any ``core: true`` lesson
  (a proposal for a human to take upstream as a plugin PR — never auto-applied).

It writes **only** under the workspace ``learning/`` tree. It never edits Test
Commander's shipped methodology, commands, or templates, and never modifies
third-party installed skills (Open Question Q6). Every applied promotion is a
visible ``git diff``. **Idempotent**: an already-promoted lesson is skipped.

Exit codes:
    0 - proposed (or applied; or nothing to do).
    2 - precondition failure (uninitialized workspace, no accepted lessons).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from capture_lesson import STUB_MARKER, UninitializedWorkspaceError, workspace_dir

BLOCK_RE = re.compile(
    r"^---\n(?P<fm>.*?)\n---\n(?P<body>.*?)(?=^---\n|\Z)", re.DOTALL | re.MULTILINE
)
FIELD_RE = re.compile(r"^(\w+):\s*(.*)$")
CANONICAL_KEYS = (
    "schema", "id", "source", "origin", "category", "severity", "status", "core",
    "captured_at", "summary",
)

GUIDANCE_HEADER = (
    "# Promoted Guidance\n\n"
    "Accepted lessons promoted into project guidance under `/tc:promote-lessons "
    "--apply`. Every entry here is a visible git diff a human approved.\n"
)
CORE_HEADER = (
    "# Core Promotion Proposals\n\n"
    "Lessons that argue for a change to Test Commander's own shipped doctrine. "
    "These are proposals for a human to take upstream as a plugin PR — Test "
    "Commander never edits its shipped methodology automatically (Q6).\n"
)


class PromoteError(Exception):
    pass


class NoAcceptedError(PromoteError):
    pass


@dataclass
class PromoteOutcome:
    applied: bool
    promoted: int = 0
    core_proposed: int = 0
    proposal_path: Path | None = None


def _parse_fields(fm_text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in fm_text.splitlines():
        m = FIELD_RE.match(line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields


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


def promote(project_root: Path, *, apply: bool = False) -> PromoteOutcome:
    project_root = Path(project_root)
    workspace = workspace_dir(project_root)
    learning = workspace / "learning"
    accepted_path = learning / "accepted-lessons.md"
    text = accepted_path.read_text(encoding="utf-8") if accepted_path.is_file() else ""

    blocks = [(m.group("fm"), m.group("body")) for m in BLOCK_RE.finditer(text)]
    parsed = [(_parse_fields(fm), fm, body) for fm, body in blocks
              if _parse_fields(fm).get("schema") == "tc-lesson/v1"]
    pending = [(f, body) for f, _fm, body in parsed if f.get("status") == "accepted"]
    if not pending:
        if not text.strip() or STUB_MARKER in text:
            raise NoAcceptedError(
                "no accepted lessons in learning/accepted-lessons.md. "
                "Run /tc:review-lessons first."
            )
        return PromoteOutcome(applied=apply)  # all promoted already: idempotent no-op

    if not apply:
        proposal = learning / "promotion-proposal.md"
        lines = ["# Promotion proposal", "",
                 "_Proposed by `/tc:promote-lessons`. Re-run with `--apply` to promote "
                 "(the human-approval gate). No guidance changed yet._", "",
                 "| Lesson | Category | Scope | Summary |", "| --- | --- | --- | --- |"]
        for fields, _body in pending:
            scope = "core (upstream)" if fields.get("core") == "true" else "project guidance"
            lines.append(
                f"| {fields.get('id', '')} | {fields.get('category', '')} | {scope} | "
                f"{fields.get('summary', '').strip(chr(34))} |"
            )
        lines.append("")
        proposal.write_text("\n".join(lines), encoding="utf-8")
        return PromoteOutcome(applied=False, proposal_path=proposal)

    # --apply: the human gate is open.
    outcome = PromoteOutcome(applied=True)
    for fields, body in pending:
        if fields.get("core") == "true":
            _append_block(learning / "core-promotion-proposal.md", CORE_HEADER,
                          _render_block(fields, body))
            outcome.core_proposed += 1
        else:
            promoted = dict(fields, status="promoted")
            _append_block(learning / "promoted-guidance.md", GUIDANCE_HEADER,
                          _render_block(promoted, body))
            outcome.promoted += 1
        # Mark promoted in the accepted file so a re-apply skips it.
        old = _render_block(fields, body).rstrip("\n")
        new = _render_block(dict(fields, status="promoted"), body).rstrip("\n")
        text = text.replace(old, new)
    accepted_path.write_text(text, encoding="utf-8")
    return outcome


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Propose (default) or, with --apply, promote accepted lessons into "
            "learning/promoted-guidance.md. Writes only under learning/."
        ),
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Apply the promotion (the human-approval gate). Default: propose only.",
    )
    args = parser.parse_args(argv if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        outcome = promote(project_root, apply=args.apply)
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except NoAcceptedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if outcome.applied:
        print(
            f"promoted: {outcome.promoted} lesson(s) into learning/promoted-guidance.md; "
            f"{outcome.core_proposed} core proposal(s)"
        )
    else:
        where = outcome.proposal_path
        rel = where.relative_to(project_root) if where else "learning/promotion-proposal.md"
        print(f"proposed: see {rel} (re-run with --apply to promote)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
