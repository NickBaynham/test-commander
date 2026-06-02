# /tc:sandbox-init

Provision the sandbox configuration inside the workspace.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- CLI: `<project-root>` (defaults to the current directory).

## Outputs

- `<workspace>/.test-commander/sandbox/config.yaml` — the provider, environment
  label, target, allow-list, private-range block, and approval requirements.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.

## Behavior

1. Resolve the workspace (refuse if uninitialized).
2. Create `.test-commander/sandbox/` and write `config.yaml` from the universal
   defaults if it is absent.

Skip-not-overwrite: an existing `config.yaml` is a user-editable seed and is
preserved, so re-running never clobbers an edited allow-list (idempotent).

## Safety

- Writes only under `.test-commander/sandbox/`. No network, no execution.
- The default config blocks private network ranges and requires approval for
  external-network and destructive actions.

## Implementation

- Command: `plugins/test-commander/scripts/sandbox_init.py` (per D18; self-contained).
- Run: `python3 <plugin-root>/scripts/sandbox_init.py <project-root>`.

## Definition of Done

- Writes the sandbox config; idempotent (skip-not-overwrite); uninitialized
  refused (exit 2).
- `tc-sandbox/SKILL.md` describes the shipped command.

## See also

- [/tc:sandbox-launch](sandbox-launch.md)
- [Provider abstraction](../methodology/provider-abstraction.md)
- [Sandbox safety](../methodology/sandbox-safety.md)
- [tc-sandbox skill](../SKILL.md)
