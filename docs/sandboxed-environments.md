# Sandboxed environments

A **sandbox** is an on-demand, team-accessible Test Commander environment. It is
launched from GitHub Actions (or locally), pointed at a target application, and
torn down when the work is done. The defining property: **the Phase-10.5
controlled execution pipeline runs inside the sandbox exactly as it does
locally** — sandboxing never relaxes governance.

## Architecture

```
/tc:sandbox-* commands  ->  sandbox/providers (SandboxProvider)  ->  a backend
        |                            |                                  |
   workspace state            launch/status/sync/teardown        docker compose,
   (.test-commander/sandbox)  (dry-run plans in tests)           container host, ...
```

- **Commands** (`/tc:sandbox-*`) are self-contained plugin helpers that manage
  `<workspace>/.test-commander/sandbox/{config.yaml,state.json}` and drive a
  provider. See the [user guide](user-guide/sandbox.md).
- **Providers** (`sandbox/providers/`) implement one `SandboxProvider` interface
  (`launch → status → sync → teardown`). The MVP default is docker-compose-local;
  a generic container host and a Sprites.dev placeholder ship as refusing stubs.
- **Safety** (`sandbox/safety.py`) enforces allow-listed targeting and blocks
  private network ranges. **Governance** (`sandbox/governance.py`) runs every
  in-sandbox action through the Phase-10.5 pipeline.

## Safety model

- Allow-listed target hosts only; private/loopback/link-local ranges blocked by
  default.
- The Phase-10.5 pipeline runs inside the sandbox: a sandbox cannot execute above
  its approved permission level, and every action is audited.
- Provider credentials (Anthropic API tokens, cloud creds) are **server-side
  secrets**, never exposed to the frontend, scoped only to the jobs that need
  them.
- Clear, explicit environment labels so an ephemeral sandbox is never mistaken
  for production.

See [github-actions-sandbox.md](github-actions-sandbox.md) for the workflow and
[security-and-permissions.md](security-and-permissions.md) for the permission
model.

## MVP limitations (honest)

The Phase-12 sandbox is an MVP. Known limitations, stated plainly:

- **Local-first (Pattern A, Decision D15).** The only fully-implemented provider
  is docker-compose-local. The generic-container-host and Sprites.dev providers
  are refusing stubs — they implement the interface but are not wired to a real
  backend; a consuming project configures them.
- **Live status is not queried.** `/tc:sandbox-status` reads the persisted
  `state.json`, not a live backend query — if a container is stopped out of band,
  the persisted state can be stale. The docker-compose provider's `status()`
  reports `unknown` for the live check by design.
- **The CI workflow is dry-run by default and demonstrative.** The shipped
  workflow sequences safety → build → publish → teardown but the build/publish/
  teardown steps are placeholders (echoes) pending a real provider deployment;
  the hermetic pipeline (provider lifecycle, safety guards, in-sandbox
  governance) is fully tested in Python with a mocked provider.
- **No real cloud spend in tests.** A real (non-dry) launch is refused under
  pytest; the test suite never starts a container or spends.

These are deliberate MVP boundaries, not defects. Phase 13 builds continuous
quality mode on the same governed foundation.

## See also

- [Sandbox user guide](user-guide/sandbox.md)
- [GitHub Actions sandbox](github-actions-sandbox.md)
- [No-code tester workflow](no-code-tester-workflow.md)
- [Security and permissions](security-and-permissions.md)
