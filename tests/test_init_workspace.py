"""Step 1.2 — /tc:init helper tests.

Four cases per the plan:
  - fresh init (target dir is empty)
  - idempotent re-init (second call skips everything)
  - partial-existing (some files already present; only missing files created)
  - refusal on invalid target (file path, not a directory)
"""

from pathlib import Path

import init_workspace
import pytest

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "plugins" / "test-commander" / "templates" / "workspace"


def _template_file_count() -> int:
    return sum(1 for p in TEMPLATE.rglob("*") if p.is_file())


def test_fresh_init_creates_full_workspace(tmp_path):
    result = init_workspace.init_workspace(tmp_path)
    assert result.workspace == tmp_path / ".test-commander"
    assert result.workspace.is_dir()
    expected = _template_file_count()
    assert len(result.created) == expected
    assert len(result.skipped) == 0
    # Spot-check canonical paths
    assert (result.workspace / "project.md").is_file()
    assert (result.workspace / "policy" / "permissions.yaml").is_file()
    assert (result.workspace / "audit" / "actions.jsonl").is_file()


def test_idempotent_reinit_skips_everything(tmp_path):
    init_workspace.init_workspace(tmp_path)
    result = init_workspace.init_workspace(tmp_path)
    expected = _template_file_count()
    assert len(result.created) == 0
    assert len(result.skipped) == expected


def test_partial_existing_only_creates_missing(tmp_path):
    workspace = tmp_path / ".test-commander"
    workspace.mkdir()
    pre_existing = workspace / "project.md"
    pre_existing.write_text("# my customized project\n", encoding="utf-8")
    result = init_workspace.init_workspace(tmp_path)
    expected_total = _template_file_count()
    assert len(result.created) == expected_total - 1
    assert len(result.skipped) == 1
    # The pre-existing file's content is preserved
    assert pre_existing.read_text(encoding="utf-8") == "# my customized project\n"


def test_refuses_invalid_target_that_is_a_file(tmp_path):
    target = tmp_path / "not_a_dir"
    target.write_text("hello", encoding="utf-8")
    with pytest.raises(NotADirectoryError):
        init_workspace.init_workspace(target)
