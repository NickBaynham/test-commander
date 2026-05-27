# `/tc:review-user-stories`

Review user stories under `.test-commander/documents/uploaded/` against the Phase 2 INVEST rubric (plus role-action-benefit shape and acceptance-criteria-pointer checks), and write a structured review under `.test-commander/requirements/`. This page is the authoritative spec for the command — both Claude (at runtime) and human readers consult it.

## Inputs

- **Project root** (positional, optional, default = current working directory). Must contain a `.test-commander/` workspace (run `/tc:init` first if absent).
- **User-story sources.** Every `*.md` file under `<project-root>/.test-commander/documents/uploaded/` whose body contains at least one `US-\d+` token. Other Markdown files are ignored.

## Outputs

One file under `<project-root>/.test-commander/requirements/`:

| Path | Behavior |
| --- | --- |
| `user-story-review.md` | **Overwritten** on every run. Generated report — user edits are not preserved. |

The review file follows the structure documented in [`templates/user-story-review-template.md`](../templates/user-story-review-template.md).

## Preconditions

- `.test-commander/` exists at the project root (`/tc:init` has been run).
- At least one `US-\d+`-bearing Markdown file lives under `documents/uploaded/` (otherwise the helper writes a "no user stories found" review and exits 0).

## Behavior

1. **Validate workspace.** If `<project>/.test-commander/` is missing, raise `UninitializedWorkspaceError`, exit 2.
2. **Parse input.** Walk every `*.md` in `documents/uploaded/`. Treat a file as a user-stories source iff it contains at least one `US-\d+` token. For each story, extract `id` (zero-padded, e.g. `US-001`) and the body (the line text after `US-NNN:` plus continuation lines until the next US marker or the next Markdown heading).
3. **Apply checks.** Run all 8 mechanical checks (per [`methodology/user-story-readiness.md`](../methodology/user-story-readiness.md)):
   - Six INVEST checks: `invest-independent`, `invest-negotiable`, `invest-valuable`, `invest-estimable`, `invest-small`, `invest-testable`.
   - `role-action-benefit` shape (must contain `As a`, `I want`, `So that`).
   - `needs-acceptance-criteria` (must contain an `AC-\d+` pointer).
4. **Compute verdicts.** Each story gets one of `ready` / `needs-refinement` / `blocked` per the verdict table in the methodology doc.
5. **Write review.** Overwrite `<workspace>/requirements/user-story-review.md` with executive summary, findings table, per-story detail, and traceability footer.
6. **Print CLI summary** to stdout and exit 0.

## Safety

- Read-only outside `<project>/.test-commander/requirements/`. Does not touch source code, BDD specs, test code, or any external system.
- Network access: none.
- Idempotent: re-running against unchanged input produces a byte-identical review file.
- Workspace-bounded: every path resolved relative to the supplied project root.

## Implementation

`plugins/test-commander/scripts/review_user_stories.py` (bundled with the plugin per D18).

CLI:

```sh
python3 <plugin-root>/scripts/review_user_stories.py [project_root]
```

`project_root` defaults to the current working directory.

When invoked via the `/tc:review-user-stories` slash command, Claude resolves `<plugin-root>` from the `tc-requirements` SKILL.md location, runs the helper via `Bash`, and reports the helper's CLI output plus a narrative summary that adds the judgment layer described in the methodology doc.

## Definition of done

- Helper passes `tests/test_review_user_stories.py` (9 cases, including all 6 INVEST letters traced to the seeded fixture).
- Methodology doc covers all 8 dimensions with worked examples drawn from the seeded fixture.
- Template doc describes the output structure including the readiness verdicts.
- SKILL.md describes the shipped behavior with no deferral wording.
- Run against the seeded fixture flags every INVEST violation and emits one of three verdicts per story.

## See also

- [`methodology/user-story-readiness.md`](../methodology/user-story-readiness.md) — INVEST rubric and per-dimension checks
- [`templates/user-story-review-template.md`](../templates/user-story-review-template.md) — output structure
- [`tc-requirements` SKILL.md](../SKILL.md) — the skill that owns this command
- Planning: [Phase 2 Step 2.3 in `planning/plan.md`](../../../../../planning/plan.md)
