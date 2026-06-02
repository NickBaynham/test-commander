"""Sandbox provider abstraction (Phase 12).

Every backend implements the `SandboxProvider` interface (`base.py`). The MVP
default is the docker-compose-local provider; a generic container host and a
Sprites.dev placeholder ship as refusing stubs. `get_provider(name)` resolves a
provider by name (default deny: an unknown name raises).
"""

from __future__ import annotations

from sandbox.providers.base import SandboxProvider, SandboxState
from sandbox.providers.docker_compose import DockerComposeProvider
from sandbox.providers.mock import MockSandboxProvider
from sandbox.providers.stubs import ContainerHostProvider, SpritesProvider

PROVIDERS: dict[str, type[SandboxProvider]] = {
    "docker-compose": DockerComposeProvider,
    "generic-container-host": ContainerHostProvider,
    "sprites": SpritesProvider,
    "mock": MockSandboxProvider,
}


def get_provider(name: str) -> SandboxProvider:
    """Resolve a provider by name. Unknown -> ValueError (default deny)."""
    cls = PROVIDERS.get(name)
    if cls is None:
        raise ValueError(
            f"unknown sandbox provider: {name!r} (known: {', '.join(sorted(PROVIDERS))})"
        )
    return cls()


__all__ = ["SandboxProvider", "SandboxState", "get_provider", "PROVIDERS"]
