---
name: tc-core
description: Core Test Commander orchestration commands. Use when the user runs /tc:init, /tc:status, or /tc:journal, or asks about the current state of a Test Commander workspace. Owns the umbrella commands that initialize the .test-commander/ workspace, summarize its state, and append journal entries.
---

# tc-core

The umbrella skill for Test Commander. Owns the orchestration commands that act on the workspace itself.

## Commands

### `/tc:init`

Create the `.test-commander/` workspace inside the current consuming project. Idempotent — running again on an existing workspace updates missing files rather than overwriting.

Behavior arrives in Phase 1.

### `/tc:status`

Summarize the current workspace state: which artifacts exist, which are stale, which phases are active, and what is pending.

Behavior arrives in Phase 1.

### `/tc:journal`

Append a journal entry to `.test-commander/journal/`, or summarize recent entries. Used to record what happened in a session without committing every detail to the audit log.

Behavior arrives in Phase 1.

## Coming in Phase 1

`/tc:next` — read workspace state and recommend the next command. Deferred from Phase 0 per Open Question Q7; will be added to this same skill in Phase 1.

## Phase 0 scope

This file is the skill descriptor only. No commands are implemented yet. Phase 0 ships the scaffold so Claude Code can load the skill and recognize the command surface; Phase 1 adds the behavior.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Command reference](../../../../docs/command-reference.md)
