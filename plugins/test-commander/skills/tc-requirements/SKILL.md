---
name: tc-requirements
description: Requirements quality, user-story, acceptance-criteria, coverage, and test-seed commands for Test Commander. Use when the user runs /tc:review-requirements, /tc:review-user-stories, /tc:review-acceptance-criteria, /tc:requirements-coverage, or /tc:requirements-to-tests, or asks about requirements quality, INVEST, acceptance criteria, or requirements traceability. Owns the five commands that turn uploaded requirements documents into reviewed artifacts and traceable test-idea seeds under .test-commander/requirements/ and .test-commander/test-ideas/.
---

# tc-requirements

The requirements-intelligence skill for Test Commander. Owns the five commands that review requirements, user stories, and acceptance criteria, compute coverage, and seed test ideas — before any automation exists.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). When the user invokes one of these slash commands, run the corresponding helper with `Bash` and report the output. The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Finding the helpers

The helpers live at `scripts/<name>.py` relative to this plugin's root (the directory containing this SKILL.md is `<plugin-root>/skills/tc-requirements/`). In a development checkout that is `<repo>/plugins/test-commander/scripts/`. In the installed plugin cache it is `~/.claude/plugins/cache/test-commander-marketplace/test-commander/<version>/scripts/`. Either way, resolve the helper path relative to this SKILL.md's own location.

## Commands

### `/tc:review-requirements`

Review uploaded requirements documents against the Phase 2 rubric (16 dimensions: clarity, testability, completeness, consistency, atomicity, measurability, ac-quality, edge-cases, negative-cases, data-rules, roles-permissions, NFRs, dependencies, ambiguity, risk, automation-suitability). Writes three artifacts under `<workspace>/requirements/`: `requirements-review.md` (full report), `requirements-inventory.md` (parsed REQ-ID list in document order), and `open-questions.md` (auto-generated questions, deduplicated). Idempotent — re-runs against unchanged input produce byte-identical review and inventory; the open-questions file is line-stable.

**Run:**

```sh
python3 <plugin-root>/scripts/review_requirements.py <project-root>
```

`<project-root>` defaults to the current working directory. Per D19 the helper ships universal-core keyword sets; consuming projects extend via `<workspace>/config.yaml` under `tc-requirements:` (see [customizing for your project](../../../../docs/user-guide/customizing-for-your-project.md)).

Full spec: [commands/review-requirements.md](commands/review-requirements.md). Rubric and per-dimension checks: [methodology/requirements-quality-review.md](methodology/requirements-quality-review.md).

### `/tc:review-user-stories`

Review user stories against the INVEST rubric (Independent, Negotiable, Valuable, Estimable, Small, Testable), the role-action-benefit shape (`As a ... I want ... So that ...`), and the acceptance-criteria-pointer check. Writes `<workspace>/requirements/user-story-review.md` with findings, a per-story detail block, and a readiness verdict (`ready` / `needs-refinement` / `blocked`) per story. Idempotent — re-runs against unchanged input produce byte-identical output.

**Run:**

```sh
python3 <plugin-root>/scripts/review_user_stories.py <project-root>
```

`<project-root>` defaults to the current working directory. The INVEST checks are universal English / agile vocabulary; no domain extension is required (consuming projects pick their own `@area:`/`@persona:` tag values per D19, but the INVEST mechanics themselves are domain-agnostic).

Full spec: [commands/review-user-stories.md](commands/review-user-stories.md). Rubric and per-dimension checks: [methodology/user-story-readiness.md](methodology/user-story-readiness.md).

### `/tc:review-acceptance-criteria`

Review acceptance criteria against the Phase 2 AC rubric (five mechanical checks: `ac-missing-edge-cases`, `ac-missing-negative-cases`, `ac-untestable-predicate`, `ac-ambiguous-data-rule`, `ac-missing-role-context`) plus an `orphan` check that flags any AC whose parent user story is not in scope. Parses `AC-NNN[-NN]: Given ... When ... Then ...` entries; derives the parent story from the AC ID prefix (`AC-001-01` → `US-001`); strips parenthetical asides before applying checks so meta-commentary doesn't mask defects. Writes `<workspace>/requirements/acceptance-criteria-review.md` (overwritten byte-deterministically). Idempotent.

**Run:**

```sh
python3 <plugin-root>/scripts/review_acceptance_criteria.py <project-root>
```

