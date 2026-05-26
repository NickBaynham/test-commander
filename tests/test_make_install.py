"""Step 0.7 — make install wiring tests.

Static checks on the Makefile structure and target dependency order. Does
not execute the install chain (that is the 0.7.7 evidence drill).
"""

import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MAKEFILE = REPO / "Makefile"

EXPECTED_INSTALL_CHAIN = [
    "pdm-install",
    "validate-manifests",
    "marketplace-add",
    "plugin-install",
    "verify-skills",
]


def _makefile_text() -> str:
    return MAKEFILE.read_text(encoding="utf-8")


def _target_body(text: str, target: str) -> list[str]:
    """Return the recipe lines (tab-indented) belonging to the given target."""
    lines = text.splitlines()
    body: list[str] = []
    in_target = False
    for line in lines:
        if line.startswith(f"{target}:"):
            in_target = True
            continue
        if in_target:
            if not line:
                continue
            if line.startswith("\t"):
                body.append(line[1:])
            else:
                break
    return body


def _has_target(text: str, target: str) -> bool:
    return any(line.startswith(f"{target}:") for line in text.splitlines())


def test_install_target_exists():
    assert _has_target(_makefile_text(), "install")


def test_uninstall_target_exists():
    assert _has_target(_makefile_text(), "uninstall")


def test_install_depends_on_chain():
    text = _makefile_text()
    install_lines = [line for line in text.splitlines() if line.startswith("install:")]
    assert install_lines, "install target not found"
    deps = install_lines[0].split(":", 1)[1].split()
    for dep in EXPECTED_INSTALL_CHAIN:
        assert dep in deps, f"install missing {dep!r} dependency; got {deps}"
    indices = [deps.index(d) for d in EXPECTED_INSTALL_CHAIN]
    assert indices == sorted(indices), f"install deps out of order: {deps}"


def test_each_chain_target_exists():
    text = _makefile_text()
    for target in EXPECTED_INSTALL_CHAIN:
        assert _has_target(text, target), f"missing target {target!r}"


def test_validate_manifests_invokes_cli_on_both_manifests():
    body = _target_body(_makefile_text(), "validate-manifests")
    joined = "\n".join(body)
    assert "claude plugin validate" in joined
    assert "." in joined  # repo root for marketplace
    assert "plugins/test-commander" in joined


def test_marketplace_add_guards_against_duplicate():
    body = "\n".join(_target_body(_makefile_text(), "marketplace-add"))
    assert "marketplace list" in body
    assert "marketplace add" in body
    assert "test-commander-marketplace" in body


def test_plugin_install_guards_against_duplicate():
    body = "\n".join(_target_body(_makefile_text(), "plugin-install"))
    assert "plugin list" in body
    assert "plugin install" in body
    assert "test-commander" in body


def test_uninstall_tolerates_clean_state():
    body = _target_body(_makefile_text(), "uninstall")
    assert body, "uninstall has no recipe lines"
    for line in body:
        stripped = line.strip()
        if not stripped or stripped.startswith("@"):
            continue
        tolerates = stripped.startswith("-") or "|| true" in stripped
        assert tolerates, f"uninstall command does not tolerate clean state: {stripped!r}"


def test_help_lists_new_targets():
    if shutil.which("make") is None:  # pragma: no cover
        pytest.skip("make not on PATH")
    result = subprocess.run(
        ["make", "help"], capture_output=True, text=True, cwd=REPO, check=False
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout
    assert "install" in out
    assert "uninstall" in out
    assert "verify" in out
