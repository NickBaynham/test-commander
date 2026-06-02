"""The docker-compose-local sandbox provider (Phase 12 Step 12.2).

The MVP default (Decision D15, Pattern A): a sandbox is the local stack brought
up with docker compose. Lifecycle calls plan deterministically in dry-run mode
(no shell-out, no spend); a real (non-dry) call shells out and is refused under
pytest, so the test suite never launches Docker.
"""

from __future__ import annotations

import os
import subprocess  # noqa: S404 - guarded; never reached under pytest
from pathlib import Path

from sandbox.providers.base import SandboxProvider, SandboxState

PYTEST_ENV_VAR = "PYTEST_CURRENT_TEST"
DEFAULT_ENDPOINTS = {"web": "http://localhost:3100", "api": "http://localhost:8100"}


class SandboxLaunchRefusedError(Exception):
    """A real (non-dry) lifecycle action attempted under pytest."""


def _name(config: dict) -> str:
    return str(config.get("name", "tc-sandbox"))


def _labels(config: dict, provider: str) -> dict:
    return {
        "environment": config.get("environment_label", "Test Commander Sandbox (ephemeral)"),
        "ephemeral": "true",
        "provider": provider,
    }


class DockerComposeProvider(SandboxProvider):
    name = "docker-compose"

    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def _run_real(self, command: list[str], action: str) -> None:
        if os.environ.get(PYTEST_ENV_VAR):
            raise SandboxLaunchRefusedError(
                f"sandbox {action} refused under pytest (PYTEST_CURRENT_TEST is set); "
                "run it via the workflow or `make run` outside the test suite"
            )
        subprocess.run(command, cwd=self._repo_root(), check=True)  # pragma: no cover

    def launch(self, config: dict, *, dry_run: bool = True) -> SandboxState:
        if not dry_run:
            self._run_real(["docker", "compose", "up", "-d", "--build"], "launch")
        return SandboxState(
            name=_name(config), provider=self.name, status="running",
            endpoints=dict(DEFAULT_ENDPOINTS), labels=_labels(config, self.name),
            summary="docker compose up -d --build" + (" (dry run)" if dry_run else ""),
        )

    def sync(self, config: dict, *, dry_run: bool = True) -> SandboxState:
        if not dry_run:
            self._run_real(["docker", "compose", "up", "-d", "--build"], "sync")
        return SandboxState(
            name=_name(config), provider=self.name, status="running",
            endpoints=dict(DEFAULT_ENDPOINTS), labels=_labels(config, self.name),
            summary="workspace synced into the sandbox" + (" (dry run)" if dry_run else ""),
        )

    def teardown(self, config: dict, *, dry_run: bool = True) -> SandboxState:
        if not dry_run:
            self._run_real(["docker", "compose", "down", "-v"], "teardown")
        return SandboxState(
            name=_name(config), provider=self.name, status="stopped",
            labels=_labels(config, self.name),
            summary="docker compose down -v" + (" (dry run)" if dry_run else ""),
        )

    def status(self, config: dict) -> SandboxState:
        # Live status requires querying the backend; the command layer reads the
        # persisted state.json as the source of truth (an MVP limitation).
        return SandboxState(
            name=_name(config), provider=self.name, status="unknown",
            labels=_labels(config, self.name),
            summary="live status requires a running backend; see the persisted sandbox state",
        )
