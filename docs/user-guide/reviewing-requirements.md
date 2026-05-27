# Workflow — Reviewing Requirements (Phase 2)

This guide walks you through Test Commander's five Phase 2 commands end to end against a consuming project. The examples use the deliberately-generic seeded fixture from `tests/fixtures/seeded-flawed-requirements/` so every output is reproducible.

## What's available in Phase 2

| Command | Purpose | Writes |
| --- | --- | --- |
| `/tc:review-requirements` | Apply the 16-dimension requirements rubric (clarity, testability, completeness, consistency, atomicity, measurability, ac-quality, edge-cases, negative-cases, data-rules, roles-permissions, nfrs, dependencies, ambiguity, risk, automation-suitability). Detects broken cross-references and mutually-exclusive constraints. | `requirements/requirements-review.md`, `requirements/requirements-inventory.md`, `requirements/open-questions.md` |
| `/tc:review-user-stories` | Apply INVEST + role-action-benefit shape + acceptance-criteria-pointer checks. Assigns a `ready` / `needs-refinement` / `blocked` verdict per story. | `requirements/user-story-review.md` |
| `/tc:review-acceptance-criteria` | Apply the 5-dimension AC rubric (missing edge-cases, missing negative-cases, untestable predicates, ambiguous data rules, missing role context) plus orphan detection. | `requirements/acceptance-criteria-review.md` |
| `/tc:requirements-coverage` | Cross-reference inventory IDs with downstream artifacts (test ideas, BDD features, automation map). Surface uncovered requirements and orphans. | `requirements/requirements-coverage.md`, `traceability/requirements-map.md` |
| `/tc:requirements-to-tests` | Generate a Phase-4-compatible seed test-idea file per requirement (`tc-test-idea/v1` schema). | `test-ideas/<REQ-ID>.md` (one per requirement) and refresh of `traceability/requirements-map.md` |

All five are read-or-write-bounded, **idempotent**, and safe to run repeatedly. The first four overwrite their generated reports byte-deterministically; `/tc:requirements-to-tests` **never overwrites existing test-idea seeds** (Phase 4 enrichments survive).

Mechanical checks use **universal English and software-engineering vocabulary only** per [Decision D19](../../planning/plan.md). For domain-specific keywords (PCI, HIPAA, your role taxonomy, your risk classes), extend via `<workspace>/config.yaml` per [customizing-for-your-project.md](customizing-for-your-project.md).

## Prerequisites

- Test Commander installed (`./bootstrap.sh` then `make install` — see [getting-started.md](getting-started.md)).
- A consuming project with a `.test-commander/` workspace from `/tc:init` (Phase 1 — see [workflow.md](workflow.md)).
- Optional: `config.yaml` extended with your domain vocabulary.

## Step 0 — Upload requirements documents

Drop your requirements, user stories, and acceptance criteria into `.test-commander/documents/uploaded/`. Test Commander's helpers parse any `*.md` file containing `REQ-\d+`, `US-\d+`, or `AC-\d+` markers. Other files (README placeholders, design notes) are ignored.

The conventions the helpers expect:

```markdown
REQ-001: The system shall <behavior>. <body, including multi-line>

US-001: As a <role>, I want <action>, So that <benefit>.

## US-001: <short title>

AC-001-01: Given <precondition>, When <action>, Then <outcome>.
```

The `AC-NNN-NN` prefix maps the AC to its parent story `US-NNN`. AC IDs without a sub-segment (`AC-NNN`) are accepted but rare.

To follow this walkthrough verbatim, copy the seeded fixture:

```sh
cp /path/to/test-commander/tests/fixtures/seeded-flawed-requirements/*.md \
   .test-commander/documents/uploaded/
```

Three files land: `requirements.md` (17 REQ entries), `user-stories.md` (6 US entries), `acceptance-criteria.md` (5 AC entries).

## Step 1 — Review requirements

```sh
python3 /path/to/test-commander/plugins/test-commander/scripts/review_requirements.py .
```

Or `/tc:review-requirements` through Claude Code. Sample output against the seeded fixture:

```
workspace:        <project>/.test-commander
requirements:     17
findings:         63
open questions:   4
review:           <project>/.test-commander/requirements/requirements-review.md
inventory:        <project>/.test-commander/requirements/requirements-inventory.md
open-questions:   <project>/.test-commander/requirements/open-questions.md
```

