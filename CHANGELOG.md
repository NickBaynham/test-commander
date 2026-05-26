# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Semantic versioning applies once a `0.1.0` release exists; until then, changes are grouped by phase.

## [Unreleased]

### Phase 0 — Repository foundation (in progress)

#### Added
- Step 0.1: MIT `LICENSE`, expanded `README.md`, `CONTRIBUTING.md`, this `CHANGELOG.md`, and `TODO.md` placeholder.
- Step 0.2: documentation skeleton under `docs/` (vision, architecture, roadmap, methodology, command-reference, workspace-reference, glossary, install) and `docs/user-guide/getting-started.md`. Markdown link checker at `scripts/check_links.py`.
- Step 0.3: Python project foundation. `pyproject.toml` (PDM-managed, `requires-python = ">=3.12"`, ruff and pytest dev deps, tool config inline). `Makefile` with `install`, `lint`, `test`, `build`, `run`, `verify` targets. `docker-compose.yml` placeholder. `.gitignore` for Python/PDM/IDE artifacts. `tests/test_placeholder.py` so pytest exits cleanly before real tests arrive.
- Step 0.4: POSIX `bootstrap.sh` that detects platform (macOS / Linux / WSL / Git Bash); verifies `git`, `make`, Python 3.12, PDM, Docker; auto-installs PDM via the official installer; auto-installs `git` and `make` on Linux/WSL via apt; prints suggested-install hints for the rest and exits non-zero. Idempotent. Never modifies `PATH` or writes a make shim. Bootstrap and `make install` are separate concerns — bootstrap verifies, install installs. Syntax-checked under both bash and dash.
- Step 0.5: plugin scaffold. `.claude-plugin/marketplace.json` declares `test-commander-marketplace` and references the in-repo `test-commander` plugin via `./plugins/test-commander`. `plugins/test-commander/.claude-plugin/plugin.json` declares version `0.0.0` with author, homepage, and repository fields. Plugin gets its own MIT `LICENSE` and a contents-focused `README.md`. `plugins/test-commander/skills/tc-core/SKILL.md` is the descriptor for the `tc-core` umbrella skill — describes `/tc:init`, `/tc:status`, `/tc:journal` and notes that command behavior arrives in Phase 1. Pre-flight test suite `tests/test_plugin_scaffold.py` covers all 8 automated DoD checks (file presence, JSON validity, manifest shape, frontmatter, command references, no-behavior-yet). Validated end-to-end with `claude plugin validate`, `claude plugin marketplace add`, and `claude plugin install`; `tc-core` appears as the sole skill in `claude plugin details test-commander`.
- Step 0.6: skill verifier. `scripts/verify_skills.py` walks `plugins/test-commander/skills/*/SKILL.md`, parses YAML frontmatter, and classifies each skill as PRESENT, MISSING, MALFORMED, or UNEXPECTED. `--phase N` filter restricts the expected set; default cap is 0 (bumped per phase as new skills land). Exit code 0 when every expected skill is PRESENT and nothing MALFORMED; non-zero otherwise; UNEXPECTED warns only. Includes a 20-entry catalog mirroring the TC-Owned Skill Catalog in the plan. Wired into `make verify` between `test` and `check_links`. Pre-flight test suite `tests/test_verify_skills.py` (16 tests) covers the parser, walker, phase filter, exit codes, and a live-run integration test. `pyproject.toml` gets `pythonpath = ["scripts"]` so pytest can import the verifier without sys.path hacks. All five live drills (baseline, --phase 0, --phase 2, MALFORMED corruption, MISSING rename) match expected output and exit codes.

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
