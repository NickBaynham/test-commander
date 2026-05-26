# test-commander

The Test Commander Claude Code plugin. Skills here orchestrate the Test Commander workflow: requirements review, project knowledge ingestion, exploratory testing, BDD generation, Playwright automation, evidence and quality reporting, and a governed learning loop.

This README documents the plugin's contents. For the project overview, architecture, the phased build plan, and contribution guidelines, see the [main repository](../../README.md).

## What ships now

| Skill | Status | Purpose |
| --- | --- | --- |
| `tc-core` | Skill descriptor only | Owns `/tc:init`, `/tc:status`, `/tc:journal`, and (Phase 1) `/tc:next`. Command behavior arrives in Phase 1. |

## What arrives later

Each Test Commander skill is created by the phase that needs it. Until that phase ships, the skill does not exist. See [planning/plan.md](../../planning/plan.md) for the full roadmap.

| Skill | Phase | Owns |
| --- | --- | --- |
| `tc-requirements` | 2 | Requirements, user-story, and acceptance-criteria reviews |
| `tc-knowledge` | 3 | Learning from docs, specs, code, APIs, tests |
| `tc-explore` | 4 | Charter-based exploratory testing |
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

`make install` registers the marketplace and installs `test-commander` into Claude Code. See [docs/install.md](../../docs/install.md) for the full guide.

## License

[MIT](LICENSE). Same terms as the rest of the repository.
