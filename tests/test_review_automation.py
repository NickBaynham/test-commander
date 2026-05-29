"""Step 6.5 - /tc:review-automation (review_automation) + automate auto-run.

Drives ``review_automation.py`` against a tmp consuming project. The helper
reviews the generated specs under ``tests/e2e/*.spec.ts`` against a six-category
universal rubric, writes a per-spec verdict to
``<workspace>/automation-plan/review-summary.md``, and routes failures to
``<workspace>/requirements/open-questions.md`` as deduplicated
``[automation-review]`` gap signals.

Universal rubric categories (D19): ``inline-test-data``, ``hardcoded-wait``,
``missing-provenance``, ``weak-locator``, ``untraceable-spec``, ``assertion-free``.

Asserts the Step 6.5 contract from planning/plan.md:

- uninitialized workspace refused (exit 2);
- no specs refused, pointing at /tc:automate (exit 2);
- a deliberately-flawed seeded spec surfaces every rubric category once;
- a clean generated spec passes with zero findings;
- ``[automation-review]`` signals are deduplicated across re-runs;
- ``review_automation()`` is the same code path ``/tc:automate`` auto-runs, and
  ``--no-review`` suppresses it.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "review_automation.py"
AUTOMATE = SCRIPTS / "automate.py"
PLAN_HELPER = SCRIPTS / "automation_plan.py"
INIT = SCRIPTS / "init_workspace.py"

FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-automation"
FIXTURE_FEATURE = FIXTURE_DIR / "sign-in.feature"
FIXTURE_FLAWED_SPEC = FIXTURE_DIR / "flawed.spec.ts"

CATEGORIES = {
    "inline-test-data",
    "hardcoded-wait",
    "missing-provenance",
    "weak-locator",
    "untraceable-spec",
    "assertion-free",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def run_init(project_root: Path) -> None:
    subprocess.run(
        [sys.executable, str(INIT), str(project_root)],
        capture_output=True, text=True, check=True,
    )


def run(helper: Path, project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(helper), str(project_root), *args],
        capture_output=True, text=True,
    )


def load_module(name: str, path: Path):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def seed_planned(project_root: Path) -> None:
    run_init(project_root)
    features = project_root / ".test-commander" / "bdd" / "features"
    features.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_FEATURE, features / "sign-in.feature")
    result = run(PLAN_HELPER, project_root)
    assert result.returncode == 0, result.stderr


def seed_flawed_spec(project_root: Path) -> None:
    run_init(project_root)
    e2e = project_root / "tests" / "e2e"
    e2e.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_FLAWED_SPEC, e2e / "flawed.spec.ts")


def open_questions(project_root: Path) -> str:
    p = project_root / ".test-commander" / "requirements" / "open-questions.md"
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def review_summary(project_root: Path) -> Path:
    return project_root / ".test-commander" / "automation-plan" / "review-summary.md"


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_workspace_refused(tmp_path):
    result = run(HELPER, tmp_path)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_no_specs_refused_points_at_automate(tmp_path):
    run_init(tmp_path)
    result = run(HELPER, tmp_path)
    assert result.returncode == 2, result.stdout
    assert "/tc:automate" in result.stderr


# ---------------------------------------------------------------------------
# Rubric coverage
# ---------------------------------------------------------------------------


def test_flawed_spec_surfaces_every_category(tmp_path):
    seed_flawed_spec(tmp_path)
    module = load_module("review_automation", HELPER)
    outcome = module.review_automation(tmp_path)
    found = {f.category for findings in outcome.findings_by_spec.values() for f in findings}
    missing = CATEGORIES - found
    assert not missing, f"rubric missed categories: {sorted(missing)}; found {sorted(found)}"


def test_clean_generated_spec_passes(tmp_path):
    seed_planned(tmp_path)
    run(AUTOMATE, tmp_path, "--no-review")  # generate without auto-review
    module = load_module("review_automation", HELPER)
    outcome = module.review_automation(tmp_path)
    sign_in = [
        f for spec, findings in outcome.findings_by_spec.items()
        for f in findings if "sign-in" in spec
    ]
    assert sign_in == [], f"clean generated spec must pass; got {sign_in}"


# ---------------------------------------------------------------------------
# Open-questions routing + dedup
# ---------------------------------------------------------------------------


def test_routes_findings_to_open_questions(tmp_path):
    seed_flawed_spec(tmp_path)
    run(HELPER, tmp_path)
    text = open_questions(tmp_path)
    assert "[automation-review]" in text, "findings must route to open-questions"


def test_open_questions_deduplicated(tmp_path):
    seed_flawed_spec(tmp_path)
    run(HELPER, tmp_path)
    run(HELPER, tmp_path)
    text = open_questions(tmp_path)
    lines = [ln for ln in text.split("\n") if "[automation-review]" in ln]
    assert len(lines) == len(set(lines)), f"duplicate [automation-review] lines: {lines}"


# ---------------------------------------------------------------------------
# Review summary
# ---------------------------------------------------------------------------


def test_writes_review_summary(tmp_path):
    seed_flawed_spec(tmp_path)
    run(HELPER, tmp_path)
    assert review_summary(tmp_path).is_file(), "review must write a review-summary.md"


# ---------------------------------------------------------------------------
# Shared code path: /tc:automate auto-run + --no-review suppression
# ---------------------------------------------------------------------------


def test_automate_autorun_wires_review(tmp_path):
    seed_planned(tmp_path)
    run(AUTOMATE, tmp_path)  # no --no-review
    assert review_summary(tmp_path).is_file(), (
        "/tc:automate must auto-run the review (review-summary.md present)"
    )


def test_no_review_suppresses_autorun(tmp_path):
    seed_planned(tmp_path)
    run(AUTOMATE, tmp_path, "--no-review")
    assert not review_summary(tmp_path).exists(), (
        "--no-review must suppress the auto-run"
    )


def test_autorun_matches_standalone(tmp_path, tmp_path_factory):
    # Auto-run path
    seed_planned(tmp_path)
    run(AUTOMATE, tmp_path)
    autorun = review_summary(tmp_path).read_text(encoding="utf-8")
    # Standalone path in a separate project: generate (suppressed) then review
    other = tmp_path_factory.mktemp("standalone")
    seed_planned(other)
    run(AUTOMATE, other, "--no-review")
    run(HELPER, other)
    standalone = review_summary(other).read_text(encoding="utf-8")
    assert autorun == standalone, "auto-run and standalone review must share one code path"
