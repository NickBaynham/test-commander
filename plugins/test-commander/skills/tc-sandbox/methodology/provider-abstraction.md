# Provider abstraction methodology

A sandbox is an on-demand Test Commander environment. The commands never talk to
a cloud or to docker directly — they drive a `SandboxProvider`
(`sandbox/providers/base.py`), so the same six commands work against any backend.

## The interface

`SandboxProvider` declares a four-call lifecycle:

- `launch(config, dry_run)` — provision the environment; return a `SandboxState`
  (name, status, endpoints, labels, provider).
- `status(config)` — read the current state.
- `sync(config, dry_run)` — push the committed workspace into the sandbox.
- `teardown(config, dry_run)` — stop and clean up; idempotent.

`SandboxState` is the carrier the commands persist to
`<workspace>/.test-commander/sandbox/state.json`.

## Providers

- **docker-compose-local** — the MVP default (Decision D15, Pattern A). Brings the
  stack up with docker compose locally. A real launch shells out and is refused
  under pytest; tests drive it as a dry run.
- **generic container host** and **Sprites.dev** — refusing stubs (Q8 default).
  They implement the interface but refuse with a clear "not configured for this
  deployment" message, so the abstraction is exercised without a real backend.

## Dry run

Every lifecycle call accepts `dry_run`. Under pytest, and by default in CI, the
provider plans the action and returns the resulting state without spending real
cloud or launching a real container — no real spend in tests. A real (non-dry)
call shells out and is refused under pytest (`SandboxLaunchRefusedError`).

Resolve a provider by name with `get_provider(name)` (default deny: an unknown
name raises). Shipped in Step 12.2 (`tests/test_sandbox_providers.py`).
