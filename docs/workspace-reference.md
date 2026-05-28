# Workspace Reference

Each consuming project gets a `.test-commander/` workspace at its repo root. The workspace holds every quality artifact Test Commander produces — requirements reviews, exploration notes, BDD specs, automation plans, evidence, learning, quality reports, traceability, visuals, sessions, journal, and runs.

The workspace is created by [`/tc:init`](../plugins/test-commander/skills/tc-core/commands/init.md). Re-running `/tc:init` is safe — existing files are preserved; only missing files are copied from the bundled template.

> The plan's canonical layout is in [../planning/plan.md](../planning/plan.md) under "Workspace Layout". This page reflects that layout with per-directory purpose and owning-phase notes. Drift between this page and the bundled template at `plugins/test-commander/templates/workspace/` is caught by `tests/test_workspace_template.py`.

## Layout

```
.test-commander/
  project.md                  # Phase 1 — project identity
  config.yaml                 # Phase 1 — feature flags, defaults
  methodology.md              # Phase 1 — methodology choices
  documents/
    uploaded/                 # Phase 3 — raw uploaded docs
    index.md                  # Phase 3 — index of uploads
  requirements/               # Phase 2 — requirements review artifacts (populated)
    requirements-inventory.md   # /tc:review-requirements
    requirements-review.md      # /tc:review-requirements
    user-story-review.md        # /tc:review-user-stories
    acceptance-criteria-review.md  # /tc:review-acceptance-criteria
    open-questions.md           # /tc:review-requirements (append-only, dedup)
    requirements-coverage.md    # /tc:requirements-coverage
  product-knowledge/          # Phase 3 — extracted project knowledge
    system-model.md
    business-rules.md
    user-journeys.md
    entities.md
    assumptions.md
    code-derived-model.md
    spec-derived-model.md
    documentation-model.md
    api-model.md
    tests-coverage.md
  charters/                   # Phase 4 — exploration charters
  exploration-notes/          # Phase 4 — session notes
  test-ideas/                 # Phase 4 (owner); Phase 2 seeds via /tc:requirements-to-tests
  bdd/                        # Phase 5 — BDD artifacts
    features/                 #   .feature files
    summaries/                #   per-feature Markdown summaries
  automation-plan/            # Phase 6 — per-feature automation plans
  test-data/                  # Phase 6 — declarative test data
    seed/                     #   baseline fixtures
    scenarios/                #   per-suite scenarios
    factories/                #   regenerable factories
  risk-register/              # Phase 2+ — known and suspected risks
    risk-register.md
  quality-report/             # Phase 7 — live release-readiness report
    current-quality-report.md
    history/                  #   committed snapshots
  traceability/               # Phase 5 — requirement -> test links
    requirements-map.md
    test-map.md
    automation-map.md
  evidence/                   # Phase 7 — test-run artifacts
    screenshots/              #   committed
    videos/                   #   git-ignored (opt-in lfs)
    traces/                   #   git-ignored (opt-in lfs)
    logs/                     #   committed
  learning/                   # Phase 8 — governed learning loop
    lessons-inbox.md
    accepted-lessons.md
    rejected-lessons.md
    needs-human-review.md
  visuals/                    # Phase 9 — diagrams and infographics
    mermaid/
    svg/
    png/
    infographic/
  sessions/                   # Phase 4 — per-session records
  journal/                    # Phase 1 — append-only narrative journal
  runs/                       # Phase 7 — per-run records
  policy/                     # Phase 10.5 — governance policy
    permissions.yaml
    approvals.yaml
  audit/                      # Phase 10.5 — append-only audit log
    actions.jsonl
    approvals/
```

## Per-directory purpose

### Workspace root

| File | Owning phase | Purpose |
| --- | --- | --- |
| `project.md` | 1 | Project identity, initialization timestamp, Test Commander version, project-level overrides. |
| `config.yaml` | 1 | Project-level configuration: defaults, feature flags, policy overrides, and **domain-specific extensions** to the rubric keyword sets shipped by Test Commander (PCI/HIPAA vocabulary, role taxonomies, risk taxonomies). See [customizing for your project](user-guide/customizing-for-your-project.md). |
| `methodology.md` | 1 | Per-project methodology selections: exploration style, BDD conventions, automation suitability rules. |