`<project-root>` defaults to the current working directory. The `ac-missing-role-context` check honors `<workspace>/config.yaml` extensions under `tc-requirements.roles-permissions:` for domain-specific verbs and roles (per D19).

Full spec: [commands/review-acceptance-criteria.md](commands/review-acceptance-criteria.md). Rubric and per-dimension checks: [methodology/acceptance-criteria-quality.md](methodology/acceptance-criteria-quality.md).

### `/tc:requirements-coverage`

Cross-reference requirement IDs with downstream artifacts (test ideas under `test-ideas/`, BDD features under `bdd/features/`, the automation map under `traceability/automation-map.md`) and write a coverage matrix to `<workspace>/requirements/requirements-coverage.md` plus a parallel traceability map at `<workspace>/traceability/requirements-map.md`. Requires the inventory artifact from `/tc:review-requirements` (Step 2.2); refuses with `InventoryMissingError` if the inventory is still the unmodified template stub. Idempotent — re-runs against unchanged input produce byte-identical output.

**Run:**

```sh
python3 <plugin-root>/scripts/requirements_coverage.py <project-root>
```

`<project-root>` defaults to the current working directory. Coverage is read-only with respect to downstream artifacts; this command never modifies test ideas, features, or automation files.

Full spec: [commands/requirements-coverage.md](commands/requirements-coverage.md). Output structure: [templates/requirements-coverage-template.md](templates/requirements-coverage-template.md).

### `/tc:requirements-to-tests`

For every reviewed requirement, generate a seed test-idea file under `<workspace>/test-ideas/<REQ-ID>.md` containing a Phase-4-compatible YAML frontmatter schema (`tc-test-idea/v1`), a verbatim copy of the requirement body, candidate scenario titles (happy / edge / negative), and the Phase 2 review findings that flagged this requirement. Refreshes `<workspace>/traceability/requirements-map.md` so each REQ row links to its new seed. Requires `requirements-review.md` from `/tc:review-requirements` (Step 2.2); refuses with `ReviewMissingError` if the review is still the unmodified template stub. Optional input: when `acceptance-criteria-review.md` is present (Step 2.4), each seed flips `ac_review_present: true` and includes a pointer to the AC review.

**Idempotency contract.** Existing `test-ideas/<REQ-ID>.md` files are **never** overwritten — Phase 4 (`tc-explore`) will enrich them with charters and refined ideas, and those enrichments survive re-runs. The traceability map is regenerated byte-deterministically on every run via the embedded `requirements_coverage.coverage()` refresh.

**Run:**

```sh
python3 <plugin-root>/scripts/requirements_to_tests.py <project-root>
```

`<project-root>` defaults to the current working directory. The seed schema is the Phase 4 contract; downstream skills read `tc-test-idea/v1` files without modifying their stable keys.

Full spec + the schema contract: [commands/requirements-to-tests.md](commands/requirements-to-tests.md).

## What to do when a slash command fires

All five Phase 2 commands are shipped (`/tc:review-requirements`, `/tc:review-user-stories`, `/tc:review-acceptance-criteria`, `/tc:requirements-coverage`, `/tc:requirements-to-tests`). For each invocation: resolve `<plugin-root>` relative to this SKILL.md, determine `<project-root>` (the user's current working directory unless specified otherwise), run the bundled helper via `Bash`, and report the helper's CLI output. Then add the narrative judgment layer described in the relevant methodology doc (where one exists) — explain *why* each finding matters in product context, rank severity, and identify gaps the keyword check could miss. Per-command judgment-layer focus:

- `/tc:review-requirements` — narrate the 16-dimension rubric findings, prioritize severity, surface AI-judgment dimensions the keyword check could not cover.
- `/tc:review-user-stories` — narrate INVEST findings, propose ready/needs-refinement/blocked progressions, translate subjective predicates into measurable proxies.
- `/tc:review-acceptance-criteria` — propose concrete edge cases, failure modes, role qualifiers, and measurable thresholds; flag orphan ACs for product-owner resolution.
- `/tc:requirements-coverage` — uncovered-requirement prioritization (risk-aware) and orphan resolution.
- `/tc:requirements-to-tests` — call out newly-created seeds, explain how the seed's `phase_2_findings` should shape downstream scenario authoring, note Phase 4 enrichment is expected.

If a helper exits non-zero, surface its stderr and the relevant per-command page.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-core skill](../tc-core/SKILL.md)
