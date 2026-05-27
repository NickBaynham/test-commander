# `/tc:requirements-to-tests`

For every reviewed requirement, generate a seed test-idea file under `.test-commander/test-ideas/<REQ-ID>.md` with a Phase-4-compatible YAML frontmatter schema (`tc-test-idea/v1`). Refresh the traceability map so each requirement links to its new seed. This page is the authoritative spec **and the Phase 4 schema contract**.

## Inputs

- **Project root** (positional, optional, default = current working directory). Must contain a `.test-commander/` workspace (run `/tc:init` first if absent).
- **Requirements review.** `<project-root>/.test-commander/requirements/requirements-review.md` produced by `/tc:review-requirements` (Step 2.2). The unmodified workspace template stub does NOT count — the helper requires the review to bear the Step 2.2 generator's structural markers (`## Executive summary` and `## Findings`).
- **Source requirements.** `documents/uploaded/*.md` files containing `REQ-\d+` markers; the helper re-parses them to recover bodies, not the inventory cell contents.
- **Acceptance-criteria review** (optional). `<workspace>/requirements/acceptance-criteria-review.md` produced by `/tc:review-acceptance-criteria` (Step 2.4). When present and generated, each seed includes a "Related acceptance-criteria findings" section and the schema's `ac_review_present` flag flips to `true`.

## Outputs

| Path | Behavior |
| --- | --- |
| `test-ideas/<REQ-ID>.md` (one per parsed REQ) | **Created if absent; preserved if present.** Phase 4 (`tc-explore`) enriches these files; user edits survive re-runs. |
| `traceability/requirements-map.md` | **Overwritten** by the embedded `requirements_coverage.coverage()` refresh after seeds are written. Same shape as Step 2.5's map; rows now include the new `test-ideas/<REQ-ID>.md` link per REQ. |

## Phase 4 schema contract (`tc-test-idea/v1`)

Every emitted seed file begins with a YAML frontmatter block of this exact shape:

```yaml
---
schema: tc-test-idea/v1
requirement_id: REQ-001
requirement_title: <first ~12 words of requirement body, trimmed>
source: documents/uploaded/<filename.md>
status: seed
ac_review_present: <true|false>
phase_2_findings:
  - clarity
  - testability
  - <other dimensions>
candidates:
  - id: REQ-001-happy-01
    title: Happy path
    type: positive
    source: helper-derived
  - id: REQ-001-edge-01
    title: Edge case (define from product knowledge)
    type: edge
    source: helper-derived | ac-review
  - id: REQ-001-negative-01
    title: Negative case (define from product knowledge)
    type: negative
    source: helper-derived | ac-review
generated_by: /tc:requirements-to-tests
---
```

**Stable keys** (Phase 4 must read these without modification):

- `schema` — version stamp; future schema revisions bump the version (`tc-test-idea/v2`, etc.) and Phase 4 reads `v1` files until migrated.
- `requirement_id` — the REQ-NNN this seed belongs to.
- `requirement_title` — short title derived from the body (display only).
- `source` — relative path to the originating Markdown document.
- `status` — `seed` from Step 2.6; Phase 4 may transition to `enriched`, `automated`, etc.
- `ac_review_present` — whether an AC review was in scope when the seed was generated.
- `phase_2_findings` — the rubric dimensions flagged for this REQ in Step 2.2.
- `candidates` — list of `{id, title, type, source}`. `type ∈ {positive, edge, negative}`. Phase 4 may append to this list but should not modify or remove existing entries authored by Step 2.6 (those are anchors for traceability).
- `generated_by` — provenance.

The body after the frontmatter is human-editable Markdown. Phase 4 will append charters and exploration notes here; Step 2.6 ships only the seeded scenario titles plus references back to the requirement.

## Preconditions

- `.test-commander/` exists at the project root.
- `requirements-review.md` exists and shows Step 2.2 generator markers; otherwise the helper raises `ReviewMissingError` (exit 2).
- (Optional) `acceptance-criteria-review.md` exists and shows Step 2.4 generator markers; if so, seeds reference it.

## Behavior

1. **Validate workspace.** Missing `.test-commander/` → `UninitializedWorkspaceError`, exit 2.
2. **Validate review.** Missing or stub `requirements-review.md` → `ReviewMissingError`, exit 2.
3. **Parse requirements.** Re-use `review_requirements.parse_workspace()` to get the full list of `Requirement` objects with id, body, and source filename.
4. **Compute per-REQ findings.** Re-run the Step 2.2 mechanical checks via `review_requirements.apply_checks()` to populate `phase_2_findings` for each REQ. The traceability map will likewise use the same Phase 2 view.
5. **Detect AC review.** If `acceptance-criteria-review.md` is present with Step 2.4 generator markers (`## Executive summary` or `no acceptance criteria found`), set `ac_review_present` true; otherwise false.
6. **Write seeds.** For each REQ, target path = `test-ideas/<REQ-ID>.md`. If the path exists, **skip** (preserving Phase 4 enrichment and user edits). Otherwise write the seed (frontmatter + body).
7. **Refresh traceability map** by calling `requirements_coverage.coverage()`. The map now reflects every newly-linked seed.
8. **Print CLI summary** to stdout and exit 0.

## Safety

- Test-idea files: **never** overwritten. Re-running is a no-op for existing seeds.
- Traceability map: overwritten byte-deterministically by the coverage refresh.
- Read-only outside `<workspace>/test-ideas/` and `<workspace>/traceability/`.
- Network access: none.
- Workspace-bounded: every path resolved relative to the supplied project root.

## Implementation

`plugins/test-commander/scripts/requirements_to_tests.py` (bundled with the plugin per D18).

CLI:

```sh
python3 <plugin-root>/scripts/requirements_to_tests.py [project_root]
```

`project_root` defaults to the current working directory.

When invoked via the `/tc:requirements-to-tests` slash command, Claude resolves `<plugin-root>` from the `tc-requirements` SKILL.md location, runs the helper via `Bash`, reports the helper's CLI output, and adds a narrative summary that highlights any newly-created seeds and how their phase_2_findings should shape downstream scenario authoring.

## Definition of done

- Helper passes `tests/test_requirements_to_tests.py` (9 cases: uninitialized refused, missing-review refused, one seed per parsed REQ, schema header shape, user edits preserved on re-run, idempotent file count, traceability map updated with seed links, AC review present adds reference section, AC review absent omits it).
- Every emitted seed validates against the `tc-test-idea/v1` schema documented above.
- SKILL.md describes the shipped behavior with no deferral wording — by end of Step 2.6 all five Phase 2 commands ship.
- The traceability map after Step 2.6 links every REQ to its `test-ideas/<REQ-ID>.md`.

## See also

- [`commands/review-requirements.md`](review-requirements.md) — produces the review this command depends on.
- [`commands/requirements-coverage.md`](requirements-coverage.md) — coverage scanner Step 2.6 re-uses to refresh the traceability map.
- [`commands/review-acceptance-criteria.md`](review-acceptance-criteria.md) — optional input; presence flips `ac_review_present` true in every seed.
- [`tc-requirements` SKILL.md](../SKILL.md) — the skill that owns this command.
- Planning: [Phase 2 Step 2.6 in `planning/plan.md`](../../../../../planning/plan.md).