The helper writes three artifacts. The **review** carries an executive summary, a per-dimension findings count, a flat findings table (REQ-ID × dimension × verbatim trigger), per-requirement detail blocks, and a traceability footer. The **inventory** is the canonical REQ-ID list in document order (Phase 2.5 and 2.6 read it). The **open-questions** file collects detected broken references and mutual-exclusion pairs, deduplicated by `(question-text, requirement-id)`.

Each REQ that triggered a rubric dimension is named in the review; the seeded fixture flags every one of the 16 dimensions at least once. Re-run is byte-identical for the review and inventory; `open-questions.md` is append-only and never gains duplicates on re-run.

## Step 2 — Review user stories

```sh
python3 .../scripts/review_user_stories.py .
```

Or `/tc:review-user-stories`. Sample output:

```
workspace:        <project>/.test-commander
stories:          6
findings:         13
review:           <project>/.test-commander/requirements/user-story-review.md
```

Every seeded story flags `needs-acceptance-criteria` because none of them cite an AC pointer. Plus one finding per INVEST letter, one per shape violation. The review's verdict column gives you `ready` / `needs-refinement` / `blocked` per story so you can prioritize.

For details on each INVEST dimension, see [`methodology/user-story-readiness.md`](../../plugins/test-commander/skills/tc-requirements/methodology/user-story-readiness.md).

## Step 3 — Review acceptance criteria

```sh
python3 .../scripts/review_acceptance_criteria.py .
```

Or `/tc:review-acceptance-criteria`. Sample output:

```
workspace:        <project>/.test-commander
ACs:              5
parent stories:   6
findings:         13
review:           <project>/.test-commander/requirements/acceptance-criteria-review.md
```

The helper derives each AC's parent story from the AC ID prefix (`AC-001-01` → `US-001`), groups findings by parent story, and surfaces any AC whose parent is not in scope as an `orphan` finding. AC bodies have parenthetical asides stripped before checks run, so meta-commentary like `(Happy path only — no edge cases.)` does not falsely satisfy the edge-cases keyword check; the original body is preserved for display.

For details on each AC dimension, see [`methodology/acceptance-criteria-quality.md`](../../plugins/test-commander/skills/tc-requirements/methodology/acceptance-criteria-quality.md).

## Step 4 — Coverage

```sh
python3 .../scripts/requirements_coverage.py .
```

Or `/tc:requirements-coverage`. The helper requires the inventory artifact from Step 1; without it, exit code 2.

Sample output:

```
workspace:        <project>/.test-commander
requirements:     17
covered:          0
not yet covered:  17
orphans:          0
coverage:         <project>/.test-commander/requirements/requirements-coverage.md
traceability:     <project>/.test-commander/traceability/requirements-map.md
```

At this point every requirement is reported `not yet covered` — no downstream artifacts exist yet. That's expected; Step 5 lands seed test ideas and re-running coverage after that will show every requirement linked to its seed.

The coverage file carries the full report (executive summary, coverage matrix, not-yet-covered list, orphan list, traceability footer). The traceability map at `traceability/requirements-map.md` is the leaner per-REQ link table that downstream skills (Phase 3, 4, 5, 6, 7) consume.

## Step 5 — Seed test ideas

```sh
python3 .../scripts/requirements_to_tests.py .
```

Or `/tc:requirements-to-tests`. The helper requires `requirements-review.md` from Step 1; refuses if absent or still the template stub.

Sample output after a fresh run:

```
workspace:        <project>/.test-commander
requirements:     17
created:          17
skipped (exists): 0
ac_review:        present
traceability:     <project>/.test-commander/traceability/requirements-map.md
```

One seed file lands per requirement at `test-ideas/<REQ-ID>.md`. Each begins with a Phase-4-compatible YAML frontmatter (`tc-test-idea/v1`) carrying the requirement ID, title, source, Phase 2 findings for that requirement, three anchor candidate scenarios (happy / edge / negative), and an `ac_review_present` flag set to `true` when Step 3 has been run.

The full schema and what Phase 4 may modify vs preserve is documented in [`commands/requirements-to-tests.md`](../../plugins/test-commander/skills/tc-requirements/commands/requirements-to-tests.md).

**Strict idempotency:** existing seed files are **never** overwritten. Phase 4 (`tc-explore`) enriches these files with charters and refined ideas; those enrichments survive re-runs. The second invocation prints `created: 0, skipped: 17`.

