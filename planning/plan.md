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
    - Once all prereqs are present, prints `Next step: make install` and exits 0. Does not run `make install` itself — keeps verify and install as separate concerns.
    - Is idempotent: re-running detects what's already installed and does nothing for those.
    - Does not write a `make` shim or modify PATH in destructive ways.
    - Supports `--help` for usage; otherwise verifies unconditionally.

15. **Runtime topology: three patterns, MVP locks to A with B opt-in.** Test Commander has three runtime roles — orchestrator (the brain), test runtime (Playwright/Postman/etc.), and viewer (web console). These can be deployed in three patterns:
    - **Pattern A — Local-first.** Claude Code runs on the user's laptop. Docker hosts auxiliary services and the viewer for local dev. No Claude in the cloud. **This is the MVP default.**
    - **Pattern B — Headless Claude in CI.** GitHub Actions runs Claude Code with an API token. Single-tenant per token. **Opt-in for Phase 13 continuous quality only.**
    - **Pattern C — Anthropic API via Agent SDK.** Backend calls the API directly; multi-tenant SaaS. **Deferred past v1.**
    Docker is for auxiliary services (databases) and the viewer/test-runtime, never for the orchestrator. See *Runtime Topology* section.

16. **Frontend users drive Test Commander workflows, not raw Claude Code.** Any UI that fronts the orchestrator must route every request through the controlled execution pipeline introduced in Phase 10.5: intent router → command planner → permission policy → approval gate → bounded execution → artifact capture → diff validation → audit log. The web console is never a raw Claude terminal in a browser. This rule applies to Phase 10, 10.5, 11, 12, and 13 without exception.

17. **Plan steps use the `claude` CLI, not interactive slash commands.** The Claude Code `/plugin`, `/skill`, etc. slash commands may be unavailable in some sessions (headless, CI, certain editor environments). Every plan step that validates, installs, lists, or removes plugins or skills uses the equivalent `claude plugin ...` CLI subcommands. Slash commands remain valid for ad-hoc interactive use, but the canonical, scriptable, environment-independent path is the CLI. Discovered during Step 0.5 when `/plugin marketplace add` returned "isn't available in this environment" while `claude plugin marketplace add` worked. Specifically the plan favors:
    - `claude plugin validate <path>` for manifest schema checks (run before install).
    - `claude plugin marketplace add <path>` and `claude plugin marketplace list`.
    - `claude plugin install <name>@<marketplace>`, `claude plugin list`, `claude plugin details <name>`.
    - `claude plugin uninstall <name>` for teardown.

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
| Q13 | Default policy for `safe-write` actions: always approve, always prompt, or configurable per deployment? | Phase 10.5 | Configurable per deployment, default to "always prompt" so single-user installs do not surprise the operator. |
| Q14 | Role assignment in a single-user local install vs multi-user deployment? | Phase 10.5 | Single-user local default: caller is `Admin`. Multi-user: requires explicit identity provider integration; not in v1. |

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
| `tc-governance` | Phase 10.5 | (templates and policy schemas; invoked by runtime, not user commands) | (none — novel layer) |
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

## Runtime Topology

Test Commander has three runtime roles. Each can be deployed in different ways. This section names them, locks the MVP target, and constrains every later phase.

### Three roles

| Role | What it does | Where it can run |
| --- | --- | --- |
| Orchestrator | Reads workspace, generates BDD, decides what to automate, drafts the quality report | Claude (desktop Claude Code or Anthropic API) |
| Test runtime | Executes Playwright tests, runs Postman collections, collects evidence | Node.js + browsers, locally or containerized |
| Viewer | Renders workspace artifacts as a team-accessible dashboard | FastAPI + Next.js + Postgres |

### Three deployment patterns

- **Pattern A — Local-first (MVP default).** Orchestrator is the user's local Claude Code. Workspace files live in the consuming project's git. Docker hosts auxiliary services (Postgres, the viewer, optional containerized Playwright) on the same machine. The team sees results by reading committed workspace files or by running the viewer themselves. No Claude in the cloud. Cheap, simple, no API billing.
- **Pattern B — Headless Claude in CI (opt-in for Phase 13).** A GitHub Actions runner installs Claude Code in headless mode with an Anthropic API token stored as a CI secret. Used for the continuous quality agent. Single-tenant per token; usage bills to that account.
- **Pattern C — Anthropic API via Agent SDK (deferred past v1).** Backend invokes the Anthropic API directly using the Agent SDK. Skills are loaded by the SDK at runtime. Real multi-tenant SaaS. Major rearchitecture; not in scope until Phase 14+.

### What Docker is for

Docker hosts the **test runtime** and the **viewer** (and their auxiliary services). Docker does not host the **orchestrator**. The compose stack grows per phase:

| Phase | Compose service added |
| --- | --- |
| 6 | Optional `playwright` for reproducible browsers |
| 10 | `db` (Postgres), `api` (FastAPI), `web` (Next.js) |
| 11 | `mcp` (MCP server) |
| 12 | The same stack, deployed to a sandbox provider |

### Frontend never drives raw Claude

The web console (Phase 10) and every later UI route requests through the controlled execution pipeline defined in Phase 10.5. There is no raw Claude prompt in a browser. See Decision D16.

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
- Once all prerequisites are present, prints `Next step: make install` and exits 0. The user runs `make install` explicitly; bootstrap and install stay separate.

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
  policy/                  # phase 10.5
    permissions.yaml
    approvals.yaml
  audit/                   # phase 10.5
    actions.jsonl
    approvals/
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

**Tooling rule (Decision D17).** Any phase step that touches plugins, marketplaces, or installed skills uses the `claude plugin ...` CLI, never `/plugin` slash commands. The CLI is available in every Claude Code environment; slash commands are not. Validate manifests with `claude plugin validate` before any install or marketplace registration — schema problems are far cheaper to fix before install state is created.

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

Six sub-steps. Test-first: write the scaffold-validation tests before the artifacts so red turns green deliberately. Sub-steps 0.5.1–0.5.4 run in parallel; 0.5.5 after them; 0.5.6 last.

##### 0.5.1 — Marketplace manifest
- **Deliverables.** `.claude-plugin/marketplace.json`.
- **Content.** `$schema` pointing at the Anthropic marketplace schema; `name: "test-commander-marketplace"`; `description`; `owner` (name + email); `plugins` array with one entry referencing `plugins/test-commander/`.
- **Definition of done.** Valid JSON; field shape mirrors `~/.claude/plugins/marketplaces/claude-plugins-official/.claude-plugin/marketplace.json`.

##### 0.5.2 — Plugin manifest
- **Deliverables.** `plugins/test-commander/.claude-plugin/plugin.json`.
- **Content.** `name: "test-commander"`, `description`, `version: "0.0.0"` (matches `pyproject.toml`), `author` (name + email), optional `homepage` / `repository`.
- **Definition of done.** Valid JSON; field shape mirrors `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/.claude-plugin/plugin.json`.

##### 0.5.3 — Plugin metadata
- **Deliverables.** `plugins/test-commander/LICENSE` (MIT, mirrors the repo LICENSE) and `plugins/test-commander/README.md` (under 100 lines; what the plugin is, what skills it ships now, what arrives later, link back to repo root).
- **Definition of done.** Both files exist; no broken links.

##### 0.5.4 — tc-core skill
- **Deliverables.** `plugins/test-commander/skills/tc-core/SKILL.md`.
- **Content.** YAML frontmatter (`name: tc-core`, single-line `description` written as a trigger statement). Body describes `/tc:init`, `/tc:status`, `/tc:journal` and notes that command behavior arrives in Phase 1. `/tc:next` mentioned only as a Phase 1 follow-up (per Q7).
- **Definition of done.** Frontmatter parses; `name` kebab-case; `description` non-empty; body references the three commands; no `commands/` files yet.

##### 0.5.5 — Structural sanity check + manifest schema validation
- **Deliverables.** No new files. Run:
  - `make verify` — confirms `tests/test_plugin_scaffold.py` turns green.
  - `claude plugin validate <repo-root>` — schema-validates `marketplace.json` against the published Claude Code marketplace schema.
  - `claude plugin validate <repo-root>/plugins/test-commander` — schema-validates `plugin.json` against the plugin schema.
- **Definition of done.** `make verify` clean; both `claude plugin validate` invocations print `✔ Validation passed`. If either validate fails, iterate on the manifest before continuing to 0.5.6 — fixing schema problems before the install step is much faster than fixing them after.

