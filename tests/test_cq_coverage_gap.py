"""Step 13.3 - /tc:coverage-gap-analysis.

Takes the impacted set and checks it against existing coverage (the test map /
automation plan at traceability/coverage.yaml). An impacted feature that is not
automated - or has no coverage record at all - is a gap, surfaced with
provenance. Read-only and deterministic; never invents coverage.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
FIXTURE = REPO / "tests" / "fixtures" / "seeded-continuous"

import coverage_gap_analysis  # noqa: E402
import impact_analysis  # noqa: E402


def seed(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    (ws / "product-knowledge").mkdir(parents=True)
    (ws / "traceability").mkdir(parents=True)
    shutil.copy(FIXTURE / "impact-map.yaml", ws / "product-knowledge" / "impact-map.yaml")
    shutil.copy(FIXTURE / "coverage.yaml", ws / "traceability" / "coverage.yaml")
    return project


def test_gap_flags_uncovered_impacted_feature(tmp_path: Path):
    project = seed(tmp_path)
    result = coverage_gap_analysis.analyze(project, impacted_features=["sign-in", "search"])
    gap_features = {g["feature"] for g in result["gaps"]}
    assert gap_features == {"search"}  # search is impacted but not automated
    assert "sign-in" in result["covered"]


def test_gap_has_provenance(tmp_path: Path):
    project = seed(tmp_path)
    result = coverage_gap_analysis.analyze(project, impacted_features=["search"])
    gap = result["gaps"][0]
    assert gap["reason"] == "not automated"
    assert gap["source"]  # cites where the (lack of) coverage was recorded


def test_gap_never_invents_coverage(tmp_path: Path):
    project = seed(tmp_path)
    # A feature with no coverage record is a gap, not assumed covered.
    result = coverage_gap_analysis.analyze(project, impacted_features=["unknown-feature"])
    assert result["gaps"][0]["feature"] == "unknown-feature"
    assert result["gaps"][0]["reason"] == "no coverage record"
    assert result["covered"] == []


def test_gap_reads_impacted_set_from_impact_json(tmp_path: Path):
    project = seed(tmp_path)
    impact_analysis.analyze(project, diff_path=FIXTURE / "pr-diff.txt")
    result = coverage_gap_analysis.analyze(project)  # reads impact.json
    assert {g["feature"] for g in result["gaps"]} == {"search"}


def test_gap_is_deterministic(tmp_path: Path):
    project = seed(tmp_path)
    a = coverage_gap_analysis.analyze(project, impacted_features=["sign-in", "search"])
    b = coverage_gap_analysis.analyze(project, impacted_features=["sign-in", "search"])
    assert a == b


def test_gap_writes_report(tmp_path: Path):
    project = seed(tmp_path)
    coverage_gap_analysis.analyze(project, impacted_features=["sign-in", "search"])
    report = project / ".test-commander" / "continuous" / "coverage-gap-analysis.md"
    assert report.is_file() and "search" in report.read_text(encoding="utf-8")


def test_gap_refuses_uninitialized(tmp_path: Path):
    assert coverage_gap_analysis.main([str(tmp_path / "nope")]) == 2


def test_gap_requires_a_coverage_map(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".test-commander").mkdir(parents=True)  # no traceability/coverage.yaml
    with pytest.raises(FileNotFoundError):
        coverage_gap_analysis.analyze(project, impacted_features=["search"])
