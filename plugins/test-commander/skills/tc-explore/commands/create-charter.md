# `/tc:create-charter`

The Phase 4 charter-creation command. Reads Phase-3 product-knowledge artifacts plus Phase-2 open-questions plus the project's risk-register to either accept an explicit `--target`/`--mission` charter scope OR auto-suggest one based on the entity with the highest mention count, then writes a charter file to `<workspace>/charters/<CH-NNN>.md` with YAML frontmatter carrying every CHARTER_REQUIRED_FIELDS key (the Step-4.1 cross-phase contract) and a structured body (Mission / Target Area / Time-Box / Risk Areas / Acceptance Criteria / Out of Scope / Phase 3 Sources).

## Inputs

- `<workspace>/product-knowledge/entities.md` (required; refused with precondition error if still the template stub) - the cross-source entity index. Auto-suggestion picks the entity with the highest mention count.
- `<workspace>/product-knowledge/user-journeys.md` (optional but cited) - bolded journey titles contribute to the mention-count tally.
- `<workspace>/product-knowledge/system-model.md` (optional but cited) - the synthesized cross-source overview.
- `<workspace>/requirements/open-questions.md` (optional but cited) - entity mentions in the gap-signal backlog boost the entity's mention-count score.
- `<workspace>/risk-register/risk-register.md` (optional but cited) - lines matching universal-core OR project-extended risk keywords surface as risk-areas.
- `<workspace>/config.yaml` (optional) - the `tc-explore.charters:` block configures the helper. Recognized keys:
  - `risk-keywords: [...]` - additive list of project-specific risk keywords that extend the universal core.
  - `area-keywords: [...]` - additive list of project-specific area keywords (reserved for `/tc:explore` auto-detection in Step 4.3).

## Outputs

| Path | Mode | Owner |
| --- | --- | --- |
| `<workspace>/charters/CH-NNN.md` | overwrite on first create; skip-not-overwrite on re-run | this command |
| stdout | informational CLI report (`created: N  skipped: N -> CH-NNN at <path>`) | this command |

`<workspace>/exploration-notes/`, `<workspace>/sessions/`, `<workspace>/test-ideas/`, `<workspace>/requirements/open-questions.md`, and `<workspace>/traceability/` are NOT touched - those are owned by Steps 4.3-4.5 and Phase 5 respectively.

## Preconditions

- `<workspace>/.test-commander/` exists (`/tc:init` has run - Phase 1).
- At least one Phase-3 product-knowledge artifact has been generated (i.e. `/tc:learn-from-docs` has run). The helper detects template-stub state via the synthesizer's empty-marker check and refuses with a precondition error directing the user at `/tc:learn-from-docs`.

## Behavior

1. Resolve the workspace and load `tc-explore.charters:` extensions from `<workspace>/config.yaml`.
2. Assert at least one product-knowledge artifact is generated (not still the template stub); collect the list of consumed artifacts for the charter's `phase_3_sources:` frontmatter field.
3. **Explicit path (`--target` or `--mission` supplied):** build a `Suggestion` from the supplied scope. Default mission is generated from the target if only `--target` is supplied; default target is generated from the mission if only `--mission` is supplied.
4. **Auto-suggestion path (neither flag supplied):** parse entities from `entities.md`'s `## From <source>` sections; tally mention counts across entities.md, user-journeys.md, and open-questions.md; rank by `(mention_count, alphabetical_name)`; pick the top entity. Build a Suggestion with a generic mission ("Discover whether the {top} flow behaves correctly under the documented risk conditions"), target ("{top}-related endpoints and pages"), risk-areas extracted from risk-register.md (or generic defaults if empty), three generic acceptance criteria, and two generic out-of-scope items.
5. **Idempotency check** (unless `--new-id` is set): scan `<workspace>/charters/CH-*.md` for a charter whose `target:` frontmatter field matches the new target (case-insensitive exact match). If found, skip - CLI reports `created: 0 skipped: 1 -> <existing-CH-ID>`. The existing charter's bytes are preserved verbatim (user edits intact).
6. **Allocation** (no skip): scan existing CH-NNN files, allocate NNN+1 zero-padded to 3 digits.
7. **Render** the charter from the `Suggestion` + allocated ID + ISO-8601 `created_at` timestamp + the consumed `phase_3_sources` list. The render shape is documented in [`templates/charter-template.md`](../templates/charter-template.md).
8. Write to `<workspace>/charters/CH-NNN.md`. Print `created: 1 skipped: 0 -> CH-NNN at <path>`.
9. Exit 0.

## Safety

- Refuses uninitialized workspace with exit 2 before any IO.
- Refuses empty Phase-3 product-knowledge with exit 2; precondition error names `/tc:learn-from-docs`.
- ID allocation is single-process (no `fcntl.flock` in v1; concurrent invocation is a documented failure mode in the plan's Step 4.2 deliverables but not implemented in v1; consuming projects should serialize charter creation through the user-facing UI).
- Skip-not-overwrite for existing charters preserves user edits byte-for-byte (mirrors the Phase 2 Step 2.6 idempotency contract for downstream-enriched artifacts).
- No shell-out; no network; no writes outside `<workspace>/charters/`.
- Per D19, the universal-core risk-keyword and area-keyword sets carry no domain vocabulary.

## Implementation

- Helper: `plugins/test-commander/scripts/create_charter.py` (~470 lines).
- Establishes the Phase 4 helper-mirroring skeleton that Steps 4.3-4.5 will copy-rename. The differences between siblings concentrate in source parsing and the per-command extraction logic; workspace IO, config loading, ID allocation, and idempotency handling are fungible.
- Tests: `tests/test_create_charter.py` (14 cases - uninit refused, product-knowledge missing refused with precondition error, --target generates CH-001 with all CHARTER_REQUIRED_FIELDS, charter passes well-formed shape check with required body sections, phase_3_sources lists consumed artifacts, auto-suggestion picks highest-mention entity, ties broken alphabetically, idempotent re-run produces skipped:1 with byte-identical charter, --new-id reallocates as CH-002, user-edited body preserved on skip, risk-keywords and area-keywords config extensions work).

## Definition of Done

- Helper passes all 14 test cases.
- Charter render shape matches `CHARTER_REQUIRED_FIELDS` (the Step 4.1 scaffold-test contract) literally.
- Methodology covers all 6 rubric dimensions (mission specificity, target scope, time-box discipline, risk-area enumeration, acceptance-criteria testability, out-of-scope discipline) with worked examples + Claude-judgment-layer paragraphs.
- Umbrella `exploratory-testing.md` documents the cross-command workflow + cross-phase write boundaries + test-idea enrichment contract.
- Charter and target-app templates authored.
- Per-command page complete (this file).
- `tc-explore/SKILL.md` describes `/tc:create-charter`'s shipped behavior with no deferral wording for this command.
- `make verify` chain green.

## See also

- [Charter-based-exploration methodology](../methodology/charter-based-exploration.md) - charter rubric and Claude judgment layer.
- [Umbrella exploratory-testing methodology](../methodology/exploratory-testing.md) - cross-command workflow and cross-phase write boundaries.
- [Charter template](../templates/charter-template.md) - the render shape.
- [Target-app template](../templates/target-app-template.md) - for consuming projects describing their own target.
- [Seeded charter (CH-001)](../../../../../tests/fixtures/seeded-exploration-session/charter.md) - worked example.
