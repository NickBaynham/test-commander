#!/usr/bin/env python3
"""Test Commander journal — append and summarize.

One file per day under `.test-commander/journal/YYYY-MM-DD.md`. Each entry is
an H2 timestamp heading followed by Markdown body text. AI-generated
summaries are out of scope for Step 1.4 (deferred to Phase 8, learning loop).
"""

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"
JOURNAL_DIRNAME = "journal"
DAY_FILE_FMT = "%Y-%m-%d.md"
TIMESTAMP_FMT = "%Y-%m-%dT%H:%M:%SZ"
ENTRY_HEADING_RE = re.compile(r"^##\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\s*$")


@dataclass(frozen=True)
class Entry:
    timestamp: datetime
    body: str
    source_path: Path


@dataclass(frozen=True)
class AppendResult:
    path: Path
    timestamp: datetime


@dataclass(frozen=True)
class SummaryResult:
    entries: list[Entry]
    range_start: date | None
    range_end: date | None


def _journal_dir(workspace: Path) -> Path:
    return Path(workspace) / JOURNAL_DIRNAME


def _validate_body(body: str) -> None:
    if not isinstance(body, str) or not body.strip():
        raise ValueError("journal entry body must be a non-empty, non-whitespace string")
    for line in body.splitlines():
        if ENTRY_HEADING_RE.match(line):
            raise ValueError(
                "journal entry body must not contain an H2 timestamp heading "
                "matching '## YYYY-MM-DDTHH:MM:SSZ'"
            )


def append(
    workspace: Path,
    body: str,
    timestamp: datetime | None = None,
) -> AppendResult:
    """Append a timestamped entry to today's journal day file.

    Raises:
        FileNotFoundError: workspace is not an existing directory (run /tc:init).
        ValueError: body is empty or contains a structural conflict.
    """
    workspace = Path(workspace)
    if not workspace.is_dir():
        raise FileNotFoundError(
            f"workspace not initialized at {workspace}; run /tc:init"
        )
    _validate_body(body)
    ts = timestamp or datetime.now(UTC)
    if ts.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    journal_dir = _journal_dir(workspace)
    journal_dir.mkdir(parents=True, exist_ok=True)
    day_file = journal_dir / ts.strftime(DAY_FILE_FMT)
    is_new = not day_file.exists()
    with day_file.open("a", encoding="utf-8") as f:
        if is_new:
            f.write(f"# {ts.strftime('%Y-%m-%d')}\n\n")
        f.write(f"## {ts.strftime(TIMESTAMP_FMT)}\n\n{body.strip()}\n\n")
    return AppendResult(path=day_file, timestamp=ts)


def _parse_day_file(path: Path) -> list[Entry]:
    text = path.read_text(encoding="utf-8")
    entries: list[Entry] = []
    current_ts: datetime | None = None
    current_body: list[str] = []
    for line in text.splitlines():
        match = ENTRY_HEADING_RE.match(line)
        if match:
            if current_ts is not None:
                entries.append(
                    Entry(
                        timestamp=current_ts,
                        body="\n".join(current_body).strip(),
                        source_path=path,
                    )
                )
            current_ts = datetime.strptime(match.group(1), TIMESTAMP_FMT).replace(tzinfo=UTC)
            current_body = []
        elif current_ts is not None:
            current_body.append(line)
    if current_ts is not None:
        entries.append(
            Entry(
                timestamp=current_ts,
                body="\n".join(current_body).strip(),
                source_path=path,
            )
        )
    return entries


def summarize(
    workspace: Path,
    start: date | None = None,
    end: date | None = None,
) -> SummaryResult:
    """Return chronological entries within [start, end] (inclusive)."""
    workspace = Path(workspace)
    journal_dir = _journal_dir(workspace)
    if not journal_dir.is_dir():
        return SummaryResult(entries=[], range_start=start, range_end=end)
    entries: list[Entry] = []
    for path in sorted(journal_dir.glob("*.md")):
        if path.name == "README.md":
            continue
        entries.extend(_parse_day_file(path))
    if start is not None:
        entries = [e for e in entries if e.timestamp.date() >= start]
    if end is not None:
        entries = [e for e in entries if e.timestamp.date() <= end]
    entries.sort(key=lambda e: e.timestamp)
    return SummaryResult(entries=entries, range_start=start, range_end=end)


def _parse_date_arg(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Test Commander journal.")
    parser.add_argument(
        "--target",
        type=Path,
        default=Path.cwd(),
        help="Project root (default: current directory).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_append = sub.add_parser("append", help="Append a timestamped entry.")
    p_append.add_argument("body")

    p_summary = sub.add_parser("summarize", help="Print chronological summary.")
    p_summary.add_argument("--from", dest="from_date", type=_parse_date_arg)
    p_summary.add_argument("--to", dest="to_date", type=_parse_date_arg)

    args = parser.parse_args(argv)
    workspace = args.target / WORKSPACE_DIRNAME

    if args.command == "append":
        try:
            result = append(workspace, args.body)
        except (ValueError, FileNotFoundError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"entry: {result.timestamp.strftime(TIMESTAMP_FMT)}")
        print(f"file:  {result.path}")
        return 0

    if args.command == "summarize":
        summary = summarize(workspace, start=args.from_date, end=args.to_date)
        if not summary.entries:
            print("(no journal entries)")
            return 0
        for entry in summary.entries:
            print(f"## {entry.timestamp.strftime(TIMESTAMP_FMT)}")
            print()
            print(entry.body)
            print()
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
