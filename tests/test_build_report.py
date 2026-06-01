"""Step 7.5 - /tc:report (build_report) end-to-end tests.

Drives ``build_report.py`` against a tmp consuming project seeded with a
``/tc:run`` record (and, for the traceability assertion, the full upstream
chain). The helper aggregates the workspace into
``quality-report/current-quality-report.md`` with every spec'd section, keeps
facts / interpretation / human-review separated, snapshots a full copy to
``quality-report/history/<YYYY-MM-DD-HHmm>.md`` under the injected clock, and -
via the extended ``traceability_map`` - resolves the ``Test result`` and
``Quality report`` columns of ``test-map.md`` from ``pending``.

Asserts the Step 7.5 contract from planning/plan.md.
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
HELPER = SCRIPTS / "build_report.py"
RUN_HELPER = SCRIPTS / "run_tests.py"
INIT = SCRIPTS / "init_workspace.py"

FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-results"
FIXTURE_REPORT = FIXTURE_DIR / "results.json"
FIXTURE_MAP = FIXTURE_DIR / "automation-map.md"
FIXTURE_SPEC = FIXTURE_DIR / "sign-in.spec.ts"
FIXTURE_FEATURE = REPO / "tests" / "fixtures" / "seeded-automation" / "sign-in.feature"

FIXED_NOW = "2026-01-15T09:30:00"
RUN_ID = "RUN-20260115-093000"
SNAPSHOT_NAME = "2026-01-15-0930.md"

SECTION_TITLES = [
    "Executive summary",
    "Coverage",
    "Requirements readiness",
    "Exploratory findings",
    "Automated regression status",
    "Known risks",
    "Known defects",
    "Open questions",
    "Automation health",
    "Flaky tests",
    "Evidence summary",
    "Traceability summary",
    "Recommendations",
    "Release readiness",
    "Recent changes",
]


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


def seed_run(project_root: Path, *, mode: str = "all") -> Path:
    """Init + drop the Phase-6 chain + produce a run record."""
    run_init(project_root)
    ws = project_root / ".test-commander"
    (ws / "traceability").mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_MAP, ws / "traceability" / "automation-map.md")
    e2e = project_root / "tests" / "e2e"
    e2e.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_SPEC, e2e / "sign-in.spec.ts")
    run_mod = load("run_tests", RUN_HELPER)
    run_mod.run(project_root, mode=mode, now=datetime.fromisoformat(FIXED_NOW),
                report=FIXTURE_REPORT, no_index=True)
    return ws


def seed_full_chain(project_root: Path) -> Path:
    """seed_run plus a generated inventory and a bdd feature, so the
    traceability map can resolve the scenario-level chain."""
    ws = seed_run(project_root)
    inv = ws / "requirements" / "requirements-inventory.md"
    inv.parent.mkdir(parents=True, exist_ok=True)
    inv.write_text(
        "# Requirements inventory\n\nTotal: **1**\n\n"
        "| REQ-ID | Title |\n| --- | --- |\n| REQ-001 | Sign-in |\n",
        encoding="utf-8",
    )
    feats = ws / "bdd" / "features"
    feats.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_FEATURE, feats / "sign-in.feature")
    return ws


def report_text(ws: Path) -> str:
    return (ws / "quality-report" / "current-quality-report.md").read_text(encoding="utf-8")


def do_build(project_root: Path):
    mod = load("build_report", HELPER)
    return mod, mod.build_report(project_root, now=datetime.fromisoformat(FIXED_NOW))


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_workspace_refused(tmp_path):
    result = cli(tmp_path, "--now", FIXED_NOW)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------


def test_report_has_every_section(tmp_path):
    ws = seed_run(tmp_path)
    do_build(tmp_path)
    text = report_text(ws)
    for title in SECTION_TITLES:
        assert f"## {title}" in text, f"missing section: {title}"


def test_facts_interpretation_review_separated(tmp_path):
    ws = seed_run(tmp_path)
    do_build(tmp_path)
    text = report_text(ws)
    for tag in ("[fact]", "[interpretation]", "[review]"):
        assert tag in text, f"the report must separate classes - missing {tag}"


def test_regression_status_from_latest_run(tmp_path):
    ws = seed_run(tmp_path)
    do_build(tmp_path)
    text = report_text(ws)
    assert RUN_ID in text, "the report must name the latest run"
    # 1 passed / 1 failed / 1 flaky from the seeded report.
    assert "passed: 1" in text and "failed: 1" in text and "flaky: 1" in text


def test_history_snapshot_written_under_injected_clock(tmp_path):
    ws = seed_run(tmp_path)
    do_build(tmp_path)
    snapshot = ws / "quality-report" / "history" / SNAPSHOT_NAME
    assert snapshot.is_file(), "history snapshot must use the injected-clock filename"
    assert snapshot.read_bytes() == (
        ws / "quality-report" / "current-quality-report.md"
    ).read_bytes(), "the snapshot is a full copy of the current report"


def test_deterministic_byte_stable(tmp_path):
    ws = seed_run(tmp_path)
    do_build(tmp_path)
    first = report_text(ws)
    do_build(tmp_path)
    assert report_text(ws) == first, "same inputs + same clock -> byte-identical report"


def test_outcome_reports_paths(tmp_path):
    seed_run(tmp_path)
    _, outcome = do_build(tmp_path)
    assert outcome.report_path.name == "current-quality-report.md"
    assert outcome.snapshot_path.name == SNAPSHOT_NAME


# ---------------------------------------------------------------------------
# test-map downstream resolution
# ---------------------------------------------------------------------------


def test_test_map_downstream_columns_resolve(tmp_path):
    ws = seed_full_chain(tmp_path)
    do_build(tmp_path)
    test_map = (ws / "traceability" / "test-map.md").read_text(encoding="utf-8")
    rows = [ln for ln in test_map.split("\n") if ln.startswith("| REQ-001 |")]
    assert rows, "test-map must carry REQ-001 scenario rows"
    # No downstream column for an executed+reported scenario stays pending.
    for cs, status in (("CS-001-001", "passed"), ("CS-001-002", "failed"),
                       ("CS-001-003", "flaky")):
        row = next((r for r in rows if cs in r), None)
        assert row is not None, f"missing test-map row for {cs}"
        # cells 0-5: req, test-idea, scenario, automated, test-result, quality-report
        cells = [c.strip() for c in row.strip("|").split("|")]
        assert cells[4] == status, f"{cs} Test result should be {status}, got {cells[4]!r}"
        assert cells[5] != "pending", f"{cs} Quality report must resolve once the report exists"