##### 0.5.6 — CLI install (no slash commands)
- **Deliverables.** None. Verification only.
- **Commands.** Run from the repo root:
  ```sh
  claude plugin marketplace add "$PWD"
  claude plugin install test-commander@test-commander-marketplace
  claude plugin list
  claude plugin details test-commander
  ```
- **Why CLI.** Per Decision D17, slash commands like `/plugin marketplace add` may be unavailable in some Claude Code sessions. The `claude plugin ...` CLI works in every environment, is scriptable, and is what `make install` will wire up in Step 0.7.
- **Definition of done.**
  - `claude plugin marketplace add` prints `✔ Successfully added marketplace: test-commander-marketplace`.
  - `claude plugin install` prints `✔ Successfully installed plugin: test-commander@test-commander-marketplace`.
  - `claude plugin list` includes `test-commander@test-commander-marketplace`.
  - `claude plugin details test-commander` lists `tc-core` under `Skills (1)`.
  - `~/.claude/plugins/installed_plugins.json` has a `test-commander@test-commander-marketplace` entry.

##### Pre-flight tests

Before 0.5.1 begins, `tests/test_plugin_scaffold.py` lands red. It asserts every automated DoD item below. The implementation steps turn it green.

##### Definition of done — consolidated 10 checks

Eight automated; two interactive. The interactive checks gate 0.5.6.

| # | Check | Type | How |
| --- | --- | --- | --- |
| 1 | All five artifact paths exist | auto | `pytest` file-existence assertions |
| 2 | `.claude-plugin/marketplace.json` parses as JSON | auto | `json.load` in pytest |
| 3 | `marketplace.json` lists `test-commander` as a plugin | auto | pytest |
| 4 | `plugins/test-commander/.claude-plugin/plugin.json` parses | auto | pytest |
| 5 | `plugin.json` has expected fields (`name`, `description`, `version`) | auto | pytest |
| 6 | `tc-core/SKILL.md` has valid YAML frontmatter with `name` and `description` | auto | regex parse in pytest |
| 7 | `SKILL.md` body references `/tc:init`, `/tc:status`, `/tc:journal` | auto | grep-style assertion |
| 8 | No command behavior implemented yet | auto | `commands/` absent or empty |
| 9 | Marketplace + plugin install succeed without error | CLI | `claude plugin marketplace add` + `claude plugin install` both print success; `installed_plugins.json` has the entry |
| 10 | `tc-core` appears in skill inventory; no load errors | CLI | `claude plugin details test-commander` lists `tc-core` under `Skills (1)` |

##### Validation sequence

1. Write `tests/test_plugin_scaffold.py`. Run `make test` — expect failures for every Step 0.5 deliverable.
2. Author 0.5.1–0.5.4 in parallel.
3. Run `make verify` — automated checks 1–8 turn green.
4. Run `claude plugin validate <repo-root>` and `claude plugin validate <repo-root>/plugins/test-commander` — both must print `✔ Validation passed`. If either fails, iterate on the manifest before continuing.
5. Run `claude plugin marketplace add "$PWD"` from the repo root.
6. Run `claude plugin install test-commander@test-commander-marketplace`.
7. Run `claude plugin list` and `claude plugin details test-commander` — confirm install and skill inventory.
8. Read `~/.claude/plugins/installed_plugins.json` and confirm the entry.
9. If any of 4–8 fail, iterate on the manifest until accepted.

##### Failure modes

- Wrong/missing `source` shape for a local plugin in `marketplace.json`. **Mitigation:** the correct shape is a relative string like `"./plugins/<name>"` (confirmed against the on-disk `~/.claude/plugins/marketplaces/marketplace/.claude-plugin/marketplace.json`). `claude plugin validate` catches this before install.
- Required field present in the schema but missing from the manifest. **Mitigation:** `claude plugin validate` reports the specific field. Iterate, re-validate.
- `description` triggers the skill too broadly or too narrowly. **Mitigation:** iterate on wording; no rebuild required.
- Plugin install fails after a previous failed attempt left stale state. **Mitigation:** `claude plugin uninstall test-commander` then re-install.
- Slash commands (`/plugin marketplace add`, `/plugin install`) unavailable in the session. **Mitigation:** per Decision D17, the plan uses `claude plugin ...` CLI subcommands, which work in every environment. Do not fall back to slash commands.

#### 0.6 — Skill verifier

Seven sub-steps. Test-first: the pytest suite lands red before the script. Sub-steps 0.6.1–0.6.4 can be authored in one pass (one file); 0.6.5 is the parallel test file; 0.6.6 wires `make verify`; 0.6.7 is the live drill.

##### 0.6.1 — Expected-skill catalog
- **Deliverables.** A module-level constant in `scripts/verify_skills.py` mapping every TC-owned skill name to the phase that creates it. Sourced from the *TC-Owned Skill Catalog* table earlier in this plan.
- **Definition of done.** Catalog contains an entry for every skill the plan declares (currently 20). Phase numbers match the plan's catalog.
- **Review.** Side-by-side diff against the plan's catalog table during code review.

##### 0.6.2 — Frontmatter parser and validator
- **Deliverables.** A pure function `parse_frontmatter(skill_md_path) -> ParseResult` that extracts the leading `---...---` YAML block. No PyYAML dependency; regex parsing only (same approach as `tests/test_plugin_scaffold.py`).
- **Validation rules.**
  - `name` field present.
  - `name` matches the parent directory name.
  - `name` is kebab-case (`^[a-z][a-z0-9-]*$`).
  - `description` field present and non-empty after `strip()`.
- **Definition of done.** Returns a `ParseResult` with one of: `ok`, `malformed(reason)`. Pure; no I/O outside the file read.

##### 0.6.3 — Walker and phase filter
- **Deliverables.** A function that, given the catalog and an optional `phase_cap: int`, walks `plugins/test-commander/skills/*/SKILL.md` and returns a `dict[str, Status]` where `Status` is `PRESENT | MISSING | MALFORMED | UNEXPECTED`.
- **Behavior.**
  - For each expected skill (with `phase <= phase_cap`, default = unbounded): check directory + SKILL.md existence; parse; classify.
  - For each on-disk skill not in the catalog: report `UNEXPECTED` (warn only — does not fail the run).
- **Definition of done.** Deterministic for a given workspace state; testable with fixture directories.

##### 0.6.4 — Reporter and exit code
- **Deliverables.** A CLI entry point in `scripts/verify_skills.py` (`if __name__ == "__main__"`). Supports `--phase N` and `--help`. Default phase cap: unbounded (verify everything authored so far).
- **Output format.** One line per checked skill, aligned: `skill-name        PRESENT (phase N)`. Summary footer with counts and overall verdict.
- **Exit code.** `0` if every expected skill is `PRESENT` and no `MALFORMED` exists. `1` otherwise. `UNEXPECTED` does not affect the exit code (warn only).
- **Definition of done.** Matches the documented contract; output is grep-friendly.

##### 0.6.5 — Pre-flight tests
- **Deliverables.** `tests/test_verify_skills.py`.
- **Coverage.** One test per DoD assertion (see table below): valid frontmatter, four MALFORMED variants, MISSING, UNEXPECTED, phase filter, exit codes, live tc-core PRESENT.
- **Fixture pattern.** `tmp_path` per test; each test materializes a tiny synthetic `plugins/test-commander/skills/<name>/SKILL.md` and points the verifier at it.
- **Definition of done.** Suite is red before 0.6.4 is written; green after.

##### 0.6.6 — Wire into `make verify`
- **Deliverables.** Update `Makefile` so the `verify` target runs `pdm run python3 scripts/verify_skills.py` after `lint` and `test`, before `check_links.py`. Order matters: catch skill drift before chasing link errors.
- **Definition of done.** `make verify` prints the per-skill report; exits 0 when state is good; non-zero (and stops the chain) when a skill is `MALFORMED` or `MISSING`.

##### 0.6.7 — Live drill
- **Deliverables.** No new files. Validation only.
- **Drills.**
  1. `python3 scripts/verify_skills.py` (no flags) — expect `tc-core PRESENT`, exit 0.
  2. `python3 scripts/verify_skills.py --phase 0` — expect `tc-core PRESENT`, exit 0.
  3. `python3 scripts/verify_skills.py --phase 2` — expect `tc-core PRESENT` and `tc-requirements MISSING`, exit 1.
  4. Temporarily strip the `description:` line from `tc-core/SKILL.md`. Re-run — expect `tc-core MALFORMED`, exit 1. Restore the file.
  5. Temporarily rename the `tc-core` directory to `_tc-core-tmp`. Re-run — expect `tc-core MISSING`, exit 1. Restore.
