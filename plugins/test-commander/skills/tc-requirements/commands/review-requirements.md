# `/tc:review-requirements`

Review requirements under `.test-commander/documents/uploaded/` against the Phase 2 rubric and write the review, inventory, and open-questions artifacts. This page is the authoritative spec for the command — both Claude (at runtime) and human readers consult it.

## Inputs

- **Project root** (positional, optional, default = current working directory). Must contain a `.test-commander/` workspace (run `/tc:init` first if absent).
- **Requirements sources.** Every `*.md` file under `<project-root>/.test-commander/documents/uploaded/` whose body contains at least one `REQ-\d+` token. Other Markdown files in that directory are ignored.
- **Configuration extensions** (optional). `<project-root>/.test-commander/config.yaml` under `tc-requirements:` for project-specific keyword extensions. See [Customizing for your project](../../../../../docs/user-guide/customizing-for-your-project.md).

## Outputs

Three files under `<project-root>/.test-commander/requirements/`:

| Path | Behavior |
| --- | --- |
| `requirements-review.md` | **Overwritten** on every run. Generated report — user edits are not preserved. |
| `requirements-inventory.md` | **Overwritten** with the freshly-parsed REQ-ID list in document order. |
| `open-questions.md` | **Appended** with new questions; deduplicated by `(REQ-ID, question text)`. User-authored content above the auto-generated lines is preserved. |

The review file follows the structure documented in [`templates/requirements-review-template.md`](../templates/requirements-review-template.md).

## Preconditions

- `.test-commander/` exists at the project root (`/tc:init` has been run).
- At least one `REQ-\d+`-bearing Markdown file lives under `documents/uploaded/` (otherwise the helper writes a "no requirements found" review and exits 0).

## Behavior

1. **Validate workspace.** If `<project>/.test-commander/` is missing, raise `UninitializedWorkspaceError`, exit 2.
2. **Parse input.** Walk every `*.md` in `documents/uploaded/`. Treat a file as a requirements source iff it contains at least one `REQ-\d+` token. For each requirement, extract `id` (zero-padded, e.g. `REQ-001`) and the body (the line text after `REQ-NNN:` plus continuation lines until the next REQ marker or the next Markdown heading).
3. **Detect collisions.** If two source files declare the same `REQ-NNN`, raise `RequirementCollisionError`, exit 2. **No artifacts are written on collision.**
4. **Load extensions.** Read `<workspace>/config.yaml`'s `tc-requirements:` block (tolerant parser; missing or malformed file = empty extensions). Union with universal cores.
5. **Apply checks.** Run all 16 mechanical checks (per `methodology/requirements-quality-review.md`). Findings sorted by `(req-id, dimension, detail)` for determinism.
6. **Generate open questions.** Broken `REQ-\d+` references and mutual-exclusion pairs each produce one open question; other findings appear only in the review.
7. **Write artifacts.** Overwrite review and inventory; append (deduped) to open-questions.
8. **Print CLI summary** to stdout and exit 0.

## Safety

- The helper is read-only outside `<project>/.test-commander/requirements/`. It does not touch source code, BDD specs, test code, or any external system.
- Network access: none.
- Idempotent: re-running against unchanged input produces byte-identical review and inventory files; open-questions file is line-stable.
- Workspace-bounded: every path is resolved relative to the supplied project root; the helper never writes outside that root.

## Implementation

`plugins/test-commander/scripts/review_requirements.py` (bundled with the plugin per D18).

CLI:

```sh
python3 <plugin-root>/scripts/review_requirements.py [project_root]
```

`project_root` defaults to the current working directory.

When invoked via the `/tc:review-requirements` slash command, Claude resolves `<plugin-root>` from the `tc-requirements` SKILL.md location, runs the helper via `Bash`, and reports the helper's CLI output plus a narrative summary that adds the judgment layer described in the methodology doc.

## Definition of done

- Helper passes `tests/test_review_requirements.py` (10 cases, including all 16 partition-table dimensions traced to the seeded fixture).
- Methodology doc covers all 16 requirement-level dimensions with worked examples drawn from the seeded fixture.
- Template doc describes the output structure.
- SKILL.md describes shipped behavior with no deferral wording.
- Run against the seeded fixture produces a review file whose findings table names every dimension.

## See also

- [`methodology/requirements-quality-review.md`](../methodology/requirements-quality-review.md) — the rubric and per-dimension checks
- [`templates/requirements-review-template.md`](../templates/requirements-review-template.md) — output structure
- [Customizing for your project](../../../../../docs/user-guide/customizing-for-your-project.md) — `config.yaml` extension model
- [`tc-requirements` SKILL.md](../SKILL.md) — the skill that owns this command
- Planning: [Phase 2 Step 2.2 in `planning/plan.md`](../../../../../planning/plan.md)