### `documents/` — Phase 3

Source documents uploaded by the user (specs, PRDs, design notes). `uploaded/` holds raw uploads; `index.md` is the searchable index built by `/tc:learn-from-docs`.

### `requirements/` — Phase 2 (shipped)

Outputs of the five Phase 2 commands:

| File | Written by | Mode |
| --- | --- | --- |
| `requirements-inventory.md` | `/tc:review-requirements` | Overwrite |
| `requirements-review.md` | `/tc:review-requirements` | Overwrite |
| `open-questions.md` | `/tc:review-requirements` | Append (deduplicated by `(question-text, requirement-id)`) |
| `user-story-review.md` | `/tc:review-user-stories` | Overwrite |
| `acceptance-criteria-review.md` | `/tc:review-acceptance-criteria` | Overwrite |
| `requirements-coverage.md` | `/tc:requirements-coverage` | Overwrite |

All overwrite-mode files are byte-deterministic — re-running against unchanged input produces identical bytes. `open-questions.md` gains new questions only when new broken references or new mutual-exclusion pairs are detected.

End-to-end walkthrough: [user-guide/reviewing-requirements.md](user-guide/reviewing-requirements.md). For the rubric methodology see [requirements-quality-review.md](../plugins/test-commander/skills/tc-requirements/methodology/requirements-quality-review.md), [user-story-readiness.md](../plugins/test-commander/skills/tc-requirements/methodology/user-story-readiness.md), and [acceptance-criteria-quality.md](../plugins/test-commander/skills/tc-requirements/methodology/acceptance-criteria-quality.md).

### `product-knowledge/` — Phase 3 (shipped)

