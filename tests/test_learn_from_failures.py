"""Step 8.3 - /tc:learn-from-failures (learn_from_failures) end-to-end tests.

Drives ``learn_from_failures.py`` against a tmp consuming project that has a
Phase-7 ``runs/<RUN-ID>/analysis.md``. The helper turns the triaged
``product-defect`` and ``flaky`` rows into ``tc-lesson/v1`` candidate lessons
via the shared ``append_lessons`` engine, with ``runs/.../analysis.md:<line>``
provenance.

Asserts the Step 8.3 contract from planning/plan.md.
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
HELPER = SCRIPTS / "learn_from_failures.py"
INIT = SCRIPTS / "init_workspace.py"
FIXTURE_ANALYSIS = REPO / "tests" / "fixtures" / "seeded-learning" / "analysis.md"

FIXED_NOW = "2026-01-15T09:30:00"
RUN_ID = "RUN-20260115-093000"


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


def seed_run_with_analysis(project_root: Path) -> Path:
    run_init(project_root)
    run_dir = project_root / ".test-commander" / "runs" / RUN_ID
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_ANALYSIS, run_dir / "analysis.md")
    return project_root / ".test-commander"


def inbox_text(ws: Path) -> str:
    return (ws / "learning" / "lessons-inbox.md").read_text(encoding="utf-8")


def do_learn(project_root: Path, **kwargs):
    mod = load("learn_from_failures", HELPER)
    kwargs.setdefault("now", datetime.fromisoformat(FIXED_NOW))
    return mod, mod.learn_from_failures(project_root, **kwargs)


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_workspace_refused(tmp_path):
    result = cli(tmp_path)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_no_analysis_refused(tmp_path):
    run_init(tmp_path)
    result = cli(tmp_path)
    assert result.returncode == 2, result.stdout
    assert "/tc:analyze-results" in result.stderr


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------


def test_captures_product_defect_and_flaky(tmp_path):
    ws = seed_run_with_analysis(tmp_path)
    _, appended = do_learn(tmp_path)
    assert appended == 2
    text = inbox_text(ws)
    assert "category: product-defect-pattern" in text
    assert "category: flaky-pattern" in text
    assert re.search(rf"origin:\s*runs/{RUN_ID}/analysis\.md:\d+", text), (
        "lessons must carry runs/.../analysis.md:<line> provenance"
    )
    assert "source: /tc:learn-from-failures" in text


def test_dedup_on_rerun(tmp_path):
    seed_run_with_analysis(tmp_path)
    do_learn(tmp_path)
    do_learn(tmp_path)
    ws = tmp_path / ".test-commander"
    ids = re.findall(r"^id:\s*LESSON-\d+", inbox_text(ws), flags=re.MULTILINE)
    assert len(ids) == 2, "re-run must not duplicate failure-derived lessons"


def test_deterministic(tmp_path):
    ws = seed_run_with_analysis(tmp_path)
    do_learn(tmp_path)
    first = (ws / "learning" / "lessons-inbox.md").read_bytes()
    do_learn(tmp_path)
    assert (ws / "learning" / "lessons-inbox.md").read_bytes() == first
