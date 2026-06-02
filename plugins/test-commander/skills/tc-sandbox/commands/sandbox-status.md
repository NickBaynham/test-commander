# /tc:sandbox-status

Report the current sandbox state.

## Inputs

- `<workspace>/.test-commander/sandbox/state.json` (if a sandbox was launched).
- CLI: `<project-root>`.

## Outputs

- Printed status (`none` | `running` | `stopped`) and any endpoints. No writes.

## Preconditions

- The workspace exists. Otherwise exit 2.

## Behavior

1. Resolve the workspace.
2. Read the persisted `state.json` (the source of truth for the command layer).
3. Report `none` if no sandbox has been launched; otherwise the persisted status
   and endpoints.

The persisted state is authoritative (the docker-compose provider's live status
is an MVP limitation — see [provider-abstraction.md](../methodology/provider-abstraction.md)).

## Safety

- Read-only. No network, no execution, no writes.

## Implementation

- Command: `plugins/test-commander/scripts/sandbox_status.py` (per D18).
- Run: `python3 <plugin-root>/scripts/sandbox_status.py <project-root>`.

## Definition of Done

- Reports the persisted status (`none` before launch); uninitialized refused
  (exit 2).
- `tc-sandbox/SKILL.md` describes the shipped command.

## See also

- [/tc:sandbox-launch](sandbox-launch.md)
- [/tc:sandbox-export](sandbox-export.md)
- [tc-sandbox skill](../SKILL.md)
