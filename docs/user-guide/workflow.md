# Workflow — First Walkthrough

This guide takes you through the four Phase 1 commands end to end against a consuming project.

## What's available in Phase 1

| Command | Purpose |
| --- | --- |
| `/tc:init` | Create `.test-commander/` inside the project, copying from the bundled template. |
| `/tc:status` | Read the workspace and print a snapshot: file counts, populated counts, per-phase status. |
| `/tc:journal` | Append a timestamped narrative entry, or summarize entries in a date range. |
| `/tc:next` | Read the snapshot and recommend the next Test Commander command. |

All four are read-or-write-bounded, idempotent where it makes sense, and safe to run repeatedly.

## Prerequisites

- Test Commander installed: `./bootstrap.sh` then `make install` from the `test-commander` repo (see [getting-started.md](getting-started.md)).
- A consuming project directory (any folder where you want to track quality work).

## Step 1 — Initialize

From the consuming project root:

```sh
python3 /path/to/test-commander/plugins/test-commander/scripts/init_workspace.py .
```

Or, when invoked through Claude Code, just ask for `/tc:init`. The script creates `.test-commander/` and copies the workspace template into it. Output:

```
workspace: <project>/.test-commander
created:   63
skipped:   0

New files:
  README.md
  audit/README.md
  ...
```

Re-running is a no-op (`created: 0, skipped: 63`); existing files are never overwritten.

## Step 2 — Customize project metadata

`/tc:init` copies the template verbatim, including placeholder content in `project.md`, `config.yaml`, and `methodology.md`. Open each and replace the placeholders with project-specific values:

- `project.md` — project name, repository URL, owner, Test Commander version.
- `config.yaml` — feature flags, defaults, policy overrides for this project. This is also where domain-specific extensions to the rubric live once Phase 2 ships (see [customizing-for-your-project.md](customizing-for-your-project.md) for the full extension model — PCI/HIPAA vocabulary, your role taxonomy, your risk classes).
- `methodology.md` — exploration style, BDD conventions, automation suitability rules.

This is the manual step Phase 1 ships with. Later phases will offer a guided `/tc:init` mode that fills these in interactively.

## Step 3 — Check status

```sh
python3 /path/to/test-commander/plugins/test-commander/scripts/workspace_state.py .
```

Or `/tc:status` through Claude Code. Sample output for a workspace where `project.md` and a Phase 2 file have been touched:

```
workspace: <project>/.test-commander  (initialized)
last activity: 2026-05-26T22:35:07+00:00
files: 63 total, 2 populated

by bucket:
  project.md                   1  (1 populated)
  requirements                 7  (1 populated)
  ...

phase status:
  1     Workspace                  in_progress
  2     Requirements               in_progress
  3     Project knowledge          not_started
  ...
```

"Populated" = file bytes differ from the bundled template. A phase is `in_progress` once at least one file it owns is populated.

## Step 4 — Append a journal entry

```sh
python3 /path/to/test-commander/plugins/test-commander/scripts/journal.py --target . append "Initialized workspace and reviewed first batch of requirements."
```

Or `/tc:journal append "..."` through Claude Code. The entry lands in `.test-commander/journal/YYYY-MM-DD.md` as a timestamped H2 section. Append to the same day adds a second section to the same file. The journal is append-only; never edited in place.

Summarize a range:

```sh
python3 .../journal.py --target . summarize --from 2026-05-20 --to 2026-05-31
```

Empty bodies are refused; bodies containing an H2 timestamp heading are refused (would corrupt parsing).

## Step 5 — Ask "what next?"

```sh
python3 /path/to/test-commander/plugins/test-commander/scripts/next_step.py .
```

Or `/tc:next` through Claude Code. The engine reads the snapshot and returns a ranked list of recommendations. The top match comes back as `next:`; downstream gaps follow as `followups:`. Sample output after editing `project.md`:

```
next: /tc:review-requirements  (Phase 2)
  Review the project's requirements: testability, clarity, completeness.
  Surfaces gaps and ambiguity before any test work begins.

followups:
  /tc:learn-from-docs  (Phase 3)
  /tc:create-charter  (Phase 4)
  /tc:generate-bdd  (Phase 5)
  /tc:automation-plan  (Phase 6)
  /tc:run  (Phase 7)
  /tc:learn  (Phase 8)
```

The recommendation rules are documented in [`next-step-inference.md`](../../plugins/test-commander/skills/tc-core/methodology/next-step-inference.md).

## What changed on disk

After this walkthrough, the consuming project contains:

- `.test-commander/` — 63 starter files from the template, plus your edits to `project.md`.
- `.test-commander/journal/YYYY-MM-DD.md` — your day's entries.

Everything is plain Markdown and YAML; commit it all to git.

## Beyond Phase 1

`/tc:next` will recommend `/tc:review-requirements` when Phase 1 metadata is filled in. That command lands in Phase 2. For the full phased roadmap, see [../../planning/plan.md](../../planning/plan.md).

## See also

- [Getting started](getting-started.md) — install and verify
- [Customizing for your project](customizing-for-your-project.md) — extend the universal core with your domain vocabulary
- [Workspace reference](../workspace-reference.md) — per-directory purpose
- [Command reference](../command-reference.md) — index of every command
- [Per-command pages](../../plugins/test-commander/skills/tc-core/commands/) — full behavior for each command
