"""Step 1.4 — journal helper tests.

Five cases per the plan: append to empty, append to existing, summarize
range, summarize empty, malformed entry refused.
"""

from datetime import UTC, date, datetime
from pathlib import Path

import journal
import pytest


def _make_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / ".test-commander"
    (ws / "journal").mkdir(parents=True)
    return ws


# 1. append to empty

def test_append_to_empty_journal(tmp_path):
    ws = _make_workspace(tmp_path)
    ts = datetime(2026, 5, 26, 14, 0, 0, tzinfo=UTC)
    result = journal.append(ws, "first entry", timestamp=ts)
    assert result.path == ws / "journal" / "2026-05-26.md"
    text = result.path.read_text(encoding="utf-8")
    # Day heading + timestamp heading + body
    assert "# 2026-05-26" in text
    assert "## 2026-05-26T14:00:00Z" in text
    assert "first entry" in text


# 2. append to existing day file

def test_append_to_existing_day(tmp_path):
    ws = _make_workspace(tmp_path)
    ts1 = datetime(2026, 5, 26, 14, 0, 0, tzinfo=UTC)
    ts2 = datetime(2026, 5, 26, 15, 30, 0, tzinfo=UTC)
    r1 = journal.append(ws, "first", timestamp=ts1)
    r2 = journal.append(ws, "second", timestamp=ts2)
    assert r1.path == r2.path
    text = r1.path.read_text(encoding="utf-8")
    # Both entries present
    assert text.count("## 2026-05-26T") == 2
    assert "first" in text
    assert "second" in text
    # Chronological order preserved
    assert text.index("first") < text.index("second")
    # Single day heading
    assert text.count("# 2026-05-26\n") == 1


# 3. summarize with range filter

def test_summarize_range(tmp_path):
    ws = _make_workspace(tmp_path)
    journal.append(ws, "May 24", timestamp=datetime(2026, 5, 24, 10, 0, tzinfo=UTC))
    journal.append(ws, "May 25", timestamp=datetime(2026, 5, 25, 10, 0, tzinfo=UTC))
    journal.append(ws, "May 26", timestamp=datetime(2026, 5, 26, 10, 0, tzinfo=UTC))
    summary = journal.summarize(ws, start=date(2026, 5, 25), end=date(2026, 5, 25))
    assert len(summary.entries) == 1
    assert summary.entries[0].body == "May 25"
    # Without filters: all three
    all_entries = journal.summarize(ws)
    assert len(all_entries.entries) == 3
    # Verify chronological order
    bodies = [e.body for e in all_entries.entries]
    assert bodies == ["May 24", "May 25", "May 26"]


# 4. summarize empty

def test_summarize_empty(tmp_path):
    ws = _make_workspace(tmp_path)
    summary = journal.summarize(ws)
    assert summary.entries == []


def test_summarize_when_journal_dir_missing(tmp_path):
    """No journal dir at all — should return empty gracefully."""
    ws = tmp_path / ".test-commander"
    ws.mkdir()
    summary = journal.summarize(ws)
    assert summary.entries == []


# 5. malformed entry refused

def test_append_refuses_empty_body(tmp_path):
    ws = _make_workspace(tmp_path)
    with pytest.raises(ValueError):
        journal.append(ws, "   ")


def test_append_refuses_body_with_h2_timestamp_heading(tmp_path):
    """Body containing a line like '## 2026-05-26T...' would corrupt parsing."""
    ws = _make_workspace(tmp_path)
    body = "intro\n## 2026-05-26T14:00:00Z\ncorruption attempt"
    with pytest.raises(ValueError):
        journal.append(ws, body)


# Bonus: missing workspace
def test_append_requires_initialized_workspace(tmp_path):
    ws = tmp_path / ".test-commander"
    with pytest.raises(FileNotFoundError):
        journal.append(ws, "entry")