- **Definition of done.** Every drill matches expectations exactly.

##### Definition of done — consolidated 12 checks

Ten automated; two manual (the Makefile wiring and the live drill).

| # | Check | Type | How |
| --- | --- | --- | --- |
| 1 | `scripts/verify_skills.py` exists | auto | pytest file-existence |
| 2 | Frontmatter parser extracts `name` and `description` from a valid SKILL.md | auto | pytest with fixture |
| 3 | MALFORMED flagged when `name` is missing | auto | pytest with fixture |
| 4 | MALFORMED flagged when `description` is missing or empty | auto | pytest |
| 5 | MALFORMED flagged when `name` is not kebab-case | auto | pytest |
| 6 | MALFORMED flagged when `name` does not match the directory | auto | pytest |
| 7 | MISSING flagged when an expected skill directory is absent | auto | pytest |
| 8 | `--phase N` restricts the expected skill set to skills with `phase <= N` | auto | pytest |
| 9 | Exit code `0` when all expected skills are PRESENT | auto | pytest |
| 10 | Exit code non-zero on any MALFORMED or MISSING | auto | pytest |
| 11 | `make verify` invokes the verifier between `test` and `check_links` | manual | inspect Makefile, run `make verify` |
| 12 | Live drills (0.6.7) all match expected output and exit codes | manual | run the five drills |

##### Validation sequence

1. Write `tests/test_verify_skills.py`. Run `make test` — expect failures for every assertion.
2. Author 0.6.1–0.6.4 in `scripts/verify_skills.py`.
3. Run `make test` — green.
4. Update `Makefile` per 0.6.6. Run `make verify` — confirm the verifier is invoked between `test` and `check_links`.
5. Run drills 1 and 2 (0.6.7). Confirm output and exit codes.
6. Run drill 3 — confirm phase filter behavior.
7. Run drill 4 with a temporary frontmatter corruption — confirm MALFORMED. Restore.
8. Run drill 5 with a temporary directory rename — confirm MISSING. Restore.
9. Final `make verify` clean.

##### Failure modes

- YAML parser edge cases (multi-line values, quoted strings). **Mitigation:** Phase 0 needs only `name` and `description` on single lines. Document the assumption in the parser; revisit when a later skill needs multi-line frontmatter.
- Skill directory exists but no `SKILL.md` inside. **Mitigation:** Treat as MALFORMED with reason `"missing SKILL.md"`.
- `SKILL.md` exists but is empty. **Mitigation:** Treat as MALFORMED with reason `"empty frontmatter"`.
- Catalog drift between `verify_skills.py` and the plan's catalog table. **Mitigation:** Code review catches it; we do not write a brittle parser of the plan's Markdown table. Document the catalog as "kept in sync with `planning/plan.md` by code review."
- Unexpected skill directory authored ahead of its phase. **Mitigation:** Reported as `UNEXPECTED` (warn only, exit 0). Useful when scaffolding ahead of schedule.

#### 0.7 — `make install` wiring

Seven sub-steps. Test-first: the Makefile pre-flight tests land red before the targets exist. Sub-step 0.7.7 is an explicit DoD evaluation that captures evidence of success.

##### 0.7.1 — Manifest validation target
- **Deliverables.** A `validate-manifests` Make target that runs `claude plugin validate` against both the marketplace root and the plugin root.
- **Behavior.** Aborts on any validation failure. Runs **before** any state-changing step in `install` so schema errors are caught before marketplace registration.
- **Definition of done.** `make validate-manifests` exits 0 today and prints both `✔ Validation passed` lines.

##### 0.7.2 — Marketplace registration target (idempotent)
- **Deliverables.** A `marketplace-add` Make target.
- **Behavior.** Inspects `claude plugin marketplace list`; if `test-commander-marketplace` is absent, runs `claude plugin marketplace add "$PWD"`; if present, no-op.
- **Definition of done.** First invocation registers; second invocation is a clean no-op (no error, no duplicate entry in `~/.claude/plugins/known_marketplaces.json`).

##### 0.7.3 — Plugin install target (idempotent)
- **Deliverables.** A `plugin-install` Make target.
- **Behavior.** Inspects `claude plugin list`; if `test-commander` is absent, runs `claude plugin install test-commander@test-commander-marketplace`; if present, no-op.
- **Definition of done.** First invocation installs; second invocation is a clean no-op (no error, no duplicate entry in `~/.claude/plugins/installed_plugins.json`).

##### 0.7.4 — Wire `install` and add `uninstall`
- **Deliverables.** Updated `Makefile`. New target dependency chain:
  ```
  install: pdm-install validate-manifests marketplace-add plugin-install verify-skills
  ```
  Each step is its own target. A new `uninstall` target reverses the install (`claude plugin uninstall test-commander` then `claude plugin marketplace remove test-commander-marketplace`); both prefixed with `-` so partial state cleans up.
- **Definition of done.** `make install` runs the chain in order; `make uninstall` removes both registrations without erroring on already-clean state. `make help` lists both new targets.

