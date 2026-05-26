# Test Commander — Phased Build Plan

## Product Positioning

Test Commander is an AI-assisted testing system and quality intelligence center. It helps teams move from requirements and exploration to BDD, automation, evidence, reporting, and continuous improvement.

## North Star

Test Commander is a core agentic testing system and quality intelligence center that turns requirements, exploration, automation, evidence, reporting, and continuous learning into one visible workflow.

## Core Implementation Principle

Build in layers. Each phase produces a working, demonstrable increment.

```
Methodology first
  -> CLI / Claude Code skill pack
  -> Artifact model
  -> Playwright automation
  -> Quality report
  -> Learning loop
  -> Web console
  -> Sandboxed team environment
  -> Continuous quality agent
```

---

## Decisions

These decisions are settled. They constrain every phase below.

1. **Vendor and own all skills.** Test Commander owns every skill it ships. Skills live under `.claude/skills/test-commander/<sub-skill>/SKILL.md` inside this repo. There is no runtime dependency on external skill plugins. Community skills (the ones in the current environment) serve as design references and pattern inspiration only — we author our own copies adapted to the Test Commander workspace, naming, and traceability model. This avoids compatibility drift in directory layouts, file naming, and tool expectations, and lets us evolve skills in lockstep with the workspace schema. See *Skill Authoring Strategy*.
2. **Test Commander is a skill pack first, runtime second.** Phases 0–5 and Phases 7–9 author Markdown skills, methodology, templates, and command guidance — Claude Code executes by reading them. Phase 6 introduces the first executable code (Playwright framework). Phase 10 adds the web/API runtime.
3. **No `examples/` directory.** Real projects bring their own artifacts. Sample apps are not part of the repo.
4. **All BDD lives under `.test-commander/bdd/`** including feature files (`.test-commander/bdd/features/`). Nothing BDD-related lives at the repo root.
5. **Workspace is committed to git.** `.test-commander/` is checked in, including `quality-report/history/`. Test runs in `.test-commander/runs/` are committed as snapshots; large binaries (videos, traces) follow git-lfs rules documented per phase.
6. **Test data lives outside code.** Path: `.test-commander/test-data/`. Tests reference data through fixtures; no inline data in `.ts` files. Claude can regenerate test data on demand via `/tc:generate-test-data`.
7. **Capstone includes Phase 3.** Project knowledge is foundational for exploration, BDD generation, and automation. The capstone is: 0, 1, 2, 3, 4, 5, 6, 7, 8, 10.
8. **Playwright framework is built lazily.** `/tc:build-framework` is a one-time, idempotent skill. Any command that needs the framework (`/tc:automate`, `/tc:run`) checks for its presence first and invokes `/tc:build-framework` if missing. The framework is never built before automation is actually needed.
9. **Every phase has Review, Test, and Documentation steps.** See *Per-Phase Conventions*.
10. **`make install` provisions the full environment.** Python (PDM), Node (Playwright), and a verification step that lists every TC-owned skill the current phase set requires and confirms each is present in `.claude/skills/test-commander/`. See *Environment Setup*.
11. **Phase 3 precedes Phase 4 in every rollout.** Exploration reads from `.test-commander/product-knowledge/`, which is created in Phase 3. The capstone order respects this; no shortcut is permitted.
12. **Plugin structure follows Claude Code's convention.** Verified against installed plugins on disk. The repo is a self-contained marketplace plus a single plugin:
    ```
    test-commander/                       (repo root = marketplace)
      .claude-plugin/marketplace.json
      plugins/
        test-commander/                   (the plugin)
          .claude-plugin/plugin.json
          skills/
            tc-core/SKILL.md
            tc-requirements/SKILL.md
            tc-bdd/SKILL.md
            ...
          LICENSE
          README.md
    ```
    There is **no umbrella `SKILL.md`** — the plugin manifest provides identity. `tc-core` is a sibling skill that owns the orchestration commands (`/tc:init`, `/tc:status`, `/tc:journal`, `/tc:next`). Skills are discoverable to Claude Code as `test-commander:<skill-name>`.

13. **Platform support: macOS, Linux, Windows-via-WSL or Git Bash. No PowerShell.** All shell scripts are POSIX-compatible. Windows users run under WSL2 (preferred) or Git Bash. We explicitly do not target PowerShell and do not maintain PowerShell equivalents. The bootstrap script detects platform and routes accordingly.

14. **`bootstrap.sh` precedes `make install`.** Because `make` itself is a prerequisite, the repo ships a POSIX `bootstrap.sh` at the root that:
    - Detects the platform (macOS, Linux, WSL, Git Bash).
    - Checks for `make`, Python 3.12, PDM, Docker, Git.
    - Auto-installs what is safe and non-controversial (PDM via its official installer; Git if missing on Linux).
    - For "questionable" tools (Docker runtime choice — Docker Desktop, Colima, Rancher Desktop, Podman; Python via system package manager vs pyenv), **prints a suggested install list and exits** without installing.
    - Once all prereqs are present, hands off to `make install`.
    - Is idempotent: re-running detects what's already installed and does nothing for those.
    - Does not write a `make` shim or modify PATH in destructive ways.

---

## Open Questions

Unresolved decisions. Each should be answered before its dependent phase begins.

| # | Question | Affects | Default if unanswered |
| --- | --- | --- | --- |
| Q1 | Should Test Commander handle non-Playwright testing — API (Postman), performance, accessibility — as first-class capabilities, or only as integrations? | Phase 3, 6, 7 | Postman API testing is in scope (Postman skills are installed); perf and a11y are out of scope for v1. |
| Q2 | Multi-project support: can one Test Commander installation manage several `.test-commander/` workspaces, or is it strictly one-per-repo? | Phase 1, 10, 11 | One-per-repo for v1. |
| Q3 | Quality report history: full snapshot per `/tc:report` run, or diff-based? | Phase 7 | Full snapshot. Cheap, auditable, git compresses well. |
| Q4 | Should `/tc:next` run automatically after every command, or only on request? | Phase 1 | On request only. Proactive suggestions can be a Phase 8 learning-loop feature. |
| Q5 | Large evidence (videos, traces): commit, git-lfs, or external store? | Phase 7 | Git-ignored by default with a documented opt-in for `git-lfs`. Screenshots are committed. |
| Q6 | Should the learning loop write back into installed third-party skills, or only into Test Commander's own guidance files? | Phase 8 | Only into Test Commander's `learning/` folder. We never modify third-party skills. |
| Q7 | Should `/tc:next` be a sub-command of `tc-core` or its own sub-skill `tc-next`? | Phase 1 | Sub-command of `tc-core` to keep the umbrella unified. Promote to standalone only if heuristics grow large. |
| Q8 | Sandbox provider for Phase 12: docker-compose only, or also adapters for Coder, Daytona, Sprites.dev, GitHub Codespaces? | Phase 12 | docker-compose first; stub a generic adapter and a Sprites.dev placeholder; defer others until requested. |
| Q9 | Web-console auth model: loopback-only, shared-secret token, OS-user binding, full multi-user? | Phase 10 | Loopback-only for v1 (single user, no auth). Document the threat model. |
| Q10 | Quality-report history retention: keep forever in git, rotate after N snapshots, archive externally? | Phase 7, revisit at 8 | Keep forever in git for now. Add a `tc:archive-history` command later if size becomes painful. |
| Q11 | Test-data generator format: Python factories, YAML manifests, Markdown specs, or a mix? | Phase 6 | Markdown specs plus YAML manifests for declarative data; Python factories only where a generator is too complex to express declaratively. |
| Q12 | Should we evaluate a public Mermaid/diagram skill before authoring `tc-visualize`, or build it ourselves from the start? | Phase 9 | Author `tc-visualize` ourselves; Mermaid is simple enough that a wrapper is not worth the dependency. Evaluate public options only if scope grows. |

