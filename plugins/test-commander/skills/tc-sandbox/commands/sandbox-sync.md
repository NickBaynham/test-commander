# /tc:sandbox-sync

Sync the committed workspace into the running sandbox.

## Inputs

- `<workspace>/.test-commander/sandbox/config.yaml` (from `/tc:sandbox-init`).
- CLI: `<project-root>`; `--real` to actually sync (default is a dry run).

## Outputs

- Updated `<workspace>/.test-commander/sandbox/state.json`.

## Preconditions

- The workspace exists and `/tc:sandbox-init` has run. Otherwise exit 2.

## Behavior

1. Load the config and resolve the provider.
2. Run the provider's `sync` (push the committed workspace into the sandbox) and
   persist the resulting state.

A dry run by default; `--real` shells out (refused under pytest).

## Safety

- The workspace is committed to git (Decision D5); sync pushes that committed
  state, never uncommitted secrets. A real sync is refused under pytest.

## Implementation

- Command: `plugins/test-commander/scripts/sandbox_sync.py` (per D18).
- Run: `python3 <plugin-root>/scripts/sandbox_sync.py <project-root> [--real]`.

## Definition of Done

- Drives the provider's `sync`, persists the state; missing config/workspace
  refused (exit 2).
- `tc-sandbox/SKILL.md` describes the shipped command.

## See also

- [/tc:sandbox-launch](sandbox-launch.md)
- [/tc:sandbox-stop](sandbox-stop.md)
- [tc-sandbox skill](../SKILL.md)
