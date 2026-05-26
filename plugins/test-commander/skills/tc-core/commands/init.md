# `/tc:init`

Initialize the Test Commander workspace inside a consuming project. Copies the bundled workspace template into `<project_root>/.test-commander/`.

## Inputs

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `target` | no | current working directory | The consuming project's root. The workspace lands at `<target>/.test-commander/`. |

## Outputs

- A new `.test-commander/` directory at the target, populated from the workspace template bundled with the plugin (`plugins/test-commander/templates/workspace/`).
- Stdout summary: `workspace: <path>`, `created: N`, `skipped: N`, plus a list of every newly-created file relative to the workspace root.
- Exit code 0 on success; 2 on invalid target.

## Preconditions

- Test Commander plugin installed (`make install` ran cleanly, or the plugin is cached at `~/.claude/plugins/cache/...`).
- Target path either does not exist (it will be created) or is an existing directory.
- Target path must **not** point to a regular file.

## Behavior

1. Validate the target. Refuse with `NotADirectoryError` if the path exists and is a file.
2. Create `<target>/.test-commander/` if absent.
3. Walk the bundled workspace template (`plugins/test-commander/templates/workspace/`).
4. For each file in the template:
   - If the corresponding file in the workspace already exists, record it as **skipped** (the user's content is preserved verbatim).
   - Otherwise, copy the file from the template, creating parent directories as needed. Record it as **created**.
5. Print the summary and exit 0.

The command is **idempotent**. Re-running on an existing workspace produces no diff for files already present and only adds files that have appeared in the template since the previous init.

## Safety

- Never overwrites files inside `.test-commander/`. Customizations to `project.md`, `methodology.md`, `config.yaml`, or any other file are preserved.
- Never writes outside the target directory.
- Refuses to coerce a file path into a directory; aborts before touching anything.
- Never reads or writes anywhere on the filesystem outside the target and the bundled template.

## Implementation

Implemented by `plugins/test-commander/scripts/init_workspace.py` (per D18 — helpers ship inside the plugin). Invoke as:

```sh
python3 plugins/test-commander/scripts/init_workspace.py [target]
```

When invoked through the installed plugin cache, the path resolves to `~/.claude/plugins/cache/test-commander-marketplace/test-commander/<version>/scripts/init_workspace.py`. The bundled template is found relative to the script's own location.

## Definition of Done

- `<target>/.test-commander/` exists and contains every directory and file from the bundled template.
- Pre-existing files in `.test-commander/` are unchanged.
- Output reports non-negative counts of `created` and `skipped`.
- Exit code 0 on success; non-zero only on invalid target or missing template.

## See also

- [Workspace reference](../../../../../docs/workspace-reference.md)
- [Phased plan](../../../../../planning/plan.md)
- Sibling commands: `/tc:status`, `/tc:journal`, `/tc:next` (Phase 1)
