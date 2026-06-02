"""The SandboxProvider interface + the SandboxState carrier (Phase 12).

Every backend (docker-compose-local, generic container host, Sprites.dev)
implements this one interface, so the six `/tc:sandbox-*` commands work against
any provider. The implementations land in Step 12.2; this is the abstraction the
commands and the safety guards build on.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SandboxState:
    """The state of a sandbox, persisted to <workspace>/.test-commander/sandbox/state.json."""

    name: str
    provider: str = ""
    status: str = "stopped"  # stopped | running
    endpoints: dict = field(default_factory=dict)
    labels: dict = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "provider": self.provider,
            "status": self.status,
            "endpoints": dict(self.endpoints),
            "labels": dict(self.labels),
            "summary": self.summary,
        }


class SandboxProvider(ABC):
    """A sandbox backend. Implements the launch -> status -> sync -> teardown lifecycle."""

    name: str = "base"

    @abstractmethod
    def launch(self, config: dict, *, dry_run: bool = True) -> SandboxState:
        """Provision the environment and return its state."""

    @abstractmethod
    def status(self, config: dict) -> SandboxState:
        """Return the current sandbox state."""

    @abstractmethod
    def sync(self, config: dict, *, dry_run: bool = True) -> SandboxState:
        """Push the committed workspace into the sandbox; return the state."""

    @abstractmethod
    def teardown(self, config: dict, *, dry_run: bool = True) -> SandboxState:
        """Stop and clean up the sandbox; idempotent."""
