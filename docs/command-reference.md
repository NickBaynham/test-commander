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

## Planned commands (not yet implemented)

These will gain per-command pages as their phases ship.

| Command | Skill | Phase |
| --- | --- | --- |
| `/tc:review-requirements` | `tc-requirements` | 2 |
| `/tc:review-user-stories` | `tc-requirements` | 2 |
| `/tc:review-acceptance-criteria` | `tc-requirements` | 2 |
| `/tc:requirements-coverage` | `tc-requirements` | 2 |
| `/tc:requirements-to-tests` | `tc-requirements` | 2 |
| `/tc:learn-from-docs` | `tc-knowledge` | 3 |
| `/tc:learn-from-specs` | `tc-knowledge` | 3 |
| `/tc:learn-from-code` | `tc-knowledge` | 3 |
| `/tc:learn-from-api` | `tc-knowledge` | 3 |
| `/tc:learn-from-tests` | `tc-knowledge` | 3 |
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