##### 0.7.5 — Pre-flight tests
- **Deliverables.** `tests/test_make_install.py`.
- **Coverage.** Each test maps to one DoD assertion below.
  - Static: required targets exist (`install`, `uninstall`, `validate-manifests`, `marketplace-add`, `plugin-install`, `verify-skills`).
  - Static: `install` depends on those targets in the documented order (parse `make -n install` dry-run output).
  - Idempotency markers: `marketplace-add` and `plugin-install` both check existence before invoking the CLI.
  - PATH probe: `claude` binary is on `$PATH` (xfail-style note if not, since CI without Claude Code can't run the dynamic test).
- **Note.** A live end-to-end test belongs in 0.7.7, not here — it has side effects on the developer's installed plugins.
- **Definition of done.** Suite is red before 0.7.1–0.7.4 land; green after.

##### 0.7.6 — Documentation
- **Deliverables.**
  - Update `docs/install.md` so the "what `make install` does" list matches the new five-target chain exactly. Add a one-line "How to uninstall: `make uninstall`" subsection.
  - Update `docs/user-guide/getting-started.md` step 3 to mention that re-running `make install` is safe (idempotent).
  - Update `plugins/test-commander/README.md` "Install" section so the order matches reality.
  - Add a troubleshooting entry to `docs/install.md`: "claude plugin install fails with `already installed`" — mitigation: run `make uninstall` then `make install`, or re-run `make install` (idempotent path should handle it cleanly).
- **Definition of done.** Each user-facing doc accurately reflects the implementation. `make verify` (link check included) clean.

##### 0.7.7 — Final DoD evaluation (proof of success)

An explicit end-to-end drill that produces evidence the install actually works. Output captured to a temp log; not committed.

- **Procedure.**
  1. Snapshot state before: `claude plugin marketplace list` and `claude plugin list`.
  2. `make uninstall` to reach a known-clean state.
  3. Confirm clean: marketplace and plugin both absent.
  4. `make install` — capture full stdout/stderr to `/tmp/tc-install-fresh.log`.
  5. Confirm presence: `claude plugin marketplace list` shows `test-commander-marketplace`; `claude plugin list` shows `test-commander@test-commander-marketplace`; `claude plugin details test-commander` lists `tc-core` under `Skills (1)`; `scripts/verify_skills.py` reports `OK`.
  6. `make install` again — capture to `/tmp/tc-install-rerun.log`.
  7. Confirm idempotency: no errors; no duplicates; the same final state.
  8. (Optional) `make uninstall` then `make install` once more to fully reset to a known good state.
- **Evidence.** The two log files plus the JSON-state snapshots. Pasted into the commit message as proof; not committed to the repo.
- **Definition of done.** Every numbered step above completes as described, with no unexpected output.

##### Definition of done — consolidated 12 checks

Eight automated, four evidence-based.

| # | Check | Type | How |
| --- | --- | --- | --- |
| 1 | `validate-manifests` target exists and runs `claude plugin validate` on both manifests | auto | Makefile parse + `make -n validate-manifests` |
| 2 | `marketplace-add` target exists and is idempotent | auto | pytest checks existence-then-add pattern |
| 3 | `plugin-install` target exists and is idempotent | auto | pytest checks existence-then-install pattern |
| 4 | `install` depends on the documented chain in order | auto | parse `make -n install` output |
| 5 | `uninstall` target exists and tolerates already-clean state | auto | pytest checks `-` prefix on commands |
| 6 | `make help` lists all new targets | auto | grep `make help` output |
| 7 | All Makefile tests in `tests/test_make_install.py` pass | auto | `make test` |
| 8 | `make verify` chain still clean | auto | `make verify` |
| 9 | Live fresh install: `make uninstall` then `make install` succeeds and leaves the system in the expected state | evidence | 0.7.7 captured log |
| 10 | Live idempotent re-run: second `make install` produces no error and no duplicates | evidence | 0.7.7 captured log + state-snapshot diff |
| 11 | All user-facing docs match the implementation | evidence | code review against the chain |
| 12 | Troubleshooting entry for "already installed" present and accurate | evidence | code review |

##### Validation sequence

1. Write `tests/test_make_install.py`. Run `make test` — expect failures.
2. Author 0.7.1–0.7.3 (the three sub-targets).
3. Author 0.7.4 (wire `install`, add `uninstall`, update `help`).
4. Run `make test` — expect green for the Makefile tests.
5. Update docs (0.7.6). Run `make verify` — link check must remain clean.
6. Run 0.7.7 end-to-end. Capture both logs. Confirm each numbered step.
7. Re-run `make verify` once more for a clean final state.
8. If 0.7.7 surfaces any unexpected behavior, iterate on 0.7.2/0.7.3 and re-run.

##### Failure modes

- `claude plugin marketplace add` errors when the marketplace is already registered. **Mitigation:** the idempotency guard in `marketplace-add` checks `marketplace list` first; if hit anyway, run `make uninstall` to clean state.
- `claude plugin install` errors when the plugin is already installed. **Mitigation:** same guard pattern in `plugin-install`; `make uninstall` as fallback.
- `claude` binary missing from `$PATH`. **Mitigation:** the Makefile probes early and prints a one-line install hint pointing at the bootstrap script.
- Schema validation passes but install fails. **Mitigation:** `claude plugin validate` runs first; if install still fails, the captured log identifies which step erred. Iterate on the manifest.
- Stale marketplace cache after manifest change. **Mitigation:** `make uninstall` then `make install` forces a re-read; document in the new troubleshooting entry.
- `~/.claude/plugins/installed_plugins.json` corruption or unexpected scope. **Mitigation:** `claude plugin list` is the source of truth, not the JSON; the targets read from the CLI, not the JSON.

#### 0.8 — Public-skill evaluation

Five sub-steps. Research + write-up + cross-reference. Two hours of work, not two days.

##### 0.8.1 — Catalog scan
- **Deliverables.** Scratch list of plausible plugin candidates per category, with URLs.
- **Source order.** First pass: grep `~/.claude/plugins/plugin-catalog-cache.json` for hits. Fallback: targeted WebFetch on the Anthropic plugin marketplace if the cache has no clear match.
- **Categories.** Mermaid/diagram, devbox/sandbox (Coder, Daytona, Sprites.dev), traceability-matrix, accessibility-testing, performance-testing.
- **Definition of done.** Every category has either a named candidate or an explicit "no clear match" note.

##### 0.8.2 — Per-candidate evaluation
- **Deliverables.** Five draft paragraphs, one per category.
- **Required fields per paragraph.** What it does / Why interesting for Test Commander / Decision (adopt as design reference / pass / defer, with reason) / Link if available.
- **Definition of done.** Five paragraphs in draft, each addressing all four fields, each no longer than five sentences.

##### 0.8.3 — Author `docs/skill-evaluation.md` and fold-back any plan deltas
- **Deliverables.** `docs/skill-evaluation.md`, under 100 lines. Header explains purpose, when it was written (Phase 0), and that it informs the TC-Owned Skill Catalog and Open Questions Q1 and Q12.
- **Plan fold-back.** If any candidate's adopt-decision contradicts a current plan decision (e.g., changes Q12's "build our own Mermaid" default), update `planning/plan.md` in the same commit. Same-commit rule keeps the plan and the evaluation consistent.
- **Definition of done.** Doc exists, under 100 lines, all five candidates covered, plan deltas (if any) applied.

##### 0.8.4 — Pre-flight tests, cross-links, and verify
- **Deliverables.** `tests/test_skill_evaluation.py`. Asserts the doc exists, has one section per category, each section contains all four required fields, and the file is under 100 lines.
- **Cross-links.** Add a link to the evaluation doc from `docs/methodology.md` and from the README's documentation index.
- **Definition of done.** Test suite green. `make verify` clean (link check covers the new doc and its cross-links).

##### 0.8.5 — Final DoD evaluation
- **Procedure.** Read the doc end to end. For each "adopt as design reference" decision, confirm the corresponding row in the TC-Owned Skill Catalog cites the reference (e.g., `tc-visualize` row cites an adopted Mermaid skill). If any new question emerged during research, ensure it landed in the Open Questions table.
- **Definition of done.** Single read-through confirms every decision is actionable, every adoption is reflected in the skill catalog, and no question was lost.

##### Definition of done — consolidated 10 checks

Six automated, four code-review.

| # | Check | Type | How |
| --- | --- | --- | --- |
| 1 | `docs/skill-evaluation.md` exists | auto | pytest |
| 2 | All five categories present | auto | pytest grep on section headers |
| 3 | Each section has all four fields (what / why / decision / link) | auto | pytest |
| 4 | File under 100 lines | auto | pytest |
| 5 | All links resolve | auto | `scripts/check_links.py` |
| 6 | `make verify` chain clean | auto | full chain |
| 7 | Cross-links from `docs/methodology.md` and README present | manual | code review |
| 8 | Every "adopt" decision shows up in the TC-Owned Skill Catalog row | manual | code review |
| 9 | Any plan-affecting decision folded back into `planning/plan.md` in the same commit | manual | git diff review |
| 10 | Any new question added to Open Questions (Q13+) | manual | grep plan |

##### Validation sequence

1. Scan the marketplace catalog cache (0.8.1).
2. Draft per-candidate writeups (0.8.2).
3. Synthesize the doc and fold-back any plan deltas (0.8.3).
4. Author the pre-flight test and the cross-links; run `make verify` (0.8.4).
5. Final read-through (0.8.5).
6. Update CHANGELOG, commit, push.

##### Failure modes

- Catalog cache is stale or empty. **Mitigation:** fall back to WebFetch of the Anthropic plugin marketplace; document the fallback in the doc.
- No clear match in a category. **Mitigation:** explicitly write "no clear match found" with a one-line search summary. Not a blocker.
- Doc grows past one page. **Mitigation:** tighten paragraphs; split into per-category subdocs only if absolutely necessary.
- Adopt-decision contradicts a prior plan decision. **Mitigation:** fold the change into `planning/plan.md` in the same commit so plan and evaluation never disagree.
- Candidate is dramatically better than what we can author. **Mitigation:** that is a question, not a unilateral pivot. Raise it as an Open Question; D1 (vendor-and-own) is not bypassed without explicit reconsideration.

#### 0.9 — Smoke test and Phase 0 sign-off

Six sub-steps. Verification + documentation + ceremony. The final sub-step is the explicit DoD evaluation that closes Phase 0 with evidence and a git tag.

##### 0.9.1 — Cold-user smoke test of getting-started.md
- **Deliverables.** A captured log of an end-to-end walkthrough of `docs/user-guide/getting-started.md`. Reach a clean state via `make uninstall`, then follow each numbered step in the guide verbatim.
- **Steps executed (verbatim from the guide).**
  1. Clone the repository (skip if already cloned; document the equivalence).
  2. `./bootstrap.sh` — should pass on this machine.
  3. `make install` — full five-step chain succeeds end to end.
  4. Confirm the plugin loaded — `claude plugin list` shows `test-commander@test-commander-marketplace`; `claude plugin details test-commander` lists `tc-core` under `Skills (1)`.
- **Definition of done.** Each numbered step succeeds. Output captured to `/tmp/tc-phase0-walkthrough.log`. If any step fails, fix the cause and re-run before continuing to 0.9.2.

