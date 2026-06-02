"""Server-sent events for the web console (Phase 10 Step 10.3).

The console pushes a `changed` event when the workspace changes (e.g. a journal
append), so open pages refresh. Change detection is a content-and-mtime snapshot
of the workspace (excluding the derived `.web/` index); the SSE generator polls
it. The generator is bounded by `max_events` so tests never spin forever.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Iterator
from pathlib import Path


def snapshot_state(workspace: Path) -> str:
    """A hash of every workspace file's path + mtime + size (excluding .web/)."""
    h = hashlib.sha256()
    for p in sorted(workspace.rglob("*")):
        if not p.is_file() or ".web" in p.relative_to(workspace).parts:
            continue
        stat = p.stat()
        h.update(str(p.relative_to(workspace)).encode())
        h.update(str(stat.st_mtime_ns).encode())
        h.update(str(stat.st_size).encode())
    return h.hexdigest()


def detect_change(prev_state: str, workspace: Path) -> tuple[bool, str]:
    """Return (changed, new_state) relative to a prior snapshot."""
    new_state = snapshot_state(workspace)
    return (new_state != prev_state, new_state)


def _format_event(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


def event_stream(
    workspace: Path, *, max_events: int | None = None, poll_seconds: float = 1.0
) -> Iterator[str]:
    """Yield SSE frames: a `connected` frame, then a `changed` frame per change.

    `max_events` bounds the total frames (including `connected`) so a test or a
    one-shot client terminates; production passes None (runs until the client
    disconnects).
    """
    emitted = 0
    yield _format_event("connected", "ok")
    emitted += 1
    state = snapshot_state(workspace)
    while max_events is None or emitted < max_events:
        changed, state = detect_change(state, workspace)
        if changed:
            yield _format_event("changed", "workspace")
            emitted += 1
        else:
            if max_events is not None:
                break
            time.sleep(poll_seconds)
