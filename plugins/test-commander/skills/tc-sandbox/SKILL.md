---
name: tc-sandbox
description: Sandboxed Test Commander environments launched from GitHub Actions. Use when the user runs /tc:sandbox-init, /tc:sandbox-launch, /tc:sandbox-status, /tc:sandbox-sync, /tc:sandbox-stop, or /tc:sandbox-export, or asks to spin up an on-demand, team-accessible Test Commander environment against a target application. A sandbox is governed exactly as the local runtime is - the Phase-10.5 controlled execution pipeline runs inside it, provider credentials stay server-side, and targeting is safe-by-default (allow-listed domains, blocked private network ranges, approvals for external and destructive actions). Sandboxing never relaxes governance.
---

# tc-sandbox

The sandbox skill for Test Commander. It owns the six `/tc:sandbox-*` commands that launch, inspect, sync, and tear down an on-demand Test Commander environment, plus the **provider abstraction** (`sandbox/providers/`) and the **GitHub Actions workflows** (`.github/workflows/`) that run them.

Each command is a self-contained Python helper bundled inside the plugin (per Decision D18) that drives the provider abstraction. The per-command pages under `commands/` are the authoritative behavior spec.

## Two disciplines

- **Governance travels with the sandbox.** The Phase-10.5 controlled execution pipeline runs in the sandbox exactly as it does locally — a sandbox cannot execute above its approved permission level, and provider credentials (Anthropic API tokens, cloud creds) are **server-side secrets**, never exposed to the frontend, scoped only to the runtime jobs that need them.
- **Safe-by-default targeting.** Allow-listed target domains only; private network ranges (RFC 1918, loopback, link-local) blocked by default; secret-scanning guidance; approvals required for external-network and destructive actions; clear, explicit environment labels. CI is exercised as a **dry run with a mocked provider** — no real cloud spend in tests, and a real launch is refused under pytest.

## Provider abstraction

Every backend implements one `SandboxProvider` interface (`sandbox/providers/base.py`) with a `launch → status → sync → teardown` lifecycle. The MVP default is the **docker-compose-local** provider (Decision D15, Pattern A); a generic container host and a Sprites.dev placeholder ship as refusing stubs (Q8 default).

## Status

Phase 12 (Step 12.4). The provider abstraction, the six commands, the workflows, and the safety guards are all shipped:

- Provider abstraction + the docker-compose-local provider + the refusing stubs — **shipped (Step 12.2).** `sandbox/providers/` ships the `DockerComposeProvider` (the MVP default — lifecycle calls plan deterministically in dry-run; a real launch shells out and is refused under pytest), the `ContainerHostProvider`/`SpritesProvider` refusing stubs (Q8 default), a `MockSandboxProvider` for hermetic testing, and `get_provider(name)` (default deny on an unknown name). See [methodology/provider-abstraction.md](methodology/provider-abstraction.md).
- The six `/tc:sandbox-*` commands — **shipped (Step 12.3).** Self-contained plugin helpers (D18) that manage `<workspace>/.test-commander/sandbox/{config.yaml,state.json}` and drive the provider:
  - `/tc:sandbox-init` — write the sandbox config (skip-not-overwrite; idempotent). [commands/sandbox-init.md](commands/sandbox-init.md)
  - `/tc:sandbox-launch` — launch via the provider; persist state; idempotent on a running sandbox; dry run by default. [commands/sandbox-launch.md](commands/sandbox-launch.md)
  - `/tc:sandbox-status` — report the persisted state (`none`/`running`/`stopped`). [commands/sandbox-status.md](commands/sandbox-status.md)
  - `/tc:sandbox-sync` — push the committed workspace into the sandbox. [commands/sandbox-sync.md](commands/sandbox-sync.md)
  - `/tc:sandbox-stop` — tear down; idempotent. [commands/sandbox-stop.md](commands/sandbox-stop.md)
  - `/tc:sandbox-export` — write a shareable bundle (endpoints, labels, status). [commands/sandbox-export.md](commands/sandbox-export.md)
- The GitHub Actions workflow + the safety guards — **shipped (Step 12.4).** `.github/workflows/test-commander-sandbox.yml` (manual `workflow_dispatch` only; `dry_run` defaults true) sequences a safety check → build → publish → teardown (teardown always runs). `sandbox/safety.py` enforces the allow-list and blocks private/loopback/link-local ranges by default (`check_target`); `sandbox/governance.py` (`run_in_sandbox`) runs the Phase-10.5 pipeline inside the sandbox, so a sandbox cannot execute above its approved level. See [methodology/sandbox-safety.md](methodology/sandbox-safety.md).

See [methodology/provider-abstraction.md](methodology/provider-abstraction.md) and [methodology/sandbox-safety.md](methodology/sandbox-safety.md).

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [tc-governance skill](../tc-governance/SKILL.md)
- [tc-web skill](../tc-web/SKILL.md)