After Step 5 the helper refreshes the traceability map (re-uses Step 4's scanner) so every REQ now links to its `test-ideas/<REQ-ID>.md`.

## What changed on disk

After the full walkthrough:

```
.test-commander/
├── documents/
│   └── uploaded/
│       ├── requirements.md            # your input
│       ├── user-stories.md            # your input
│       └── acceptance-criteria.md     # your input
├── requirements/
│   ├── requirements-review.md         # Step 1 (generated)
│   ├── requirements-inventory.md      # Step 1 (generated)
│   ├── open-questions.md              # Step 1 (append-only)
│   ├── user-story-review.md           # Step 2 (generated)
│   ├── acceptance-criteria-review.md  # Step 3 (generated)
│   └── requirements-coverage.md       # Step 4 (generated)
├── traceability/
│   └── requirements-map.md            # Step 4, refreshed by Step 5
└── test-ideas/
    ├── REQ-001.md                     # Step 5 (seed; never overwritten)
    ├── REQ-002.md
    └── …  one per requirement
```

Every generated report (the four `*review*` files, the coverage matrix, the traceability map) is **byte-deterministic** — re-running against unchanged input produces identical bytes. The test-idea seeds are **created-once**: Phase 4 will enrich them and your enrichments survive.

`open-questions.md` is the only file where re-running adds content — but only when a new question is detected. Duplicates by `(question-text, requirement-id)` are suppressed.

Commit everything in `.test-commander/` to git per [Decision D5](../../planning/plan.md).

## Re-running after edits

The five commands are designed to be re-run iteratively as you refine your requirements:

1. Edit a requirement in `documents/uploaded/*.md`.
2. Re-run `/tc:review-requirements` → review and inventory update.
3. Re-run `/tc:requirements-coverage` → coverage and traceability map refresh.
4. `/tc:requirements-to-tests` is safe to re-run — existing seeds are preserved; new requirements get new seeds.

The Phase 1 helper `/tc:next` reads the workspace state and recommends the next step after Phase 2 (typically a Phase 3 `/tc:learn-from-*` command).

## Customizing for your project domain

Test Commander ships with **universal English and software-engineering vocabulary only**. Your project supplies its own domain vocabulary through `<workspace>/config.yaml` extensions to the `tc-requirements` schema. Three rubric dimensions accept extensions:

- `data-rules` — sensitive-data keywords (PCI: `PAN`, `primary account number`; HIPAA: `PHI`; etc.).
- `risk` — compliance-keyword extensions per regulatory regime.
- `roles-permissions` — domain-specific permission verbs and role qualifiers.

See [customizing-for-your-project.md](customizing-for-your-project.md) for the full extension model with worked examples (e-commerce, healthcare, research data platform).

INVEST checks, AC rubric checks, ambiguity adjectives, and security anti-patterns use universal vocabulary and accept no extensions — they apply identically to every product domain.

## Beyond Phase 2

After Phase 2 ships, `/tc:next` typically recommends a Phase 3 command (`/tc:learn-from-docs`, `/tc:learn-from-code`, etc.) to ingest project knowledge. Phase 3 enriches the requirements review by feeding domain knowledge into downstream skills. See [the phased plan](../../planning/plan.md) for the full roadmap.

## See also

- [Workspace reference](../workspace-reference.md) — per-directory purpose, including `requirements/` and `test-ideas/`.
- [Command reference](../command-reference.md) — index of every command, by phase.
- [Customizing for your project](customizing-for-your-project.md) — config.yaml extension model.
- [tc-requirements SKILL.md](../../plugins/test-commander/skills/tc-requirements/SKILL.md) — Claude's entry point.
- Methodology: [requirements-quality-review.md](../../plugins/test-commander/skills/tc-requirements/methodology/requirements-quality-review.md) · [user-story-readiness.md](../../plugins/test-commander/skills/tc-requirements/methodology/user-story-readiness.md) · [acceptance-criteria-quality.md](../../plugins/test-commander/skills/tc-requirements/methodology/acceptance-criteria-quality.md)
- Per-command pages: [review-requirements](../../plugins/test-commander/skills/tc-requirements/commands/review-requirements.md) · [review-user-stories](../../plugins/test-commander/skills/tc-requirements/commands/review-user-stories.md) · [review-acceptance-criteria](../../plugins/test-commander/skills/tc-requirements/commands/review-acceptance-criteria.md) · [requirements-coverage](../../plugins/test-commander/skills/tc-requirements/commands/requirements-coverage.md) · [requirements-to-tests](../../plugins/test-commander/skills/tc-requirements/commands/requirements-to-tests.md)
