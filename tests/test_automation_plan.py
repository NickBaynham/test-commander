"""Step 6.3 - /tc:automation-plan (automation_plan) end-to-end tests.

Drives ``automation_plan.py`` against a tmp consuming project seeded with the
clean ``sign-in.feature`` from ``tests/fixtures/seeded-automation/``. The helper
scans ``bdd/features/*.feature``, scores each scenario against the universal
seven-factor suitability rubric, and writes
``<workspace>/automation-plan/<area>.md`` ranking scenarios
``automate`` / ``consider`` / ``manual``.

Asserts the Step 6.3 contract from planning/plan.md:

- uninitialized workspace refused (exit 2);
- no feature files is not an error - the run notes "no scenarios" (exit 0);
- a seeded clean feature produces a plan with every scenario scored and a
  recommended order;
- ``@automated-candidate`` scenarios are always ranked ``automate``;
- ``@manual`` scenarios are always ranked ``manual``;
- the plan is deterministic (byte-identical re-run);
- ``tc-automate.suitability.weights`` config changes the ranking.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "automation_plan.py"
INIT = SCRIPTS / "init_workspace.py"

FIXTURE_FEATURE = REPO / "tests" / "fixtures" / "seeded-automation" / "sign-in.feature"


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


def run_plan(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HELPER), str(project_root), *args],
        capture_output=True,
        text=True,
    )


def load_module():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))  # automation_plan imports sibling review_bdd
    spec = importlib.util.spec_from_file_location("automation_plan", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def seed_feature(project_root: Path, text: str | None = None, name: str = "sign-in") -> Path:
    run_init(project_root)
    features_dir = project_root / ".test-commander" / "bdd" / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    dest = features_dir / f"{name}.feature"
    if text is None:
        shutil.copy(FIXTURE_FEATURE, dest)
    else:
        dest.write_text(text, encoding="utf-8")
    return dest


def plan_path(project_root: Path, area: str = "sign-in") -> Path:
    return project_root / ".test-commander" / "automation-plan" / f"{area}.md"


# A borderline, non-candidate scenario: traceable + deterministic + right-sized
# + data-ready, but no class/risk/persona tag. Scores below the automate
# threshold under the default weights (-> consider) and flips to automate when
# the traceable weight is boosted via config.
BORDERLINE_FEATURE = """\
@area:search
Feature: Search

  @area:search @req:REQ-009 @cs:CS-009-001
  Scenario: Search returns matching results
    Given a populated index
    When the user searches for a known term
    Then matching results are listed
"""

MANUAL_FEATURE = """\
@area:onboarding
Feature: Onboarding

  @area:onboarding @req:REQ-010 @cs:CS-010-001 @smoke @risk:high @persona:admin @manual
  Scenario: Guided onboarding tour
    Given a newly provisioned account
    When the admin starts the onboarding tour
    Then the tour highlights each primary surface
"""


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_workspace_refused(tmp_path):
    result = run_plan(tmp_path)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_no_features_is_not_an_error(tmp_path):
    run_init(tmp_path)
    result = run_plan(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "no scenarios" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Plan generation
# ---------------------------------------------------------------------------


def test_seeded_feature_scores_every_scenario(tmp_path):
    seed_feature(tmp_path)
    result = run_plan(tmp_path)
    assert result.returncode == 0, result.stderr
    text = plan_path(tmp_path).read_text(encoding="utf-8")
    for scenario in (
        "Sign in with valid credentials",
        "Sign in is rejected with an invalid password",
        "Session expires after the idle timeout",
    ):
        assert scenario in text, f"plan must score scenario {scenario!r}"


def test_plan_has_recommended_order(tmp_path):
    seed_feature(tmp_path)
    run_plan(tmp_path)
    text = plan_path(tmp_path).read_text(encoding="utf-8").lower()
    assert "recommended order" in text


def test_automated_candidates_ranked_automate(tmp_path):
    seed_feature(tmp_path)
    module = load_module()
    outcome = module.build_plan(tmp_path)
    ranks = outcome.ranks_by_area["sign-in"]
    assert ranks, "expected scored scenarios"
    assert all(rank == "automate" for rank in ranks.values()), ranks


def test_manual_tag_forces_manual(tmp_path):
    seed_feature(tmp_path, MANUAL_FEATURE, name="onboarding")
    module = load_module()
    outcome = module.build_plan(tmp_path)
    ranks = outcome.ranks_by_area["onboarding"]
    assert all(rank == "manual" for rank in ranks.values()), (
        f"@manual must force manual even with a high score: {ranks}"
    )


def test_deterministic_byte_identical_rerun(tmp_path):
    seed_feature(tmp_path)
    run_plan(tmp_path)
    first = plan_path(tmp_path).read_bytes()
    run_plan(tmp_path)
    assert plan_path(tmp_path).read_bytes() == first


# ---------------------------------------------------------------------------
# Config-tunable ranking
# ---------------------------------------------------------------------------


def test_default_weights_rank_borderline_as_consider(tmp_path):
    seed_feature(tmp_path, BORDERLINE_FEATURE, name="search")
    module = load_module()
    outcome = module.build_plan(tmp_path)
    ranks = outcome.ranks_by_area["search"]
    assert set(ranks.values()) == {"consider"}, ranks


def test_config_weights_change_ranking(tmp_path):
    seed_feature(tmp_path, BORDERLINE_FEATURE, name="search")
    config = tmp_path / ".test-commander" / "config.yaml"
    config.write_text(
        "tc-automate:\n"
        "  suitability:\n"
        "    weights:\n"
        "      traceable: 6\n",
        encoding="utf-8",
    )
    module = load_module()
    outcome = module.build_plan(tmp_path)
    ranks = outcome.ranks_by_area["search"]
    assert set(ranks.values()) == {"automate"}, (
        f"boosting the traceable weight must flip the borderline scenario to "
        f"automate: {ranks}"
    )
