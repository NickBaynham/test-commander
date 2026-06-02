"""Step 12.2 - the SandboxProvider implementations.

The docker-compose-local provider is the MVP default (Decision D15): its
lifecycle calls plan deterministically in dry-run mode (no shell-out, no spend),
and a real (non-dry) launch is refused under pytest. The generic-container-host
and Sprites.dev providers are refusing stubs (Q8 default). A MockSandboxProvider
records the lifecycle for the command + integration tests to drive hermetically.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from sandbox.providers import get_provider  # noqa: E402
from sandbox.providers.base import SandboxProvider, SandboxState  # noqa: E402
from sandbox.providers.docker_compose import (  # noqa: E402
    DockerComposeProvider,
    SandboxLaunchRefusedError,
)
from sandbox.providers.mock import MockSandboxProvider  # noqa: E402
from sandbox.providers.stubs import (  # noqa: E402
    ContainerHostProvider,
    SandboxNotConfiguredError,
    SpritesProvider,
)

CONFIG = yaml.safe_load(
    (REPO / "tests" / "fixtures" / "seeded-sandbox" / "config.yaml").read_text(encoding="utf-8")
)


# ---------------------------------------------------------------------------
# docker-compose-local provider (the MVP default)
# ---------------------------------------------------------------------------


def test_docker_compose_launch_dry_run():
    state = DockerComposeProvider().launch(CONFIG, dry_run=True)
    assert isinstance(state, SandboxState)
    assert state.status == "running"
    assert state.provider == "docker-compose"
    assert "web" in state.endpoints and "api" in state.endpoints
    # The ephemeral label is always present so a sandbox is never mistaken for prod.
    assert state.labels.get("ephemeral") == "true"
    assert state.labels.get("environment")


def test_docker_compose_teardown_dry_run_is_stopped():
    assert DockerComposeProvider().teardown(CONFIG, dry_run=True).status == "stopped"


def test_docker_compose_sync_dry_run_is_running():
    assert DockerComposeProvider().sync(CONFIG, dry_run=True).status == "running"


def test_docker_compose_real_launch_refused_under_pytest():
    with pytest.raises(SandboxLaunchRefusedError):
        DockerComposeProvider().launch(CONFIG, dry_run=False)


# ---------------------------------------------------------------------------
# Refusing stubs (Q8 default)
# ---------------------------------------------------------------------------


def test_container_host_stub_refuses_cleanly():
    with pytest.raises(SandboxNotConfiguredError):
        ContainerHostProvider().launch(CONFIG, dry_run=True)


def test_sprites_stub_refuses_cleanly():
    with pytest.raises(SandboxNotConfiguredError):
        SpritesProvider().launch(CONFIG, dry_run=True)


# ---------------------------------------------------------------------------
# Mock provider (records the lifecycle; for the command + integration tests)
# ---------------------------------------------------------------------------


def test_mock_provider_records_lifecycle():
    mock = MockSandboxProvider()
    assert mock.launch(CONFIG).status == "running"
    assert mock.sync(CONFIG).status == "running"
    assert mock.teardown(CONFIG).status == "stopped"
    assert mock.calls == ["launch", "sync", "teardown"]


def test_mock_provider_launch_is_idempotent():
    mock = MockSandboxProvider()
    mock.launch(CONFIG)
    mock.launch(CONFIG)
    # A second launch does not double-provision; status stays running.
    assert mock.status(CONFIG).status == "running"


# ---------------------------------------------------------------------------
# Registry + interface conformance
# ---------------------------------------------------------------------------


def test_get_provider_resolves_known_and_rejects_unknown():
    assert isinstance(get_provider("docker-compose"), DockerComposeProvider)
    assert isinstance(get_provider("generic-container-host"), ContainerHostProvider)
    assert isinstance(get_provider("sprites"), SpritesProvider)
    with pytest.raises(ValueError):
        get_provider("does-not-exist")


def test_all_providers_implement_the_interface():
    for provider in (DockerComposeProvider(), ContainerHostProvider(),
                     SpritesProvider(), MockSandboxProvider()):
        assert isinstance(provider, SandboxProvider)
