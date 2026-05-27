---
name: tc-core
description: Core Test Commander orchestration commands. Use when the user runs /tc:init, /tc:status, /tc:journal, or /tc:next, or asks about the current state of a Test Commander workspace. Owns the four commands that initialize the .test-commander/ workspace, summarize its state, append journal entries, and recommend the next command.
---

# tc-core

The umbrella skill for Test Commander. Owns the four orchestration commands that act on the workspace itself.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). When the user invokes one of these slash commands, run the corresponding helper with `Bash` and report the output. The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Finding the helpers

The helpers live at `scripts/<name>.py` relative to this plugin's root (the directory containing this SKILL.md is `<plugin-root>/skills/tc-core/`). In a development checkout that is `<repo>/plugins/test-commander/scripts/`. In the installed plugin cache it is `~/.claude/plugins/cache/test-commander-marketplace/test-commander/<version>/scripts/`. Either way, resolve the helper path relative to this SKILL.md's own location.

## Commands

### `/tc:init`

Initialize a Test Commander workspace inside the user's current project. Copies the bundled template at `<plugin-root>/templates/workspace/` into `<project-root>/.test-commander/`. Idempotent — existing files are preserved.

**Run:**

```sh
python3 <plugin-root>/scripts/init_workspace.py <project-root>
```

`<project-root>` defaults to the current working directory if the user does not supply one.

Full spec: [commands/init.md](commands/init.md).

### `/tc:status`

Print a snapshot of the workspace: file counts per bucket, populated counts (files differing from the bundled template), per-phase status (`not_started` / `in_progress`), and last-activity timestamp. Read-only.

**Run:**

```sh
python3 <plugin-root>/scripts/workspace_state.py <project-root>
```

Full spec: [commands/status.md](commands/status.md).

### `/tc:journal`

Append a timestamped narrative entry to today's day file, or summarize chronological entries within a date range.

**Run (append):**

```sh
python3 <plugin-root>/scripts/journal.py --target <project-root> append "<body>"
```

**Run (summarize):**

```sh
python3 <plugin-root>/scripts/journal.py --target <project-root> summarize [--from YYYY-MM-DD] [--to YYYY-MM-DD]
```

The body must be non-empty and must not contain an H2 timestamp heading. Day files live at `.test-commander/journal/YYYY-MM-DD.md`.

Full spec: [commands/journal.md](commands/journal.md).

### `/tc:next`

Recommend the next Test Commander command based on the current workspace state. Reads the snapshot, applies the rules documented in [methodology/next-step-inference.md](methodology/next-step-inference.md), and prints a ranked recommendation list with the top match on a `next:` line.

**Run:**

```sh
python3 <plugin-root>/scripts/next_step.py <project-root>
```

Full spec: [commands/next.md](commands/next.md).

## What to do when a slash command fires

1. Identify which of the four commands the user wants.
2. Resolve `<plugin-root>` relative to this SKILL.md.
3. Determine `<project-root>` — current working directory unless the user specified otherwise.
4. Run the helper via `Bash` and pipe the output back to the user.
5. If the helper exits non-zero, surface its stderr and the relevant per-command page so the user can act on it.

The helpers are deterministic, idempotent where it makes sense, and bounded to the project root. They never write outside the target directory.

## See also

- [Plugin README](../../README.md)
- [Workflow walkthrough](../../../../docs/user-guide/workflow.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [Phased plan](../../../../planning/plan.md)