##### 0.9.2 — Per-step DoD audit
- **Deliverables.** A line-by-line audit of every Step 0.1 through 0.8 against its DoD list in this plan.
- **What to check for each step.** Every DoD item green; every test in the step's pytest file passes; every deliverable present on disk; every cross-link resolves; every Failure Mode has its mitigation in place.
- **Definition of done.** All eight prior steps' DoD lists pass with no exceptions. Any unmet item is a blocker — fix it before continuing.

##### 0.9.3 — Plan and CHANGELOG updates
- **Deliverables.**
  - `planning/plan.md` — replace the `### Phase 0` To Do sub-section with a single line: `Phase 0 complete (YYYY-MM-DD) — see Completed`. Move the nine Phase 0 To Do items into the `## Completed` section under a `### Phase 0 — Repository foundation (YYYY-MM-DD)` heading, each item marked done.
  - `CHANGELOG.md` — change the heading `Phase 0 — Repository foundation (in progress)` to `Phase 0 — Repository foundation (complete YYYY-MM-DD)`. Add a one-line summary at the top of the Phase 0 section.
- **Definition of done.** To Do Phase 0 section reduced to the marker line; Completed section has all nine items with the date; CHANGELOG reflects the closing.

##### 0.9.4 — Documentation final pass
- **Deliverables.** Edits where any documentation drift has accumulated during Phase 0.
- **What to read.** README, `docs/user-guide/getting-started.md`, `docs/install.md`, `plugins/test-commander/README.md`. Cross-references and links checked manually.
- **Definition of done.** Every Phase 0 fact in the docs matches reality. No stale "in Phase 0 we will do X" wording. All links resolve. Tone consistent.

##### 0.9.5 — Pre-flight tests for sign-off
- **Deliverables.** `tests/test_phase_0_signoff.py`.
- **Coverage.**
  - All five Phase 0 pytest files exist (`test_plugin_scaffold`, `test_verify_skills`, `test_make_install`, `test_skill_evaluation`, plus the placeholder).
  - CHANGELOG's Phase 0 section is marked complete.
  - `plan.md` Completed section contains Phase 0 entries with a date.
  - `plan.md` To Do Phase 0 sub-section is the marker line, not the original checklist.
- **Definition of done.** Sign-off test suite green. Test-first: it lands red before 0.9.3's plan/CHANGELOG edits.

##### 0.9.6 — Final DoD evaluation (close Phase 0)
- **Procedure.**
  1. Run `make verify` — every test green, link checker clean.
  2. Run `python3 scripts/verify_skills.py` — `tc-core PRESENT`, exit 0.
  3. Run `claude plugin list` — confirm `test-commander@test-commander-marketplace`.
  4. Re-run the smoke test from 0.9.1 to confirm idempotency.
  5. Capture all output to `/tmp/tc-phase0-signoff.log`.
  6. Commit the plan/CHANGELOG/docs updates and the sign-off test in one final commit.
  7. Push to origin.
  8. Create annotated tag: `git tag -a phase-0 -m "Phase 0 — Repository foundation complete."`.
  9. Push tag: `git push origin phase-0`.
- **Definition of done.** All nine numbered steps complete. Tag visible on origin (`git ls-remote origin phase-0` resolves). Evidence log captured. Phase 0 is closed.

##### Definition of done — consolidated 13 checks

Eight automated; five evidence-based.

| # | Check | Type | How |
| --- | --- | --- | --- |
| 1 | All five Phase 0 pytest files exist | auto | `test_phase_0_signoff.py` file-existence asserts |
| 2 | CHANGELOG Phase 0 section marked complete | auto | sign-off test grep |
| 3 | `plan.md` Completed section has Phase 0 entries | auto | sign-off test grep |
| 4 | `plan.md` To Do Phase 0 sub-section is the marker line | auto | sign-off test grep |
| 5 | `make verify` chain clean | auto | full chain |
| 6 | `verify_skills.py` reports OK with `tc-core PRESENT` | auto | direct invocation |
| 7 | Total pytest count meets expected minimum (≥ 41) | auto | sign-off test |
| 8 | `tests/test_phase_0_signoff.py` passes | auto | pytest |
| 9 | Cold-user walkthrough of `getting-started.md` succeeds | evidence | `/tmp/tc-phase0-walkthrough.log` |
| 10 | Per-step DoD audit: 0.1–0.8 all green | evidence | manual review notes |
| 11 | README and user-guide read clean (no stale facts) | evidence | code review |
| 12 | `phase-0` annotated tag created and pushed | evidence | `git tag -l phase-0` + `git ls-remote origin phase-0` |
| 13 | Final commit + push complete | evidence | `git log --oneline -1` shows the sign-off commit on origin |

##### Validation sequence

1. Run cold-user smoke test (0.9.1). Capture log. Fix anything that fails before proceeding.
2. Audit each previous step's DoD (0.9.2). Block on any unmet item.
3. Update `plan.md` and `CHANGELOG.md` (0.9.3).
4. Final doc read-through (0.9.4). Edit any drift.
5. Write `tests/test_phase_0_signoff.py` (0.9.5). Run `make test` — confirm green.
6. Run the full DoD evaluation (0.9.6) including the annotated tag and tag push.

##### Failure modes

- A previous step's DoD turns out not to be green. **Mitigation:** that step reopens. 0.9 cannot close while any earlier DoD is unmet. Fix, re-verify, then return to 0.9.
- The cold-user smoke test surfaces an undocumented step. **Mitigation:** update `docs/user-guide/getting-started.md` so the gap closes; re-run the walkthrough. Treat as a Phase 0 doc bug, not a Phase 1 issue.
- Tag already exists locally (replay of 0.9). **Mitigation:** the annotated tag is intentional. If the prior tag was wrong, delete it (`git tag -d phase-0` then `git push origin :refs/tags/phase-0`) and recreate. Never force-overwrite an existing tag on origin without explicit user confirmation.
- CHANGELOG closing entry diverges from To Do completion. **Mitigation:** the sign-off test (0.9.5) checks both. Both must agree before the test passes.
- `make verify` fails late in 0.9.6 because of an unrelated change. **Mitigation:** the sign-off commit must follow a green verify. Do not push the sign-off if verify is red.

#### Ordering and parallelism

- Strict order: 0.1 → 0.2 → 0.3 → 0.4 → 0.5 → 0.6 → 0.7 → 0.9.
- 0.8 (skill evaluation) can run in parallel with any of 0.3–0.7.
- 0.9 is always last.

---

## Phase 1 — Workspace and Artifact Model

**Goal.** Canonical `.test-commander/` workspace and the first four core commands (`/tc:init`, `/tc:status`, `/tc:journal`, `/tc:next`).

**Architecture.** Each `/tc:*` command is implemented as a small Python helper script plus a Markdown command file inside `tc-core/`. The SKILL.md command file describes the workflow Claude follows; the helper does the deterministic work (file I/O, state inspection, heuristics). This split is what makes TDD possible — helpers are unit-testable; command files are reviewed against their behavior contract.

**Phase-1 design decisions (folded in).**

- **Per-command page location.** Command pages live next to their SKILL.md inside the plugin (`plugins/test-commander/skills/tc-core/commands/<command>.md`). Single source of truth: the same file is what Claude reads and what users read. `docs/command-reference.md` becomes an index that links into the plugin.
- **`/tc:next` returns a ranked list.** Top recommendation surfaces as `next:` for one-glance reading; ranked alternatives follow with explanations.

**Skills authored.** Extend `tc-core` with `/tc:next`, the workspace template, and the four command files.

**Design references.** `superpowers:writing-skills` (command file structure), `superpowers:writing-plans` (planning heuristics for `/tc:next`).

### Phase 1 — Execution outline

Eight sub-steps. TDD throughout: every implementation step lands its tests red before turning them green. Sub-step 1.6 is the dedicated documentation pass; 1.7 is the dedicated testing finalization; 1.8 is the sign-off with a `phase-1` tag.

#### 1.1 — Workspace template
- **Deliverables.** `templates/workspace/` directory tree mirroring the canonical `.test-commander/` layout from this plan. Every starter file has a heading and a "filled in by Phase N" note.
- **Tests first.** `tests/test_workspace_template.py` asserts every directory and starter file from the plan's Workspace Layout exists in the template.
- **Definition of done.** Template matches the layout exactly; pytest green.
- **Review.** Manual diff against the plan's Workspace Layout block; no surprise files added later.

