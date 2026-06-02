# Anti-patterns

Recurring mistakes the learning loop is built to catch and, once a project
confirms them, to encode as guidance. Shipped universal starters; the workspace's
promoted guidance adds project-specific ones (it never edits this file).

| Anti-pattern | Why it hurts | The lesson |
| --- | --- | --- |
| Treating a flaky pass as a real pass | hides non-determinism that will fail in CI | a `flaky` result is a determinism debt, not a green light |
| Inlining test data in specs | couples the test to its data; breaks reuse | reach data through a fixture (D6) |
| Asserting nothing | a test that can't fail proves nothing | every test makes at least one meaningful assertion |
| Brittle locators | break on benign UI change | prefer role/label/test-id over CSS/XPath |
| Promoting guidance silently | erodes trust; un-reviewable | promotion is a visible, human-approved diff |

`/tc:learn-from-exploration` and `/tc:learn-from-failures` surface candidate
anti-patterns from real sessions and runs; `/tc:review-lessons` routes the
ambiguous ones to a human.
