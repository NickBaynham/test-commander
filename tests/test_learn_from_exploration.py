"""Step 8.4 - /tc:learn-from-exploration (learn_from_exploration) tests.

Drives ``learn_from_exploration.py`` against a tmp project with a Phase-4
exploration note. The helper turns recorded anomalies into ``anti-pattern``
candidates and coverage gaps into ``coverage-gap`` candidates via the shared
``append_lessons`` engine, with ``exploration-notes/<file>:<line>`` provenance.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "learn_from_exploration.py"
INIT = SCRIPTS / "init_workspace.py"
FIXTURE_NOTE = REPO / "tests" / "fixtures" / "seeded-learning" / "SESS-20260115-001.md"

FIXED_NOW = "2026-01-15T09:30:00"


def run_init(project_root: Path) -> None:
    subprocess.run([sys.executable, str(INIT), str(project_root)],
                   capture_output=True, text=True, check=True)


def cli(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HELPER), str(project_root), *args],
                          capture_output=True, text=True)


def load(name: str, path: Path):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def seed_exploration(project_root: Path) -> Path:
    run_init(project_root)
    notes = project_root / ".test-commander" / "exploration-notes"
    notes.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_NOTE, notes / FIXTURE_NOTE.name)
    return project_root / ".test-commander"


def inbox_text(ws: Path) -> str:
    return (ws / "learning" / "lessons-inbox.md").read_text(encoding="utf-8")


def do_learn(project_root: Path, **kwargs):
    mod = load("learn_from_exploration", HELPER)
    kwargs.setdefault("now", datetime.fromisoformat(FIXED_NOW))
    return mod, mod.learn_from_exploration(project_root, **kwargs)


def test_uninitialized_workspace_refused(tmp_path):
    result = cli(tmp_path)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_no_exploration_refused(tmp_path):
    run_init(tmp_path)
    result = cli(tmp_path)
    assert result.returncode == 2, result.stdout
    assert "/tc:explore" in result.stderr


def test_captures_anomalies_and_coverage_gaps(tmp_path):
    ws = seed_exploration(tmp_path)
    _, appended = do_learn(tmp_path)
    assert appended >= 3, "two anomalies + one coverage gap expected"
    text = inbox_text(ws)
    assert "category: anti-pattern" in text
    assert "category: coverage-gap" in text
    assert re.search(r"origin:\s*exploration-notes/SESS-[\w-]+\.md:\d+", text)
    assert "source: /tc:learn-from-exploration" in text


def test_dedup_on_rerun(tmp_path):
    ws = seed_exploration(tmp_path)
    do_learn(tmp_path)
    first = len(re.findall(r"^id:\s*LESSON-\d+", inbox_text(ws), flags=re.MULTILINE))
    do_learn(tmp_path)
    assert len(re.findall(r"^id:\s*LESSON-\d+", inbox_text(ws), flags=re.MULTILINE)) == first


def test_deterministic(tmp_path):
    ws = seed_exploration(tmp_path)
    do_learn(tmp_path)
    first = (ws / "learning" / "lessons-inbox.md").read_bytes()
    do_learn(tmp_path)
    assert (ws / "learning" / "lessons-inbox.md").read_bytes() == first