#### 1.2 — `/tc:init` (TDD)
- **Helper.** `scripts/init_workspace.py` — copies the template into a target directory; idempotent; reports created vs skipped.
- **Command file.** `plugins/test-commander/skills/tc-core/commands/init.md` (also serves as the user-facing reference per the per-command-page decision).
- **Tests first.** `tests/test_init_workspace.py` — fresh init, idempotent re-init on existing workspace, partial-existing case (some files present), refusal on invalid target (e.g. a file path, not a directory).
- **Definition of done.** Helper passes all four cases; command file follows the per-command structure; nothing executes outside the target directory.
- **Verification.** Pytest + smoke run against a tmp dir leaves the expected tree.

#### 1.3 — `/tc:status` (TDD)
- **Helper.** `scripts/workspace_state.py` — reads `.test-commander/`, returns a structured snapshot (artifact counts, last-modified, completeness per phase). Shared with `/tc:next` in 1.5.
- **Command file.** `tc-core/commands/status.md` formats the snapshot for users.
- **Tests first.** `tests/test_workspace_state.py` — empty workspace, partial workspace, full workspace (fixtures generated from the template + selective additions).
- **Definition of done.** Helper returns the documented snapshot shape (typed); command file authored; output is grep-friendly.
- **Verification.** Snapshot deterministic per fixture; output passes a structural assertion.

#### 1.4 — `/tc:journal` (TDD)
- **Helper.** `scripts/journal.py` — append (timestamped) and summarize (chronological, by date range).
- **Command file.** `tc-core/commands/journal.md`.
- **Tests first.** `tests/test_journal.py` — append to empty, append to existing, summarize range, summarize empty, malformed entry refused.
- **Definition of done.** Helper passes all five cases; command file authored; journal files are valid Markdown.
- **Verification.** Pytest; resulting journal files render cleanly.
- **Out of scope.** AI-generated summaries — that lives in Phase 8 (learning loop).

#### 1.5 — `/tc:next` heuristics engine (TDD)
- **Methodology.** `plugins/test-commander/skills/tc-core/methodology/next-step-inference.md` — documents the recommendation rules with examples.
- **Engine.** `scripts/next_step.py` — reads `workspace_state`, applies heuristics, returns a ranked recommendation list with explanations.
- **Command file.** `tc-core/commands/next.md`.
- **Tests first.** `tests/test_next_step.py` with one fixture per heuristic: empty workspace, requirements-unreviewed, BDD-without-automation-plan, automation-without-runs, run-without-report, etc. Every rule documented in `next-step-inference.md` has at least one passing fixture.
- **Definition of done.** Every documented heuristic has a passing test case; recommendations include an explanation, not just a command name; the top recommendation surfaces as `next:` on its own line.
- **Verification.** Pytest with per-heuristic fixtures; ranked list output passes a structural assertion.

#### 1.6 — Documentation pass *(dedicated step)*
- **Deliverables.**
  - Fill in `docs/workspace-reference.md` (canonical layout, per-directory purpose, owning phase).
  - Update `docs/command-reference.md` so the four commands link into their per-command pages inside the plugin.
  - Author `docs/user-guide/workflow.md` — first end-to-end walkthrough: `/tc:init` → `/tc:status` → `/tc:journal` → `/tc:next`.
  - Refresh `README.md`, `docs/install.md`, and `docs/user-guide/getting-started.md` for any Phase 1 mentions ("Phase 1 starts next" → "Phase 1 in progress" / "complete").
- **Definition of done.** Every doc accurate against the implementation; all cross-links resolve; link checker green.
- **Verification.** `python3 scripts/check_links.py` clean; manual read-through against the Phase 1 deliverables.

#### 1.7 — Testing finalization *(dedicated step, separate from per-command TDD)*
- **Deliverables.**
  - Bump `DEFAULT_PHASE_CAP` in `scripts/verify_skills.py` from `0` to `1` so the verifier expects `tc-core` to ship `/tc:next`.
  - `tests/test_phase_1_integration.py` — integration smoke that creates a fresh tmp consuming project, invokes the four helpers in sequence (`init` → `status` → `journal` → `next`), and asserts each transition matches expectations.
- **Definition of done.** Integration smoke passes; phase cap bump reflected; full `make verify` chain green.
- **Verification.** Captured `make verify` output; `verify_skills.py` reports `tc-core PRESENT (phase 1)`.

#### 1.8 — Sign-off *(matches the Phase 0 sign-off pattern)*
- **Deliverables.**
  - Cold-user walkthrough following `docs/user-guide/workflow.md` from a fresh tmp consuming project; output to `/tmp/tc-phase1-walkthrough.log`.
  - Per-step DoD audit across 1.1–1.7.
  - `planning/plan.md` — move Phase 1 To Do items to Completed with the date.
  - `CHANGELOG.md` — mark Phase 1 complete; add the closing summary.
  - `tests/test_phase_1_signoff.py` (test-first; mirrors `test_phase_0_signoff.py`).
- **Final DoD evaluation.** `make verify` → smoke replay → commit → push → annotated `phase-1` tag → tag push. Capture to `/tmp/tc-phase1-signoff.log`.
- **Definition of done.** 13-check table (8 automated + 5 evidence-based) all green; tag visible on origin.

#### Definition of done — consolidated 13 checks

Eight automated; five evidence-based.

| # | Check | Type | How |
| --- | --- | --- | --- |
| 1 | All Phase 1 test files exist (`test_workspace_template`, `test_init_workspace`, `test_workspace_state`, `test_journal`, `test_next_step`, `test_phase_1_integration`, `test_phase_1_signoff`) | auto | sign-off test |
| 2 | All four helpers exist (`init_workspace.py`, `workspace_state.py`, `journal.py`, `next_step.py`) | auto | sign-off test |
| 3 | All four command files exist (`init.md`, `status.md`, `journal.md`, `next.md` under `tc-core/commands/`) | auto | sign-off test |
| 4 | `tc-core/methodology/next-step-inference.md` exists | auto | sign-off test |
| 5 | `templates/workspace/` matches the plan's Workspace Layout | auto | template test |
| 6 | `verify_skills.py` cap bumped to 1; reports `tc-core PRESENT (phase 1)` | auto | `make verify` |
| 7 | Integration smoke (`test_phase_1_integration`) passes | auto | pytest |
| 8 | `make verify` chain clean | auto | full chain |
| 9 | Cold-user walkthrough of `workflow.md` succeeds | evidence | `/tmp/tc-phase1-walkthrough.log` |
| 10 | Per-step DoD audit clean (1.1–1.7) | evidence | audit notes |
| 11 | Plan: To Do Phase 1 collapsed to marker; Completed has Phase 1 entries | evidence | grep + sign-off test |
| 12 | CHANGELOG Phase 1 section marked complete with date | evidence | sign-off test |
| 13 | `phase-1` annotated tag created and pushed | evidence | `git tag -l phase-1` + `git ls-remote origin phase-1` |

#### TDD pattern used in 1.2–1.5

```
write tests (red)             # define expected behavior per case
  → implement helper (green)  # minimum code to pass
    → author SKILL.md command file
      → verify (pytest + make verify)
```

No implementation lands before its tests. No tests are added after the fact.

#### Validation sequence

1. Author 1.1 (template) with its test. Confirm pytest red → green.
2. For each of 1.2, 1.3, 1.4, 1.5 in order: write tests, implement helper, author command file, run pytest.
3. 1.6 documentation pass. Run `make verify`.
4. 1.7 testing finalization: bump cap, integration smoke. Run `make verify`.
5. 1.8 sign-off: cold-user walkthrough, audit, plan/CHANGELOG updates, sign-off test, commit, push, tag.

#### Failure modes

- A heuristic's expected output is ambiguous. **Mitigation:** the test fixture is the source of truth; if the fixture is unclear, fix the fixture and the heuristic together.
- `workspace_state` snapshot grows over time and breaks fixture asserts. **Mitigation:** structural asserts (field presence) rather than exact-string asserts; bump snapshot tests deliberately when the shape changes.
- Per-command page in the plugin is too prose-heavy for Claude to follow. **Mitigation:** structure each command file with explicit sections (`Inputs`, `Outputs`, `Preconditions`, `Behavior`, `Safety`, `Definition of Done`); reviewable.
- `/tc:next` recommends something the user already did. **Mitigation:** the helper reads timestamps and journal entries; recently-completed work is excluded from recommendations.
- Workspace template drifts from the plan's Workspace Layout. **Mitigation:** `test_workspace_template.py` parses the plan's layout block and asserts equivalence (or compares against a frozen list documented inline).

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

