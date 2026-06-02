# /tc:sandbox-export

Export a shareable bundle of the sandbox's endpoints, labels, and status.

## Inputs

- `<workspace>/.test-commander/sandbox/{state.json,config.yaml}`.
- CLI: `<project-root>`.

## Outputs

- `<workspace>/.test-commander/sandbox/export.json` — name, provider, status,
  environment label, endpoints, and target, so a team (or a CI job posting to a
  PR comment) can find and reach the environment.

## Preconditions

- The workspace exists. Otherwise exit 2.

## Behavior

1. Resolve the workspace and read the persisted state (and config for the label
   and target).
2. Write the export bundle.

Read-only with respect to the sandbox; writes only the export bundle.

## Safety

- Exports only endpoints, labels, status, and target — never secrets (provider
  credentials are server-side and never enter the workspace).

## Implementation

- Command: `plugins/test-commander/scripts/sandbox_export.py` (per D18).
- Run: `python3 <plugin-root>/scripts/sandbox_export.py <project-root>`.

## Definition of Done

- Writes the export bundle (endpoints, labels, status); uninitialized refused
  (exit 2).
- `tc-sandbox/SKILL.md` describes the shipped command.

## See also

- [/tc:sandbox-status](sandbox-status.md)
- [tc-sandbox skill](../SKILL.md)
