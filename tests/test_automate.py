"""Step 6.4 - /tc:automate (automate, generation only) end-to-end tests.

Drives ``automate.py`` against a tmp consuming project seeded with the clean
``sign-in.feature`` from ``tests/fixtures/seeded-automation/`` and its
``/tc:automation-plan`` output. The helper builds the framework lazily, then
renders TypeScript page objects (``tests/pages/``), per-area fixtures
(``tests/fixtures/``), and specs (``tests/e2e/<area>.spec.ts``) for
``automate``-ranked / ``@automated-candidate`` scenarios, each carrying a
``// @req:REQ-NNN @cs:CS-NNN-NNN`` provenance comment and reaching test data
only through a fixture. It writes ``traceability/automation-map.md`` linking
each scenario to its spec.

Asserts the Step 6.4 contract from planning/plan.md:

- uninitialized workspace refused (exit 2);
- no automation plan refused, pointing at /tc:automation-plan (exit 2);
- a seeded clean feature produces a spec + page object with valid TS structure,
  provenance comments, and a fixture-mediated data reference (no inlined data);
- the framework is auto-built when absent (lazy-init via ensure_framework);
- automation-map.md links each scenario to its spec;
- the generated tree is byte-stable on re-run and a user-edits region in the
  page object is preserved;
- the cross-phase write boundary holds (bdd/ and product-knowledge/ untouched).

Review wiring (the generate-time auto-run and /tc:review-automation) ships in
Step 6.5; 6.4 is generation-only. No browser is launched and no
``npx playwright test`` is run.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "automate.py"
PLAN_HELPER = SCRIPTS / "automation_plan.py"
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


def run_plan(project_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PLAN_HELPER), str(project_root)],
        capture_output=True,
        text=True,
    )


def run_automate(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HELPER), str(project_root), *args],
        capture_output=True,
        text=True,
    )


def load_module():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("automate", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def seed_feature(project_root: Path) -> None:
    run_init(project_root)
    features_dir = project_root / ".test-commander" / "bdd" / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURE_FEATURE, features_dir / "sign-in.feature")


def seed_planned(project_root: Path) -> None:
    """Init, seed the clean feature, and run /tc:automation-plan."""
    seed_feature(project_root)
    result = run_plan(project_root)
    assert result.returncode == 0, result.stderr


def spec_path(project_root: Path, area: str = "sign-in") -> Path:
    return project_root / "tests" / "e2e" / f"{area}.spec.ts"


def page_path(project_root: Path, name: str = "SignInPage") -> Path:
    return project_root / "tests" / "pages" / f"{name}.ts"


def map_path(project_root: Path) -> Path:
    return project_root / ".test-commander" / "traceability" / "automation-map.md"


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def balanced(text: str) -> bool:
    depth = 0
    for ch in text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


# ---------------------------------------------------------------------------
# Preconditions
# ---------------------------------------------------------------------------


def test_uninitialized_workspace_refused(tmp_path):
    result = run_automate(tmp_path)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_no_plan_refused_points_at_automation_plan(tmp_path):
    seed_feature(tmp_path)  # feature present but /tc:automation-plan not run
    result = run_automate(tmp_path)
    assert result.returncode == 2, result.stdout
    assert "/tc:automation-plan" in result.stderr


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def test_generates_spec_and_page_object(tmp_path):
    seed_planned(tmp_path)
    result = run_automate(tmp_path)
    assert result.returncode == 0, result.stderr
    assert spec_path(tmp_path).is_file(), "expected tests/e2e/sign-in.spec.ts"
    assert page_path(tmp_path).is_file(), "expected tests/pages/SignInPage.ts"


def test_spec_carries_provenance(tmp_path):
    seed_planned(tmp_path)
    run_automate(tmp_path)
    spec = spec_path(tmp_path).read_text(encoding="utf-8")
    assert "@req:REQ-001" in spec, "spec must carry a @req: provenance comment"
    assert "@cs:CS-001-" in spec, "spec must carry a @cs: provenance comment"


def test_spec_reaches_data_via_fixture_not_inline(tmp_path):
    seed_planned(tmp_path)
    run_automate(tmp_path)
    spec = spec_path(tmp_path).read_text(encoding="utf-8")
    assert "../fixtures/sign-in" in spec, "spec must import its per-area fixture"
    fixture = tmp_path / "tests" / "fixtures" / "sign-in.ts"
    assert fixture.is_file(), "expected a generated per-area fixture"
    assert "test-data" in fixture.read_text(encoding="utf-8"), (
        "fixture must reach data via the .test-commander/test-data/ tree (D6)"
    )


def test_spec_has_a_real_assertion(tmp_path):
    """The generated TS is authored to pass the Step 6.5 review (not
    assertion-free)."""
    seed_planned(tmp_path)
    run_automate(tmp_path)
    spec = spec_path(tmp_path).read_text(encoding="utf-8")
    assert "expect(" in spec, "spec must contain at least one assertion"


def test_generated_ts_is_well_formed(tmp_path):
    seed_planned(tmp_path)
    run_automate(tmp_path)
    for path in (spec_path(tmp_path), page_path(tmp_path)):
        text = path.read_text(encoding="utf-8")
        assert balanced(text), f"{path.name} has unbalanced brackets"
        assert "import" in text, f"{path.name} must have imports"
    # The page object imports @playwright/test directly; the spec imports
    # test/expect from its per-area fixture (the D6 fixture-mediated path).
    assert "@playwright/test" in page_path(tmp_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Lazy-init
# ---------------------------------------------------------------------------


def test_lazy_init_builds_framework_when_absent(tmp_path):
    seed_planned(tmp_path)
    assert not (tmp_path / "tests" / "playwright.config.ts").exists()
    run_automate(tmp_path)
    assert (tmp_path / "tests" / "playwright.config.ts").is_file(), (
        "automate must build the framework lazily via ensure_framework"
    )


# ---------------------------------------------------------------------------
# Traceability hand-off
# ---------------------------------------------------------------------------


def test_automation_map_links_scenario_to_spec(tmp_path):
    seed_planned(tmp_path)
    run_automate(tmp_path)
    text = map_path(tmp_path).read_text(encoding="utf-8")
    assert "REQ-001" in text
    assert "CS-001-" in text
    assert "tests/e2e/sign-in.spec.ts" in text


# ---------------------------------------------------------------------------
# Idempotency + write boundary
# ---------------------------------------------------------------------------


def test_idempotent_byte_stable_rerun(tmp_path):
    seed_planned(tmp_path)
    run_automate(tmp_path)
    before_tree = snapshot(tmp_path / "tests")
    before_map = map_path(tmp_path).read_bytes()
    run_automate(tmp_path)
    assert snapshot(tmp_path / "tests") == before_tree
    assert map_path(tmp_path).read_bytes() == before_map


def test_preserves_user_edits_region_in_page_object(tmp_path):
    seed_planned(tmp_path)
    run_automate(tmp_path)
    page = page_path(tmp_path)
    text = page.read_text(encoding="utf-8")
    marker = "// === end custom methods ==="
    assert marker in text, "page object must carry a preserved user-edits region"
    edited = text.replace(
        marker, "  async customStep(): Promise<void> {}\n" + "  " + marker
    )
    page.write_text(edited, encoding="utf-8")
    run_automate(tmp_path)
    assert "customStep" in page.read_text(encoding="utf-8"), (
        "re-run must preserve the user-edits region of the page object"
    )


def test_write_boundary_bdd_and_knowledge_untouched(tmp_path):
    seed_planned(tmp_path)
    ws = tmp_path / ".test-commander"
    before_bdd = snapshot(ws / "bdd")
    before_pk = snapshot(ws / "product-knowledge")
    run_automate(tmp_path)
    assert snapshot(ws / "bdd") == before_bdd, "automate must not write bdd/"
    assert snapshot(ws / "product-knowledge") == before_pk, (
        "automate must not write product-knowledge/"
    )
