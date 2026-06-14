"""/tc:generate-test-plan and /tc:update-test-plan (test_plan) end-to-end tests.

Drives ``test_plan.py`` against a tmp consuming project seeded with a minimal
requirements inventory and traceability map.

Asserts:

- uninitialized workspace refused (exit 2);
- init-only (stub inventory, no REQ rows) refused (exit 2);
- generate writes test-plan.md + coverage-map.md from a real inventory;
- coverage status is derived (automated / planned / uncovered);
- coverage-map.md is byte-deterministic across re-runs;
- test-plan.md is skip-not-overwrite (human edits survive);
- --force re-creates test-plan.md;
- --refresh regenerates coverage-map.md but never touches test-plan.md.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "test_plan.py"
INIT = SCRIPTS / "init_workspace.py"

INVENTORY = """\
# Requirements Inventory

| ID | Source | Body |
| --- | --- | --- |
| REQ-001 | `r.md` | The system shall let an admin create a patient. |
| REQ-002 | `r.md` | The system shall reject a duplicate email. |
| REQ-003 | `r.md` | The dashboard shall show total counts. |
"""

# REQ-001 automated, REQ-002 planned (test idea only), REQ-003 absent -> uncovered.
REQ_MAP = """\
# Requirements Map

| REQ-ID | Test ideas | BDD features | Automation |
| --- | --- | --- | --- |
| REQ-001 | `test-ideas/REQ-001.md` | _(none)_ | `automation-map.md#REQ-001` |
| REQ-002 | `test-ideas/REQ-002.md` | _(none)_ | _(none)_ |
"""


def run_init(project_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(INIT), str(project_root)],
        capture_output=True,
        text=True,
        check=True,
    )


def run_plan(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HELPER), str(project_root), *args],
        capture_output=True,
        text=True,
    )


def workspace(project_root: Path) -> Path:
    return project_root / ".test-commander"


def seed(project_root: Path, *, with_map: bool = True) -> None:
    run_init(project_root)
    ws = workspace(project_root)
    (ws / "requirements" / "requirements-inventory.md").write_text(INVENTORY, encoding="utf-8")
    if with_map:
        (ws / "traceability" / "requirements-map.md").write_text(REQ_MAP, encoding="utf-8")


def test_uninitialized_workspace_refused(tmp_path):
    result = run_plan(tmp_path)
    assert result.returncode == 2
    assert "init" in result.stderr.lower()


def test_init_only_stub_inventory_refused(tmp_path):
    run_init(tmp_path)
    result = run_plan(tmp_path)
    assert result.returncode == 2
    assert "inventory" in result.stderr.lower()


def test_generate_writes_both_artifacts(tmp_path):
    seed(tmp_path)
    result = run_plan(tmp_path)
    assert result.returncode == 0, result.stderr
    ws = workspace(tmp_path)
    assert (ws / "test-plan" / "test-plan.md").is_file()
    assert (ws / "test-plan" / "coverage-map.md").is_file()


def test_coverage_status_derivation(tmp_path):
    seed(tmp_path)
    run_plan(tmp_path)
    cov = (workspace(tmp_path) / "test-plan" / "coverage-map.md").read_text(encoding="utf-8")
    assert "| REQ-001 |" in cov and "automated" in cov
    assert "| REQ-003 |" in cov and "uncovered" in cov
    # REQ-002 has a test idea but no automation -> planned.
    req002 = [ln for ln in cov.splitlines() if ln.startswith("| REQ-002 |")][0]
    assert "planned" in req002


def test_coverage_map_deterministic(tmp_path):
    seed(tmp_path)
    run_plan(tmp_path)
    first = (workspace(tmp_path) / "test-plan" / "coverage-map.md").read_bytes()
    run_plan(tmp_path)
    second = (workspace(tmp_path) / "test-plan" / "coverage-map.md").read_bytes()
    assert first == second


def test_plan_is_skip_not_overwrite(tmp_path):
    seed(tmp_path)
    run_plan(tmp_path)
    plan = workspace(tmp_path) / "test-plan" / "test-plan.md"
    plan.write_text("EDITED BY HUMAN", encoding="utf-8")
    result = run_plan(tmp_path)
    assert result.returncode == 0
    assert plan.read_text(encoding="utf-8") == "EDITED BY HUMAN"
    assert "skipped" in result.stdout


def test_force_recreates_plan(tmp_path):
    seed(tmp_path)
    run_plan(tmp_path)
    plan = workspace(tmp_path) / "test-plan" / "test-plan.md"
    plan.write_text("EDITED BY HUMAN", encoding="utf-8")
    run_plan(tmp_path, "--force")
    assert plan.read_text(encoding="utf-8") != "EDITED BY HUMAN"
    assert "Test Plan" in plan.read_text(encoding="utf-8")


def test_refresh_updates_map_not_plan(tmp_path):
    seed(tmp_path)
    run_plan(tmp_path)
    plan = workspace(tmp_path) / "test-plan" / "test-plan.md"
    plan.write_text("EDITED BY HUMAN", encoding="utf-8")
    result = run_plan(tmp_path, "--refresh")
    assert result.returncode == 0
    assert plan.read_text(encoding="utf-8") == "EDITED BY HUMAN"
    assert (workspace(tmp_path) / "test-plan" / "coverage-map.md").is_file()


def test_requirement_count_in_plan(tmp_path):
    seed(tmp_path)
    run_plan(tmp_path)
    plan = (workspace(tmp_path) / "test-plan" / "test-plan.md").read_text(encoding="utf-8")
    assert "**3**" in plan  # REQUIREMENT_COUNT substituted
    assert "| REQ-001 |" in plan  # inventory block substituted


# A Playwright-shaped report: REQ-003 has a passing test (-> automated), REQ-002 has
# only a failing test (-> automated-failing). REQ-001 is not referenced by any test.
RESULTS_JSON = """\
{
  "suites": [
    {
      "title": "patients.spec.ts",
      "file": "tests/api/patients.spec.ts",
      "specs": [
        { "title": "REQ-003 dashboard shows totals", "ok": true, "tests": [] }
      ],
      "suites": [
        {
          "title": "validation",
          "specs": [
            { "title": "REQ-002 rejects duplicate email", "ok": false, "tests": [] }
          ]
        }
      ]
    }
  ]
}
"""


def _coverage(project_root: Path) -> str:
    return (workspace(project_root) / "test-plan" / "coverage-map.md").read_text(encoding="utf-8")


def _row(cov: str, req_id: str) -> str:
    return [ln for ln in cov.splitlines() if ln.startswith(f"| {req_id} |")][0]


def test_results_explicit_path_marks_run_status(tmp_path):
    seed(tmp_path, with_map=False)
    (tmp_path / "results.json").write_text(RESULTS_JSON, encoding="utf-8")
    result = run_plan(tmp_path, "--results", "results.json")
    assert result.returncode == 0, result.stderr
    cov = _coverage(tmp_path)
    assert "automated" in _row(cov, "REQ-003")
    assert "automated-failing" in _row(cov, "REQ-002")
    # REQ-001 has no test and no map link -> uncovered.
    assert "uncovered" in _row(cov, "REQ-001")
    assert "results:" in result.stdout


def test_results_autodetect_default_path(tmp_path):
    seed(tmp_path, with_map=False)
    report_dir = tmp_path / "playwright-report"
    report_dir.mkdir()
    (report_dir / "results.json").write_text(RESULTS_JSON, encoding="utf-8")
    run_plan(tmp_path)  # no --results; should autodetect
    cov = _coverage(tmp_path)
    assert "automated" in _row(cov, "REQ-003")
    assert "automated-failing" in _row(cov, "REQ-002")


def test_run_status_overrides_map(tmp_path):
    # REQ-002 is "planned" via the map (test-idea only), but a failing run wins.
    seed(tmp_path, with_map=True)
    (tmp_path / "results.json").write_text(RESULTS_JSON, encoding="utf-8")
    run_plan(tmp_path, "--results", "results.json")
    cov = _coverage(tmp_path)
    assert "automated-failing" in _row(cov, "REQ-002")


def test_missing_results_file_is_ignored(tmp_path):
    seed(tmp_path, with_map=False)
    result = run_plan(tmp_path, "--results", "does-not-exist.json")
    assert result.returncode == 0
    assert "results: none" in result.stdout