**Goal.** Team-facing console for Test Commander, scoped to **read-only and proposed workflows only**. Execution lands in Phase 10.5, behind the controlled execution pipeline. Phase 10 ships the UI shell, indexing, and the proposal-card surface; it does not execute anything that changes the workspace or runs tests.

**Implementation.** Next.js + FastAPI + SQLite + SSE + local-filesystem artifacts. Pages: Dashboard, Quality Report, Journal, Sessions, Requirements, Test Runs, Evidence, Chat, Settings. Realtime via SSE. Backend services for artifact indexing, journal viewing, quality-report rendering, and **proposal generation** (not execution).

Structure as previously specified under `apps/web/`, `apps/api/`, `runtime/`.

**Skills authored.** `tc-web` covering init/start/sync/index-artifacts/export, plus the artifact indexer and SSE event stream specs.

**Design references.** `web-scaffold:create-website` (Next.js + FastAPI scaffold structure), `frontend-design:frontend-design` (dashboard and infographic embedding patterns).

**Commands.** `/tc:web-init`, `/tc:web-start`, `/tc:web-sync`, `/tc:web-index-artifacts`, `/tc:web-export`.

**Chat (MVP).** Read-only Q&A from indexed artifacts. Suggests Test Commander commands as **proposal cards** that the user can review. Cannot execute file-modifying or test-running commands — that capability arrives in Phase 10.5 via the controlled execution pipeline.

**Documentation.** `docs/user-guide/web-console.md`, `docs/web-console.md`, `docs/runtime-api.md`.

**Review step.**

- Pages render against a populated workspace; SSE updates appear on journal append; chat enforces the approval gate.

**Test step.**

- End-to-end: `make run` brings up the stack via docker compose; smoke navigations across all pages succeed.

**Definition of done.**

- All pages work, SSE delivers updates, indexer keeps up with workspace changes, chat enforces gating, user guide complete.

---

## Phase 10.5 — Controlled Agent Execution and Policy-Governed Chat

**Goal.** Make the web console safe to expose. Every user request — chat message, button click, automation — flows through a policy-governed pipeline before it can touch Claude or the workspace. Users drive Test Commander workflows; they never drive raw Claude Code.

**Why this phase exists.** A web console with a raw chat prompt that talks to Claude Code is a security liability: prompt injection, arbitrary file write, unbounded test execution, secret exfiltration. Phase 10.5 inserts the controls that make multi-user use possible. It also constrains Phases 11, 12, and 13 so they cannot bypass governance.

**Execution pipeline.**

```
Frontend chat / request
  -> Intent router
  -> Command planner
  -> Permission policy
  -> Approval gate
  -> Bounded agent execution
  -> Artifact capture
  -> Diff validation
  -> Journal / audit log
```

### Components

1. **Intent router.** Maps natural-language requests and button actions to known Test Commander workflows. Examples: "review these requirements" -> `/tc:review-requirements`; "generate BDD for checkout" -> `/tc:generate-bdd --area checkout`; "why did checkout fail?" -> read-only artifact query. Unknown intents default to a read-only Q&A path; the router cannot synthesize new commands on its own.

2. **Command planner.** Produces an explicit, displayable plan before execution. The plan includes: command, files likely to be read, files likely to be created or changed, permission level required, target environment if applicable, expected artifacts, and whether human approval is required.

3. **Permission policy engine.** Classifies every action into one of: `read-only`, `safe-write`, `code-write`, `execute-tests`, `external-network`, `destructive`, `admin`. Policy is configurable per deployment and per role. Examples by level:

| Level | Examples |
| --- | --- |
| read-only | View quality report, ask questions from indexed artifacts, summarize test results, show screenshots, explain failures |
| safe-write | Review requirements, generate open questions, create test ideas, update risk register, generate diagrams, update quality report |
| code-write | Generate Playwright tests, modify page objects, update fixtures, change test data, refactor automation |
| execute-tests | Run smoke / regression / feature tests, run browser exploration |
| external-network | Explore target website, call target APIs, run tests against staging |
| destructive | Reset test data, delete artifacts, install dependencies, modify environment config, change GitHub Actions, destroy sandbox |
| admin | Manage secrets, change provider credentials, change sandbox policy, change permission rules |

4. **Approval gate.** Required for `code-write`, `execute-tests`, `external-network`, `destructive`, and `admin` actions. Configurable for `safe-write`. The UI shows an approval card before execution.

   ```
   Command:
     /tc:automate --feature checkout
   This will:
     - read .test-commander/bdd/features/checkout.feature
     - create or modify tests/e2e/checkout.spec.ts
     - create or modify tests/pages/CheckoutPage.ts
     - update .test-commander/traceability/automation-map.md
     - optionally run checkout tests
   Permission level:
     code-write + execute-tests
   Approve?
   ```

5. **Bounded agent execution.** The agent receives a structured instruction, not the raw user prompt. Includes command name, scope, allowed and disallowed paths, allowed and disallowed actions, expected outputs, safety rules, and journal requirements. Example:

   ```
   You are running Test Commander command /tc:coverage-gap-analysis.
   Scope:
     - Read-only analysis
     - Do not modify application source files
     - Do not run tests
     - Do not access external network
   Allowed reads:
     - .test-commander/
     - specs/
     - tests/
     - src/
   Outputs:
     - Update .test-commander/coverage/coverage-gap-analysis.md
     - Add a journal entry
     - Propose next actions requiring approval
   ```

6. **Agent adapter abstraction.** `AgentAdapter` interface so the runtime is decoupled from any specific backend. Implementations: `ClaudeCodeCliAdapter`, `AnthropicApiAdapter`, `MockAgentAdapter`, future provider adapters. Interface methods: `execute_command`, `stream_events`, `capture_result`, `report_files_changed`, `report_artifacts_created`, `report_usage_if_available`.

   Scaffolding lives at `runtime/agent_adapters/` (`base.py`, `mock_agent.py`, `claude_code_cli.py`, `anthropic_api.py`). Phase 10.5 ships the mock adapter and the Claude Code adapter; the API adapter is stubbed.

7. **Output validation.** After execution, the runtime diffs the workspace and verifies: files changed match the planned scope, no secret files touched, no unexpected network access, expected outputs were produced. Violations mark the run failed and require admin review. Per level:

   - `safe-write` may update `.test-commander/**`, `specs/bdd/**`.
   - `code-write` may update `tests/**`, `playwright.config.ts`, `package.json` only when approved.
   - **No command** may modify `.env`, secrets files, deployment credentials, production config, or cloud credentials without admin approval.

8. **Secret safety.** Frontend users never see provider secrets. AI provider keys stay server-side, injected only into runtime jobs that need them. Logs and artifacts redact secrets. Environment variables are never dumped into prompts or reports. Commands that attempt to print environment variables are flagged. Tokens are scoped and short-lived where possible.

9. **Audit journal.** Append-only log of every action. Entry fields: user, timestamp, original user request, mapped intent, proposed command, approval status, approver, permission level, files read, files changed, artifacts created, tests run, target URLs used, status, summary, evidence links.

### Roles

| Role | Default permissions |
| --- | --- |
| Viewer | View reports, view evidence, ask read-only questions |
| Tester | Viewer + upload docs, review requirements, generate test ideas, generate BDD, approved exploration, approved test runs |
| Automation Engineer | Tester + generate Playwright tests (with approval), modify page objects, update fixtures, review automation plans |
| Maintainer | Automation Engineer + approve code-write actions, create PRs, manage project settings |
| Admin | All actions including manage secrets, manage provider credentials, manage sandbox policy, manage users and roles |

### Frontend behavior (constrains Phase 10 UI)

The chat interface must support:

- Read-only Q&A from indexed artifacts.
- Workflow suggestions.
- Command proposal cards.
- Approval cards.
- Live execution logs (server-streamed, redacted).
- Artifact links.
- File diff summaries.
- Test result summaries.

The frontend must not expose:

- Raw shell.
- Raw Claude Code prompt input.
- Unrestricted file editing.
- Secret values.
- Uncontrolled network targeting.

These can be relaxed per-role only with explicit admin configuration. Default deny.

### Workspace additions

```
.test-commander/
  policy/
    permissions.yaml   # role -> allowed permission levels
    approvals.yaml     # which actions require approval
  audit/
    actions.jsonl      # append-only audit log
    approvals/         # individual approval records
```

