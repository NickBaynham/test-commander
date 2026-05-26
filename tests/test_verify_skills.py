"""Step 0.6 — skill verifier tests.

Covers the 10 automated DoD checks for Step 0.6 in planning/plan.md.
The two manual checks (Makefile wiring and live drill) are validated
separately during 0.6.6 and 0.6.7.
"""

import subprocess
import sys
from pathlib import Path

import verify_skills

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "verify_skills.py"


def _write_skill(skills_root: Path, name: str, frontmatter_body: str) -> Path:
    skill_dir = skills_root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(f"---\n{frontmatter_body}\n---\n\nBody.\n")
    return skill_md


# --- Frontmatter parser ---

def test_parse_valid_frontmatter(tmp_path):
    skill_md = _write_skill(
        tmp_path, "tc-core", "name: tc-core\ndescription: Core orchestration."
    )
    result = verify_skills.parse_frontmatter(skill_md, expected_name="tc-core")
    assert result.ok
    assert result.name == "tc-core"
    assert result.description == "Core orchestration."


def test_parse_missing_name(tmp_path):
    skill_md = _write_skill(tmp_path, "tc-core", "description: nope")
    result = verify_skills.parse_frontmatter(skill_md, expected_name="tc-core")
    assert not result.ok
    assert "name" in result.reason.lower()


def test_parse_missing_description(tmp_path):
    skill_md = _write_skill(tmp_path, "tc-core", "name: tc-core")
    result = verify_skills.parse_frontmatter(skill_md, expected_name="tc-core")
    assert not result.ok
    assert "description" in result.reason.lower()


def test_parse_empty_description(tmp_path):
    skill_md = _write_skill(tmp_path, "tc-core", "name: tc-core\ndescription:   ")
    result = verify_skills.parse_frontmatter(skill_md, expected_name="tc-core")
    assert not result.ok
    assert "description" in result.reason.lower()


def test_parse_non_kebab_name(tmp_path):
    skill_md = _write_skill(
        tmp_path, "Tc-Core", "name: Tc-Core\ndescription: nope"
    )
    result = verify_skills.parse_frontmatter(skill_md, expected_name="Tc-Core")
    assert not result.ok
    assert "kebab" in result.reason.lower()


def test_parse_name_directory_mismatch(tmp_path):
    skill_md = _write_skill(
        tmp_path, "tc-core", "name: tc-other\ndescription: nope"
    )
    result = verify_skills.parse_frontmatter(skill_md, expected_name="tc-core")
    assert not result.ok
    assert "match" in result.reason.lower() or "directory" in result.reason.lower()


# --- Walker ---

def test_walker_present(tmp_path):
    _write_skill(tmp_path, "tc-core", "name: tc-core\ndescription: ok")
    results = verify_skills.walk_skills(tmp_path, {"tc-core": 0})
    assert results["tc-core"].status == "PRESENT"


def test_walker_missing(tmp_path):
    tmp_path.mkdir(exist_ok=True)
    results = verify_skills.walk_skills(tmp_path, {"tc-core": 0})
    assert results["tc-core"].status == "MISSING"


def test_walker_malformed(tmp_path):
    _write_skill(tmp_path, "tc-core", "name: tc-core")  # missing description
    results = verify_skills.walk_skills(tmp_path, {"tc-core": 0})
    assert results["tc-core"].status == "MALFORMED"


def test_walker_unexpected(tmp_path):
    _write_skill(tmp_path, "tc-rogue", "name: tc-rogue\ndescription: ok")
    results = verify_skills.walk_skills(tmp_path, {"tc-core": 0})
    assert results["tc-rogue"].status == "UNEXPECTED"
    assert results["tc-core"].status == "MISSING"


def test_walker_phase_filter(tmp_path):
    _write_skill(tmp_path, "tc-core", "name: tc-core\ndescription: ok")
    catalog = {"tc-core": 0, "tc-requirements": 2}
    cap0 = verify_skills.walk_skills(tmp_path, catalog, phase_cap=0)
    assert "tc-core" in cap0
    assert "tc-requirements" not in cap0
    cap2 = verify_skills.walk_skills(tmp_path, catalog, phase_cap=2)
    assert "tc-core" in cap2
    assert cap2["tc-requirements"].status == "MISSING"


# --- Reporter and exit code ---

def test_exit_code_zero_when_all_present(tmp_path):
    _write_skill(tmp_path, "tc-core", "name: tc-core\ndescription: ok")
    results = verify_skills.walk_skills(tmp_path, {"tc-core": 0})
    _, exit_code = verify_skills.report(results)
    assert exit_code == 0


def test_exit_code_nonzero_when_missing(tmp_path):
    tmp_path.mkdir(exist_ok=True)
    results = verify_skills.walk_skills(tmp_path, {"tc-core": 0})
    _, exit_code = verify_skills.report(results)
    assert exit_code == 1


def test_exit_code_nonzero_when_malformed(tmp_path):
    _write_skill(tmp_path, "tc-core", "name: tc-core")
    results = verify_skills.walk_skills(tmp_path, {"tc-core": 0})
    _, exit_code = verify_skills.report(results)
    assert exit_code == 1


def test_exit_code_zero_with_only_unexpected(tmp_path):
    _write_skill(tmp_path, "tc-rogue", "name: tc-rogue\ndescription: ok")
    results = verify_skills.walk_skills(tmp_path, {}, phase_cap=0)
    _, exit_code = verify_skills.report(results)
    assert exit_code == 0


# --- Live end-to-end ---

def test_live_run_against_repo():
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert "tc-core" in result.stdout
    assert "PRESENT" in result.stdout
    assert result.returncode == 0, (
        f"exit code {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
