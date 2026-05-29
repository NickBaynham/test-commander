"""Step 6.6 - /tc:generate-test-data (generate_test_data) end-to-end tests.

Drives ``generate_test_data.py`` against a tmp consuming project seeded with the
clean ``sign-in.feature``. The helper populates ``<workspace>/test-data/`` from
the BDD scenarios (per Q11: JSON fixtures under ``seed/`` + Markdown specs under
``scenarios/``) so the per-area fixture ``/tc:automate`` generates can reach its
data through a file rather than inlining it (Decision D6).

Asserts the Step 6.6 contract from planning/plan.md:

- uninitialized workspace refused (exit 2);
- no BDD features refused, pointing at /tc:generate-bdd (exit 2);
- a seeded feature populates test-data/seed/<area>.json + scenarios/<area>.md;
- the seed JSON is valid JSON carrying the generated marker;
- the fixture /tc:automate generates references a test-data/ file that now
  exists (the D6 loop closes);
- generation is byte-stable on re-run;
- user-authored data (a file with no generated marker) is preserved.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "generate_test_data.py"
AUTOMATE = SCRIPTS / "automate.py"
PLAN_HELPER = SCRIPTS / "automation_plan.py"
INIT = SCRIPTS / "init_workspace.py"

FIXTURE_FEATURE = REPO / "tests" / "fixtures" / "seeded-automation" / "sign-in.feature"


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


def seed_feature(project_root: Path) -> None:
    run_init(project_root)
    features = project_root / ".test-commander" / "bdd" / "features"
    features.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_FEATURE, features / "sign-in.feature")


def seed_json(project_root: Path, area: str = "sign-in") -> Path:
    return project_root / ".test-commander" / "test-data" / "seed" / f"{area}.json"


def scenario_md(project_root: Path, area: str = "sign-in") -> Path:
    return project_root / ".test-commander" / "test-data" / "scenarios" / f"{area}.md"


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_workspace_refused(tmp_path):
    result = run(HELPER, tmp_path)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_no_features_refused_points_at_generate_bdd(tmp_path):
    run_init(tmp_path)
    result = run(HELPER, tmp_path)
    assert result.returncode == 2, result.stdout
    assert "/tc:generate-bdd" in result.stderr


# ---------------------------------------------------------------------------
# Population
# ---------------------------------------------------------------------------


def test_seeded_populates_test_data(tmp_path):
    seed_feature(tmp_path)
    result = run(HELPER, tmp_path)
    assert result.returncode == 0, result.stderr
    assert seed_json(tmp_path).is_file(), "expected test-data/seed/sign-in.json"
    assert scenario_md(tmp_path).is_file(), "expected test-data/scenarios/sign-in.md"


def test_seed_json_is_valid_and_marked(tmp_path):
    seed_feature(tmp_path)
    run(HELPER, tmp_path)
    data = json.loads(seed_json(tmp_path).read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    assert data.get("_generated_by") == "/tc:generate-test-data", (
        "generated seed JSON must carry the generated marker"
    )


# ---------------------------------------------------------------------------
# The D6 loop: the generated fixture's data reference resolves
# ---------------------------------------------------------------------------


def test_fixture_data_reference_resolves(tmp_path):
    seed_feature(tmp_path)
    assert run(PLAN_HELPER, tmp_path).returncode == 0
    assert run(AUTOMATE, tmp_path, "--no-review").returncode == 0
    fixture = tmp_path / "tests" / "fixtures" / "sign-in.ts"
    fixture_text = fixture.read_text(encoding="utf-8")
    # The fixture points at test-data/seed/sign-in.json (relative to tests/fixtures/).
    assert "test-data/seed/sign-in.json" in fixture_text
    run(HELPER, tmp_path)
    assert seed_json(tmp_path).is_file(), (
        "generate-test-data must create the seed file the fixture references (D6)"
    )


# ---------------------------------------------------------------------------
# Idempotency + user-authored preservation
# ---------------------------------------------------------------------------


def test_idempotent_byte_stable_rerun(tmp_path):
    seed_feature(tmp_path)
    run(HELPER, tmp_path)
    before = snapshot(tmp_path / ".test-commander" / "test-data")
    run(HELPER, tmp_path)
    assert snapshot(tmp_path / ".test-commander" / "test-data") == before


def test_user_authored_data_preserved(tmp_path):
    seed_feature(tmp_path)
    user = seed_json(tmp_path)
    user.parent.mkdir(parents=True, exist_ok=True)
    user.write_text('{"hand": "authored"}\n', encoding="utf-8")
    run(HELPER, tmp_path)
    assert user.read_text(encoding="utf-8") == '{"hand": "authored"}\n', (
        "user-authored data (no generated marker) must be preserved"
    )
