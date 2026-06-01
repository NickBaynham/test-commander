"""Step 7.4 - /tc:analyze-results (analyze_results) end-to-end tests.

Drives ``analyze_results.py`` against a tmp consuming project that has a
``/tc:run`` record (produced by ``run_tests.py`` from the recorded report in
``tests/fixtures/seeded-results/``). The helper triages every non-passed
result against the universal rubric (product-defect / test-defect /
environment / flaky), writes the analysis into the run record, and routes
confirmed gaps to ``requirements/open-questions.md`` as deduplicated
``[test-analysis]`` signals.

Asserts the Step 7.4 contract from planning/plan.md:

- uninitialized workspace refused (exit 2);
- no runs refused, pointing at ``/tc:run`` (exit 2);
- the seeded report's failure and flaky case are each classified exactly once
  (the assertion failure as ``product-defect``, the pass-on-retry as ``flaky``);
- ``[test-analysis]`` signals are routed and deduplicated;
- a clean (all-passed) run produces no signals;
- the analysis is deterministic (byte-stable re-run).
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "analyze_results.py"
RUN_HELPER = SCRIPTS / "run_tests.py"
INIT = SCRIPTS / "init_workspace.py"

FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-results"
FIXTURE_REPORT = FIXTURE_DIR / "results.json"
FIXTURE_MAP = FIXTURE_DIR / "automation-map.md"
FIXTURE_SPEC = FIXTURE_DIR / "sign-in.spec.ts"

FIXED_NOW = "2026-01-15T09:30:00"
RUN_ID = "RUN-20260115-093000"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_init(project_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(INIT), str(project_root)],
        capture_output=True,
        text=True,
        check=True,
    )


def cli(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HELPER), str(project_root), *args],
        capture_output=True,
        text=True,
    )


def load(name: str, path: Path):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def seed_run_workspace(project_root: Path) -> Path:
    run_init(project_root)
    ws = project_root / ".test-commander"
    (ws / "traceability").mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_MAP, ws / "traceability" / "automation-map.md")
    e2e = project_root / "tests" / "e2e"
    e2e.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_SPEC, e2e / "sign-in.spec.ts")
    return ws


def make_run_record(project_root: Path, *, mode: str = "all") -> str:
    run_mod = load("run_tests", RUN_HELPER)
    outcome = run_mod.run(
        project_root,
        mode=mode,
        now=datetime.fromisoformat(FIXED_NOW),
        report=FIXTURE_REPORT,
        no_index=True,
    )
    return outcome.run_id


def analysis_file(ws: Path, run_id: str = RUN_ID) -> Path:
    return ws / "runs" / run_id / "analysis.md"


def open_questions(ws: Path) -> str:
    path = ws / "requirements" / "open-questions.md"
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def analysis_lines(ws: Path) -> list[str]:
    return [
        ln for ln in open_questions(ws).split("\n") if "[test-analysis]" in ln
    ]


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_workspace_refused(tmp_path):
    result = cli(tmp_path)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_no_runs_refused(tmp_path):
    run_init(tmp_path)
    result = cli(tmp_path)
    assert result.returncode == 2, result.stdout
    assert "/tc:run" in result.stderr


# ---------------------------------------------------------------------------
# Triage
# ---------------------------------------------------------------------------


def test_failure_and_flaky_each_classified_once(tmp_path):
    ws = seed_run_workspace(tmp_path)
    run_id = make_run_record(tmp_path)
    mod = load("analyze_results", HELPER)
    outcome = mod.analyze(tmp_path, run_id=run_id)
    cats = {c.cs_id: c.category for c in outcome.classifications}
    assert cats == {"CS-001-002": "product-defect", "CS-001-003": "flaky"}, cats
    # The passed result is not triaged.
    assert "CS-001-001" not in cats
    # Each appears exactly once as a triage-table row (last cell = the category).
    rows = [ln for ln in analysis_file(ws).read_text(encoding="utf-8").split("\n")
            if ln.startswith("| REQ-")]
    assert sum(1 for ln in rows if ln.rstrip().endswith("| product-defect |")) == 1
    assert sum(1 for ln in rows if ln.rstrip().endswith("| flaky |")) == 1


def test_routes_test_analysis_signals(tmp_path):
    ws = seed_run_workspace(tmp_path)
    run_id = make_run_record(tmp_path)
    mod = load("analyze_results", HELPER)
    mod.analyze(tmp_path, run_id=run_id)
    lines = analysis_lines(ws)
    assert any("product-defect" in ln and "CS-001-002" in ln for ln in lines)
    assert any("flaky" in ln and "CS-001-003" in ln for ln in lines)


def test_signals_deduplicated_on_rerun(tmp_path):
    ws = seed_run_workspace(tmp_path)
    run_id = make_run_record(tmp_path)
    mod = load("analyze_results", HELPER)
    mod.analyze(tmp_path, run_id=run_id)
    first = len(analysis_lines(ws))
    mod.analyze(tmp_path, run_id=run_id)
    assert len(analysis_lines(ws)) == first, "re-analysis must not duplicate signals"


def test_clean_run_produces_no_signals(tmp_path):
    ws = seed_run_workspace(tmp_path)
    # smoke mode selects only the passed scenario (CS-001-001).
    run_id = make_run_record(tmp_path, mode="smoke")
    mod = load("analyze_results", HELPER)
    outcome = mod.analyze(tmp_path, run_id=run_id)
    assert outcome.classifications == []
    assert analysis_lines(ws) == []


def test_analysis_is_deterministic(tmp_path):
    ws = seed_run_workspace(tmp_path)
    run_id = make_run_record(tmp_path)
    mod = load("analyze_results", HELPER)
    mod.analyze(tmp_path, run_id=run_id)
    first = analysis_file(ws).read_bytes()
    mod.analyze(tmp_path, run_id=run_id)
    assert analysis_file(ws).read_bytes() == first


def test_defaults_to_latest_run(tmp_path):
    ws = seed_run_workspace(tmp_path)
    make_run_record(tmp_path)
    mod = load("analyze_results", HELPER)
    outcome = mod.analyze(tmp_path)  # no run_id -> latest
    assert outcome.run_id == RUN_ID
    assert analysis_file(ws).is_file()
