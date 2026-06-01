---
name: tc-evidence
description: Evidence indexing for Test Commander. Use when reasoning about how run artifacts such as screenshots, videos, traces, and reports are routed into the workspace evidence tree under the commit-versus-ignore policy, or how the evidence index links each artifact to its run and scenario. An internal cross-cutting indexer with no user-facing command, invoked by tc-run after a run and later by the web console.
---

# tc-evidence

The evidence skill for Test Commander. It is an **internal cross-cutting indexer with no user-facing command** — it is invoked by `tc-run` after a run completes, and later by `tc-web` (the web console). It routes raw run artifacts into the workspace evidence tree per the evidence policy, writes the evidence index, and manages the evidence `.gitignore` and the `git-lfs` opt-in.

The indexer is implemented as a Python helper script bundled inside the plugin (per Decision D18). Because there is no `/tc:*` command, there is no per-command page under `commands/`; the methodology under `methodology/` is the authoritative behavior spec.

## Status

Phase 7 scaffold (Step 7.1). The indexer is registered but its behavior is not yet shipped:

- evidence indexing — behavior arrives in Step 7.3. It will route screenshots to the committed `evidence/screenshots/` tree, videos and traces to `evidence/{videos,traces}/` (git-ignored by default, with a documented `git-lfs` opt-in), and JSON/HTML reports to a committed location, then write `<workspace>/evidence/evidence-index.md` linking each artifact to its run and scenario. `tc-run` calls it automatically after a run (suppressible with `--no-index`).

When Step 7.3 lands, this SKILL.md is updated to describe the shipped behavior and the deferral wording above is removed.

## Evidence policy

Screenshots are committed; videos and traces are git-ignored by default with a documented `git-lfs` opt-in; JSON/HTML reports are committed and referenced from the quality report. The policy is config-tunable and enforced by the indexer, not by an author's discipline.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-run skill](../tc-run/SKILL.md)
- [tc-quality-report skill](../tc-quality-report/SKILL.md)
