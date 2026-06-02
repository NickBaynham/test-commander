---
name: tc-learning
description: Governed continuous learning for Test Commander. Use when the user runs /tc:learn, /tc:learn-from-failures, /tc:learn-from-exploration, /tc:learn-from-feedback, /tc:review-lessons, or /tc:promote-lessons, or asks about capturing candidate lessons from runs, exploration, and feedback, reviewing them into accepted, rejected, and needs-human-review buckets, and promoting accepted lessons into project guidance under a human-approval gate. Owns the six commands of the learning loop, which never silently rewrites Test Commander's own methodology or any third-party skill.
---

# tc-learning

The continuous-learning skill for Test Commander. Owns the six commands that turn signals from runs, exploration, and human feedback into reviewed, governed project guidance — the learning loop that "learns continuously, improves deliberately."

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

The loop has three stages: **capture** (`/tc:learn` and the three `/tc:learn-from-*` commands append candidate lessons to `learning/lessons-inbox.md`), **review** (`/tc:review-lessons` sorts candidates into `accepted` / `rejected` / `needs-human-review`), and **promote** (`/tc:promote-lessons` moves accepted lessons into project guidance under a human-approval gate). Test Commander **never silently rewrites** its own methodology, commands, or templates, and never modifies third-party installed skills (Open Question Q6) — every promotion is a visible `git diff` into the workspace `learning/` tree only.

## Status

Phase 8 scaffold (Step 8.1). The six commands are registered but their behavior is not yet shipped:

- `/tc:learn` — behavior arrives in Step 8.2. It will append a candidate lesson (the `tc-lesson/v1` schema) to `learning/lessons-inbox.md` from a freeform `--note` or by aggregating cross-workspace signals, with `path:line` provenance and a stable `LESSON-NNN` id.
- `/tc:learn-from-failures` — behavior arrives in Step 8.3. It will derive candidate lessons from the Phase-7 `runs/<RUN-ID>/analysis.md` triage (recurring `product-defect` and `flaky` patterns).
- `/tc:learn-from-exploration` — behavior arrives in Step 8.4. It will derive candidate lessons from the Phase-4 `exploration-notes/` and `sessions/` (recurring anomalies and coverage gaps).
- `/tc:learn-from-feedback` — behavior arrives in Step 8.5. It will derive candidate lessons from resolved human feedback (`requirements/open-questions.md` and an optional `documents/uploaded/feedback.md`).
- `/tc:review-lessons` — behavior arrives in Step 8.6. It will classify every inbox candidate into `accepted` / `rejected` / `needs-human-review`, move it to the matching `learning/` file, and clear the inbox.
- `/tc:promote-lessons` — behavior arrives in Step 8.7. It will propose promotions by default and, only with `--apply` (the human-approval gate), move accepted lessons into `learning/promoted-guidance.md` — never the shipped methodology, never third-party skills.

When Steps 8.2–8.7 land, this SKILL.md is updated to describe the shipped behavior and the deferral wording above is removed.

## Commands

### `/tc:learn`

Appends a candidate lesson to the lessons inbox. Full behavior is documented in the per-command page once Step 8.2 ships the helper.

### `/tc:learn-from-failures`

Derives candidate lessons from the latest test-run triage. Full behavior is documented in the per-command page once Step 8.3 ships the helper.

### `/tc:learn-from-exploration`

Derives candidate lessons from exploration notes and session summaries. Full behavior is documented in the per-command page once Step 8.4 ships the helper.

### `/tc:learn-from-feedback`

Derives candidate lessons from resolved human feedback. Full behavior is documented in the per-command page once Step 8.5 ships the helper.

### `/tc:review-lessons`

Classifies inbox candidates into accepted / rejected / needs-human-review. Full behavior is documented in the per-command page once Step 8.6 ships the helper.

### `/tc:promote-lessons`

Promotes accepted lessons into project guidance under a human-approval gate. Full behavior is documented in the per-command page once Step 8.7 ships the helper.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-run skill](../tc-run/SKILL.md)
- [tc-explore skill](../tc-explore/SKILL.md)
