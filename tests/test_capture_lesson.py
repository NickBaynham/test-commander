"""Step 8.2 - /tc:learn (capture_lesson) end-to-end tests.

Drives ``capture_lesson.py`` against a tmp consuming project. The helper appends
a candidate lesson (the ``tc-lesson/v1`` schema) to
``learning/lessons-inbox.md`` from a freeform ``--note``, allocating a monotonic
``LESSON-NNN`` id and deduplicating by ``(source, origin, summary)``. The shared
``append_lessons`` engine is what every ``/tc:learn-from-*`` command reuses.

Asserts the Step 8.2 contract from planning/plan.md.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "capture_lesson.py"
INIT = SCRIPTS / "init_workspace.py"

FIXED_NOW = "2026-01-15T09:30:00"
FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL | re.MULTILINE)
LESSON_BLOCK_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL | re.MULTILINE)


def run_init(project_root: Path) -> None:
    subprocess.run([sys.executable, str(INIT), str(project_root)],
                   capture_output=True, text=True, check=True)


def cli(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HELPER), str(project_root), *args],
                          capture_output=True, text=True)


def load():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("capture_lesson", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def inbox(project_root: Path) -> Path:
    return project_root / ".test-commander" / "learning" / "lessons-inbox.md"


def lesson_ids(text: str) -> list[str]:
    return re.findall(r"^id:\s*(LESSON-\d+)", text, flags=re.MULTILINE)


def do_learn(project_root: Path, **kwargs):
    mod = load()
    kwargs.setdefault("now", datetime.fromisoformat(FIXED_NOW))
    return mod, mod.learn(project_root, **kwargs)


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_workspace_refused(tmp_path):
    result = cli(tmp_path, "--note", "x")
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------


def test_note_appends_one_valid_candidate(tmp_path):
    run_init(tmp_path)
    do_learn(tmp_path, note="Sign-in error copy should be asserted explicitly.")
    text = inbox(tmp_path).read_text(encoding="utf-8")
    assert "schema: tc-lesson/v1" in text
    assert "status: candidate" in text
    assert "captured_at: 2026-01-15T09:30:00" in text
    assert lesson_ids(text) == ["LESSON-001"]
    assert "Sign-in error copy should be asserted explicitly." in text


def test_id_allocator_is_monotonic(tmp_path):
    run_init(tmp_path)
    do_learn(tmp_path, note="first observation")
    do_learn(tmp_path, note="second observation")
    assert lesson_ids(inbox(tmp_path).read_text(encoding="utf-8")) == ["LESSON-001", "LESSON-002"]


def test_injected_clock_makes_inbox_byte_stable(tmp_path):
    run_init(tmp_path)
    do_learn(tmp_path, note="a stable note")
    first = inbox(tmp_path).read_bytes()
    do_learn(tmp_path, note="a stable note")  # same (source, origin, summary) -> dedup
    assert inbox(tmp_path).read_bytes() == first


def test_duplicate_not_reappended(tmp_path):
    run_init(tmp_path)
    do_learn(tmp_path, note="dup note", origin="requirements/open-questions.md:5")
    do_learn(tmp_path, note="dup note", origin="requirements/open-questions.md:5")
    assert len(lesson_ids(inbox(tmp_path).read_text(encoding="utf-8"))) == 1


def test_append_lessons_is_the_shared_engine(tmp_path):
    run_init(tmp_path)
    mod = load()
    lesson = mod.Lesson(
        source="/tc:learn-from-failures",
        origin="runs/RUN-1/analysis.md:8",
        category="product-defect-pattern",
        severity="medium",
        summary="a derived lesson",
        body="A lesson appended via the shared engine.",
    )
    appended = mod.append_lessons(tmp_path / ".test-commander", [lesson],
                                  datetime.fromisoformat(FIXED_NOW))
    assert appended == 1
    text = inbox(tmp_path).read_text(encoding="utf-8")
    assert "category: product-defect-pattern" in text
    assert "source: /tc:learn-from-failures" in text