Structured knowledge extracted from project artifacts. Five **per-source models** capture findings from one source each; four **cross-cutting artifacts** are populated cumulatively (each `/tc:learn-from-*` command writes its own `## From <source>` section, preserving every other source's section across re-runs); **`system-model.md`** is the synthesized top-level overview, regenerated by `synthesize_system_model.py` at the end of every helper run.

Per-source models:

| File | Written by | Mode |
| --- | --- | --- |
| `documentation-model.md` | `/tc:learn-from-docs` | Overwrite |
| `spec-derived-model.md` | `/tc:learn-from-specs` | Overwrite |
| `code-derived-model.md` | `/tc:learn-from-code` | Overwrite |
| `api-model.md` | `/tc:learn-from-api` | Overwrite |
| `tests-coverage.md` | `/tc:learn-from-tests` | Overwrite |

Cross-cutting artifacts (section-overwrite per source; stable section order `documents` → `specs` → `code` → `api` → `tests`):

| File | Contributing commands | Mode |
| --- | --- | --- |
| `entities.md` | all five `/tc:learn-from-*` | Section-overwrite |
| `user-journeys.md` | `/tc:learn-from-docs` only | Section-overwrite |
| `business-rules.md` | `/tc:learn-from-docs`, `/tc:learn-from-specs`, `/tc:learn-from-api` | Section-overwrite |
| `assumptions.md` | `/tc:learn-from-docs` only | Section-overwrite |

Synthesized overview:

| File | Written by | Mode |
| --- | --- | --- |
| `system-model.md` | `synthesize_system_model.py` (called by every `/tc:learn-from-*` helper) | Overwrite |

Gap signals from every helper route to `<workspace>/requirements/open-questions.md` (deduplicated by `(source-id, question-text)`, with a `[<kind>]` prefix on tc-knowledge entries — `[undocumented-function]`, `[language-unsupported-in-v1]`, `[unimplemented-endpoint]`, `[unspecified-endpoint]`, `[mismatched-status]`, `[unsupported-test-runner]`, `[untested-function]`).

Phase 3 does **not** write to `<workspace>/traceability/`. Cross-source traceability is Phase 5's responsibility; Phase 3 supplies the inputs.

End-to-end walkthrough: [user-guide/building-project-knowledge.md](user-guide/building-project-knowledge.md). For per-command methodology see [project-knowledge.md](../plugins/test-commander/skills/tc-knowledge/methodology/project-knowledge.md) (umbrella), [learning-from-documents.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-documents.md), [learning-from-specs.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-specs.md), [learning-from-code.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-code.md), [learning-from-api.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-api.md), and [learning-from-tests.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-tests.md).

### `charters/`, `exploration-notes/`, `test-ideas/`, `sessions/` — Phase 4 (owner)

Charters scope each exploratory session. Notes capture observations, surprises, bugs, ideas. Test-idea files hold specific, falsifiable claims that could be tested. Session records persist per-session metadata.

**`test-ideas/` is seeded by Phase 2.** `/tc:requirements-to-tests` writes one `test-ideas/<REQ-ID>.md` per reviewed requirement with the Phase-4-compatible `tc-test-idea/v1` schema (one happy + one edge + one negative anchor scenario per REQ). Phase 4 enriches these seeds with charters, exploration sessions, and refined ideas; **Phase 2 never overwrites existing seeds** so Phase 4 enrichments survive re-runs. The `tc-test-idea/v1` schema contract is documented in [`commands/requirements-to-tests.md`](../plugins/test-commander/skills/tc-requirements/commands/requirements-to-tests.md).

### `bdd/` — Phase 5

`features/` contains the Gherkin `.feature` files; `summaries/` contains per-feature Markdown summaries with traceability links. Generated and reviewed by Test Commander; readable by product owners.

### `automation-plan/` — Phase 6

Per-feature automation plans: what to automate, why, expected coverage, suitability score.

### `test-data/` — Phase 6

Test data lives here, never in test code. `seed/` holds baseline fixtures; `scenarios/` holds per-suite test data; `factories/` holds regenerable factory definitions. Regenerate via `/tc:generate-test-data`.

### `risk-register/` — Phase 2 onward

Known and suspected risks, with the artifact that surfaced each one and the mitigation plan. Populated across Phase 2 (requirements) and Phase 4 (exploration); referenced by the quality report.

### `quality-report/` — Phase 7

`current-quality-report.md` is the single-page release-readiness summary. `/tc:report` rewrites it in full and snapshots a copy to `history/YYYY-MM-DD-HHmm.md`. Per Decision D5 (committed history) and Open Question Q10 (retention policy), snapshots stay in git for now.

### `traceability/` — Phase 5

Three maps maintained by `/tc:traceability-map`: requirement → test idea → BDD scenario, then test idea → BDD scenario → automated test, then automated test → result → quality report.

### `evidence/` — Phase 7

Artifacts from `/tc:run`. Screenshots and logs committed by default. Videos and traces are git-ignored unless `git-lfs` is opted in (per Decision D5 / Open Question Q5).

### `learning/` — Phase 8

Governed learning loop: `lessons-inbox.md` receives candidate lessons; `/tc:review-lessons` classifies them; `/tc:promote-lessons` moves accepted lessons into project guidance. Test Commander never silently rewrites methodology — every promotion is visible in `git diff`.

### `visuals/` — Phase 9

Mermaid source plus rendered SVG/PNG. `infographic/` holds higher-design-effort visuals for the quality report.

### `journal/` — Phase 1

Append-only narrative journal. `/tc:journal append "..."` writes one H2 timestamp section per call to a day file (`YYYY-MM-DD.md`). `/tc:journal summarize` prints entries chronologically within an inclusive `--from`/`--to` range.

### `runs/` — Phase 7

Per-run records from `/tc:run`: JSON/HTML reports, evidence references, failure triage.

### `policy/` and `audit/` — Phase 10.5

Controlled-execution governance. `policy/permissions.yaml` maps roles to permission levels. `policy/approvals.yaml` says which actions require approval. `audit/actions.jsonl` is the append-only canonical action log; `audit/approvals/` holds individual approval records.

## What gets committed

Decision D5: the workspace is committed to git. Quality-report history snapshots commit. Test runs in `runs/` commit. The exceptions are listed under `evidence/` above (videos and traces git-ignored by default; opt-in lfs).

## What lives outside the workspace

Test code lives at `tests/` in the consuming project, not under `.test-commander/`. Test data flows from `.test-commander/test-data/` into `tests/` via fixtures (Decision D6) — never inline data in test files.
