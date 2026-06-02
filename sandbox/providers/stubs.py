"""Refusing provider stubs (Phase 12 Step 12.2).

The generic-container-host and Sprites.dev providers (Q8 default) implement the
`SandboxProvider` interface but refuse cleanly: they are not configured for this
deployment. They exercise the abstraction without a real backend and make the
extension point explicit for a consuming project.
"""

from __future__ import annotations

from sandbox.providers.base import SandboxProvider, SandboxState


class SandboxNotConfiguredError(Exception):
    """A provider that is a placeholder for a not-yet-configured backend."""


class _RefusingProvider(SandboxProvider):
    name = "refusing"

    def _refuse(self) -> SandboxState:
        raise SandboxNotConfiguredError(
            f"the {self.name} sandbox provider is not configured for this deployment; "
            "use the docker-compose provider, or configure this backend"
        )

    def launch(self, config: dict, *, dry_run: bool = True) -> SandboxState:
        return self._refuse()

    def status(self, config: dict) -> SandboxState:
        return self._refuse()

    def sync(self, config: dict, *, dry_run: bool = True) -> SandboxState:
        return self._refuse()

    def teardown(self, config: dict, *, dry_run: bool = True) -> SandboxState:
        return self._refuse()


class ContainerHostProvider(_RefusingProvider):
    name = "generic-container-host"


class SpritesProvider(_RefusingProvider):
    name = "sprites"
