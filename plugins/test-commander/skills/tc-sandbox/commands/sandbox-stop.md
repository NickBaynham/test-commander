# /tc:sandbox-stop

Tear the sandbox down.

## Inputs

- `<workspace>/.test-commander/sandbox/{config.yaml,state.json}`.
- CLI: `<project-root>`; `--real` to actually tear down (default is a dry run).

## Outputs

- Updated `state.json` with status `stopped`.

## Preconditions

- The workspace exists. Otherwise exit 2.

## Behavior

1. Read the current state.
2. If no sandbox is running (already stopped or never launched), no-op
   (idempotent).
3. Otherwise resolve the provider, run its `teardown`, and persist the stopped
   state.

A dry run by default; `--real` shells out (refused under pytest).

## Safety

- Teardown is idempotent — stopping an already-stopped sandbox does nothing.
- Clean teardown is part of the no-lingering-environment discipline.

## Implementation

- Command: `plugins/test-commander/scripts/sandbox_stop.py` (per D18).
- Run: `python3 <plugin-root>/scripts/sandbox_stop.py <project-root> [--real]`.

## Definition of Done

- Drives the provider's `teardown`, persists the stopped state, idempotent;
  uninitialized refused (exit 2).
- `tc-sandbox/SKILL.md` describes the shipped command.

## See also

- [/tc:sandbox-launch](sandbox-launch.md)
- [/tc:sandbox-status](sandbox-status.md)
- [tc-sandbox skill](../SKILL.md)
