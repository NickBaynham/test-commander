# Glossary

| Term | Meaning |
| --- | --- |
| Charter | A bounded statement of what an exploratory session will investigate. |
| BDD | Behavior-Driven Development. Gherkin scenarios capturing expected behavior in business-readable form. |
| Test idea | A specific, falsifiable claim that could be tested. May or may not become automated. |
| Traceability | The link chain from requirement to test idea to BDD scenario to automated test to result to quality report. |
| Risk register | The list of known and suspected risks, tied to the artifacts that surfaced them. |
| Quality report | The current single-page summary of release readiness for a consuming project. |
| Quality gate | A PASS / WARN / FAIL judgement against configured criteria. |
| Lesson | A candidate improvement captured by the learning loop, awaiting human review before promotion. |
| Workspace | The `.test-commander/` directory inside a consuming project. |
| Plugin | The Claude Code plugin at `plugins/test-commander/`. |
| Skill | A unit of capability under `plugins/test-commander/skills/<name>/`, identified by a `SKILL.md`. |
| Marketplace | The Claude Code marketplace declared by `.claude-plugin/marketplace.json` at the repo root. |
| Capstone | The minimum set of phases (0, 1, 2, 3, 4, 5, 6, 7, 8, 10) that delivers the end-to-end story. |
| Sandbox | A team-accessible ephemeral environment launched from GitHub Actions (Phase 12). |
| Autonomy mode | A graded level of agent independence, from read-only-advisor to governed-autonomy (Phase 13). |

This glossary grows as each phase introduces new terms.
