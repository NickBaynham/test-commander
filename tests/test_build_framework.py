"""Step 6.2 - /tc:build-framework (build_framework) end-to-end tests.

Drives ``build_framework.py`` against a tmp consuming project. The helper
scaffolds the project-root Playwright/TypeScript framework lazily: the
``tests/{e2e,pages,components,fixtures,utils}/`` tree plus
``tests/playwright.config.ts`` and ``tests/package.json``, created only when
absent and a byte-stable no-op on re-run.

Asserts the Step 6.2 contract from planning/plan.md:

- uninitialized workspace refused (exit 2);
- a first run scaffolds the full tree with ``playwright.config.ts`` and
  ``package.json``;
- re-running is a byte-stable no-op (``created: 0``);
- the generated config and the four bundled ``.ts`` object templates parse as
  well-formed TypeScript (structural assertion only - the suite never invokes
  ``tsc`` or Playwright);
- ``package.json`` is valid JSON declaring the ``@playwright/test`` dev dep;
- ``ensure_framework`` is the lazy-init entry point the Phase 6.4 generator
  will call before rendering any TypeScript.

No browser is launched and no ``npx playwright test`` is run: Phase 6 generates
and structurally validates artifacts; execution is Phase 7's ``/tc:run``.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "build_framework.py"
INIT = SCRIPTS / "init_workspace.py"

TEMPLATES_DIR = (
    REPO / "plugins" / "test-commander" / "skills" / "tc-build-framework" / "templates"
)
OBJECT_TEMPLATES = [
    "page-object-template.ts",
    "component-object-template.ts",
    "playwright-spec-template.ts",
    "fixture-template.ts",
]
SUBDIRS = ["e2e", "pages", "components", "fixtures", "utils"]


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


def run_build(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HELPER), str(project_root), *args],
        capture_output=True,
        text=True,
    )


def load_module():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("build_framework", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def snapshot_tree(tests_dir: Path) -> dict[str, bytes]:
    """Map every file under tests/ to its bytes (for byte-stability checks)."""
    return {
        str(p.relative_to(tests_dir)): p.read_bytes()
        for p in sorted(tests_dir.rglob("*"))
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
    result = run_build(tmp_path)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


# ---------------------------------------------------------------------------
# First run - scaffolds the tree
# ---------------------------------------------------------------------------


def test_first_run_scaffolds_full_tree(tmp_path):
    run_init(tmp_path)
    result = run_build(tmp_path)
    assert result.returncode == 0, result.stderr
    tests_dir = tmp_path / "tests"
    assert (tests_dir / "playwright.config.ts").is_file()
    assert (tests_dir / "package.json").is_file()
    for sub in SUBDIRS:
        assert (tests_dir / sub).is_dir(), f"missing tests/{sub}/"


def test_first_run_reports_created(tmp_path):
    run_init(tmp_path)
    result = run_build(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "created" in result.stdout.lower()


# ---------------------------------------------------------------------------
# Idempotency - byte-stable no-op on re-run
# ---------------------------------------------------------------------------


def test_rerun_is_byte_stable_noop(tmp_path):
    run_init(tmp_path)
    run_build(tmp_path)
    tests_dir = tmp_path / "tests"
    before = snapshot_tree(tests_dir)
    result = run_build(tmp_path)
    assert result.returncode == 0, result.stderr
    after = snapshot_tree(tests_dir)
    assert before == after, "re-run must not change any framework file"


def test_rerun_creates_nothing(tmp_path):
    module = load_module()
    run_init(tmp_path)
    module.ensure_framework(tmp_path)
    outcome = module.ensure_framework(tmp_path)
    assert outcome.created == [], f"re-run created {outcome.created}"
    assert outcome.skipped, "re-run must report skipped paths"


# ---------------------------------------------------------------------------
# Structural validity (no tsc, no browser)
# ---------------------------------------------------------------------------


def test_playwright_config_is_well_formed(tmp_path):
    run_init(tmp_path)
    run_build(tmp_path)
    config = (tmp_path / "tests" / "playwright.config.ts").read_text(encoding="utf-8")
    assert "defineConfig" in config, "config must call defineConfig"
    assert "export default defineConfig(" in config
    assert "testDir" in config, "config must set testDir"
    assert balanced(config), "config has unbalanced brackets"


def test_package_json_is_valid_json_with_playwright(tmp_path):
    run_init(tmp_path)
    run_build(tmp_path)
    data = json.loads((tmp_path / "tests" / "package.json").read_text(encoding="utf-8"))
    assert data.get("name"), "package.json must have a name"
    assert "test" in data.get("scripts", {}), "package.json must define a test script"
    dev = data.get("devDependencies", {})
    assert "@playwright/test" in dev, "package.json must declare @playwright/test"


def test_object_templates_present_and_well_formed(tmp_path):
    for name in OBJECT_TEMPLATES:
        path = TEMPLATES_DIR / name
        assert path.is_file(), f"missing bundled template {name}"
        text = path.read_text(encoding="utf-8")
        assert balanced(text), f"{name} has unbalanced brackets"
        assert "import" in text, f"{name} must import from @playwright/test"
        assert "@playwright/test" in text, f"{name} must reference @playwright/test"


def test_spec_template_carries_provenance_placeholder():
    text = (TEMPLATES_DIR / "playwright-spec-template.ts").read_text(encoding="utf-8")
    assert "@req:" in text and "@cs:" in text, (
        "spec template must carry a @req:/@cs: provenance comment placeholder"
    )


def test_fixture_template_reaches_data_via_test_data():
    text = (TEMPLATES_DIR / "fixture-template.ts").read_text(encoding="utf-8")
    assert "test-data" in text, (
        "fixture template must reach data via the .test-commander/test-data/ tree (D6)"
    )


# ---------------------------------------------------------------------------
# Lazy-init entry point
# ---------------------------------------------------------------------------


def test_ensure_framework_builds_when_absent(tmp_path):
    module = load_module()
    run_init(tmp_path)
    outcome = module.ensure_framework(tmp_path)
    assert outcome.created, "ensure_framework must build the framework when absent"
    assert (tmp_path / "tests" / "playwright.config.ts").is_file()


def test_ensure_framework_refuses_uninitialized(tmp_path):
    module = load_module()
    try:
        module.ensure_framework(tmp_path)
    except module.UninitializedWorkspaceError:
        return
    raise AssertionError("ensure_framework must refuse an uninitialized workspace")