---

## Skill Authoring Strategy

Test Commander vendors and owns every skill it uses. We author each skill from scratch inside this repository, tuned to the TC workspace and naming. Community skills are *design references* — patterns, prompts, and structural ideas we learn from — never runtime dependencies. This eliminates compatibility risk from upstream changes (renames, directory shifts, behavior drift) and lets us iterate on skills in lockstep with the workspace schema.

### Authoring Rules

1. Every TC skill lives at `plugins/test-commander/skills/<skill-name>/SKILL.md`.
2. Each skill has its own `SKILL.md` (with YAML frontmatter: `name`, `description`), a `methodology/` folder (where applicable), a `templates/` folder, and a `commands/` folder mapping `/tc:*` commands to behavior.
3. Where a community skill informed the design, the skill's `README.md` cites it as a *reference*, never an import. Respect the source skill's license; we are authoring originals, not redistributing.
4. Skill content reads the TC workspace directly (`.test-commander/...`). No skill calls another plugin's skill at runtime.
5. `tc-core` orchestrates other TC skills by command invocation, not by file include.
6. Tests for skills live under `plugins/test-commander/skills/<skill-name>/tests/` (Markdown fixtures, expected outputs).

### TC-Owned Skill Catalog

Every skill listed here is created by the phase noted in the *Created in* column. Phase 0 creates only `tc-core`.

| Skill | Created in | Commands routed | Reference (design only) |
| --- | --- | --- | --- |
| `tc-core` | Phase 0 / 1 | `/tc:init`, `/tc:status`, `/tc:journal`, `/tc:next` (per Q7) | superpowers (writing-plans, writing-skills) |
| `tc-requirements` | Phase 2 | `/tc:review-requirements`, `/tc:review-user-stories`, `/tc:review-acceptance-criteria`, `/tc:requirements-coverage`, `/tc:requirements-to-tests` | business-requirements, logical-consistency |
| `tc-knowledge` | Phase 3 | `/tc:learn-from-docs`, `/tc:learn-from-specs`, `/tc:learn-from-code`, `/tc:learn-from-api`, `/tc:learn-from-tests` | context7, postman (agent-ready-apis, search, generate-spec) |
| `tc-explore` | Phase 4 | `/tc:create-charter`, `/tc:explore`, `/tc:test-ideas`, `/tc:session-summary` | mcp-exploratory-testing (explore-app, explore-workflow, review-exploration) |
| `tc-bdd` | Phase 5 | `/tc:generate-bdd`, `/tc:review-bdd` | exploratory-to-bdd (generate-bdd, review-bdd, explore-to-bdd) |
| `tc-traceability` | Phase 5 | `/tc:traceability-map` | (none) |
| `tc-build-framework` | Phase 6 | `/tc:build-framework` (lazy, idempotent) | agentic-playwright-automation:setup-playwright-framework |
| `tc-automation-plan` | Phase 6 | `/tc:automation-plan` | (none) |
| `tc-automate` | Phase 6 | `/tc:automate`, `/tc:review-automation` | agentic-playwright-automation (convert-bdd-to-playwright, generate-playwright-test, generate-playwright-suite, review-playwright-test) |
| `tc-test-data` | Phase 6 | `/tc:generate-test-data` | (none) |
| `tc-run` | Phase 7 | `/tc:run`, `/tc:analyze-results` | agentic-playwright-automation:investigate-playwright-failure, postman (run-collection, test) |
| `tc-quality-report` | Phase 7 | `/tc:report`, `/tc:quality-gate` | (none) |
| `tc-evidence` | Phase 7 | indexer (cross-cutting; invoked by `tc-run` and the web console) | (none) |
| `tc-learning` | Phase 8 | `/tc:learn`, `/tc:learn-from-failures`, `/tc:learn-from-exploration`, `/tc:learn-from-feedback`, `/tc:review-lessons`, `/tc:promote-lessons` | superpowers (receiving-code-review, systematic-debugging) |
| `tc-visualize` | Phase 9 | `/tc:visualize`, all `/tc:diagram-*`, `/tc:generate-infographic`, `/tc:render-visuals` | frontend-design (infographics only) |
| `tc-web` | Phase 10 | `/tc:web-init`, `/tc:web-start`, `/tc:web-sync`, `/tc:web-index-artifacts`, `/tc:web-export` | web-scaffold:create-website, frontend-design |
| `tc-mcp` | Phase 11 | (server, not commands) | anthropic-skills:skill-creator |
| `tc-sandbox` | Phase 12 | `/tc:sandbox-*` | (none) |
| `tc-continuous-quality` | Phase 13 | `/tc:watch-changes`, `/tc:impact-analysis`, `/tc:coverage-gap-analysis`, `/tc:propose-tests`, `/tc:create-test-pr`, `/tc:continuous-quality-check` | agentic-playwright-automation:investigate-playwright-failure |

If Q7 promotes `/tc:next` to its own skill, `tc-next` is added and `tc-core` retains only init/status/journal.

### Public Skill Evaluation (Phase 0 task)

Before authoring new skills from scratch, Phase 0 includes a brief evaluation pass for these public-marketplace candidates. Adopt as a design reference (not a runtime dep) only if materially helpful:

- A Mermaid/diagram authoring skill (informs `tc-visualize`).
- A devbox/sandbox skill — Coder, Daytona, Sprites.dev (informs `tc-sandbox`).
- A traceability-matrix skill (informs `tc-traceability`).
- An accessibility-testing skill (informs scope decision under Q1).
- A performance-testing skill (informs scope decision under Q1).

The evaluation outputs to `docs/skill-evaluation.md` and feeds the To Do list.

---

## Environment Setup

Two-stage install. `bootstrap.sh` ensures the prerequisites for `make` itself; `make install` then provisions the project.

### Stage 1 — `bootstrap.sh`

POSIX shell script at the repo root. Detects platform and verifies/installs prerequisites.

**Platforms supported.**

- macOS (bash/zsh, Homebrew).
- Linux (bash, distro package manager).
- Windows via WSL2 (Ubuntu by default; bash + apt).
- Windows via Git Bash (limited — sufficient for Git operations and reading the repo; full functionality requires WSL).
- **PowerShell is explicitly not supported.** No PowerShell scripts, no `.ps1` files.

**Prerequisites verified.**

