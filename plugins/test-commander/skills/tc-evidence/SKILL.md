---
name: tc-evidence
description: Evidence indexing for Test Commander. Use when reasoning about how run artifacts such as screenshots, videos, traces, and reports are routed into the workspace evidence tree under the commit-versus-ignore policy, or how the evidence index links each artifact to its run and scenario. An internal cross-cutting indexer with no user-facing command, invoked by tc-run after a run and later by the web console.
---

# tc-evidence

The evidence skill for Test Commander. It is an **internal cross-cutting indexer with no user-facing command** — it is invoked by `tc-run` after a run completes, and later by `tc-web` (the web console). It routes raw run artifacts into the workspace evidence tree per the evidence policy, writes the evidence index, and manages the evidence `.gitignore` and the `git-lfs` opt-in.

The indexer is implemented as a Python helper script bundled inside the plugin (per Decision D18). Because there is no `/tc:*` command, there is no per-command page under `commands/`; the methodology under `methodology/` is the authoritative behavior spec.

## Status

Phase 7 (Step 7.3). The indexer is **shipped**:

- evidence indexing — **shipped (Step 7.3).** `index_run_evidence(project_root, run_id)` routes screenshots to the committed `evidence/screenshots/` tree, videos and traces to `evidence/{videos,traces}/` (git-ignored by default via `evidence/.gitignore`, with a documented `git-lfs` opt-in), and logs/reports to the committed `evidence/logs/` tree, then rebuilds `<workspace>/evidence/evidence-index.md` over every run record, linking each artifact to its run and scenario provenance. `/tc:run` calls it automatically after a run (suppressible with `--no-index`). Deterministic: the index is rebuilt from the `runs/<RUN-ID>/results.json` records, so a re-run over unchanged records is byte-identical.

## Evidence policy

Screenshots, logs, and reports are committed; videos and traces are git-ignored by default (`evidence/.gitignore`) with a documented `git-lfs` opt-in. The policy is enforced by the indexer, not by an author's discipline. Full detail: [methodology/evidence-management.md](methodology/evidence-management.md).

## Implementation

- Helper: `plugins/test-commander/scripts/index_evidence.py` (per D18).
- Entry point: `index_run_evidence(project_root, run_id, *, source_root=None)` — the function `/tc:run` auto-runs and the web console (Phase 10) will reuse. A thin CLI (`index_evidence.py <project-root> --run-id <RUN-ID>`) exists for manual / debugging use; there is no `/tc:*` command.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-run skill](../tc-run/SKILL.md)
- [tc-quality-report skill](../tc-quality-report/SKILL.md)
