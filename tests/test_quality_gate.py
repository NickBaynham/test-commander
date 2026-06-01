"""Step 7.6 - /tc:quality-gate (quality_gate) end-to-end tests.

Drives ``quality_gate.py`` against a tmp consuming project that has a run
record and a generated quality report. The gate evaluates the latest run
against project-defined thresholds (``tc-quality-report.gate.thresholds``) and
returns PASS / WARN / FAIL with a per-criterion breakdown.

Asserts the Step 7.6 contract from planning/plan.md:

- uninitialized workspace refused (exit 2);
- no report refused, pointing at ``/tc:report`` (exit 2);
- the seeded run FAILs the default thresholds (a failing test);
- config thresholds change the verdict (loose -> PASS, flaky-only -> WARN);
- deterministic (byte-stable verdict file).
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
HELPER = SCRIPTS / "quality_gate.py"
RUN_HELPER = SCRIPTS / "run_tests.py"
REPORT_HELPER = SCRIPTS / "build_report.py"
INIT = SCRIPTS / "init_workspace.py"

FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-results"
FIXTURE_REPORT = FIXTURE_DIR / "results.json"
FIXTURE_MAP = FIXTURE_DIR / "automation-map.md"
FIXTURE_SPEC = FIXTURE_DIR / "sign-in.spec.ts"

FIXED_NOW = "2026-01-15T09:30:00"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_init(project_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(INIT), str(project_root)],
        capture_output=True, text=True, check=True,
    )


def cli(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HELPER), str(project_root), *args],
        capture_output=True, text=True,
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


def seed_run(project_root: Path) -> Path:
    run_init(project_root)
    ws = project_root / ".test-commander"
    (ws / "traceability").mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_MAP, ws / "traceability" / "automation-map.md")
    e2e = project_root / "tests" / "e2e"
    e2e.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_SPEC, e2e / "sign-in.spec.ts")
    load("run_tests", RUN_HELPER).run(
        project_root, now=datetime.fromisoformat(FIXED_NOW),
        report=FIXTURE_REPORT, no_index=True,
    )
    return ws


def seed_run_and_report(project_root: Path) -> Path:
    ws = seed_run(project_root)
    load("build_report", REPORT_HELPER).build_report(
        project_root, now=datetime.fromisoformat(FIXED_NOW)
    )
    return ws


def write_config(ws: Path, body: str) -> None:
    (ws / "config.yaml").write_text(body, encoding="utf-8")


def do_gate(project_root: Path):
    mod = load("quality_gate", HELPER)
    return mod, mod.gate(project_root)


def verdict_file(ws: Path) -> Path:
    return ws / "quality-report" / "quality-gate.md"


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_workspace_refused(tmp_path):
    result = cli(tmp_path)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_no_report_refused(tmp_path):
    seed_run(tmp_path)  # a run, but no /tc:report yet
    result = cli(tmp_path)
    assert result.returncode == 2, result.stdout
    assert "/tc:report" in result.stderr


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------


def test_seeded_run_fails_default_thresholds(tmp_path):
    ws = seed_run_and_report(tmp_path)
    _, outcome = do_gate(tmp_path)
    assert outcome.verdict == "FAIL", outcome.verdict
    text = verdict_file(ws).read_text(encoding="utf-8")
    assert "FAIL" in text
    assert "pass rate" in text and "failed tests" in text and "flaky tests" in text


def test_loose_thresholds_pass(tmp_path):
    ws = seed_run_and_report(tmp_path)
    write_config(ws, (
        "tc-quality-report:\n"
        "  gate:\n"
        "    thresholds:\n"
        "      min-pass-rate: 0.0\n"
        "      max-failed: 5\n"
        "      max-flaky: 5\n"
        "      max-open-questions: 100\n"
    ))
    _, outcome = do_gate(tmp_path)
    assert outcome.verdict == "PASS", outcome.verdict


def test_flaky_only_warns(tmp_path):
    ws = seed_run_and_report(tmp_path)
    # Allow failures and a low pass rate, but flag any flaky test.
    write_config(ws, (
        "tc-quality-report:\n"
        "  gate:\n"
        "    thresholds:\n"
        "      min-pass-rate: 0.0\n"
        "      max-failed: 5\n"
        "      max-flaky: 0\n"
        "      max-open-questions: 100\n"
    ))
    _, outcome = do_gate(tmp_path)
    assert outcome.verdict == "WARN", outcome.verdict


def test_deterministic(tmp_path):
    ws = seed_run_and_report(tmp_path)
    do_gate(tmp_path)
    first = verdict_file(ws).read_bytes()
    do_gate(tmp_path)
    assert verdict_file(ws).read_bytes() == first


def test_cli_exit_code_reflects_fail(tmp_path):
    seed_run_and_report(tmp_path)
    result = cli(tmp_path)
    assert result.returncode == 1, result.stdout  # FAIL -> non-zero for CI
    assert "FAIL" in result.stdout
