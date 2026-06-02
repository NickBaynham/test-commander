# /tc:sandbox-launch

Launch the on-demand Test Commander sandbox via its configured provider.

## Inputs

- `<workspace>/.test-commander/sandbox/config.yaml` (from `/tc:sandbox-init`).
- CLI: `<project-root>`; `--real` to actually launch (default is a dry run).

## Outputs

- `<workspace>/.test-commander/sandbox/state.json` — the launched state (name,
  provider, status, endpoints, labels).

## Preconditions

- The workspace exists and `/tc:sandbox-init` has run. Otherwise exit 2.

## Behavior

1. Load the config and the current state.
2. If a sandbox is already running, leave it as is (idempotent — no re-provision).
3. Otherwise resolve the provider and run its `launch`, then persist the state.

A dry run by default: the provider plans the launch and returns the resulting
state without spending real cloud. `--real` shells out; a real launch is refused
under pytest.

## Safety

- Governance travels with the sandbox: the Phase-10.5 pipeline runs inside it.
- The provider's launch is a dry run unless `--real`; a real launch is refused
  under pytest. Provider credentials are server-side secrets.

## Implementation

- Command: `plugins/test-commander/scripts/sandbox_launch.py` (per D18).
- Run: `python3 <plugin-root>/scripts/sandbox_launch.py <project-root> [--real]`.

## Definition of Done

- Drives the provider's `launch`, persists `state.json`, idempotent on a running
  sandbox; missing config/workspace refused (exit 2).
- `tc-sandbox/SKILL.md` describes the shipped command.

## See also

- [/tc:sandbox-status](sandbox-status.md)
- [/tc:sandbox-stop](sandbox-stop.md)
- [tc-sandbox skill](../SKILL.md)
