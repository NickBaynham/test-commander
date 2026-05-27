# Test Commander

An AI-assisted testing system and quality intelligence center. Test Commander helps teams move from requirements and exploration to BDD, automation, evidence, and reporting — with a continuous learning loop and a team-facing console.

It is built as a Claude Code plugin plus a small Python and TypeScript runtime. It is designed to be installed once and grown phase by phase.

> Status: Phase 1 complete (2026-05-26); Phase 2 starts next. `tc-core` ships `/tc:init`, `/tc:status`, `/tc:journal`, `/tc:next`. See [planning/plan.md](planning/plan.md) for the full roadmap and [docs/user-guide/workflow.md](docs/user-guide/workflow.md) for the first walkthrough.

## What Test Commander Is

- A disciplined workflow that turns product context into testable artifacts: requirements reviews, exploration notes, test ideas, BDD specs, Playwright automation, evidence, and a live quality report.
- A Claude Code plugin (`test-commander`) with skills that orchestrate each step.
- A workspace convention (`.test-commander/`) that keeps every quality artifact in one place, versioned in git, with full traceability.
- A continuous learning loop that captures lessons from failures, exploration, and human feedback — and applies them only after human review.

## What Test Commander Is Not

- It is not a replacement for skilled testers.
- It is not a fully autonomous QA system.
- It is not a promise that AI can understand every product perfectly.
- It is not a test automation silver bullet.
- It is not a wrapper over third-party skill plugins — every skill is owned in-repo.

## Who Benefits

| Role | Value |
| --- | --- |
| Testers | Charter-based exploration, captured observations and risks, generated test ideas, BDD that's actually readable. |
| Automation engineers | Playwright framework scaffolded on demand, page objects and fixtures generated from BDD, test data kept out of code. |
| Developers | Requirements reviews catch ambiguity before code; impact analysis and proposed tests on PRs (later phases). |
| Product owners | Live quality report with release-readiness; coverage gaps and open questions visible. |
| Engineering leaders | Traceability from requirement to test result; risk register; learning loop that improves the test strategy over time. |

## How Test Commander Evolves

Test Commander is built in 13 phases. Each phase produces a working, demonstrable increment. The capstone target is phases 0–3, 4–8, and 10. Phases 9, 11, 12, and 13 follow.

See [planning/plan.md](planning/plan.md) for the full phased plan, including Decisions, Open Questions, and per-phase Definition of Done.

The roadmap summary:

| Phase | Name |
| --- | --- |
| 0 | Repository foundation |
| 1 | Workspace and artifact model |
| 2 | Requirements and user story intelligence |
| 3 | Project knowledge ingestion |
| 4 | Exploratory testing |
| 5 | BDD generation and traceability |
| 6 | Playwright framework (lazy) and automation |
| 7 | Execution, evidence, and quality report |
| 8 | Continuous learning |
| 9 | Visual documentation and infographics |
| 10 | Web console MVP |
| 11 | Runtime API and MCP server |
| 12 | Sandboxed testing environment |
| 13 | Continuous quality agent |

## Getting Started

> The full install guide lives in [docs/install.md](docs/install.md) (filled out in Step 0.2). What follows is the short version.

Prerequisites the script will check for you:

- `make`
- Python 3.12
- PDM
- Docker (any compatible runtime)
- Git

Two-stage install:

```sh
./bootstrap.sh    # verifies prereqs; auto-installs the safe ones
make install      # provisions the project and registers the Claude Code plugin
```

Platforms supported: macOS, Linux, Windows via WSL2 or Git Bash. PowerShell is explicitly not supported.

Once installed, open Claude Code and confirm `test-commander:tc-core` appears in available skills.

## Core Workflow

The eventual end-to-end flow (commands roll out across phases):

```
/tc:init
/tc:review-requirements
/tc:learn-from-code
/tc:create-charter --area <feature>
/tc:explore --target <url> --charter <feature>
/tc:test-ideas --area <feature>
/tc:generate-bdd --area <feature>
/tc:automation-plan --area <feature>
/tc:generate-test-data --area <feature>
/tc:automate --feature <feature>
/tc:run --suite smoke
/tc:report
/tc:learn
/tc:next
```

`/tc:next` always tells you what to do next based on the state of `.test-commander/`.

## Repository Layout

```
test-commander/
  .claude-plugin/marketplace.json     # local marketplace
  plugins/test-commander/             # the Claude Code plugin
    .claude-plugin/plugin.json
    skills/
      tc-core/SKILL.md                # phase 0
      tc-requirements/SKILL.md        # phase 2
      tc-bdd/SKILL.md                 # phase 5
      ...
  docs/                               # vision, architecture, methodology, user guide
  planning/plan.md                    # the phased plan
  scripts/                            # verify_skills.py and friends
  bootstrap.sh                        # prereq checker
  Makefile                            # install / lint / test / build / run / verify
  pyproject.toml                      # PDM, Python 3.12+
```

The per-project quality workspace lives at `.test-commander/` in *consuming* projects, not here.

## Documentation

- [Vision](docs/vision.md)
- [Architecture](docs/architecture.md)
- [Roadmap](docs/roadmap.md)
- [Methodology](docs/methodology.md)
- [Command reference](docs/command-reference.md)
- [Workspace reference](docs/workspace-reference.md)
- [Glossary](docs/glossary.md)
- [Install guide](docs/install.md)
- [User guide — getting started](docs/user-guide/getting-started.md)
- [User guide — first workflow walkthrough](docs/user-guide/workflow.md)
- [Public-skill evaluation pass](docs/skill-evaluation.md)
- [Controlled agent execution](docs/controlled-agent-execution.md)
- [Security and permissions](docs/security-and-permissions.md)
- [Chat command governance](docs/chat-command-governance.md)
- [Runtime approval flow](docs/runtime-approval-flow.md)
- [Agent adapters](docs/agent-adapters.md)
- [Phased plan](planning/plan.md)

Most `docs/` files are stubs in Phase 0 and get filled in by their owning phase.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version: pick a phase step, build it small, test it, document it, raise a PR referencing the plan step.

## License

[MIT](LICENSE).
