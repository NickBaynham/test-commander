"""Step 8.6 - /tc:review-lessons (review_lessons) end-to-end tests.

Drives ``review_lessons.py`` against a tmp project whose
``learning/lessons-inbox.md`` is the seeded one-per-classification inbox. The
helper classifies each candidate into accepted / rejected / needs-human-review,
moves it to the matching ``learning/`` file with its ``status`` updated, and
clears the inbox.

Rubric (precedence): severity ``high`` -> needs-human-review; a summary already
in ``accepted-lessons.md`` -> rejected (a duplicate adding nothing); otherwise
-> accepted.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "review_lessons.py"
INIT = SCRIPTS / "init_workspace.py"
FIXTURE_INBOX = REPO / "tests" / "fixtures" / "seeded-learning" / "lessons-inbox.md"

# LESSON-002's summary in the seeded fixture (a duplicate of an accepted note).
DUP_SUMMARY = "Duplicate of an already-accepted process note"


def run_init(project_root: Path) -> None:
    subprocess.run([sys.executable, str(INIT), str(project_root)],
                   capture_output=True, text=True, check=True)


def cli(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HELPER), str(project_root), *args],
                          capture_output=True, text=True)


def load():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("review_lessons", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def learning(project_root: Path) -> Path:
    return project_root / ".test-commander" / "learning"


def seed_inbox(project_root: Path) -> Path:
    run_init(project_root)
    ldir = learning(project_root)
    shutil.copy(FIXTURE_INBOX, ldir / "lessons-inbox.md")
    # Seed an accepted lesson that LESSON-002 duplicates, so the rubric rejects it.
    (ldir / "accepted-lessons.md").write_text(
        "# Accepted Lessons\n\n"
        "---\nschema: tc-lesson/v1\nid: LESSON-900\nsource: /tc:learn\n"
        "origin: manual\ncategory: process\nseverity: low\nstatus: accepted\n"
        "captured_at: 2026-01-10T00:00:00\n"
        f'summary: "{DUP_SUMMARY}"\n---\n\nAn earlier accepted process note.\n',
        encoding="utf-8",
    )
    return ldir


def read(ldir: Path, name: str) -> str:
    p = ldir / name
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def test_uninitialized_workspace_refused(tmp_path):
    result = cli(tmp_path)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_no_candidates_refused(tmp_path):
    run_init(tmp_path)  # inbox is the template stub
    result = cli(tmp_path)
    assert result.returncode == 2, result.stdout
    assert "/tc:learn" in result.stderr


def test_classifies_into_three_buckets(tmp_path):
    ldir = seed_inbox(tmp_path)
    mod = load()
    mod.review_lessons(tmp_path)
    accepted = read(ldir, "accepted-lessons.md")
    rejected = read(ldir, "rejected-lessons.md")
    needs = read(ldir, "needs-human-review.md")
    assert "LESSON-001" in accepted and "status: accepted" in accepted
    assert "LESSON-002" in rejected and "status: rejected" in rejected
    assert "LESSON-003" in needs and "status: needs-human-review" in needs
    # The inbox is cleared of the reviewed candidates.
    inbox = read(ldir, "lessons-inbox.md")
    assert not re.search(r"^id:\s*LESSON-\d+", inbox, flags=re.MULTILINE), "inbox not cleared"


def test_idempotent_rerun(tmp_path):
    ldir = seed_inbox(tmp_path)
    mod = load()
    mod.review_lessons(tmp_path)
    snap = {n: (ldir / n).read_bytes() for n in
            ("accepted-lessons.md", "rejected-lessons.md", "needs-human-review.md",
             "lessons-inbox.md")}
    result = cli(tmp_path)  # re-run over the cleared inbox is a no-op (exit 0)
    assert result.returncode == 0, result.stderr
    for name, data in snap.items():
        assert (ldir / name).read_bytes() == data, f"{name} changed on idempotent re-run"
