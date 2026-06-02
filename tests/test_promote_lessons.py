"""Step 8.7 - /tc:promote-lessons (promote_lessons) end-to-end tests.

Drives ``promote_lessons.py`` against a tmp project whose
``learning/accepted-lessons.md`` carries accepted lessons. By default the helper
writes a promotion *proposal* and changes no guidance; only ``--apply`` (the
human gate) moves accepted lessons into ``learning/promoted-guidance.md`` with
``status: promoted``. A ``core: true`` lesson renders a core-promotion proposal
(never auto-applied). It writes only under ``learning/``.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "plugins" / "test-commander" / "scripts"
HELPER = SCRIPTS / "promote_lessons.py"
INIT = SCRIPTS / "init_workspace.py"

ACCEPTED = (
    "# Accepted Lessons\n\n"
    "---\nschema: tc-lesson/v1\nid: LESSON-001\nsource: /tc:learn-from-failures\n"
    "origin: runs/RUN-1/analysis.md:7\ncategory: product-defect-pattern\nseverity: medium\n"
    "status: accepted\ncaptured_at: 2026-01-15T09:30:00\n"
    'summary: "assert the sign-in rejection error copy"\n---\n\n'
    "Add an explicit assertion on the rejection error copy.\n\n"
    "---\nschema: tc-lesson/v1\nid: LESSON-002\nsource: /tc:learn\n"
    "origin: manual\ncategory: heuristic\nseverity: low\nstatus: accepted\n"
    "core: true\ncaptured_at: 2026-01-15T09:30:00\n"
    'summary: "the triage rubric should record an environment sub-reason"\n---\n\n'
    "A heuristic that argues for a change to Test Commander's own triage doctrine.\n"
)


def run_init(project_root: Path) -> None:
    subprocess.run([sys.executable, str(INIT), str(project_root)],
                   capture_output=True, text=True, check=True)


def cli(project_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(HELPER), str(project_root), *args],
                          capture_output=True, text=True)


def load():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("promote_lessons", HELPER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def learning(project_root: Path) -> Path:
    return project_root / ".test-commander" / "learning"


def seed_accepted(project_root: Path) -> Path:
    run_init(project_root)
    ldir = learning(project_root)
    (ldir / "accepted-lessons.md").write_text(ACCEPTED, encoding="utf-8")
    return ldir


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def snapshot_outside_learning(project_root: Path) -> dict[Path, bytes]:
    ws = project_root / ".test-commander"
    return {
        p.relative_to(ws): p.read_bytes()
        for p in sorted(ws.rglob("*"))
        if p.is_file() and "learning" not in p.relative_to(ws).parts
    }


def test_uninitialized_workspace_refused(tmp_path):
    result = cli(tmp_path)
    assert result.returncode == 2, result.stderr
    assert "init" in result.stderr.lower()


def test_no_accepted_refused(tmp_path):
    run_init(tmp_path)  # accepted-lessons is the template stub
    result = cli(tmp_path)
    assert result.returncode == 2, result.stdout
    assert "/tc:review-lessons" in result.stderr


def test_default_proposes_without_changing_guidance(tmp_path):
    ldir = seed_accepted(tmp_path)
    mod = load()
    mod.promote(tmp_path, apply=False)
    assert (ldir / "promotion-proposal.md").is_file(), "default must write a proposal"
    assert not (ldir / "promoted-guidance.md").is_file(), (
        "default must NOT change promoted-guidance.md (the human gate)"
    )


def test_apply_promotes_into_guidance(tmp_path):
    ldir = seed_accepted(tmp_path)
    mod = load()
    mod.promote(tmp_path, apply=True)
    guidance = read(ldir / "promoted-guidance.md")
    assert "LESSON-001" in guidance and "status: promoted" in guidance
    # The accepted lesson is marked promoted so it is not re-promoted.
    assert "status: promoted" in read(ldir / "accepted-lessons.md")


def test_apply_renders_core_proposal_for_core_lesson(tmp_path):
    ldir = seed_accepted(tmp_path)
    mod = load()
    mod.promote(tmp_path, apply=True)
    core = read(ldir / "core-promotion-proposal.md")
    assert "LESSON-002" in core, "a core: true lesson must render a core-promotion proposal"
    # A core lesson is an upstream proposal, not local guidance.
    assert "LESSON-002" not in read(ldir / "promoted-guidance.md")


def test_apply_writes_only_under_learning(tmp_path):
    seed_accepted(tmp_path)
    before = snapshot_outside_learning(tmp_path)
    load().promote(tmp_path, apply=True)
    after = snapshot_outside_learning(tmp_path)
    assert after == before, "promotion must write only under learning/ (Q6)"


def test_apply_idempotent(tmp_path):
    ldir = seed_accepted(tmp_path)
    mod = load()
    mod.promote(tmp_path, apply=True)
    guidance = read(ldir / "promoted-guidance.md")
    mod.promote(tmp_path, apply=True)
    assert read(ldir / "promoted-guidance.md") == guidance, "re-apply must not re-promote"
