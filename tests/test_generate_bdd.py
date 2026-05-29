"""Step 5.2 - /tc:generate-bdd (generate_bdd) end-to-end tests.

Drives ``generate_bdd.py`` against a tmp consuming project seeded with the
Phase-4-enriched ``REQ-001.md`` test-idea from ``tests/fixtures/seeded-bdd/``.
The helper turns each Phase-4 enrichment candidate (``CS-NNN-NNN``) into a
Gherkin scenario carrying machine-readable ``@req:``/``@cs:`` linkage tags
plus an ``@area:`` namespace tag, writes a per-feature summary, and rebuilds
the feature index.

Asserts the Step 5.2 contract from planning/plan.md:

- uninitialized workspace refused (exit 2);
- no enriched test-ideas refused with a precondition error pointing at
  ``/tc:test-ideas`` (exit 2);
- a seeded enriched seed produces a valid Gherkin feature with one scenario
  per candidate, every scenario carrying resolvable ``@req:``/``@cs:`` and an
  ``@area:`` tag;
- the ``Scenario`` dataclass recovers ``cs_id``/``type``/``title``/``source``
  from the enriched body (the cross-phase contract triangle);
- a per-feature summary is written and the feature index lists the feature;
- idempotent re-run is byte-identical;
- ``tc-bdd.tags.extra-classes`` config extensions union with the universal
  class tags.

Review wiring (the generate-time ``--no-review`` auto-run) ships in Step 5.3;
5.2 is generation-only.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "generate_bdd.py"
INIT = SCRIPTS / "init_workspace.py"

FIXTURE_DIR = REPO / "tests" / "fixtures" / "seeded-bdd"
FIXTURE_TEST_IDEA = FIXTURE_DIR / "REQ-001.md"
FIXTURE_SESSION = FIXTURE_DIR / "SESS-20260115-001.md"


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


def run_generate(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HELPER), str(project_root), *args],
        capture_output=True,
        text=True,
    )


def seed_enriched_workspace(project_root: Path) -> Path:
    """Init a workspace and drop the seeded enriched REQ-001 + its session."""
    run_init(project_root)
    ws = project_root / ".test-commander"
    (ws / "test-ideas").mkdir(parents=True, exist_ok=True)
    (ws / "sessions").mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_TEST_IDEA, ws / "test-ideas" / "REQ-001.md")
    shutil.copy(FIXTURE_SESSION, ws / "sessions" / "SESS-20260115-001.md")
    return ws


def features(ws: Path) -> list[Path]:
    return sorted((ws / "bdd" / "features").glob("*.feature"))


def load_module():
    spec = importlib.util.spec_from_file_location("generate_bdd", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module  # required so @dataclass can resolve annotations
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_workspace_refused(tmp_path):
    result = run_generate(tmp_path)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_no_enriched_test_ideas_refused(tmp_path):
    run_init(tmp_path)
    result = run_generate(tmp_path)
    assert result.returncode == 2, result.stdout
    assert "/tc:test-ideas" in result.stderr


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def test_generates_feature_with_linkage_tags(tmp_path):
    ws = seed_enriched_workspace(tmp_path)
    result = run_generate(tmp_path)
    assert result.returncode == 0, result.stderr
    feats = features(ws)
    assert len(feats) == 1, f"expected one feature file, got {feats}"
    text = feats[0].read_text(encoding="utf-8")
    assert text.lstrip().startswith("#") or "Feature:" in text
    assert "Feature:" in text
    # one scenario per Phase-4 candidate (CS-001-001 / 002 / 003)
    assert text.count("Scenario:") == 3, text
    for cs in ("CS-001-001", "CS-001-002", "CS-001-003"):
        assert f"@cs:{cs}" in text, f"missing linkage tag @cs:{cs}"
    assert text.count("@req:REQ-001") >= 3, "every scenario must carry @req:REQ-001"
    assert "@area:" in text, "feature must carry an @area: namespace tag"


def test_generated_scenarios_have_area_tag_each(tmp_path):
    ws = seed_enriched_workspace(tmp_path)
    run_generate(tmp_path)
    text = features(ws)[0].read_text(encoding="utf-8")
    # Each scenario block (tag line preceding `Scenario:`) carries @area.
    scenario_tag_lines = [
        line for line in text.splitlines()
        if line.strip().startswith("@") and "@cs:" in line
    ]
    assert len(scenario_tag_lines) == 3
    for line in scenario_tag_lines:
        assert "@area:" in line, f"scenario tag line missing @area: {line}"
        assert "@req:REQ-001" in line


def test_summary_written(tmp_path):
    ws = seed_enriched_workspace(tmp_path)
    run_generate(tmp_path)
    summaries = sorted((ws / "bdd" / "summaries").glob("*.md"))
    summaries = [p for p in summaries if p.name != "README.md"]
    assert len(summaries) == 1, f"expected one summary, got {summaries}"
    body = summaries[0].read_text(encoding="utf-8")
    assert "REQ-001" in body
    for cs in ("CS-001-001", "CS-001-002", "CS-001-003"):
        assert cs in body


def test_index_lists_feature(tmp_path):
    ws = seed_enriched_workspace(tmp_path)
    run_generate(tmp_path)
    index = (ws / "bdd" / "index.md").read_text(encoding="utf-8")
    assert "REQ-001" in index
    feat_name = features(ws)[0].name
    assert feat_name in index


def test_scenario_shape_contract_recovers_every_field(tmp_path):
    """Cross-phase contract triangle: parsing the enriched body recovers
    cs_id / type / title / source for every candidate."""
    module = load_module()
    scenarios = module.parse_scenarios(FIXTURE_TEST_IDEA)
    by_id = {s.cs_id: s for s in scenarios}
    assert set(by_id) == {"CS-001-001", "CS-001-002", "CS-001-003"}
    neg = by_id["CS-001-001"]
    assert neg.req_id == "REQ-001"
    assert neg.type == "negative"
    assert neg.title == "Expired session routes the holder back to sign-in"
    assert neg.source == "anomaly:auth-mismatch"
    assert neg.linked_anomaly == "auth-mismatch"
    # a candidate without linked_anomaly parses linked_anomaly as None
    assert by_id["CS-001-002"].linked_anomaly is None


def test_idempotent_rerun_byte_identical(tmp_path):
    ws = seed_enriched_workspace(tmp_path)
    run_generate(tmp_path)
    first = {p: p.read_bytes() for p in features(ws)}
    first_index = (ws / "bdd" / "index.md").read_bytes()
    run_generate(tmp_path)
    second = {p: p.read_bytes() for p in features(ws)}
    assert first == second, "feature files must be byte-stable across re-runs"
    assert first_index == (ws / "bdd" / "index.md").read_bytes()


def test_config_extra_classes_union(tmp_path):
    ws = seed_enriched_workspace(tmp_path)
    config = ws / "config.yaml"
    config.write_text(
        "tc-bdd:\n  tags:\n    extra-classes: [\"@automated-candidate\"]\n",
        encoding="utf-8",
    )
    run_generate(tmp_path)
    text = features(ws)[0].read_text(encoding="utf-8")
    assert "@automated-candidate" in text, "config extra-classes must union into tags"
    # universal class tags still present
    assert "@regression" in text or "@smoke" in text
