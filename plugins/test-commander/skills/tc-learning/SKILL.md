---
name: tc-learning
description: Governed continuous learning for Test Commander. Use when the user runs /tc:learn, /tc:learn-from-failures, /tc:learn-from-exploration, /tc:learn-from-feedback, /tc:review-lessons, or /tc:promote-lessons, or asks about capturing candidate lessons from runs, exploration, and feedback, reviewing them into accepted, rejected, and needs-human-review buckets, and promoting accepted lessons into project guidance under a human-approval gate. Owns the six commands of the learning loop, which never silently rewrites Test Commander's own methodology or any third-party skill.
---

# tc-learning

The continuous-learning skill for Test Commander. Owns the six commands that turn signals from runs, exploration, and human feedback into reviewed, governed project guidance — the learning loop that "learns continuously, improves deliberately."

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

The loop has three stages: **capture** (`/tc:learn` and the three `/tc:learn-from-*` commands append candidate lessons to `learning/lessons-inbox.md`), **review** (`/tc:review-lessons` sorts candidates into `accepted` / `rejected` / `needs-human-review`), and **promote** (`/tc:promote-lessons` moves accepted lessons into project guidance under a human-approval gate). Test Commander **never silently rewrites** its own methodology, commands, or templates, and never modifies third-party installed skills (Open Question Q6) — every promotion is a visible `git diff` into the workspace `learning/` tree only.

## Status

Phase 8 (Step 8.2). `/tc:learn` is end-to-end runnable; the other five commands are registered but not yet shipped:

- `/tc:learn` — **shipped (Step 8.2).** Appends a candidate lesson (the `tc-lesson/v1` schema) to `learning/lessons-inbox.md` from a freeform `--note`, with `path:line` provenance, a monotonic `LESSON-NNN` id, and `(source, origin, summary)` dedup. Owns the shared `append_lessons` inbox engine the `/tc:learn-from-*` commands reuse.
- `/tc:learn-from-failures` — **shipped (Step 8.3).** Derives candidate lessons from the Phase-7 `runs/<RUN-ID>/analysis.md` triage, mapping each classification to a lesson category (`product-defect` → `product-defect-pattern`, `flaky` → `flaky-pattern`, `test-defect` → `anti-pattern`, `environment` → `process`), with `runs/.../analysis.md:<line>` provenance, via the shared `append_lessons` engine.
- `/tc:learn-from-exploration` — **shipped (Step 8.4).** Derives candidate lessons from the Phase-4 `exploration-notes/` and `sessions/`: each recorded anomaly becomes an `anti-pattern` candidate (carrying its severity) and each coverage gap a `coverage-gap` candidate, with `exploration-notes/<file>:<line>` provenance, via the shared `append_lessons` engine.
- `/tc:learn-from-feedback` — **shipped (Step 8.5).** Derives candidate lessons from resolved human feedback — `requirements/open-questions.md` entries carrying a `_Resolved:` marker (`process`) and an optional `documents/uploaded/feedback.md` (`heuristic`) — with `path:line` provenance, via the shared `append_lessons` engine. No feedback is a no-op (exit 0), not an error.
- `/tc:review-lessons` — **shipped (Step 8.6).** Classifies every inbox candidate into `accepted` / `rejected` / `needs-human-review` (rubric: `severity: high` → needs-human-review; a `summary` already in `accepted-lessons.md` → rejected; otherwise accepted), moves it to the matching `learning/` file with its `status` updated, and clears the inbox. Idempotent.
- `/tc:promote-lessons` — behavior arrives in Step 8.7. It will propose promotions by default and, only with `--apply` (the human-approval gate), move accepted lessons into `learning/promoted-guidance.md` — never the shipped methodology, never third-party skills.

When Steps 8.3–8.7 land, this SKILL.md is updated to describe their shipped behavior and the deferral wording above is removed.

## Commands

### `/tc:learn`

