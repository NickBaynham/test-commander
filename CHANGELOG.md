# Changelog

All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Semantic versioning applies once a `0.1.0` release exists; until then, changes are grouped by phase.

## [Unreleased]

### Phase 0 — Repository foundation (in progress)

#### Added
- Step 0.1: MIT `LICENSE`, expanded `README.md`, `CONTRIBUTING.md`, this `CHANGELOG.md`, and `TODO.md` placeholder.
- Step 0.2: documentation skeleton under `docs/` (vision, architecture, roadmap, methodology, command-reference, workspace-reference, glossary, install) and `docs/user-guide/getting-started.md`. Markdown link checker at `scripts/check_links.py`.
- Step 0.3: Python project foundation. `pyproject.toml` (PDM-managed, `requires-python = ">=3.12"`, ruff and pytest dev deps, tool config inline). `Makefile` with `install`, `lint`, `test`, `build`, `run`, `verify` targets. `docker-compose.yml` placeholder. `.gitignore` for Python/PDM/IDE artifacts. `tests/test_placeholder.py` so pytest exits cleanly before real tests arrive.

---

Earlier history precedes the changelog. See `git log` for commits before this file existed.