| Tool | Auto-install policy |
| --- | --- |
| `git` | Auto-install on Linux/WSL via apt; on macOS prompt to install Xcode CLI tools; on Git Bash assume present (it's the host). |
| `make` | Auto-install on Linux/WSL via apt; on macOS prompt to install Xcode CLI tools; on Git Bash print the install command and exit (Git Bash does not ship with make). |
| Python 3.12 | Print suggested install commands per platform. Do not auto-install — users have strong opinions (pyenv, asdf, system, Homebrew). |
| PDM | Auto-install via the official PDM installer once Python 3.12 is present. |
| Docker | **Never auto-install.** Print the choice list (Docker Desktop, Colima, Rancher Desktop, Podman with docker compat) and exit. |

**Behavior.**

- Idempotent — re-running is a no-op if everything is present.
- Never modifies `PATH` destructively.
- Never writes a `make` shim or fake executable in `PATH`.
- On any "questionable" missing tool, prints a clear suggested install list and exits with non-zero so the user can decide.
- Once all prerequisites are present, the final step is `exec make install`.

### Stage 2 — `make install`

Runs only after `bootstrap.sh` succeeds. Prepares the project itself. The target grows per phase; the table tracks additions.

| Phase | `make install` adds |
| --- | --- |
| 0 | `pdm install`; create repo dirs; register the local marketplace with Claude Code (`claude plugin marketplace add .`); install the `test-commander` plugin (`claude plugin install test-commander`); run `scripts/verify_skills.py` against `plugins/test-commander/skills/`; print `next steps`. |
| 1 | `/tc:init` is callable; `make install` runs it idempotently if `.test-commander/` is absent. |
| 2 | No new system deps. Verifies `business-requirements` and `logical-consistency` plugins. |
| 3 | Verifies `context7` and `postman` plugins. |
| 4 | Verifies `mcp-exploratory-testing` plugin and Playwright MCP availability. |
| 5 | Verifies `exploratory-to-bdd` plugin. |
| 6 | Verifies `agentic-playwright-automation` plugin. Installs Node, runs `npx playwright install --with-deps`. Idempotent. |
| 7 | Adds report-generation deps if any (e.g. Pandoc only if used). |
| 8 | No new system deps. |
| 9 | Installs Mermaid CLI for headless PNG/SVG rendering. |
| 10 | Adds web/api app installs (Next.js, FastAPI). `docker compose` startup. |
| 11 | Adds MCP runtime install and registration. |
| 12 | No host deps; the workflow self-installs in CI. |
| 13 | Adds the continuous-quality CI workflow as opt-in. |

### Required Make Targets

Every phase keeps these targets working:

```
make install         # provision environment, verify skills, idempotent
make lint            # static checks
make test            # all tests (unit, integration, framework)
make build           # build any compiled artifacts
make run             # start the local stack (docker compose where applicable)
make verify          # phase-local review/test gates (see Per-Phase Conventions)
```

### Verifying Skills

`make install` ends with a skill-verification step that operates on **TC-owned skills only** (we have no runtime dependency on third-party plugins):

- Lists every TC sub-skill from the *TC-Owned Skill Catalog* expected for the current phase set.
- For each, confirms `plugins/test-commander/skills/<skill-name>/SKILL.md` exists, parses, and declares the expected `name` and `description` frontmatter.
- Reports each as `PRESENT`, `MISSING`, or `MALFORMED`.
- Exits non-zero on any `MISSING` or `MALFORMED`.
- Prints a `next steps` block telling the user which `/tc:*` skill to author next.

---

## Workspace Layout

Single source of truth for what lives where. Updated by every phase that adds artifact types.

```
.test-commander/
  project.md
  config.yaml
  methodology.md
  documents/
    uploaded/
    index.md
  requirements/
    requirements-inventory.md
    requirements-review.md
    user-story-review.md
    acceptance-criteria-review.md
    open-questions.md
    requirements-coverage.md
  product-knowledge/
    system-model.md
    business-rules.md
    user-journeys.md
    entities.md
    assumptions.md
    code-derived-model.md
    spec-derived-model.md
    documentation-model.md
    api-model.md
  charters/
  exploration-notes/
  test-ideas/
  bdd/
    features/                # .feature files live here
    summaries/
  automation-plan/
  test-data/
    seed/
    scenarios/
    factories/               # regenerable definitions
    README.md
  risk-register/
    risk-register.md
  quality-report/
    current-quality-report.md
    history/                 # committed snapshots
  traceability/
    requirements-map.md
    test-map.md
    automation-map.md
  evidence/
    screenshots/
    videos/                  # git-ignored by default; opt-in lfs
    traces/                  # git-ignored by default; opt-in lfs
    logs/
  learning/
    lessons-inbox.md
    accepted-lessons.md
    rejected-lessons.md
    needs-human-review.md
  visuals/
    mermaid/
    svg/
    png/
    infographic/
  sessions/
  journal/
  runs/
```

Test code lives at `tests/` (created in Phase 6). It must not contain data; data flows via fixtures from `.test-commander/test-data/`.

---

## Per-Phase Conventions

Every phase in this plan must include all six of these. No exceptions.

1. **Implementation.** What is created or changed.
2. **Skills used.** Which existing skills are invoked. Note any new wrapping commands.
3. **Documentation.** What is written. Always update `docs/user-guide/` for tester-facing changes, `docs/command-reference.md` for new commands, and `CHANGELOG.md` for the phase entry.
4. **Review step.** A human or peer review checklist tied to phase-specific outputs. Must complete before the phase is marked done.
5. **Test step.** Automated verification: `make verify` plus phase-specific tests. Must pass before the phase is marked done.
6. **Definition of done.** Bullet list of objective, checkable criteria.

When a Claude Code prompt is provided for a phase, it ends with this standing instruction:

> Do not implement future phases yet. Create clean extension points, but only complete the current phase. Write documentation as you go. Add review and test steps. Update the To Do and Completed lists in `planning/plan.md`.

---

## Phase 0 — Repository Foundation

**Goal.** Repo structure, conventions, dev environment, and skill-verification.

**Implementation.**

- `README.md` (MIT), `LICENSE` (MIT), `CONTRIBUTING.md`, `CHANGELOG.md`, `TODO.md`
- `bootstrap.sh` — POSIX shell, platform detection, prereq verification, suggested-install output, hands off to `make install`
- `Makefile` with `install`, `lint`, `test`, `build`, `run`, `verify`
- `docker-compose.yml` (placeholder; populated as runtimes are introduced)
- `pyproject.toml` (PDM, `requires-python = ">=3.12"`)
- `.claude-plugin/marketplace.json` — declares the local marketplace
- `plugins/test-commander/.claude-plugin/plugin.json` — declares the Test Commander plugin
- `plugins/test-commander/README.md`, `plugins/test-commander/LICENSE`
- `plugins/test-commander/skills/tc-core/SKILL.md` — first skill (init/status/journal commands; `/tc:next` deferred to Phase 1 per Q7)
- `docs/vision.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/methodology.md`, `docs/command-reference.md`, `docs/workspace-reference.md`, `docs/glossary.md`, `docs/skill-evaluation.md`
- `docs/user-guide/getting-started.md` — first tester-facing page; covers `bootstrap.sh` then `make install`
- `docs/install.md` — platform-by-platform install guide (macOS, Linux, WSL, Git Bash; explicit no-PowerShell note)
- `scripts/verify_skills.py` — used by `make install`; parses `plugins/test-commander/skills/*/SKILL.md` frontmatter

**Skills authored.** `tc-core` umbrella SKILL.md (init/status/journal commands only — `/tc:next` deferred to Phase 1 per Q7 default). Public-skill evaluation pass written to `docs/skill-evaluation.md`.

**Design references.** `anthropic-skills:skill-creator` (umbrella SKILL.md patterns), `claude-code-setup:claude-automation-recommender` (hook/skill/MCP surface validation). These inform authoring; no runtime dependency.

**Documentation.** `docs/user-guide/getting-started.md` explains what Test Commander is, what to install, and how to confirm the environment is ready.

**Review step.**

- README answers: what it is, what it is not, the roadmap, the workflow, value per persona, evolution plan.
- All linked docs exist and are non-empty.
- `bootstrap.sh` then `make install` runs clean on a fresh checkout on macOS and WSL (Git Bash gets a documented-limitations pass).
- `tc-core` skill loads in Claude Code after `make install`.

**Test step.**

- `make verify` runs: lint, link check on docs, `scripts/verify_skills.py`, plugin/marketplace JSON schema validation.
- `make install` is idempotent (running twice produces no diff and no duplicate plugin install).
- `bootstrap.sh` is idempotent.

**Definition of done.**

- Clean repo, all docs stubbed, `bootstrap.sh` + `make install` succeed on macOS and WSL, `tc-core` skill is loaded and callable in Claude Code, `scripts/verify_skills.py` reports `tc-core` PRESENT and well-formed, `getting-started.md` walks a tester through the install end-to-end.

### Phase 0 — Execution Outline

Nine small, ordered steps. Each ships an independently verifiable artifact with its own DoD and review.

#### 0.1 — Repository metadata
- **Deliverables.** `LICENSE` (MIT), `README.md` skeleton, `CONTRIBUTING.md`, `CHANGELOG.md`, `TODO.md`.
- **Definition of done.** All five files exist. README under 400 lines, answers what TC is / isn't / how it evolves / who benefits. CHANGELOG has a Phase 0 stub. TODO.md is a placeholder.
- **Review.** Manual read of README against the four-question checklist. Markdown lint clean.

#### 0.2 — Documentation skeleton
- **Deliverables.** `docs/vision.md`, `docs/architecture.md`, `docs/roadmap.md`, `docs/methodology.md`, `docs/command-reference.md`, `docs/workspace-reference.md`, `docs/glossary.md`, `docs/install.md`, `docs/user-guide/getting-started.md`.
- **Definition of done.** Each file has a heading, a one-paragraph summary, and a "filled out in Phase N" note where applicable. All cross-links from README resolve.
- **Review.** Run a Markdown link checker (small Python script under `scripts/`). Manual skim each for direction-accuracy.

#### 0.3 — Python project foundation
- **Deliverables.** `pyproject.toml` (PDM, `requires-python = ">=3.12"`), `Makefile` with `install`/`lint`/`test`/`build`/`run`/`verify` targets, `docker-compose.yml` placeholder.
- **Definition of done.** `pdm install` succeeds with empty dep list; `make lint`, `make test`, `make verify` run with exit 0; `make build` and `make run` no-op cleanly with a "nothing to do yet" message.
- **Review.** Run all six make targets; capture exit codes; confirm idempotency.

#### 0.4 — Bootstrap script
- **Deliverables.** `bootstrap.sh` (POSIX, idempotent).
- **Definition of done.** Detects platform (macOS / Linux / WSL / Git Bash); verifies `make`, Python 3.12, PDM, Docker, Git; auto-installs PDM via its official installer when missing; prints suggested-install list for Docker and Python; exits 0 when all present, non-zero with explicit guidance otherwise; never modifies `PATH`; never writes a `make` shim.
- **Review.** Three macOS scenarios — all present (pass), PDM missing (auto-installs), Docker missing (prints suggestions, exits non-zero). WSL run noted as a follow-up if not immediately available.

#### 0.5 — Plugin scaffold
- **Deliverables.** `.claude-plugin/marketplace.json`; `plugins/test-commander/.claude-plugin/plugin.json`; `plugins/test-commander/README.md`, `plugins/test-commander/LICENSE`; `plugins/test-commander/skills/tc-core/SKILL.md` (frontmatter + description of `/tc:init`, `/tc:status`, `/tc:journal`; commands not yet implemented).
- **Definition of done.** `marketplace.json` and `plugin.json` schema-valid; `tc-core/SKILL.md` has correct YAML frontmatter (`name`, `description`); skill describes the three commands; nothing implemented beyond the skill description.
- **Review.** Install the local marketplace into Claude Code (`/plugin marketplace add .`); install `test-commander`; verify `tc-core` appears in available-skills. Confirm load with no errors.

#### 0.6 — Skill verifier
- **Deliverables.** `scripts/verify_skills.py`.
- **Definition of done.** Parses every `plugins/test-commander/skills/*/SKILL.md`; reports each as PRESENT / MISSING / MALFORMED; aggregates exit code (non-zero on any non-PRESENT); supports `--phase N` to restrict the expected skill set per phase.
- **Review.** Run against the current state — `tc-core` reports PRESENT. Break the frontmatter — verifier reports MALFORMED. Rename the dir — verifier reports MISSING. Restore and re-verify.

#### 0.7 — `make install` wiring
- **Deliverables.** Wire the `Makefile` `install` target to register the local marketplace and install the plugin via `claude plugin` CLI; run `scripts/verify_skills.py` as the final step.
- **Definition of done.** On a fresh checkout, `bootstrap.sh` → `make install` results in `tc-core` loaded in Claude Code; second `make install` is a no-op; `verify_skills.py` reports PASS at the end of install.
- **Review.** Clean macOS run captured top to bottom (logs saved under a temp dir, not committed). Second run produces no diff and no duplicate plugin entry.

#### 0.8 — Public-skill evaluation
- **Deliverables.** `docs/skill-evaluation.md` (under one page).
- **Definition of done.** One paragraph per candidate — Mermaid/diagram, devbox/sandbox (Coder, Daytona, Sprites.dev), traceability-matrix, accessibility-testing, performance-testing — each stating what it does, why interesting, the decision (adopt as design reference / pass), and a link if available.
- **Review.** Every decision actionable. Any open questions surfaced get added to plan.md Open Questions, not lost.

#### 0.9 — Smoke test and Phase 0 sign-off
- **Deliverables.** Phase 0 entry in `CHANGELOG.md`; Phase 0 items moved from `To Do` to `Completed` in `plan.md` with date.
- **Definition of done.** End-to-end walkthrough of `docs/user-guide/getting-started.md` as a cold user (fresh shell, follow instructions verbatim); every step 0.1–0.8 passed its review; no remaining blockers.
- **Review.** Final read of README and `getting-started.md` for accuracy; CHANGELOG accurate; commit and tag `phase-0`.

#### Ordering and parallelism

- Strict order: 0.1 → 0.2 → 0.3 → 0.4 → 0.5 → 0.6 → 0.7 → 0.9.
- 0.8 (skill evaluation) can run in parallel with any of 0.3–0.7.
- 0.9 is always last.

---

## Phase 1 — Workspace and Artifact Model

**Goal.** Canonical `.test-commander/` workspace and the first four core commands.

**Implementation.**

- `/tc:init` — create the workspace and starter files; idempotent.
- `/tc:status` — summarize current workspace state.
- `/tc:journal` — add or summarize journal entries.
- `/tc:next` — **infer the next recommended commands** by reading workspace state (e.g. requirements present but unreviewed → suggest `/tc:review-requirements`; BDD generated but no automation plan → suggest `/tc:automation-plan`).
- Workspace template under `templates/workspace/` so `/tc:init` has a source of truth.

**Skills authored.** Extend `tc-core` to include `/tc:next`. Author the heuristics file under `.claude/skills/test-commander/tc-core/methodology/next-step-inference.md`.

**Design references.** `superpowers:writing-skills` (command file structure), `superpowers:writing-plans` (planning heuristics for `/tc:next`).

**Documentation.**

- `docs/workspace-reference.md` lists every directory and file, with purpose and producer command.
- `docs/command-reference.md` documents the four commands with inputs, outputs, preconditions, files read, files written, safety rules, definition of done.
- `docs/user-guide/workflow.md` — first walk-through: `/tc:init → /tc:status → /tc:next`.

**Review step.**

- Workspace template is exhaustive (no surprise files appear in later phases).
- `/tc:next` correctly handles: empty workspace, partially populated workspace, fully populated workspace.

**Test step.**

- Unit-style verification: a script seeds different workspace states and asserts `/tc:next` returns the expected recommendation.
- `make verify` runs the seed harness.

**Definition of done.**

- Workspace created by `/tc:init`, status summarized correctly, journal append works, `/tc:next` recommends sensibly, tester walkthrough in `workflow.md` is end-to-end runnable.

---

## Phase 2 — Requirements and User Story Intelligence

**Goal.** Review requirements, user stories, and acceptance criteria before automation exists.

**Implementation.**

- `/tc:review-requirements`, `/tc:review-user-stories`, `/tc:review-acceptance-criteria`, `/tc:requirements-coverage`, `/tc:requirements-to-tests`
- Methodology docs: `requirements-quality-review.md`, `user-story-readiness.md`, `acceptance-criteria-quality.md`
- Templates: `requirements-review-template.md`, `user-story-review-template.md`, `acceptance-criteria-review-template.md`, `requirements-coverage-template.md`

**Skills authored.** `tc-requirements` with five sub-commands. Includes methodology files for the review rubric and INVEST, plus the four templates.

**Design references.** `business-requirements:brd` and `business-requirements:analyze-requirements` (review structure, BRD output shape), `logical-consistency:logic-check` (contradictions, undefined terms, faulty inference rubric).

**Review rubric.** clarity, testability, completeness, consistency, atomicity, measurability, AC quality, edge cases, negative cases, data rules, roles/permissions, NFRs, dependencies, ambiguity, risk, automation suitability. INVEST for stories.

**Documentation.** `docs/user-guide/reviewing-requirements.md` — how a tester uploads requirements, runs the review, and reads the output.

**Review step.**

- Sample requirement set is run through the commands; reviewer confirms outputs flag the seeded defects (we maintain a small fixture set of intentionally-flawed requirements for this).

**Test step.**

- Fixture-driven test: known-bad requirements produce expected findings. `make verify` runs it.

**Definition of done.**

- All five commands work end-to-end, traceability writes occur, open questions surface, fixture test passes, tester guide is complete.

---

## Phase 3 — Project Knowledge Ingestion

**Goal.** Learn from project artifacts and produce structured knowledge.

**Implementation.**

- `/tc:learn-from-docs`, `/tc:learn-from-specs`, `/tc:learn-from-code`, `/tc:learn-from-api`, `/tc:learn-from-tests`
- Methodology docs: `project-knowledge.md`, `learning-from-code.md`, `learning-from-api.md`, `learning-from-documents.md`
- Templates for system model, code-derived model, API model, documentation model, business rules, user journeys, entities, assumptions, open questions

**Skills authored.** `tc-knowledge` with five sub-commands. Includes methodology files for each source type and templates for the eight knowledge artifacts.

**Design references.** `plugin:context7:context7` (library/framework doc lookup patterns), `postman:agent-ready-apis`, `postman:search`, `postman:generate-spec` (API discovery and spec extraction patterns). TC reads OpenAPI/Postman collections directly using its own logic; we do not call out to Postman MCP at runtime.

**Documentation.** `docs/user-guide/building-project-knowledge.md`.

**Review step.**

- Knowledge artifacts cite specific source files/lines; assumptions are flagged distinctly from confirmed facts; open questions are routed to `requirements/open-questions.md`.

**Test step.**

- Seed a small repo with known content; assert that `/tc:learn-from-code` and `/tc:learn-from-api` produce the expected entity and endpoint inventories.

**Definition of done.**

- All five commands work, traceability maps populated, knowledge artifacts cite sources, tests pass, tester guide complete.

---

## Phase 4 — Exploratory Testing and Test Idea Generation

**Goal.** Charter-based exploration that captures observations, risks, ideas, and evidence.

**Implementation.**

- `/tc:create-charter`, `/tc:explore`, `/tc:test-ideas`, `/tc:session-summary`
- Methodology: `exploratory-testing.md`, `test-idea-model.md`, `session-based-test-management.md`
- Templates: charter, exploration note, test idea, session summary

**Skills authored.** `tc-explore` with four sub-commands. Drives Playwright MCP directly. Includes methodology for charter-based exploration, the test-idea model, and session-based test management.

**Design references.** `mcp-exploratory-testing:explore-app` (app reconnaissance shape), `mcp-exploratory-testing:explore-workflow` (bounded workflow exploration), `mcp-exploratory-testing:review-exploration` (review rubric for exploration artifacts).

**Inputs read.** `.test-commander/product-knowledge/`, `requirements/`, `risk-register/`, `learning/accepted-lessons.md`.

**Documentation.** `docs/user-guide/exploring-an-app.md` — how to write a charter, drive Playwright MCP, capture findings.

**Review step.**

- `mcp-exploratory-testing:review-exploration` is run against new session reports as part of the review gate.
- Findings link back to charter ID and product knowledge.

**Test step.**

- Replay a recorded exploration on a known sample app; confirm artifact counts and shape.

**Definition of done.**

- Exploration produces charters, notes, ideas, risks, and evidence in the right folders; review skill passes the artifacts; user guide is complete.

---

## Phase 5 — BDD Generation and Traceability

**Goal.** Turn requirements, exploration, and ideas into BDD specs with full traceability.

**Implementation.**

- `/tc:generate-bdd`, `/tc:review-bdd`, `/tc:traceability-map`
- Methodology: `bdd-generation.md`, `traceability.md`
- Templates: `feature-template.feature`, `bdd-review-template.md`, `traceability-map-template.md`

**Skills authored.** `tc-bdd` for generation and review; `tc-traceability` for the cross-cutting map. Methodology and templates for both.

**Design references.** `exploratory-to-bdd:generate-bdd`, `exploratory-to-bdd:review-bdd`, `exploratory-to-bdd:explore-to-bdd` (BDD generation prompts, review rubric, exploration-to-spec bridging), `mcp-exploratory-testing:exploration-to-bdd` (handoff patterns).

**Outputs.** `.test-commander/bdd/features/*.feature`, `.test-commander/bdd/summaries/`, `.test-commander/traceability/`.

**Tags.** `@smoke`, `@regression`, `@manual`, `@exploratory`, `@automated-candidate`, `@risk:revenue`, `@risk:security`, plus feature-area tags.

**Traceability chain.** Requirement → Test Idea → BDD Scenario → Automation Candidate → Automated Test → Test Result → Quality Report.

**Documentation.** `docs/user-guide/generating-bdd.md`.

**Review step.**

- `exploratory-to-bdd:review-bdd` runs against new specs; traceability map updated and verified.

**Test step.**

- Round-trip a small requirement → BDD → traceability flow and assert the trace map contains the expected links.

**Definition of done.**

- Feature files live under `.test-commander/bdd/features/`, summaries written, traceability complete, review skill passes, user guide complete.

---

## Phase 6 — Playwright Framework (Lazy) and Strategic Automation

**Goal.** Generate the Playwright TypeScript framework on demand, then produce strategic automation.

**Implementation.**

- `/tc:build-framework` — **lazy, idempotent**. Builds `tests/` only if absent. Safe to call repeatedly.
- `/tc:automation-plan`, `/tc:automate`, `/tc:review-automation`
- `/tc:generate-test-data` — populate/regenerate `.test-commander/test-data/`. Tests reference data via fixtures.
- Methodology: `automation-suitability.md`, `playwright-standards.md`, `locator-strategy.md`, `test-data-strategy.md`
- Templates: `automation-plan-template.md`, `page-object-template.ts`, `component-object-template.ts`, `playwright-spec-template.ts`, `fixture-template.ts`, `test-data-template.json`

**Skills authored.** `tc-build-framework` (lazy), `tc-automation-plan`, `tc-automate` (single, suite, and bulk conversion paths), `tc-test-data`. Methodology and TS templates colocated.

**Design references.**

- `agentic-playwright-automation:setup-playwright-framework` (framework scaffold structure).
- `agentic-playwright-automation:convert-bdd-to-playwright` (bulk-conversion approach).
- `agentic-playwright-automation:generate-playwright-test` (single-test generation prompts).
- `agentic-playwright-automation:generate-playwright-suite` (suite-generation prompts).
- `agentic-playwright-automation:review-playwright-test` (review rubric).

**Lazy-init rule.** `/tc:automate`, `/tc:run`, and any test-generating command must check `tests/playwright.config.ts`. If missing, call `/tc:build-framework` first and continue. Document this in `docs/user-guide/automation.md`.

**Framework structure.**

```
tests/
  e2e/
  pages/
  components/
  fixtures/
  utils/
playwright.config.ts
package.json
```

Test data is **not** under `tests/`. It is under `.test-commander/test-data/` and reached through fixtures.

**Automation suitability rubric.** business criticality, repeatability, determinism, setup complexity, UI stability, maintenance cost, bug detection value.

**Documentation.** `docs/user-guide/automation.md` — explains the lazy framework, the suitability rubric, and the data flow.

**Review step.**

- `agentic-playwright-automation:review-playwright-test` runs on generated tests.
- Test data files are referenced from at least one fixture; nothing inline.

**Test step.**

- A smoke spec runs against a local example app (brought up by the tester; not vendored) and passes.

**Definition of done.**

- Framework builds on demand, tests reference data via fixtures, suitability rubric is applied in the automation plan, review skill passes, user guide complete.

---

## Phase 7 — Execution, Evidence, and Quality Report

**Goal.** Run tests, collect evidence, maintain the live quality report.

**Implementation.**

- `/tc:run`, `/tc:analyze-results`, `/tc:report`, `/tc:quality-gate`
- Methodology: `quality-reporting.md`, `evidence-management.md`, `quality-gates.md`
- Templates: `quality-report-template.md`, `test-run-summary-template.md`, `quality-gate-template.md`, `evidence-summary-template.md`

**Skills authored.** `tc-run` (Playwright and Postman execution paths, failure triage), `tc-quality-report` (report + gate), `tc-evidence` (cross-cutting indexer invoked by `tc-run` and later by `tc-web`).

**Design references.** `agentic-playwright-automation:investigate-playwright-failure` (failure-triage rubric), `postman:run-collection` and `postman:test` (Postman execution patterns; we shell out to `postman` CLI directly).

**Run modes.** smoke, regression, feature-specific, failed-only, tagged.

**Evidence policy.**

- Screenshots: committed.
- Videos and traces: git-ignored by default; opt-in `git-lfs` documented.
- JSON/HTML reports: committed; referenced from the quality report.

**Quality report sections.** executive summary, coverage, requirements readiness, exploratory findings, automated regression status, known risks, known defects, open questions, automation health, flaky tests, evidence summary, traceability summary, recommendations, release readiness, recent changes.

**History.** Each `/tc:report` snapshots `current-quality-report.md` to `history/YYYY-MM-DD-HHmm.md` and commits.

**Documentation.** `docs/user-guide/running-tests.md`, `docs/user-guide/quality-report.md`.

**Review step.**

- A snapshot in `history/` is created and committed.
- Failed tests link to evidence; flaky tests are flagged.

**Test step.**

- Smoke run produces a complete report with all sections; quality gate returns PASS/WARN/FAIL on configured criteria.

**Definition of done.**

- Run + report + gate work end-to-end, history snapshots commit cleanly, evidence policy enforced, user guides complete.

---

## Phase 8 — Continuous Learning and Self-Improvement

**Goal.** Governed continuous improvement.

**Implementation.**

- `/tc:learn`, `/tc:learn-from-failures`, `/tc:learn-from-exploration`, `/tc:learn-from-feedback`, `/tc:review-lessons`, `/tc:promote-lessons`
- Methodology: `learning-loop.md`, `lesson-taxonomy.md`, `improvement-governance.md`, `commander-doctrine.md`, `anti-patterns.md`, `heuristics.md`
- Templates: `lesson-template.md`, `improvement-proposal-template.md`, `core-promotion-template.md`

**Skills authored.** `tc-learning` with six sub-commands plus the full methodology set (learning loop, lesson taxonomy, improvement governance, commander doctrine, anti-patterns, heuristics).

**Design references.** `superpowers:receiving-code-review` (lesson intake discipline), `superpowers:systematic-debugging` (root-cause learning from failures).

**Outputs.** Files under `.test-commander/learning/` as previously specified.

**Governance.** Candidate → review → accepted/rejected/needs-human-review → promote to project guidance or core improvement proposal. Test Commander **never silently rewrites** its own methodology, commands, or templates. It never modifies third-party installed skills (Q6 default).

**Documentation.** `docs/user-guide/learning-loop.md`.

**Review step.**

- Newly captured lessons are routed through `/tc:review-lessons` before promotion.
- Promotion writes are visible in git diff and require human approval.

**Test step.**

- Simulate a failure → run `/tc:learn-from-failures` → assert a candidate lesson lands in `lessons-inbox.md` with the expected fields.

**Definition of done.**

- All six commands work, governance flow enforced, principle "learns continuously, improves deliberately" reflected in code paths, user guide complete.

---

## Phase 9 — Visual Documentation and Infographics

**Goal.** Generate visual quality artifacts.

**Implementation.**

- `/tc:visualize`, `/tc:diagram-flow`, `/tc:diagram-sequence`, `/tc:diagram-state`, `/tc:diagram-risk`, `/tc:diagram-coverage`, `/tc:diagram-traceability`, `/tc:diagram-test-strategy`, `/tc:diagram-architecture`, `/tc:generate-infographic`, `/tc:render-visuals`
- Methodology: `visual-documentation.md`, `diagram-standards.md`, `infographic-standards.md`
- Templates: Mermaid templates per diagram type, infographic brief, infographic spec

**Skills authored.** `tc-visualize` covering all diagram commands plus infographic generation and headless rendering.

**Design references.** `frontend-design:frontend-design` (infographic layout patterns where richer visuals are required). Per Q12 default, we author Mermaid generation ourselves rather than wrapping a public diagram skill.

**Default format.** Mermaid Markdown. `/tc:render-visuals` runs Mermaid CLI (added by `make install` at this phase) to produce SVG/PNG.

**Rules.** Prefer Mermaid. Never invent flows or metrics. Every visual cites its source artifacts. Quality report links to relevant visuals.

**Documentation.** `docs/user-guide/visuals.md`.

**Review step.**

- Every committed visual passes a "sources cited" check.
- Rendered SVGs match the Mermaid source.

**Test step.**

- Generate one visual per supported type from a fixture workspace and assert presence + source citation.

**Definition of done.**

- All commands work, visuals are renderable, quality report links work, user guide complete.

---

## Phase 10 — Web Console MVP

**Goal.** Team-facing console for Test Commander.

**Implementation.** Next.js + FastAPI + SQLite + SSE + local-filesystem artifacts. Pages: Dashboard, Quality Report, Journal, Sessions, Requirements, Test Runs, Evidence, Chat, Settings. Realtime via SSE. Backend services for artifact indexing, command execution, journal, quality report.

Structure as previously specified under `apps/web/`, `apps/api/`, `runtime/`.

**Skills authored.** `tc-web` covering init/start/sync/index-artifacts/export, plus the artifact indexer and SSE event stream specs.

**Design references.** `web-scaffold:create-website` (Next.js + FastAPI scaffold structure), `frontend-design:frontend-design` (dashboard and infographic embedding patterns).

**Commands.** `/tc:web-init`, `/tc:web-start`, `/tc:web-sync`, `/tc:web-index-artifacts`, `/tc:web-export`.

**Chat (MVP).** Answers from indexed artifacts. Suggests Test Commander commands. Requires approval before file-modifying or test-running commands.

**Documentation.** `docs/user-guide/web-console.md`, `docs/web-console.md`, `docs/runtime-api.md`.

**Review step.**

- Pages render against a populated workspace; SSE updates appear on journal append; chat enforces the approval gate.

**Test step.**

- End-to-end: `make run` brings up the stack via docker compose; smoke navigations across all pages succeed.

**Definition of done.**

- All pages work, SSE delivers updates, indexer keeps up with workspace changes, chat enforces gating, user guide complete.

---

## Phase 11 — Runtime API and MCP Server

**Goal.** Expose Test Commander to other tools and agents.

**Implementation.** Expanded FastAPI Runtime API and a new MCP server at `apps/mcp/`. MCP tools as previously specified. Permission levels: read-only, safe-write, code-write, execute-tests, destructive — all enforced.

**Skills authored.** `tc-mcp` (server package and tool definitions).

**Design references.** `anthropic-skills:skill-creator` (MCP authoring patterns and tool-schema conventions).

**Documentation.** `docs/runtime-api.md`, `docs/mcp-server.md`, `docs/security-and-permissions.md`, `docs/user-guide/integrating.md`.

**Review step.**

- All MCP tools are exercised via a sample client.
- Permission gates are unit-tested.

**Test step.**

- Contract tests for every API route; MCP tool round-trip tests; security tests for destructive routes.

**Definition of done.**

- API and MCP routes work, permission gates enforced, contract tests pass, user guide complete.

---

## Phase 12 — Sandboxed Testing Environment

**Goal.** Launch a team-accessible Test Commander environment from GitHub Actions.

**Implementation.** Commands `/tc:sandbox-init`, `/tc:sandbox-launch`, `/tc:sandbox-status`, `/tc:sandbox-sync`, `/tc:sandbox-stop`, `/tc:sandbox-export`. Workflows under `.github/workflows/`. Provider abstraction at `sandbox/providers/`. Initial providers: docker-compose local, generic container host, Sprites-style placeholder.

**Skills authored.** `tc-sandbox` with provider abstraction. Initial providers per Q8 default: docker-compose plus stub adapters for a generic container host and a Sprites.dev placeholder.

**Design references.** Public devbox/sandbox skills (Coder, Daytona, Sprites.dev) — evaluated in Phase 0 per `docs/skill-evaluation.md`; design patterns may be borrowed.

**Safety.** Allowed target domains, blocked private network ranges by default, secret-scanning guidance, approvals for external targets and destructive commands, clear environment labels.

**Documentation.** `docs/sandboxed-environments.md`, `docs/github-actions-sandbox.md`, `docs/no-code-tester-workflow.md`, `docs/user-guide/sandbox.md`.

**Review step.**

- A sandbox launches against a sample target; endpoints publish to the PR comment; teardown is clean.

**Test step.**

- CI dry-run of the workflow with mocked provider; assert image build, env publish, and teardown sequencing.

**Definition of done.**

- Sandbox launches and tears down, safety guards in place, MVP limitations documented honestly.

---

## Phase 13 — Continuous Quality Agent Mode

**Goal.** Monitor application changes and propose quality updates.

**Implementation.** Commands `/tc:watch-changes`, `/tc:impact-analysis`, `/tc:coverage-gap-analysis`, `/tc:propose-tests`, `/tc:create-test-pr`, `/tc:continuous-quality-check`. Autonomy modes 0–4. Workflow `.github/workflows/test-commander-continuous-quality.yml` on `pull_request`, `push`, `schedule`, `workflow_dispatch`.

**Skills authored.** `tc-continuous-quality` with all six commands and the five autonomy-mode gates. Reuses `tc-run`'s failure-triage logic for impacted-test runs (no separate skill needed).

**Design references.** `agentic-playwright-automation:investigate-playwright-failure` (already informed `tc-run`; no additional reference here).

**Documentation.** `docs/continuous-quality-agent.md`, `docs/autonomy-levels.md`, `docs/governed-self-improvement.md`, `docs/user-guide/continuous-quality.md`.

**Review step.**

- Mode boundaries are enforced (mode 0 cannot open PRs, etc.).
- PRs opened by mode 3 are clearly labeled.

**Test step.**

- Simulate a PR with a code change; assert impact analysis identifies expected impacted features and proposes appropriate tests.

**Definition of done.**

- All modes implemented and tested, CI workflow stable, principles "autonomous where safe, human-governed where it matters" reflected, user guide complete.

---

## Capstone MVP Ordering

Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 10.

Story:

```
Initialize workspace
  -> Review requirements and stories
  -> Build project knowledge
  -> Explore the app
  -> Generate test ideas
  -> Generate BDD
  -> Build framework (lazy) and generate automation
  -> Run tests and collect evidence
  -> Publish quality report
  -> Capture lessons learned
  -> View everything in the web console
```

Then later: Phase 11 (API/MCP), Phase 12 (sandboxes), Phase 13 (continuous quality).

---

## Demo Command Sequence (after Phase 7)

```
/tc:init
/tc:review-requirements
/tc:learn-from-docs
/tc:learn-from-code
/tc:create-charter --area checkout
/tc:explore --target http://localhost:3000 --charter checkout
/tc:test-ideas --area checkout
/tc:generate-bdd --area checkout
/tc:automation-plan --area checkout
/tc:generate-test-data --area checkout
/tc:automate --feature checkout   # builds framework lazily if absent
/tc:run --suite smoke
/tc:analyze-results
/tc:report
/tc:learn
/tc:next
/tc:visualize --area checkout
```

---

## Roadmap Summary

| Phase | Name | Main Outcome |
| --- | --- | --- |
| 0 | Repo Foundation | Clean core repo, `make install`, skill verification |
| 1 | Workspace Model | `.test-commander/`, `/tc:init`, `/tc:status`, `/tc:journal`, `/tc:next` |
| 2 | Requirements Intelligence | Review requirements, stories, AC |
| 3 | Project Knowledge | Learn from docs, specs, code, API, tests |
| 4 | Exploratory Testing | Charters, sessions, observations, risks, ideas |
| 5 | BDD + Traceability | Generate scenarios and maps under `.test-commander/bdd/` |
| 6 | Playwright Automation | Lazy framework, strategic automation, test data outside code |
| 7 | Evidence + Reporting | Run tests, collect evidence, live report with committed history |
| 8 | Continuous Learning | Lessons and governed improvement |
| 9 | Visuals | Diagrams, risk maps, infographics |
| 10 | Web Console | Team-facing quality center |
| 11 | API/MCP | Tool and agent access |
| 12 | Sandboxes | GitHub Actions-launched QA workspaces |
| 13 | Continuous Quality Agent | Monitors change and proposes improvements |

---

## To Do

Phase-by-phase work items. Move to *Completed* as each lands.

### Phase 0
- [ ] Author `README.md`, `LICENSE` (MIT), `CONTRIBUTING.md`, `CHANGELOG.md`, `TODO.md`
- [ ] Author `bootstrap.sh` (POSIX, platform detection: macOS, Linux, WSL, Git Bash; prereq checks for make/python3.12/PDM/Docker/Git; suggested-install output for questionable tools; idempotent)
- [ ] Create `Makefile` with `install`, `lint`, `test`, `build`, `run`, `verify`
- [ ] Create `pyproject.toml` (PDM, `requires-python = ">=3.12"`) and `docker-compose.yml` placeholder
- [ ] Author `.claude-plugin/marketplace.json` (declares the local marketplace)
- [ ] Author `plugins/test-commander/.claude-plugin/plugin.json` (declares the plugin)
- [ ] Author `plugins/test-commander/README.md`, `plugins/test-commander/LICENSE`
- [ ] Author `plugins/test-commander/skills/tc-core/SKILL.md` (init/status/journal commands; defer `/tc:next` to Phase 1 per Q7)
- [ ] Stub `docs/` (vision, architecture, roadmap, methodology, command-reference, workspace-reference, glossary, install)
- [ ] Author `docs/user-guide/getting-started.md` and `docs/install.md` (per-platform; no-PowerShell note)
- [ ] Run the public-skill evaluation pass and write `docs/skill-evaluation.md` (Mermaid, devbox/sandbox, traceability-matrix, a11y, perf)
- [ ] Author `scripts/verify_skills.py` — verifies skills under `plugins/test-commander/skills/`
- [ ] Wire `make install` to register the local marketplace and install the plugin via `claude plugin` CLI; ensure idempotency
- [ ] Smoke-test on macOS and WSL; document Git Bash limitations
- [ ] Confirm review and test gates green

### Phase 1
- [ ] Extend `tc-core` with `/tc:next` heuristics (or split into `tc-next` if Q7 escalates)
- [ ] Implement `/tc:init`, `/tc:status`, `/tc:journal` behaviors under `tc-core/commands/`
- [ ] Build `templates/workspace/` master template
- [ ] Author `docs/user-guide/workflow.md`
- [ ] Update `docs/workspace-reference.md` and `docs/command-reference.md`
- [ ] Add `/tc:next` heuristics test harness
- [ ] Confirm review and test gates green

### Phase 2
- [ ] Author `/tc:review-requirements`, `/tc:review-user-stories`, `/tc:review-acceptance-criteria`, `/tc:requirements-coverage`, `/tc:requirements-to-tests`
- [ ] Author methodology and template files
- [ ] Build the seeded-flawed-requirements fixture
- [ ] Author `docs/user-guide/reviewing-requirements.md`
- [ ] Confirm review and test gates green

### Phase 3
- [ ] Author `/tc:learn-from-docs`, `/tc:learn-from-specs`, `/tc:learn-from-code`, `/tc:learn-from-api`, `/tc:learn-from-tests`
- [ ] Author methodology and templates
- [ ] Build seeded sample-repo fixture for knowledge extraction tests
- [ ] Author `docs/user-guide/building-project-knowledge.md`
- [ ] Confirm review and test gates green

### Phase 4
- [ ] Author `/tc:create-charter`, `/tc:explore`, `/tc:test-ideas`, `/tc:session-summary`
- [ ] Author methodology and templates
- [ ] Author `docs/user-guide/exploring-an-app.md`
- [ ] Wire `mcp-exploratory-testing:review-exploration` into the review gate
- [ ] Confirm review and test gates green

### Phase 5
- [ ] Author `/tc:generate-bdd`, `/tc:review-bdd`, `/tc:traceability-map`
- [ ] Move feature files to `.test-commander/bdd/features/`
- [ ] Author methodology and templates
- [ ] Author `docs/user-guide/generating-bdd.md`
- [ ] Confirm review and test gates green

### Phase 6
- [ ] Author `/tc:build-framework` (lazy), `/tc:automation-plan`, `/tc:automate`, `/tc:review-automation`, `/tc:generate-test-data`
- [ ] Wire the lazy-init check into commands that need the framework
- [ ] Author methodology and templates (TS templates)
- [ ] Author `docs/user-guide/automation.md`
- [ ] Confirm review and test gates green

### Phase 7
- [ ] Author `/tc:run`, `/tc:analyze-results`, `/tc:report`, `/tc:quality-gate`
- [ ] Implement history snapshot and commit flow
- [ ] Author methodology and templates
- [ ] Document evidence policy (commits vs lfs vs ignored)
- [ ] Author `docs/user-guide/running-tests.md` and `quality-report.md`
- [ ] Confirm review and test gates green

### Phase 8
- [ ] Author `/tc:learn`, `/tc:learn-from-failures`, `/tc:learn-from-exploration`, `/tc:learn-from-feedback`, `/tc:review-lessons`, `/tc:promote-lessons`
- [ ] Author methodology and templates
- [ ] Author `docs/user-guide/learning-loop.md`
- [ ] Confirm review and test gates green

### Phase 9
- [ ] Author all `/tc:diagram-*`, `/tc:visualize`, `/tc:generate-infographic`, `/tc:render-visuals`
- [ ] Add Mermaid CLI to `make install`
- [ ] Author methodology and templates
- [ ] Author `docs/user-guide/visuals.md`
- [ ] Confirm review and test gates green

### Phase 10
- [ ] Scaffold `apps/web/` and `apps/api/`
- [ ] Implement all MVP pages and the artifact indexer
- [ ] Implement SSE streams
- [ ] Implement chat with approval gating
- [ ] Author `docs/user-guide/web-console.md`, `docs/web-console.md`, `docs/runtime-api.md`
- [ ] Confirm review and test gates green

### Phase 11
- [ ] Expand FastAPI Runtime API
- [ ] Scaffold `apps/mcp/` and implement all MCP tools
- [ ] Implement and unit-test permission gates
- [ ] Author `docs/runtime-api.md`, `docs/mcp-server.md`, `docs/security-and-permissions.md`, `docs/user-guide/integrating.md`
- [ ] Confirm review and test gates green

### Phase 12
- [ ] Author sandbox commands and provider adapters
- [ ] Author GitHub Actions workflows
- [ ] Author safety guard configuration
- [ ] Author `docs/sandboxed-environments.md`, `docs/github-actions-sandbox.md`, `docs/no-code-tester-workflow.md`, `docs/user-guide/sandbox.md`
- [ ] Confirm review and test gates green

### Phase 13
- [ ] Author continuous-quality commands
- [ ] Implement autonomy mode gates
- [ ] Author the continuous-quality workflow
- [ ] Author `docs/continuous-quality-agent.md`, `docs/autonomy-levels.md`, `docs/governed-self-improvement.md`, `docs/user-guide/continuous-quality.md`
- [ ] Confirm review and test gates green

---

## Completed

Move To Do items here as phases finish, with date and short note.

_(empty)_

---

## Project Conventions

These apply across every phase.

- Work incrementally. Small, simple steps. Validate each step with tests before moving on.
- Use the latest APIs and libraries available as of the build date.
- Python: PDM as the package manager.
- Provide Make targets: `install`, `lint`, `test`, `build`, `run`, `verify`.
- `make run` brings up the local stack via `docker compose` where applicable.
- Databases and system-level tools run via Docker locally.
- No Python virtualenv inside containers unless multiple Python apps clearly conflict.
- No emojis anywhere — code, logs, UI, docs. Standard technical writing only.
- README stays under 400 lines. Link out to deeper docs.
- Maintain `CHANGELOG.md` and `TODO.md`.
- Root-cause-first debugging: reproduce, isolate with a failing test, fix, document prevention in `docs/` or `CLAUDE.md` so the same problem cannot recur.
- DRY. Short modules, classes, methods. Clear names over comments.
- No over-engineering. No defensive programming. Exception handlers only when justified.
- Test data lives under `.test-commander/test-data/`, never inline in test code, regenerable via `/tc:generate-test-data`.
- Quality-report history is committed.
- Every Test Commander skill is owned in-repo under `.claude/skills/test-commander/`. No runtime dependency on external skill plugins.
