"""Step 12.3 - the six /tc:sandbox-* command helpers.

Each helper is a self-contained plugin script (D18) that manages
<workspace>/.test-commander/sandbox/{config.yaml,state.json} and drives the
provider abstraction. Tests inject a MockSandboxProvider so the lifecycle is
exercised hermetically (no shell-out, no spend); launch and stop are idempotent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))

import sandbox_export  # noqa: E402
import sandbox_init  # noqa: E402
import sandbox_launch  # noqa: E402
import sandbox_status  # noqa: E402
import sandbox_stop  # noqa: E402
import sandbox_sync  # noqa: E402

from sandbox.providers.mock import MockSandboxProvider  # noqa: E402


def seed(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    (project / ".test-commander").mkdir(parents=True)
    return project


def init_with_config(project: Path) -> None:
    sandbox_init.init(project)


# ---------------------------------------------------------------------------
# /tc:sandbox-init
# ---------------------------------------------------------------------------


def test_init_writes_config_and_is_idempotent(tmp_path: Path):
    project = seed(tmp_path)
    cfg = sandbox_init.init(project)
    assert cfg.is_file()
    first = cfg.read_text(encoding="utf-8")
    config = yaml.safe_load(first)
    assert config["provider"] and config["allowed_domains"]
    # Idempotent: a second init leaves the (user-editable) config byte-identical.
    sandbox_init.init(project)
    assert cfg.read_text(encoding="utf-8") == first


def test_init_refuses_uninitialized_workspace(tmp_path: Path):
    assert sandbox_init.main([str(tmp_path / "nope")]) == 2


# ---------------------------------------------------------------------------
# /tc:sandbox-launch
# ---------------------------------------------------------------------------


def test_launch_drives_provider_and_persists_state(tmp_path: Path):
    project = seed(tmp_path)
    init_with_config(project)
    mock = MockSandboxProvider()
    state = sandbox_launch.launch(project, provider=mock)
    assert state["status"] == "running"
    assert mock.calls == ["launch"]
    persisted = json.loads(
        (project / ".test-commander" / "sandbox" / "state.json").read_text(encoding="utf-8")
    )
    assert persisted["status"] == "running"
    assert "web" in persisted["endpoints"]


def test_launch_is_idempotent(tmp_path: Path):
    project = seed(tmp_path)
    init_with_config(project)
    mock = MockSandboxProvider()
    sandbox_launch.launch(project, provider=mock)
    sandbox_launch.launch(project, provider=mock)
    # A second launch on a running sandbox does not re-provision.
    assert mock.calls == ["launch"]


def test_launch_requires_config(tmp_path: Path):
    project = seed(tmp_path)  # no sandbox-init
    with pytest.raises(FileNotFoundError):
        sandbox_launch.launch(project, provider=MockSandboxProvider())


# ---------------------------------------------------------------------------
# /tc:sandbox-status
# ---------------------------------------------------------------------------


def test_status_reads_persisted_state(tmp_path: Path):
    project = seed(tmp_path)
    init_with_config(project)
    assert sandbox_status.status(project)["status"] == "none"
    sandbox_launch.launch(project, provider=MockSandboxProvider())
    assert sandbox_status.status(project)["status"] == "running"


# ---------------------------------------------------------------------------
# /tc:sandbox-sync
# ---------------------------------------------------------------------------


def test_sync_drives_provider(tmp_path: Path):
    project = seed(tmp_path)
    init_with_config(project)
    mock = MockSandboxProvider()
    sandbox_launch.launch(project, provider=mock)
    state = sandbox_sync.sync(project, provider=mock)
    assert state["status"] == "running"
    assert "sync" in mock.calls


# ---------------------------------------------------------------------------
# /tc:sandbox-stop
# ---------------------------------------------------------------------------


def test_stop_tears_down_and_is_idempotent(tmp_path: Path):
    project = seed(tmp_path)
    init_with_config(project)
    mock = MockSandboxProvider()
    sandbox_launch.launch(project, provider=mock)
    stopped = sandbox_stop.stop(project, provider=mock)
    assert stopped["status"] == "stopped"
    assert "teardown" in mock.calls
    # Stopping an already-stopped sandbox is a no-op (no second teardown).
    sandbox_stop.stop(project, provider=mock)
    assert mock.calls.count("teardown") == 1


# ---------------------------------------------------------------------------
# /tc:sandbox-export
# ---------------------------------------------------------------------------


def test_export_writes_a_shareable_bundle(tmp_path: Path):
    project = seed(tmp_path)
    init_with_config(project)
    sandbox_launch.launch(project, provider=MockSandboxProvider())
    out = sandbox_export.export(project)
    assert out.is_file()
    bundle = json.loads(out.read_text(encoding="utf-8"))
    assert bundle["status"] == "running"
    assert bundle["environment_label"]
    assert "web" in bundle["endpoints"]
