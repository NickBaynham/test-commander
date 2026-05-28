# test-commander

The Test Commander Claude Code plugin. Skills here orchestrate the Test Commander workflow: requirements review, project knowledge ingestion, exploratory testing, BDD generation, Playwright automation, evidence and quality reporting, and a governed learning loop.

This README documents the plugin's contents. For the project overview, architecture, the phased build plan, and contribution guidelines, see the [main repository](../../README.md).

## What ships now

| Skill | Status | Purpose |
| --- | --- | --- |
| `tc-core` | Phase 1 shipped | Owns `/tc:init`, `/tc:status`, `/tc:journal`, `/tc:next`. |
| `tc-requirements` | Phase 2 shipped | Owns `/tc:review-requirements`, `/tc:review-user-stories`, `/tc:review-acceptance-criteria`, `/tc:requirements-coverage`, `/tc:requirements-to-tests`. |
| `tc-knowledge` | Phase 3 shipped | Owns `/tc:learn-from-docs`, `/tc:learn-from-specs`, `/tc:learn-from-code`, `/tc:learn-from-api`, `/tc:learn-from-tests` plus the shared `synthesize_system_model.py`. |
| `tc-explore` | Phase 4 shipped | Owns `/tc:create-charter`, `/tc:explore` (with the internal exploration-review sub-mode), `/tc:session-summary`, `/tc:test-ideas`. |

## What arrives later

Each Test Commander skill is created by the phase that needs it. Until that phase ships, the skill does not exist. See [planning/plan.md](../../planning/plan.md) for the full roadmap.

| Skill | Phase | Owns |
| --- | --- | --- |
| `tc-bdd`, `tc-traceability` | 5 | BDD generation and traceability maps |
| `tc-build-framework`, `tc-automation-plan`, `tc-automate`, `tc-test-data` | 6 | Playwright framework and strategic automation |
| `tc-run`, `tc-quality-report`, `tc-evidence` | 7 | Execution, evidence, quality report |
| `tc-learning` | 8 | Governed continuous learning |
| `tc-visualize` | 9 | Mermaid diagrams and infographics |
| `tc-web`, `tc-governance`, `tc-mcp`, `tc-sandbox`, `tc-continuous-quality` | 10–13 | Web console, controlled execution, API/MCP, sandboxes, continuous quality |

## Install

This plugin is consumed via the local marketplace at the repository root.

```sh
./bootstrap.sh
make install
```

`make install` validates the manifests, registers the marketplace, installs `test-commander` into Claude Code, and verifies the loaded skills. It is idempotent — re-runs are safe. Use `make uninstall` to reverse. See [docs/install.md](../../docs/install.md) for the full guide.

## License

[MIT](LICENSE). Same terms as the rest of the repository.
