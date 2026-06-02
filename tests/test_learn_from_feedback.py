"""Step 8.5 - /tc:learn-from-feedback (learn_from_feedback) tests.

Drives ``learn_from_feedback.py`` against a tmp project. The helper reads
resolved human feedback (``requirements/open-questions.md`` entries carrying a
``_Resolved:`` marker, plus an optional ``documents/uploaded/feedback.md``) and
turns each into a ``process`` candidate via the shared ``append_lessons``
engine. With no resolved feedback it is a no-op (not an error).
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
HELPER = SCRIPTS / "learn_from_feedback.py"
INIT = SCRIPTS / "init_workspace.py"
FIXTURE_OPEN_Q = REPO / "tests" / "fixtures" / "seeded-learning" / "open-questions.md"

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


def seed_feedback(project_root: Path) -> Path:
    run_init(project_root)
    oq = project_root / ".test-commander" / "requirements" / "open-questions.md"
    oq.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_OPEN_Q, oq)
    return project_root / ".test-commander"


def inbox(project_root: Path) -> Path:
    return project_root / ".test-commander" / "learning" / "lessons-inbox.md"


def do_learn(project_root: Path, **kwargs):
    mod = load("learn_from_feedback", HELPER)
    kwargs.setdefault("now", datetime.fromisoformat(FIXED_NOW))
    return mod, mod.learn_from_feedback(project_root, **kwargs)


def test_uninitialized_workspace_refused(tmp_path):
    result = cli(tmp_path)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_no_feedback_is_not_an_error(tmp_path):
    run_init(tmp_path)  # template open-questions has no _Resolved: items
    _, appended = do_learn(tmp_path)
    assert appended == 0
    result = cli(tmp_path)
    assert result.returncode == 0, result.stderr


def test_captures_resolved_feedback(tmp_path):
    seed_feedback(tmp_path)
    _, appended = do_learn(tmp_path)
    assert appended >= 1
    text = inbox(tmp_path).read_text(encoding="utf-8")
    assert "source: /tc:learn-from-feedback" in text
    assert re.search(r"origin:\s*requirements/open-questions\.md:\d+", text)


def test_dedup_on_rerun(tmp_path):
    seed_feedback(tmp_path)
    do_learn(tmp_path)
    first = len(re.findall(r"^id:\s*LESSON-\d+", inbox(tmp_path).read_text(encoding="utf-8"),
                           flags=re.MULTILINE))
    do_learn(tmp_path)
    second = len(re.findall(r"^id:\s*LESSON-\d+", inbox(tmp_path).read_text(encoding="utf-8"),
                            flags=re.MULTILINE))
    assert first == second


def test_deterministic(tmp_path):
    seed_feedback(tmp_path)
    do_learn(tmp_path)
    first = inbox(tmp_path).read_bytes()
    do_learn(tmp_path)
    assert inbox(tmp_path).read_bytes() == first