### Skills authored

`tc-governance` — owns policy templates, approval-card templates, bounded-prompt templates per command, and the audit log schema.

### Documentation

- `docs/controlled-agent-execution.md` — full architecture and flow.
- `docs/security-and-permissions.md` — roles, permissions, secret safety, output validation rules.
- `docs/chat-command-governance.md` — intent router and command planner behavior.
- `docs/runtime-approval-flow.md` — approval card lifecycle and gate semantics.
- `docs/agent-adapters.md` — adapter interface and implementations.
- `docs/user-guide/governance.md` — tester-facing explainer.

### Review step

- Every action above `safe-write` shows an approval card before execution.
- Every executed action produces an audit entry.
- Output validation catches at least one seeded violation (out-of-scope file write).
- Bounded prompts contain no raw user text in instruction-critical sections.

### Test step

- Integration test: simulate an unsafe user request ("delete all evidence") and assert the policy engine blocks it before reaching the agent.
- Integration test: simulate a code-write request, generate the approval card, deny it, assert no files change.
- Integration test: approve the same request via the mock adapter; assert the audit log records the approval and the post-execution diff matches the plan.
- Integration test: bypass attempt — directly call the agent adapter with no plan; assert the runtime refuses.

### Definition of done

- Intent router, command planner, permission engine, approval gate, bounded executor, output validator, and audit journal all implemented end-to-end with the mock adapter.
- `ClaudeCodeCliAdapter` implemented and gated behind the same controls.
- `tc-governance` skill authored with templates.
- All five new docs written.
- Web console (Phase 10) wired to the pipeline; no UI path can execute an action without it.
- `docs/user-guide/governance.md` explains the model.

---

## Phase 11 — Runtime API and MCP Server

**Goal.** Expose Test Commander to other tools and agents — **through the same controlled execution pipeline** introduced in Phase 10.5. The API and MCP server are alternative front-ends to the same governance layer; they cannot bypass intent routing, planning, permissions, approvals, output validation, or audit.

**Implementation.** Expanded FastAPI Runtime API and a new MCP server at `apps/mcp/`. MCP tools as previously specified. Every API and MCP endpoint enters the Phase 10.5 pipeline; there is no "direct execution" backdoor. Permission levels (`read-only`, `safe-write`, `code-write`, `execute-tests`, `external-network`, `destructive`, `admin`) are enforced server-side.

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

**Safety.** Allowed target domains, blocked private network ranges by default, secret-scanning guidance, approvals for external targets and destructive commands, clear environment labels. **The Phase 10.5 controlled execution pipeline runs inside the sandbox just as it does locally** — sandboxing does not relax governance. Provider credentials (Anthropic API tokens, cloud creds) live as **server-side secrets**, are never exposed to the frontend, and are scoped to the runtime jobs that need them.

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

**Implementation.** Commands `/tc:watch-changes`, `/tc:impact-analysis`, `/tc:coverage-gap-analysis`, `/tc:propose-tests`, `/tc:create-test-pr`, `/tc:continuous-quality-check`. Autonomy modes 0–4 (read-only-advisor, assisted-testing, approved-execution, pull-request-automation, governed-autonomy). Workflow `.github/workflows/test-commander-continuous-quality.yml` on `pull_request`, `push`, `schedule`, `workflow_dispatch`.

Continuous mode runs through the **same Phase 10.5 pipeline** as the web console. The configured autonomy level decides which permission levels are auto-approved; nothing above the configured level executes without explicit human approval. Continuous agent mode must not bypass approvals.

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

Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 10 → 10.5.

Phase 10.5 joins the capstone because exposing the web console without governance is unsafe. Without 10.5, the web console is read-only-only; with 10.5, it can drive workflows safely.

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
| 10 | Web Console | Team-facing quality center (read-only and proposals) |
| 10.5 | Controlled Agent Execution | Policy-governed execution pipeline; users drive workflows, not raw Claude |
| 11 | API/MCP | Tool and agent access (through the same governance pipeline) |
| 12 | Sandboxes | GitHub Actions-launched QA workspaces |
| 13 | Continuous Quality Agent | Monitors change and proposes improvements |

---

## To Do

Phase-by-phase work items. Move to *Completed* as each lands.

### Phase 0

Phase 0 complete (2026-05-26) — see Completed.

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
- [ ] Implement read-only chat (Q&A + proposal cards only — execution arrives in Phase 10.5)
- [ ] Author `docs/user-guide/web-console.md`, `docs/web-console.md`, `docs/runtime-api.md`
- [ ] Confirm review and test gates green

### Phase 10.5
- [ ] Author `plugins/test-commander/skills/tc-governance/SKILL.md` with policy/approval/bounded-prompt templates
- [ ] Scaffold `runtime/agent_adapters/` (`base.py`, `mock_agent.py`, `claude_code_cli.py`, `anthropic_api.py` stub)
- [ ] Implement intent router (NL + button -> known TC workflow)
- [ ] Implement command planner (produces displayable plan)
- [ ] Implement permission policy engine (7 levels, role-aware)
- [ ] Implement approval gate (UI card + record)
- [ ] Implement bounded executor (structured instruction wrapping)
- [ ] Implement output validator (diff against plan, secret-redaction, network checks)
- [ ] Implement audit journal (`.test-commander/audit/actions.jsonl` + per-approval records)
- [ ] Wire Phase 10 web console to the pipeline; remove any direct-execution paths
- [ ] Seed default `policy/permissions.yaml` and `policy/approvals.yaml`
- [ ] Author `docs/controlled-agent-execution.md`, `docs/security-and-permissions.md`, `docs/chat-command-governance.md`, `docs/runtime-approval-flow.md`, `docs/agent-adapters.md`, `docs/user-guide/governance.md`
- [ ] Confirm review and test gates green (including the four integration tests in Phase 10.5 Test step)

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

### Phase 0 — Repository foundation (2026-05-26)

End-to-end clean install verified: `./bootstrap.sh` → `make install` → `test-commander:tc-core` loaded in Claude Code. 42-test suite green; 23-file Markdown link check clean. Tagged `phase-0` on origin.

- [x] Step 0.1: MIT `LICENSE`, expanded `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `TODO.md`.
- [x] Step 0.2: documentation skeleton under `docs/` (vision, architecture, roadmap, methodology, command-reference, workspace-reference, glossary, install) and `docs/user-guide/getting-started.md`. Markdown link checker `scripts/check_links.py`.
- [x] Step 0.3: Python project foundation. `pyproject.toml` (PDM, `requires-python = ">=3.12"`, ruff + pytest dev deps), `Makefile` with six targets, `docker-compose.yml` placeholder, `.gitignore`, `.python-version`, `tests/test_placeholder.py`.
- [x] Step 0.4: POSIX `bootstrap.sh` — platform detection, prereq verification, PDM auto-install, suggested-install output for Docker/Python. Idempotent.
- [x] Step 0.5: plugin scaffold. `.claude-plugin/marketplace.json`, `plugins/test-commander/.claude-plugin/plugin.json`, plugin LICENSE + README, `tc-core/SKILL.md`. Validated via `claude plugin validate`, installed via `claude plugin install`. `tests/test_plugin_scaffold.py` (11 tests).
- [x] Step 0.6: `scripts/verify_skills.py` walks `plugins/test-commander/skills/`, classifies skills as PRESENT/MISSING/MALFORMED/UNEXPECTED, supports `--phase N`. 20-entry catalog. Wired into `make verify`. `tests/test_verify_skills.py` (16 tests). All five live drills passed.
- [x] Step 0.7: `make install` decomposed into a five-step chain (`pdm-install` → `validate-manifests` → `marketplace-add` → `plugin-install` → `verify-skills`). New `make uninstall`. Idempotent re-runs verified end-to-end. `tests/test_make_install.py` (9 tests).
- [x] Step 0.8: `docs/skill-evaluation.md` — public-marketplace scan of 209 plugin entries across Mermaid, sandbox, traceability, a11y, perf. All five decisions "pass"; no plan deltas. `tests/test_skill_evaluation.py` (4 tests).
- [x] Step 0.9: Phase 0 sign-off. Cold-user smoke test passed, per-step DoD audit clean, plan + CHANGELOG updated, `tests/test_phase_0_signoff.py` (5 tests), annotated tag `phase-0` pushed to origin.

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
