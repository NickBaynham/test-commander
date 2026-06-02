"""Step 13.2 - /tc:watch-changes + /tc:impact-analysis.

Change detection parses a PR/push diff into changed files; impact analysis maps
those files to impacted features and requirements via the workspace impact map
(product-knowledge/impact-map.yaml, produced from Phase-3 knowledge + Phase-5
traceability). Deterministic, read-only, with provenance; never invents impact.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
FIXTURE = REPO / "tests" / "fixtures" / "seeded-continuous"

import impact_analysis  # noqa: E402
import watch_changes  # noqa: E402


def seed(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    ws = project / ".test-commander"
    (ws / "product-knowledge").mkdir(parents=True)
    shutil.copy(FIXTURE / "impact-map.yaml", ws / "product-knowledge" / "impact-map.yaml")
    return project


def diff_path() -> Path:
    return FIXTURE / "pr-diff.txt"


# ---------------------------------------------------------------------------
# /tc:watch-changes
# ---------------------------------------------------------------------------


def test_watch_parses_the_diff_into_changed_files(tmp_path: Path):
    project = seed(tmp_path)
    summary = watch_changes.watch(project, diff_path=diff_path())
    assert "src/auth/signin.py" in summary["changed_files"]
    assert "src/search/query.py" in summary["changed_files"]
    assert "README.md" in summary["changed_files"]
    assert summary["count"] == 3


def test_watch_persists_changes(tmp_path: Path):
    project = seed(tmp_path)
    watch_changes.watch(project, diff_path=diff_path())
    assert (project / ".test-commander" / "continuous" / "changes.json").is_file()


def test_watch_refuses_uninitialized(tmp_path: Path):
    assert watch_changes.main([str(tmp_path / "nope"), "--diff", str(diff_path())]) == 2


# ---------------------------------------------------------------------------
# /tc:impact-analysis
# ---------------------------------------------------------------------------


def test_impact_maps_files_to_features_and_requirements(tmp_path: Path):
    project = seed(tmp_path)
    result = impact_analysis.analyze(project, diff_path=diff_path())
    assert set(result["features"]) == {"sign-in", "search"}
    assert set(result["requirements"]) == {"REQ-001", "REQ-014"}


def test_impact_never_invents_impact(tmp_path: Path):
    project = seed(tmp_path)
    result = impact_analysis.analyze(project, diff_path=diff_path())
    # checkout is in the impact map but no checkout file changed -> not impacted.
    assert "checkout" not in result["features"]
    # README.md matches no pattern -> contributes nothing.
    assert all(p["file"] != "README.md" for p in result["provenance"])


def test_impact_has_provenance(tmp_path: Path):
    project = seed(tmp_path)
    result = impact_analysis.analyze(project, diff_path=diff_path())
    prov = {(p["file"], p["pattern"]) for p in result["provenance"]}
    assert ("src/auth/signin.py", "src/auth/") in prov
    assert ("src/search/query.py", "src/search/") in prov


def test_impact_is_deterministic(tmp_path: Path):
    project = seed(tmp_path)
    a = impact_analysis.analyze(project, diff_path=diff_path())
    b = impact_analysis.analyze(project, diff_path=diff_path())
    assert a == b


def test_impact_writes_a_report(tmp_path: Path):
    project = seed(tmp_path)
    impact_analysis.analyze(project, diff_path=diff_path())
    report = project / ".test-commander" / "continuous" / "impact-analysis.md"
    assert report.is_file()
    assert "sign-in" in report.read_text(encoding="utf-8")


def test_impact_refuses_uninitialized(tmp_path: Path):
    assert impact_analysis.main([str(tmp_path / "nope"), "--diff", str(diff_path())]) == 2


def test_impact_requires_an_impact_map(tmp_path: Path):
    project = tmp_path / "proj"
    (project / ".test-commander").mkdir(parents=True)  # no product-knowledge/impact-map.yaml
    with pytest.raises(FileNotFoundError):
        impact_analysis.analyze(project, diff_path=diff_path())
