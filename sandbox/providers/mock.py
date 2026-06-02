"""MockSandboxProvider - deterministic, no real backend (Phase 12 Step 12.2).

Used to build and test the sandbox commands + workflows hermetically (mirrors the
governance MockAgentAdapter). It records every lifecycle call and returns a
deterministic state; launch is idempotent (a second launch does not double-
provision).
"""

from __future__ import annotations

from sandbox.providers.base import SandboxProvider, SandboxState

MOCK_ENDPOINTS = {"web": "http://localhost:3100", "api": "http://localhost:8100"}


class MockSandboxProvider(SandboxProvider):
    name = "mock"

    def __init__(self) -> None:
        self.calls: list[str] = []
        self._running = False

    def _labels(self, config: dict) -> dict:
        return {
            "environment": config.get("environment_label", "Test Commander Sandbox (mock)"),
            "ephemeral": "true",
            "provider": self.name,
        }

    def launch(self, config: dict, *, dry_run: bool = True) -> SandboxState:
        self.calls.append("launch")
        self._running = True
        return SandboxState(
            name=str(config.get("name", "tc-sandbox")), provider=self.name, status="running",
            endpoints=dict(MOCK_ENDPOINTS), labels=self._labels(config),
            summary="mock launch",
        )

    def status(self, config: dict) -> SandboxState:
        self.calls.append("status")
        return SandboxState(
            name=str(config.get("name", "tc-sandbox")), provider=self.name,
            status="running" if self._running else "stopped",
            endpoints=dict(MOCK_ENDPOINTS) if self._running else {},
            labels=self._labels(config), summary="mock status",
        )

    def sync(self, config: dict, *, dry_run: bool = True) -> SandboxState:
        self.calls.append("sync")
        return SandboxState(
            name=str(config.get("name", "tc-sandbox")), provider=self.name, status="running",
            endpoints=dict(MOCK_ENDPOINTS), labels=self._labels(config), summary="mock sync",
        )

    def teardown(self, config: dict, *, dry_run: bool = True) -> SandboxState:
        self.calls.append("teardown")
        self._running = False
        return SandboxState(
            name=str(config.get("name", "tc-sandbox")), provider=self.name, status="stopped",
            labels=self._labels(config), summary="mock teardown",
        )
