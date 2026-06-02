# /tc:web-init

Provision the web console's configuration inside the workspace.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- CLI: `<project-root>` (defaults to the current directory).

## Outputs

- `<workspace>/.test-commander/.web/console.json` — the console config
  (`api_base`, `web_port`, schema). Idempotent: re-running leaves it
  byte-identical.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.

## Behavior

1. Resolve the workspace (refuse if uninitialized).
2. Write `.web/console.json` with the default API base and web port.

Writes only the console's own config — never a workspace artifact.

## Safety

- Writes only under `.web/`. No network, no command execution.

## Implementation

- Command: `plugins/test-commander/scripts/web_init.py` (per D18; self-contained).
- Run: `python3 <plugin-root>/scripts/web_init.py <project-root>`.

## Definition of Done

- Writes the console config; idempotent; uninitialized refused (exit 2).
- `tc-web/SKILL.md` describes the shipped command.

## See also

- [/tc:web-start](web-start.md)
- [Web console architecture](../methodology/web-architecture.md)
- [tc-web skill](../SKILL.md)
