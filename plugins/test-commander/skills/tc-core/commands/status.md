# `/tc:status`

Summarize the state of the Test Commander workspace under a project root.

## Inputs

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `target` | no | current working directory | The consuming project's root. The workspace is read from `<target>/.test-commander/`. |

## Outputs

A grep-friendly report on stdout:

- Workspace path and initialization state (initialized / not initialized).
- Last activity timestamp (UTC ISO 8601) if the workspace exists.
- File counts: total and "populated" (differs from the bundled template).
- Per-bucket breakdown: each top-level file or directory with its file count and populated count.
- Per-phase status: `not_started` (no user content yet) or `in_progress` (at least one owned file differs from the template).

Exit code 0 in every case (including missing workspace — the report itself tells the user what to do).

## Preconditions

- Test Commander plugin installed.
- Target either exists as a directory or does not exist (a missing workspace is a valid, reportable state).

## Behavior

1. Build a `WorkspaceSnapshot` from `<target>/.test-commander/` against the bundled template.
2. If the workspace directory does not exist, print "workspace does not exist; run /tc:init" and exit 0.
3. Otherwise print the workspace path, initialization state, last activity, totals, per-bucket breakdown, and per-phase status.

The helper is **read-only**. It never writes to the workspace or the filesystem.

## What "populated" means

A file is **populated** iff its bytes differ from the corresponding file in the bundled template (`plugins/test-commander/templates/workspace/`). A workspace file with no template counterpart (e.g., the user added `requirements/extra-note.md`) counts as populated.

## What "phase status" means

Each phase owns a set of workspace paths (files and directories). The owning map is documented in `workspace_state.PHASE_OWNERSHIP`:

| Phase | Owned paths |
| --- | --- |
| 1 | `project.md`, `config.yaml`, `methodology.md`, `journal/` |
| 2 | `requirements/`, `risk-register/` |
| 3 | `product-knowledge/`, `documents/` |
| 4 | `charters/`, `exploration-notes/`, `test-ideas/`, `sessions/` |
| 5 | `bdd/`, `traceability/` |
| 6 | `automation-plan/`, `test-data/` |
| 7 | `quality-report/`, `evidence/`, `runs/` |
| 8 | `learning/` |
| 9 | `visuals/` |
| 10.5 | `policy/`, `audit/` |

A phase is `in_progress` iff at least one owned path has a populated file. Otherwise `not_started`. There is no automatic "complete" detection in Phase 1 — completion is the user's call.

## Safety

- Read-only. Never modifies the workspace, the template, or any other path.
- Never resolves symlinks outside the target.
- Never reads files at paths outside the workspace and the template.

## Implementation

Implemented by `plugins/test-commander/scripts/workspace_state.py`. Invoke as:

```sh
python3 plugins/test-commander/scripts/workspace_state.py [target]
```

The script imports cleanly and is also used by `/tc:next` (Step 1.5) without re-reading the filesystem.

## Definition of Done

- Snapshot is deterministic across consecutive calls for the same workspace state.
- Snapshot shape matches the documented contract (`workspace`, `exists`, `initialized`, `last_modified`, `counts`, `populated`, `phase_status`).
- Report is grep-friendly: each line is self-contained with predictable column placement.
- Exit code is 0 in every case the helper does not raise.
- Read-only — verified by unit tests that assert no template or workspace bytes change after a snapshot call.

## See also

- [`/tc:init`](init.md)
- [Workspace reference](../../../../../docs/workspace-reference.md)
- [Phased plan](../../../../../planning/plan.md)
