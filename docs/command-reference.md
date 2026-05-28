# Command Reference

This file is the index. Per-command pages — inputs, outputs, preconditions, behavior, safety, definition of done — live next to their skill at `plugins/test-commander/skills/<skill>/commands/<command>.md`. Per the Phase 1 design decision, the per-command page is the single source of truth that Claude reads at runtime and that users read for reference.

## Phase 1 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:init` | `tc-core` | [init.md](../plugins/test-commander/skills/tc-core/commands/init.md) |
| `/tc:status` | `tc-core` | [status.md](../plugins/test-commander/skills/tc-core/commands/status.md) |
| `/tc:journal` | `tc-core` | [journal.md](../plugins/test-commander/skills/tc-core/commands/journal.md) |
| `/tc:next` | `tc-core` | [next.md](../plugins/test-commander/skills/tc-core/commands/next.md) |

For the methodology behind `/tc:next`'s recommendations, see [next-step-inference.md](../plugins/test-commander/skills/tc-core/methodology/next-step-inference.md).

## Phase 2 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:review-requirements` | `tc-requirements` | [review-requirements.md](../plugins/test-commander/skills/tc-requirements/commands/review-requirements.md) |
| `/tc:review-user-stories` | `tc-requirements` | [review-user-stories.md](../plugins/test-commander/skills/tc-requirements/commands/review-user-stories.md) |
| `/tc:review-acceptance-criteria` | `tc-requirements` | [review-acceptance-criteria.md](../plugins/test-commander/skills/tc-requirements/commands/review-acceptance-criteria.md) |
| `/tc:requirements-coverage` | `tc-requirements` | [requirements-coverage.md](../plugins/test-commander/skills/tc-requirements/commands/requirements-coverage.md) |
| `/tc:requirements-to-tests` | `tc-requirements` | [requirements-to-tests.md](../plugins/test-commander/skills/tc-requirements/commands/requirements-to-tests.md) |

For the rubric methodology, see [requirements-quality-review.md](../plugins/test-commander/skills/tc-requirements/methodology/requirements-quality-review.md), [user-story-readiness.md](../plugins/test-commander/skills/tc-requirements/methodology/user-story-readiness.md), and [acceptance-criteria-quality.md](../plugins/test-commander/skills/tc-requirements/methodology/acceptance-criteria-quality.md). End-to-end walkthrough: [user-guide/reviewing-requirements.md](user-guide/reviewing-requirements.md).

## Phase 3 commands (shipped)

| Command | Skill | Per-command page |
| --- | --- | --- |
| `/tc:learn-from-docs` | `tc-knowledge` | [learn-from-docs.md](../plugins/test-commander/skills/tc-knowledge/commands/learn-from-docs.md) |
| `/tc:learn-from-specs` | `tc-knowledge` | [learn-from-specs.md](../plugins/test-commander/skills/tc-knowledge/commands/learn-from-specs.md) |
| `/tc:learn-from-code` | `tc-knowledge` | [learn-from-code.md](../plugins/test-commander/skills/tc-knowledge/commands/learn-from-code.md) |
| `/tc:learn-from-api` | `tc-knowledge` | [learn-from-api.md](../plugins/test-commander/skills/tc-knowledge/commands/learn-from-api.md) |
| `/tc:learn-from-tests` | `tc-knowledge` | [learn-from-tests.md](../plugins/test-commander/skills/tc-knowledge/commands/learn-from-tests.md) |

All five commands write per-source models under `<workspace>/product-knowledge/`, contribute scoped `## From <source>` sections to the cross-cutting artifacts (`entities.md`, `user-journeys.md`, `business-rules.md`, `assumptions.md`), and call the shared `synthesize_system_model.py` to regenerate `system-model.md`. Gap signals route to `<workspace>/requirements/open-questions.md` with a `[<kind>]` prefix.

For the methodology behind each helper, see [project-knowledge.md](../plugins/test-commander/skills/tc-knowledge/methodology/project-knowledge.md) (umbrella) plus [learning-from-documents.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-documents.md), [learning-from-specs.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-specs.md), [learning-from-code.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-code.md), [learning-from-api.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-api.md), and [learning-from-tests.md](../plugins/test-commander/skills/tc-knowledge/methodology/learning-from-tests.md). End-to-end walkthrough: [user-guide/building-project-knowledge.md](user-guide/building-project-knowledge.md).

## Planned commands (not yet implemented)

These will gain per-command pages as their phases ship.

| Command | Skill | Phase |
| --- | --- | --- |
| `/tc:create-charter` | `tc-explore` | 4 |
| `/tc:explore` | `tc-explore` | 4 |
| `/tc:test-ideas` | `tc-explore` | 4 |
| `/tc:session-summary` | `tc-explore` | 4 |
| `/tc:generate-bdd` | `tc-bdd` | 5 |
| `/tc:review-bdd` | `tc-bdd` | 5 |
| `/tc:traceability-map` | `tc-traceability` | 5 |
| `/tc:build-framework` | `tc-build-framework` | 6 |
| `/tc:automation-plan` | `tc-automation-plan` | 6 |
| `/tc:automate` | `tc-automate` | 6 |
| `/tc:review-automation` | `tc-automate` | 6 |
| `/tc:generate-test-data` | `tc-test-data` | 6 |
| `/tc:run` | `tc-run` | 7 |
| `/tc:analyze-results` | `tc-run` | 7 |
| `/tc:report` | `tc-quality-report` | 7 |
| `/tc:quality-gate` | `tc-quality-report` | 7 |
| `/tc:learn` | `tc-learning` | 8 |
| `/tc:learn-from-failures` | `tc-learning` | 8 |
| `/tc:learn-from-exploration` | `tc-learning` | 8 |
| `/tc:learn-from-feedback` | `tc-learning` | 8 |
| `/tc:review-lessons` | `tc-learning` | 8 |
| `/tc:promote-lessons` | `tc-learning` | 8 |
| `/tc:visualize`, `/tc:diagram-*` | `tc-visualize` | 9 |
| `/tc:generate-infographic` | `tc-visualize` | 9 |
| `/tc:render-visuals` | `tc-visualize` | 9 |
| `/tc:web-*` | `tc-web` | 10 |
| `/tc:sandbox-*` | `tc-sandbox` | 12 |
| `/tc:watch-changes`, continuous-quality | `tc-continuous-quality` | 13 |
