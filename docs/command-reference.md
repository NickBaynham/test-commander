# Command Reference

Every `/tc:*` command Test Commander exposes is summarized here. Per-command pages (inputs, outputs, preconditions, behavior, safety) live next to their skill at `plugins/test-commander/skills/<skill>/commands/<command>.md`.

| Command | Skill | Phase |
| --- | --- | --- |
| `/tc:init` | `tc-core` | 1 |
| `/tc:status` | `tc-core` | 1 |
| `/tc:journal` | `tc-core` | 1 |
| `/tc:next` | `tc-core` | 1 |
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
| `/tc:watch-changes` and continuous-quality | `tc-continuous-quality` | 13 |

> Phase 0 ships no implemented commands. The table above describes the planned command surface. Per-phase columns track the rollout.