Appends a candidate lesson (the `tc-lesson/v1` schema) to `learning/lessons-inbox.md` from a freeform `--note`. Allocates a monotonic `LESSON-NNN` id, carries `path:line` provenance, and deduplicates by `(source, origin, summary)`. Deterministic via an injected clock (`--now`). This command owns the shared `append_lessons` engine (id allocation + dedup + inbox append) that every `/tc:learn-from-*` command reuses.

**Run:**

```sh
python3 <plugin-root>/scripts/capture_lesson.py <project-root> --note "..." [--origin <path:line>] [--category <name>] [--severity <low|medium|high>] [--now <ISO-8601>]
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2).

Full spec: [commands/learn.md](commands/learn.md). Methodology: [methodology/learning-loop.md](methodology/learning-loop.md).

### `/tc:learn-from-failures`

Reads every `runs/<RUN-ID>/analysis.md` (the Phase-7 `/tc:analyze-results` triage) and turns each triaged non-passed row into a `tc-lesson/v1` candidate — `product-defect` → `product-defect-pattern`, `flaky` → `flaky-pattern`, `test-defect` → `anti-pattern`, `environment` → `process` — each with `runs/<RUN-ID>/analysis.md:<line>` provenance, appended via the shared `append_lessons` engine. Deterministic; dedups on re-run. Design reference: `superpowers:systematic-debugging`.

**Run:**

```sh
python3 <plugin-root>/scripts/learn_from_failures.py <project-root> [--run-id <RUN-ID>] [--now <ISO-8601>]
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2) and the absence of any `runs/<RUN-ID>/analysis.md` (exit 2; the precondition error directs the user at `/tc:analyze-results`).

Full spec: [commands/learn-from-failures.md](commands/learn-from-failures.md).

### `/tc:learn-from-exploration`

Reads every `exploration-notes/*.md` (and `sessions/*.md`) and turns each recorded anomaly into an `anti-pattern` candidate (carrying its severity) and each `## Coverage gaps` bullet into a `coverage-gap` candidate, each with `exploration-notes/<file>:<line>` provenance, appended via the shared `append_lessons` engine. Deterministic; dedups on re-run.

**Run:**

```sh
python3 <plugin-root>/scripts/learn_from_exploration.py <project-root> [--now <ISO-8601>]
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2) and the absence of any exploration note (exit 2; the precondition error directs the user at `/tc:explore`).

Full spec: [commands/learn-from-exploration.md](commands/learn-from-exploration.md).

### `/tc:learn-from-feedback`

Reads `requirements/open-questions.md` for entries carrying a `_Resolved:` marker (→ `process` candidates) and an optional `documents/uploaded/feedback.md` (→ `heuristic` candidates), appending each as a `tc-lesson/v1` candidate with `path:line` provenance via the shared `append_lessons` engine. **No feedback is a no-op** (exit 0), not an error. Deterministic; dedups on re-run. Design reference: `superpowers:receiving-code-review`.

**Run:**

```sh
python3 <plugin-root>/scripts/learn_from_feedback.py <project-root> [--now <ISO-8601>]
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2).

Full spec: [commands/learn-from-feedback.md](commands/learn-from-feedback.md).

### `/tc:review-lessons`

Reads `learning/lessons-inbox.md` and classifies each `tc-lesson/v1` candidate, most-specific rule first: `severity: high` → `needs-human-review`; a `summary` already present in `accepted-lessons.md` → `rejected` (a duplicate); otherwise → `accepted`. Moves each to the matching `learning/` file with its `status` updated and clears the inbox. Idempotent: a re-run over an already-cleared inbox changes nothing.

**Run:**

```sh
python3 <plugin-root>/scripts/review_lessons.py <project-root>
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2) and a stub inbox with no candidates (exit 2; the precondition error directs the user at `/tc:learn`).

Full spec: [commands/review-lessons.md](commands/review-lessons.md). Methodology: [methodology/improvement-governance.md](methodology/improvement-governance.md).

### `/tc:promote-lessons`

Promotes accepted lessons into project guidance under a human-approval gate. Full behavior is documented in the per-command page once Step 8.7 ships the helper.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-run skill](../tc-run/SKILL.md)
- [tc-explore skill](../tc-explore/SKILL.md)
