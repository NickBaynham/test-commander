# `/tc:review-acceptance-criteria`

Review acceptance criteria under `.test-commander/documents/uploaded/` against the Phase 2 AC rubric and write a structured review under `.test-commander/requirements/`. This page is the authoritative spec — both Claude (at runtime) and human readers consult it.

## Inputs

- **Project root** (positional, optional, default = current working directory). Must contain a `.test-commander/` workspace (run `/tc:init` first if absent).
- **AC sources.** Every `*.md` file under `<project-root>/.test-commander/documents/uploaded/` whose body contains at least one `AC-\d+` or `US-\d+` token. AC entries are parsed via `AC-NNN[-NN]: Given ... When ... Then ...`. US tokens in the same files (or other files in the same directory) populate the in-scope user-story set for orphan detection.
- **Configuration extensions** (optional). `<project-root>/.test-commander/config.yaml` under `tc-requirements.roles-permissions:` for project-specific permission verbs and role qualifiers. See [Customizing for your project](../../../../../docs/user-guide/customizing-for-your-project.md).

## Outputs

One file under `<project-root>/.test-commander/requirements/`:

| Path | Behavior |
| --- | --- |
| `acceptance-criteria-review.md` | **Overwritten** on every run. Generated report — user edits are not preserved. |

The review file follows the structure documented in [`templates/acceptance-criteria-review-template.md`](../templates/acceptance-criteria-review-template.md).

## Preconditions

- `.test-commander/` exists at the project root (`/tc:init` has been run).
- At least one `AC-\d+`-bearing Markdown file lives under `documents/uploaded/` (otherwise the helper writes a "no acceptance criteria found" review and exits 0).

## Behavior

1. **Validate workspace.** If `<project>/.test-commander/` is missing, raise `UninitializedWorkspaceError`, exit 2.
2. **Parse input.** Walk every `*.md` in `documents/uploaded/`. From each AC/US-bearing file, extract:
   - Every `AC-NNN[-NN]: <body>` entry. The body runs from the marker line through continuation lines until the next AC/US marker or a Markdown heading.
   - Every `US-NNN` token (used only to populate the in-scope story set for orphan detection).
3. **Strip parenthetical asides** from each AC body before applying checks. Parentheticals carry meta-commentary that would otherwise satisfy the keyword checks they describe.
4. **Apply checks.** Five AC-rubric checks per the partition table in [`methodology/acceptance-criteria-quality.md`](../methodology/acceptance-criteria-quality.md):
   - `ac-missing-edge-cases` — Given/When/Then body lacks any edge keyword.
   - `ac-missing-negative-cases` — Given/When/Then body lacks any failure keyword.
   - `ac-untestable-predicate` — subjective-experience word, or vague predicate without numeric threshold.
   - `ac-ambiguous-data-rule` — ambiguity word present in the body.
   - `ac-missing-role-context` — permission verb present without a role qualifier (universal core + `config.yaml` extensions).
5. **Orphan detection.** For each AC, derive the parent story ID (`AC-NNN-NN` → `US-NNN`). If `US-NNN` is not in the in-scope story set, emit an `orphan` finding.
6. **Write review.** Overwrite `<workspace>/requirements/acceptance-criteria-review.md` with executive summary, findings grouped by parent story, a flat findings table, and a traceability footer.
7. **Print CLI summary** to stdout and exit 0.

## Safety

- Read-only outside `<project>/.test-commander/requirements/`. Does not touch source code, BDD specs, or any external system.
- Network access: none.
- Idempotent: re-running against unchanged input produces a byte-identical review file.
- Workspace-bounded: every path resolved relative to the supplied project root.

## Implementation

`plugins/test-commander/scripts/review_acceptance_criteria.py` (bundled with the plugin per D18).

CLI:

```sh
python3 <plugin-root>/scripts/review_acceptance_criteria.py [project_root]
```

`project_root` defaults to the current working directory.

When invoked via the `/tc:review-acceptance-criteria` slash command, Claude resolves `<plugin-root>` from the `tc-requirements` SKILL.md location, runs the helper via `Bash`, and reports the helper's CLI output plus a narrative summary that adds the judgment layer described in the methodology doc.

## Definition of done

- Helper passes `tests/test_review_acceptance_criteria.py` (7 cases, including all 5 AC-rubric dimensions traced to the seeded fixture).
- Methodology doc covers all 6 dimensions (the 5 rubric checks plus `orphan`) with worked examples drawn from the seeded fixture.
- Template doc describes the output structure.
- SKILL.md describes the shipped behavior with no deferral wording for this command.
- Run against the seeded fixture flags every AC-rubric defect and any orphan ACs.

## See also

- [`methodology/acceptance-criteria-quality.md`](../methodology/acceptance-criteria-quality.md) — AC rubric and per-dimension checks
- [`templates/acceptance-criteria-review-template.md`](../templates/acceptance-criteria-review-template.md) — output structure
- [`methodology/user-story-readiness.md`](../methodology/user-story-readiness.md) — parent-story INVEST rubric
- [`tc-requirements` SKILL.md](../SKILL.md) — the skill that owns this command
- Planning: [Phase 2 Step 2.4 in `planning/plan.md`](../../../../../planning/plan.md)
