# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Semantic versioning applies once a `0.1.0` release exists; until then, changes are grouped by phase.

## [Unreleased]

### Phase 0 — Repository foundation (in progress)

#### Added
- Step 0.1: MIT `LICENSE`, expanded `README.md`, `CONTRIBUTING.md`, this `CHANGELOG.md`, and `TODO.md` placeholder.
- Step 0.2: documentation skeleton under `docs/` (vision, architecture, roadmap, methodology, command-reference, workspace-reference, glossary, install) and `docs/user-guide/getting-started.md`. Markdown link checker at `scripts/check_links.py`.
- Step 0.3: Python project foundation. `pyproject.toml` (PDM-managed, `requires-python = ">=3.12"`, ruff and pytest dev deps, tool config inline). `Makefile` with `install`, `lint`, `test`, `build`, `run`, `verify` targets. `docker-compose.yml` placeholder. `.gitignore` for Python/PDM/IDE artifacts. `tests/test_placeholder.py` so pytest exits cleanly before real tests arrive.

### Plan and architecture

- New Phase 10.5 (Controlled Agent Execution and Policy-Governed Chat) inserted between Phase 10 and Phase 11. Adds intent router, command planner, permission policy, approval gate, bounded agent execution, output validation, and audit journal.
- Decisions D15 (runtime topology — three patterns, MVP locks to Pattern A) and D16 (frontend users drive workflows, not raw Claude Code) added.
- New Runtime Topology section in `planning/plan.md` defining orchestrator / test runtime / viewer roles and the deployment patterns.
- Phases 10, 11, 12, and 13 updated to route through the Phase 10.5 pipeline.
- New skill `tc-governance` added to the catalog.
- New workspace dirs `.test-commander/policy/` and `.test-commander/audit/`.
- New docs: `docs/controlled-agent-execution.md`, `docs/security-and-permissions.md`, `docs/chat-command-governance.md`, `docs/runtime-approval-flow.md`, `docs/agent-adapters.md`. Updated `docs/architecture.md` and `docs/roadmap.md`.

---

Earlier history precedes the changelog. See `git log` for commits before this file existed.
