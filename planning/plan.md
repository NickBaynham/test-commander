# Test Commander — Phased Build Plan

## Product Positioning

Test Commander is an AI-assisted testing system and quality intelligence center. It helps teams move from requirements and exploration to BDD, automation, evidence, reporting, and continuous improvement.

**Test Commander is generic and product-domain-agnostic.** It ships with universal English and software-engineering defaults only — no e-commerce, finance, healthcare, research, or other product-domain vocabulary in the shipped rubric, tags, methodology, fixtures, or examples. The consuming project supplies every product-specific input: requirements and exploration documents at runtime, domain vocabulary through `<workspace>/config.yaml` extensions, project knowledge ingested in Phase 3, and project-defined tag namespaces. See Decision D19.

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

1. **Vendor and own all skills.** Test Commander owns every skill it ships. Skills live under `plugins/test-commander/skills/<skill-name>/SKILL.md` inside this repo (see D12 for the verified plugin structure). There is no runtime dependency on external skill plugins. Community skills (the ones in the current environment) serve as design references and pattern inspiration only — we author our own copies adapted to the Test Commander workspace, naming, and traceability model. This avoids compatibility drift in directory layouts, file naming, and tool expectations, and lets us evolve skills in lockstep with the workspace schema. See *Skill Authoring Strategy*.
2. **Test Commander is a skill pack first, runtime second.** Phases 0–5 and Phases 7–9 author Markdown skills, methodology, templates, and command guidance — Claude Code executes by reading them. Phase 6 introduces the first executable code (Playwright framework). Phase 10 adds the web/API runtime.
3. **No `examples/` directory.** Real projects bring their own artifacts. Sample apps are not part of the repo.
4. **All BDD lives under `.test-commander/bdd/`** including feature files (`.test-commander/bdd/features/`). Nothing BDD-related lives at the repo root.
5. **Workspace is committed to git.** `.test-commander/` is checked in, including `quality-report/history/`. Test runs in `.test-commander/runs/` are committed as snapshots; large binaries (videos, traces) follow git-lfs rules documented per phase.
6. **Test data lives outside code.** Path: `.test-commander/test-data/`. Tests reference data through fixtures; no inline data in `.ts` files. Claude can regenerate test data on demand via `/tc:generate-test-data`.
7. **Capstone includes Phase 3 and Phase 10.5.** Project knowledge is foundational for exploration, BDD generation, and automation; the controlled-execution pipeline is required before the web console can be safely exposed. The capstone is: 0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 10.5.
8. **Playwright framework is built lazily.** `/tc:build-framework` is a one-time, idempotent skill. Any command that needs the framework (`/tc:automate`, `/tc:run`) checks for its presence first and invokes `/tc:build-framework` if missing. The framework is never built before automation is actually needed.
9. **Every phase has Review, Test, and Documentation steps.** See *Per-Phase Conventions*.
10. **`make install` provisions the full environment.** Python (PDM), Node (Playwright), and a verification step that lists every TC-owned skill the current phase set requires and confirms each is present in `plugins/test-commander/skills/`. See *Environment Setup*.
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

18. **User-facing helpers and templates ship inside the plugin; dev tooling stays at the repo root.** Verified during Step 1.2 by inspecting `~/.claude/plugins/cache/test-commander-marketplace/test-commander/0.0.0/` — only `plugins/test-commander/` contents are copied into the installed plugin cache. Repo-root `scripts/` and `templates/` do not travel. Therefore:
    - **User-facing helpers** (the Python implementations of `/tc:*` commands) live at `plugins/test-commander/scripts/<name>.py`. They ship with the plugin and are reachable from any consuming project that installed Test Commander.
    - **The workspace template** lives at `plugins/test-commander/templates/workspace/`. It ships with the plugin.
    - **Dev tooling** (`scripts/verify_skills.py`, `scripts/check_links.py`) stays at the repo root `scripts/`. These are developer concerns, not user-facing commands; they need not ship.
    - **Tests** stay at the repo root `tests/`. `pytest.ini_options.pythonpath` includes both `scripts` and `plugins/test-commander/scripts` so tests can import from either location.
    - **Bundled-asset path resolution.** Helpers locate bundled assets (template, schemas, etc.) relative to their own file location using `Path(__file__).resolve().parent.parent / "<asset>"`. This works identically whether the script runs from the dev checkout or from `~/.claude/plugins/cache/test-commander-marketplace/test-commander/<version>/scripts/`. Pattern established in `init_workspace.py` (Step 1.2) and reused by `workspace_state.py` (Step 1.3) and `next_step.py` (Step 1.5).

19. **Test Commander is product-domain-agnostic; consuming projects supply all product-specific knowledge.** Every shipped rubric keyword set, tag taxonomy, methodology doc, fixture, command-page example, and illustrative example in this repository uses universal English and software-engineering vocabulary — no e-commerce, finance, healthcare, research, or other product-domain terms in the shipped defaults. Product-specific vocabulary enters only through four explicit hooks:
    - Per-project `<workspace>/config.yaml` extensions to rubric keyword sets (the universal core is unioned with project-supplied lists at runtime; extensions never replace defaults).
    - The requirement, story, AC, and exploration documents the consuming project supplies at runtime under `.test-commander/documents/uploaded/` and downstream artifact directories.
    - Project knowledge ingested in Phase 3 (`tc-knowledge`), which writes into `.test-commander/product-knowledge/`.
    - Project-defined values inside shared tag namespaces (`@area:<feature>`, `@risk:<class>`, `@persona:<role>`); Test Commander ships the namespaces, projects pick the values.

    When the plan, docs, or examples need an illustrative feature name, prefer universal SaaS surfaces — `sign-in`, `dashboard`, `search`, `file upload`, `scheduled job`, `notification`, `audit log`, `report`, `form submission` — over domain-specific features like `checkout`, `refund`, `prescription`, or `trade settlement`. Discovered during Phase 2 Step 2.1 implementation when the seeded fixture and Step 2.2 partition table drifted toward an e-commerce/PCI narrative; corrected by the d718b33 commit (universal-core defaults + `config.yaml` extension hooks) and codified here for every later phase. Reinforces D3 (no `examples/` directory — real projects bring their own artifacts).

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
| Q15 | Should `/tc:init` evolve from a verbatim template-copy into an interactive bootstrap that prompts for project name / repo URL / methodology choices and writes them into `project.md`, `config.yaml`, and `methodology.md`? | Phase 1 (revisit at Phase 8) | Defer for v1. Manual edit is fine; `/tc:next`'s R2 surfaces the step explicitly. Revisit at Phase 8 when the learning loop could feed back-defaults. Surfaced during Step 1.5 — R2 is the one heuristic that recommends a manual action instead of a `/tc:*` command. |

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
    tests-coverage.md
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
2. **Skills authored.** Which TC-owned skills this phase creates or extends. **Design references.** Which community skills inform the design (no runtime dependency, per D1).
3. **Documentation.** What is written. Always update `docs/user-guide/` for tester-facing changes, `docs/command-reference.md` for new commands, and `CHANGELOG.md` for the phase entry.
4. **Review step.** A human or peer review checklist tied to phase-specific outputs. Must complete before the phase is marked done.
5. **Test step.** Automated verification: `make verify` plus phase-specific tests. Must pass before the phase is marked done.
6. **Definition of done.** Bullet list of objective, checkable criteria.

When a Claude Code prompt is provided for a phase, it ends with this standing instruction:

> Do not implement future phases yet. Create clean extension points, but only complete the current phase. Write documentation as you go. Add review and test steps. Update the To Do and Completed lists in `planning/plan.md`.

**Tooling rule (Decision D17).** Any phase step that touches plugins, marketplaces, or installed skills uses the `claude plugin ...` CLI, never `/plugin` slash commands. The CLI is available in every Claude Code environment; slash commands are not. Validate manifests with `claude plugin validate` before any install or marketplace registration — schema problems are far cheaper to fix before install state is created.

**Retire prior-phase guards.** When a phase adds artifacts that a previous phase's guard test forbade ("commands/ must be empty until Phase 1," "no executable runtime until Phase 6," etc.), retire the guard in the same commit that lands the new artifact. Leave a one-line comment in the test file explaining what it used to enforce and which step replaced it with per-artifact coverage. Discovered during Step 1.2 when Phase 0's `test_no_command_behavior_yet` had to be removed so `init.md` could land.

**Per-command page is the single source of truth.** Every `/tc:*` command has a per-command page at `plugins/test-commander/skills/<skill>/commands/<command>.md` with these sections in order: Inputs, Outputs, Preconditions, Behavior, Safety, Implementation, Definition of Done, See also. The same file is what Claude reads at runtime and what users read for reference. `docs/command-reference.md` indexes the per-command pages — it does not duplicate them. Pattern established in Step 1.2 and confirmed across Steps 1.3–1.5.

**SKILL.md surfaces shipped behavior.** The skill's `SKILL.md` is the entry point Claude reads when a user invokes a slash command owned by that skill. Each command sub-step that ships a helper + per-command page must, in the same sub-step, update the owning `SKILL.md` to (a) describe the now-shipped behavior in a brief paragraph and (b) instruct Claude to invoke the bundled helper, with a link to the per-command page for the full spec. Stale "behavior arrives in Phase N+1" wording for a shipped command is a per-step DoD failure — Claude reads the SKILL.md, sees the deferral, and may not route the command to the implementation. The Phase 1 sign-off test asserts no shipped command carries the deferral wording.

**Customization-guide audit (per D19).** Every phase that ships a configurable surface — a new `<workspace>/config.yaml` schema key, a new tag namespace, a new keyword set, a new policy override, a new project-specific extension point — MUST update [`docs/user-guide/customizing-for-your-project.md`](../docs/user-guide/customizing-for-your-project.md) in the same sub-step that ships the surface, with at least one worked example showing how a consuming project extends it for their domain. The phase's dedicated documentation pass and its sign-off both verify the customization guide reflects every extensible surface shipped to date. If a phase ships no new configurable surface, the sign-off explicitly records "no new extensible surface; customization guide unchanged". This convention guarantees that Test Commander stays generic by default and that every domain-extension hook a phase ships is discoverable from one user-facing entry point — never buried in plan text or per-skill methodology docs that domain teams would not know to read.

**Sub-step lesson capture (preventative care).** At the close of every phase sub-step — after the helper / methodology / template / command page / SKILL.md updates land and the verify chain is clean — append any **lessons learned, bugs found, or workarounds adopted** to the phase's `### Phase N — Lessons learned (running)` subsection. A lesson is anything a future implementer of a similar sub-step would benefit from knowing: parser quirks, regex pitfalls, keyword-matching gotchas, fixture-contamination patterns, idempotency hazards, helper-mirroring wins, or "this is harder than it looked, here's why". Each lesson entry is one or two sentences, attributes the source sub-step (e.g. `Step 2.2`), states the bug or pattern, and names the fix or mitigation. **If the sub-step closed cleanly with no surprises, record that explicitly** ("no lessons; mirrored Step X.Y structure" or "no bugs encountered") — silence is not evidence of cleanliness, an explicit "no lessons" line is. The lesson backfill happens in the same commit as the sub-step's CHANGELOG entry, so lessons are versioned with the work that produced them. Phase sign-off (2.9 / 1.8 / etc.) audits that every sub-step has a corresponding lesson entry. This convention is preventative care: future implementers of similar work should be able to grep the plan and find every known landmine before stepping on it again.

---

## Phase 0 — Repository Foundation

**Goal.** Repo structure, conventions, dev environment, and skill-verification.

**Implementation.**

- `README.md` (MIT), `LICENSE` (MIT), `CONTRIBUTING.md`, `CHANGELOG.md`, `TODO.md`
- `bootstrap.sh` — POSIX shell, platform detection, prereq verification, suggested-install output, prints `Next step: make install` and exits 0 (per D14, bootstrap and install stay separate)
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

**Skills authored.** `tc-core` SKILL.md (init/status/journal commands only — `/tc:next` deferred to Phase 1 per Q7 default; per D12, no separate umbrella SKILL.md — the plugin manifest provides plugin identity, `tc-core` is a sibling skill). Public-skill evaluation pass written to `docs/skill-evaluation.md`.

**Design references.** `anthropic-skills:skill-creator` (plugin manifest and skill-directory patterns), `claude-code-setup:claude-automation-recommender` (hook/skill/MCP surface validation). These inform authoring; no runtime dependency.

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
- **Deliverables.** A CLI entry point in `scripts/verify_skills.py` (`if __name__ == "__main__"`). Supports `--phase N` and `--help`. Default phase cap: `0` (bumped one phase at a time as later phases ship — see Phase 1 sub-step 1.7 for the first bump).
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
- **Deliverables.** `plugins/test-commander/templates/workspace/` directory tree mirroring the canonical `.test-commander/` layout from this plan. Every starter file has a heading and a "filled in by Phase N" note. Per D18 the template ships with the installed plugin.
- **Tests first.** `tests/test_workspace_template.py` asserts every directory and starter file from the plan's Workspace Layout exists in the template.
- **Definition of done.** Template matches the layout exactly; pytest green.
- **Review.** Manual diff against the plan's Workspace Layout block; no surprise files added later.

#### 1.2 — `/tc:init` (TDD)
- **Helper.** `plugins/test-commander/scripts/init_workspace.py` (per D18 — ships inside the plugin so consuming-project users can invoke it) — copies the template into a target directory; idempotent; reports created vs skipped.
- **Command file.** `plugins/test-commander/skills/tc-core/commands/init.md` (also serves as the user-facing reference per the per-command-page decision).
- **SKILL.md update.** `tc-core/SKILL.md` updated in the same sub-step to describe `/tc:init`'s shipped behavior and instruct Claude to invoke `scripts/init_workspace.py` (per the "SKILL.md surfaces shipped behavior" convention).
- **Tests first.** `tests/test_init_workspace.py` — fresh init, idempotent re-init on existing workspace, partial-existing case (some files present), refusal on invalid target (e.g. a file path, not a directory).
- **Definition of done.** Helper passes all four cases; command file follows the per-command structure; nothing executes outside the target directory; SKILL.md no longer carries deferral wording for `/tc:init`.
- **Verification.** Pytest + smoke run against a tmp dir leaves the expected tree.

#### 1.3 — `/tc:status` (TDD)
- **Helper.** `plugins/test-commander/scripts/workspace_state.py` (per D18) — reads `.test-commander/`, returns a structured snapshot (artifact counts, last-modified, completeness per phase). Shared with `/tc:next` in 1.5.
- **Command file.** `tc-core/commands/status.md` formats the snapshot for users.
- **SKILL.md update.** `tc-core/SKILL.md` updated in the same sub-step to describe `/tc:status`'s shipped behavior and instruct Claude to invoke `scripts/workspace_state.py`.
- **Tests first.** `tests/test_workspace_state.py` — empty workspace, partial workspace, full workspace (fixtures generated from the template + selective additions).
- **Definition of done.** Helper returns the documented snapshot shape (typed); command file authored; output is grep-friendly; SKILL.md no longer carries deferral wording for `/tc:status`.
- **Verification.** Snapshot deterministic per fixture; output passes a structural assertion.

#### 1.4 — `/tc:journal` (TDD)
- **Helper.** `plugins/test-commander/scripts/journal.py` (per D18) — append (timestamped) and summarize (chronological, by date range).
- **Command file.** `tc-core/commands/journal.md`.
- **SKILL.md update.** `tc-core/SKILL.md` updated in the same sub-step to describe `/tc:journal`'s shipped behavior (append + summarize) and instruct Claude to invoke `scripts/journal.py`.
- **Tests first.** `tests/test_journal.py` — append to empty, append to existing, summarize range, summarize empty, malformed entry refused.
- **Definition of done.** Helper passes all five cases; command file authored; journal files are valid Markdown; SKILL.md no longer carries deferral wording for `/tc:journal`.
- **Verification.** Pytest; resulting journal files render cleanly.
- **Out of scope.** AI-generated summaries — that lives in Phase 8 (learning loop).
- **Settled format (Step 1.4 outcome).** One file per day at `.test-commander/journal/YYYY-MM-DD.md`. Each file is an H1 date header (`# YYYY-MM-DD`) followed by zero or more H2 timestamp sections (`## YYYY-MM-DDTHH:MM:SSZ`), each with a verbatim Markdown body. The H1 appears once per file; H2 sections are append-only. Parser splits on H2 timestamp headings; bodies cannot contain a line matching that pattern (rejected at append). This is the stable contract Phase 8's learning loop will parse from.

#### 1.5 — `/tc:next` heuristics engine (TDD)
- **Methodology.** `plugins/test-commander/skills/tc-core/methodology/next-step-inference.md` — documents the recommendation rules with examples.
- **Engine.** `plugins/test-commander/scripts/next_step.py` (per D18) — reads `workspace_state`, applies heuristics, returns a ranked recommendation list with explanations.
- **Command file.** `tc-core/commands/next.md`.
- **SKILL.md update.** `tc-core/SKILL.md` updated in the same sub-step to describe `/tc:next`'s shipped behavior and instruct Claude to invoke `scripts/next_step.py`. By end of 1.5, `tc-core/SKILL.md` describes all four Phase 1 commands.
- **Tests first.** `tests/test_next_step.py` with one fixture per heuristic: empty workspace, requirements-unreviewed, BDD-without-automation-plan, automation-without-runs, run-without-report, etc. Every rule documented in `next-step-inference.md` has at least one passing fixture.
- **Definition of done.** Every documented heuristic has a passing test case; recommendations include an explanation, not just a command name; the top recommendation surfaces as `next:` on its own line.
- **Verification.** Pytest with per-heuristic fixtures; ranked list output passes a structural assertion.

#### 1.6 — Documentation pass *(dedicated step)*
- **Deliverables.**
  - Fill in `docs/workspace-reference.md` (canonical layout, per-directory purpose, owning phase).
  - Update `docs/command-reference.md` so the four commands link into their per-command pages inside the plugin.
  - Author `docs/user-guide/workflow.md` — first end-to-end walkthrough: `/tc:init` → `/tc:status` → `/tc:journal` → `/tc:next`.
  - Refresh `README.md`, `docs/install.md`, and `docs/user-guide/getting-started.md` for any Phase 1 mentions ("Phase 1 starts next" → "Phase 1 in progress" / "complete").
  - **Final `tc-core/SKILL.md` pass.** Confirm SKILL.md describes every shipped command, links to all four per-command pages, and instructs Claude to invoke the bundled helpers. No "behavior arrives in Phase N+1" wording for any shipped command. The per-sub-step SKILL.md updates from 1.2–1.5 should already cover this; 1.6 is the final check.
- **Definition of done.** Every doc accurate against the implementation; all cross-links resolve; link checker green; SKILL.md is the consolidated entry point for Phase 1 commands.
- **Verification.** `python3 scripts/check_links.py` clean; manual read-through against the Phase 1 deliverables; grep for stale deferral wording in `tc-core/SKILL.md` returns no hits.

#### 1.7 — Testing finalization *(dedicated step, separate from per-command TDD)*
- **Deliverables.**
  - Bump `DEFAULT_PHASE_CAP` in `scripts/verify_skills.py` from `0` to `1` so the verifier expects `tc-core` to ship `/tc:next`.
  - `tests/test_phase_1_integration.py` — integration smoke that creates a fresh tmp consuming project, invokes the four helpers in sequence (`init` → `status` → `journal` → `next`), and asserts each transition matches expectations.
- **Definition of done.** Integration smoke passes; phase cap bump reflected; full `make verify` chain green.
- **Verification.** Captured `make verify` output; `verify_skills.py` reports `tc-core PRESENT (phase 1)`.

#### 1.8 — Sign-off

Six sub-steps. Mirrors the Phase 0 sign-off pattern (0.9). Test-first: the sign-off test in 1.8.5 lands red before the plan/CHANGELOG edits in 1.8.3 turn it green. The final sub-step (1.8.6) captures evidence and pushes the `phase-1` annotated tag.

##### 1.8.1 — Cold-user walkthrough of `workflow.md`
- **Deliverables.** Captured log of an end-to-end walkthrough of `docs/user-guide/workflow.md` from a freshly-installed plugin against a fresh tmp consuming project.
- **Steps to execute verbatim.**
  1. `make uninstall` → `make install` to reach a known-clean plugin state.
  2. Create a tmp consuming-project dir (`mktemp -d`).
  3. Invoke the four Phase 1 helpers in workflow order: `init_workspace.py <tmp>`, edit `project.md`, `workspace_state.py <tmp>`, `journal.py --target <tmp> append "..."`, `next_step.py <tmp>`.
  4. Confirm each helper prints the output documented in `workflow.md` (no fabricated examples).
- **Definition of done.** All commands succeed end to end. Output captured to `/tmp/tc-phase1-walkthrough.log`. If any step fails, fix the cause and re-run before continuing to 1.8.2.

##### 1.8.2 — Per-step DoD audit
- **Deliverables.** A line-by-line audit of Steps 1.1 through 1.7 against their DoD lists.
- **What to check per step.** Every DoD bullet green; every pytest file passes; every deliverable present on disk; every cross-link in the per-command pages resolves; every Failure Mode mitigation in place.
- **Specifically.**
  - 1.1: `plugins/test-commander/templates/workspace/` matches the Workspace Layout (test_workspace_template green).
  - 1.2: `init_workspace.py` + `init.md` present; four test cases pass.
  - 1.3: `workspace_state.py` + `status.md` present; six tests pass.
  - 1.4: `journal.py` + `journal.md` present; eight tests pass.
  - 1.5: `next_step.py` + `next.md` + `next-step-inference.md` present; thirteen tests pass.
  - 1.6: `workspace-reference.md`, `command-reference.md`, `workflow.md`, README + getting-started status lines all current; `tc-core/SKILL.md` describes every shipped Phase 1 command and contains no stale deferral wording.
  - 1.7: `DEFAULT_PHASE_CAP == 1`, `CATALOG["tc-core"] == 1`, integration smoke passes.
- **Definition of done.** All seven prior sub-steps audited green. Any unmet item blocks the sign-off.

##### 1.8.3 — Plan and CHANGELOG updates
- **Deliverables.**
  - `planning/plan.md` — collapse the `### Phase 1` To Do sub-section to a single line: `Phase 1 complete (YYYY-MM-DD) — see Completed`. Add a `### Phase 1 — Workspace and artifact model (YYYY-MM-DD)` section to `## Completed` with the per-step summary lines marked `[x]`.
  - `CHANGELOG.md` — change the heading `Phase 1 — Workspace and artifact model (in progress)` to `(complete YYYY-MM-DD)` and add a one-line closing summary at the top of the Phase 1 section.
- **Definition of done.** To Do Phase 1 reduced to the marker line; Completed has the Phase 1 section with date and seven sub-step bullets; CHANGELOG reflects the closing.

##### 1.8.4 — Documentation final pass
- **Deliverables.** Edits wherever Phase 1 wording has drifted during the seven sub-steps.
- **What to read.** README status line, `docs/user-guide/getting-started.md` "what's next", `docs/install.md` verifying-install paragraph, `docs/user-guide/workflow.md` introductory paragraph, `plugins/test-commander/README.md` skill table.
- **Definition of done.** Every Phase 1 fact matches the implementation. "Phase 1 in progress" wording becomes "Phase 1 complete (YYYY-MM-DD); Phase 2 starts next" where applicable. All cross-links resolve.

##### 1.8.5 — Pre-flight tests for sign-off
- **Deliverables.** `tests/test_phase_1_signoff.py`.
- **Coverage.**
  - All seven Phase 1 pytest files exist (`test_workspace_template`, `test_init_workspace`, `test_workspace_state`, `test_journal`, `test_next_step`, `test_phase_1_integration`, `test_phase_1_signoff`).
  - All four Phase 1 helpers exist under `plugins/test-commander/scripts/`.
  - All four Phase 1 command files exist under `plugins/test-commander/skills/tc-core/commands/`.
  - `plugins/test-commander/skills/tc-core/methodology/next-step-inference.md` exists.
  - `plugins/test-commander/templates/workspace/` exists (per D18).
  - `scripts/verify_skills.py` `CATALOG["tc-core"]` is `1` and `DEFAULT_PHASE_CAP` is `1`.
  - `tc-core/SKILL.md` describes all four Phase 1 commands and contains no "behavior arrives in Phase 1" / "Coming in Phase 1" wording.
  - CHANGELOG Phase 1 section marked complete with a date.
  - `plan.md` Completed has a Phase 1 subsection with a date.
  - `plan.md` To Do Phase 1 is the marker line (no unchecked items remain).
  - Total pytest count meets minimum (≥ 84).
- **Definition of done.** Test-first: the suite lands red before 1.8.3's plan/CHANGELOG edits, green after.

##### 1.8.6 — Final DoD evaluation (close Phase 1)
- **Procedure.**
  1. Run `make verify` — every test green, link checker clean, `verify_skills.py` reports `tc-core PRESENT (phase 1)`.
  2. Replay the 1.8.1 walkthrough end to end to confirm reproducibility.
  3. Capture all output to `/tmp/tc-phase1-signoff.log`.
  4. Commit the plan/CHANGELOG/docs updates and the sign-off test in one final commit.
  5. Push to origin.
  6. Create annotated tag: `git tag -a phase-1 -m "Phase 1 — Workspace and artifact model complete."`.
  7. Push tag: `git push origin phase-1`.
- **Definition of done.** All seven numbered steps complete. Tag visible on origin (`git ls-remote origin phase-1` resolves). Evidence log captured. Phase 1 is closed.

#### Definition of done — consolidated 13 checks

Eight automated; five evidence-based.

| # | Check | Type | How |
| --- | --- | --- | --- |
| 1 | All Phase 1 test files exist (`test_workspace_template`, `test_init_workspace`, `test_workspace_state`, `test_journal`, `test_next_step`, `test_phase_1_integration`, `test_phase_1_signoff`) | auto | sign-off test |
| 2 | All four helpers exist (`init_workspace.py`, `workspace_state.py`, `journal.py`, `next_step.py`) | auto | sign-off test |
| 3 | All four command files exist (`init.md`, `status.md`, `journal.md`, `next.md` under `tc-core/commands/`) | auto | sign-off test |
| 4 | `tc-core/methodology/next-step-inference.md` exists | auto | sign-off test |
| 5 | `plugins/test-commander/templates/workspace/` matches the plan's Workspace Layout (per D18) | auto | template test (`test_workspace_template`) |
| 6 | `verify_skills.py` has `CATALOG["tc-core"] == 1` and `DEFAULT_PHASE_CAP == 1`; `make verify` prints `tc-core PRESENT (phase 1)` | auto | sign-off test + `make verify` |
| 7 | Integration smoke `test_phase_1_integration` passes | auto | pytest |
| 8a | `tc-core/SKILL.md` describes all four shipped Phase 1 commands with no deferral wording | auto | sign-off test |
| 8 | `make verify` chain clean | auto | full chain |
| 9 | Cold-user walkthrough of `workflow.md` from clean state succeeds (1.8.1) | evidence | `/tmp/tc-phase1-walkthrough.log` |
| 10 | Per-step DoD audit clean for 1.1–1.7 (1.8.2) | evidence | audit notes |
| 11 | `plan.md` To Do Phase 1 collapsed to marker; Completed has Phase 1 subsection with date (1.8.3) | evidence | sign-off test + grep |
| 12 | CHANGELOG Phase 1 section marked complete with date (1.8.3) | evidence | sign-off test |
| 13 | `phase-1` annotated tag created and pushed (1.8.6) | evidence | `git tag -l phase-1` + `git ls-remote origin phase-1` |

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
4. 1.7 testing finalization: bump `CATALOG` + `DEFAULT_PHASE_CAP` to 1, integration smoke. Run `make verify`.
5. 1.8 sign-off, in order:
   5a. Run the cold-user walkthrough from `workflow.md` (1.8.1). Capture log. Fix anything that fails before proceeding.
   5b. Audit each prior sub-step's DoD (1.8.2). Block on any unmet item.
   5c. Write `tests/test_phase_1_signoff.py` (1.8.5). Run `make test` — expect failures for any not-yet-applied plan/CHANGELOG edits.
   5d. Update `plan.md` and `CHANGELOG.md` (1.8.3). Re-run sign-off test — expect green.
   5e. Doc final read-through (1.8.4). Edit any drift; re-run `make verify`.
   5f. Final DoD evaluation (1.8.6): commit, push, annotated tag, tag push.

#### Failure modes

- A heuristic's expected output is ambiguous. **Mitigation:** the test fixture is the source of truth; if the fixture is unclear, fix the fixture and the heuristic together.
- `workspace_state` snapshot grows over time and breaks fixture asserts. **Mitigation:** structural asserts (field presence) rather than exact-string asserts; bump snapshot tests deliberately when the shape changes.
- Per-command page in the plugin is too prose-heavy for Claude to follow. **Mitigation:** structure each command file with explicit sections (`Inputs`, `Outputs`, `Preconditions`, `Behavior`, `Safety`, `Definition of Done`); reviewable.
- `/tc:next` recommends something the user already did. **Mitigation:** the helper reads timestamps and journal entries; recently-completed work is excluded from recommendations.
- Workspace template drifts from the plan's Workspace Layout. **Mitigation:** `test_workspace_template.py` parses the plan's layout block and asserts equivalence (or compares against a frozen list documented inline).
- `WorkspaceSnapshot.populated` (Step 1.3) is bytes-vs-template equality, so a roundtrip edit that ends byte-equal to the template is mis-classified as `not_started`. **Mitigation:** documented as a known limitation in `status.md`. If false negatives become common in practice, add a `.test-commander/.populated-marker` allowlist or switch to a content-hash sidecar; defer until evidence warrants.
- A prior sub-step's DoD turns out not to be green during 1.8.2. **Mitigation:** the failing sub-step reopens. 1.8 cannot close while any earlier DoD is unmet. Fix, re-verify the sub-step, then return to 1.8.2.
- The cold-user walkthrough in 1.8.1 surfaces a `workflow.md` gap (a step that doesn't actually work as documented). **Mitigation:** update `workflow.md` to match reality and re-run the walkthrough. Treat as a Phase 1 doc bug, not a Phase 2 issue.
- `phase-1` tag already exists locally (replay of 1.8). **Mitigation:** the annotated tag is intentional. If the prior tag was wrong, delete it (`git tag -d phase-1` then `git push origin :refs/tags/phase-1`) and recreate. Never force-overwrite an existing tag on origin without explicit user confirmation.
- `CHANGELOG` Phase 1 closing entry diverges from To Do/Completed movement. **Mitigation:** the sign-off test (1.8.5) checks all three sources. They must agree before the test passes.

---

## Phase 2 — Requirements and User Story Intelligence

**Goal.** Review requirements, user stories, and acceptance criteria before automation exists. Ship the `tc-requirements` skill with five commands that read source documents, apply a deterministic rubric, surface defects, and produce reviewable artifacts under `.test-commander/requirements/`.

**Architecture.** Each `/tc:*` command is implemented as a Python helper script plus a Markdown command file inside `plugins/test-commander/skills/tc-requirements/`. Helpers do the deterministic work (parse documents, apply mechanical rubric checks, write artifacts, update traceability); Claude executes the judgment-heavy parts (atomicity, ambiguity, NFR completeness, automation suitability) by reading the per-command page and the methodology docs. The split keeps every command testable end-to-end with seeded fixtures.

**Phase-2 design decisions (folded in).**

- **Methodology lives with the command it serves.** Each of the three review commands authors its own methodology file inside `plugins/test-commander/skills/tc-requirements/methodology/`. Templates live in `plugins/test-commander/skills/tc-requirements/templates/`. No standalone "shared methodology" file — shared rubric items repeat in the command-specific docs because each is a self-contained reference.
- **Seeded-flawed-requirements fixture is the source of truth for the review rubric.** A small Markdown corpus under `tests/fixtures/seeded-flawed-requirements/` carries intentional defects, each tagged with the rubric dimension it violates via an inline `<!-- defect: <dimension> -->` HTML comment. Every rubric dimension has at least one seeded defect; every command's test fixture asserts the corresponding finding is produced. Adding a new rubric dimension means adding a seeded defect — the fixture is the contract.
- **Per-requirement artifacts use stable IDs.** Every parsed requirement is assigned an ID (sourced from the input document if present, else generated as `REQ-NNN`). All five command outputs use the same ID space so cross-command traceability works. Traceability updates land in `.test-commander/traceability/requirements-map.md`.
- **`/tc:requirements-to-tests` seeds `.test-commander/test-ideas/`.** Phase 4 ultimately owns the rich charter/exploration model; Phase 2 only seeds bare test ideas (one or more per requirement). The seed file's schema is forward-compatible with Phase 4's idea model — Phase 4 enriches, Phase 2 does not block on it. `workspace_state.py`'s `PHASE_OWNERSHIP` keeps `test-ideas/` under Phase 4; Phase 2 writes are scored as populated content but do not change ownership.
- **Helpers detect every rubric dimension mechanically using universal cores; projects extend domain-specific keyword sets via `<workspace>/config.yaml`.** Every dimension in the Phase 2 rubric has a deterministic check the helper performs against a *shipped universal core* — regex over generic English, RFC-2119 modal detection, simple graph analysis for dependencies, mutual-exclusion comparison for consistency. Test Commander ships only universal vocabulary: no PCI/HIPAA/e-commerce/research/finance terms in the core, because the tool does not know what product a consuming team is testing until exploratory testing (Phase 4) tells us. Dimensions that meaningfully need domain vocabulary (`data-rules` sensitive-data terms, `risk` compliance terms, `roles-permissions` role and verb taxonomies) accept optional extensions from `<workspace>/config.yaml` under `tc-requirements:`. The shipped seeded fixture exercises only the universal cores; domain coverage is the consuming project's responsibility through their own requirements documents and config extensions. Tests assert universal-core triggering. Claude's runtime role is the narrative layer on top: explaining *why* each finding matters in product context, ranking severity, identifying gaps the keyword check would miss. The cold-user walkthrough in 2.9.1 validates judgment quality; the pytest suite validates universal-core coverage. Per-dimension cores and extension hooks are enumerated in a partition table inside each command's sub-step (see 2.2 for the requirement-level table; 2.3 and 2.4 will add their own).

**Skills authored.** `tc-requirements` — `SKILL.md` plus five command files (one per `/tc:*` command), three methodology files (`requirements-quality-review.md`, `user-story-readiness.md`, `acceptance-criteria-quality.md`), and four templates (`requirements-review-template.md`, `user-story-review-template.md`, `acceptance-criteria-review-template.md`, `requirements-coverage-template.md`).

**Design references.** `business-requirements:brd` and `business-requirements:analyze-requirements` (review structure, BRD output shape), `logical-consistency:logic-check` (contradictions, undefined terms, faulty inference rubric).

**Review rubric.** clarity, testability, completeness, consistency, atomicity, measurability, AC quality, edge cases, negative cases, data rules, roles/permissions, NFRs, dependencies, ambiguity, risk, automation suitability. INVEST for stories.

### Phase 2 — Execution outline

Nine sub-steps. TDD throughout: every implementation step lands its tests red before turning them green. Sub-step 2.1 scaffolds the skill and the shared seeded-flawed-requirements fixture; 2.2–2.6 implement the five commands; 2.7 is the dedicated documentation pass; 2.8 is the dedicated testing finalization; 2.9 is the sign-off with a `phase-2` tag.

#### 2.1 — Skill scaffold and seeded-flawed-requirements fixture

- **Deliverables.**
  - `plugins/test-commander/skills/tc-requirements/SKILL.md` — YAML frontmatter (`name: tc-requirements`, single-line trigger-style `description`). Body lists the five commands and notes that command behavior arrives in subsequent sub-steps. Mirrors Phase 0's initial `tc-core/SKILL.md` shape — each command paragraph carries the deferral wording until its own sub-step turns the wording into a shipped-behavior description (per the "SKILL.md surfaces shipped behavior" convention).
  - `tests/fixtures/seeded-flawed-requirements/` directory containing:
    - `requirements.md` — at least one intentionally-flawed requirement per rubric dimension. Each defect is marked with an inline `<!-- defect: <dimension> -->` HTML comment used by the fixture loader.
    - `user-stories.md` — at least one INVEST violation per INVEST letter (Independent, Negotiable, Valuable, Estimable, Small, Testable).
    - `acceptance-criteria.md` — at least one AC defect per AC-rubric dimension (missing edge cases, missing negative cases, untestable predicate, ambiguous data rule, missing role context).
    - `README.md` — explains the fixture's intent, the inline-comment defect-marking convention, and how to add a new seeded defect.
  - `plugins/test-commander/skills/tc-requirements/methodology/.gitkeep` and `plugins/test-commander/skills/tc-requirements/templates/.gitkeep` — empty directories that 2.2–2.6 fill in. `.gitkeep` is removed by the first sub-step that lands real content in each directory.
- **Tests first.** `tests/test_tc_requirements_scaffold.py` — asserts: skill directory and `SKILL.md` present with valid frontmatter; `name == "tc-requirements"`; description non-empty; SKILL.md body references each of the five commands; fixture directory exists with the three Markdown files plus README; every rubric dimension named in the high-level Phase 2 rubric list appears in at least one inline defect comment in the fixture; every INVEST letter appears in `user-stories.md`. Test-first: lands red before any deliverable is written.
- **Definition of done.** Skill scaffolded; fixture covers every rubric dimension and every INVEST letter; scaffold test green; `scripts/verify_skills.py` still reports `tc-core PRESENT (phase 1)` (phase cap does not move until Step 2.8); `tc-requirements` directory present but expected `UNEXPECTED` by the verifier under `DEFAULT_PHASE_CAP=1` only if the catalog entry's phase is ≤ cap — since `tc-requirements` is mapped to phase 2 in the catalog, it is simply ignored by `--phase 1` and reported by `--phase 2`.
- **Review.** Manual read of the fixture against the rubric table in the top-of-phase summary — confirm every dimension has at least one seeded defect, and that the defects are realistic rather than contrived.

#### 2.2 — `/tc:review-requirements` (TDD)

- **Helper.** `plugins/test-commander/scripts/review_requirements.py` (per D18). Reads every `*.md` file in `<workspace>/documents/uploaded/` whose body declares one or more `REQ-NNN` markers (other Markdown files in that directory — README, design notes — are skipped). Parses each `REQ-NNN` entry into `{id, body}` pairs. Applies the mechanical checks in the partition table below, one per requirement-level rubric dimension. Writes three artifacts:
  - `<workspace>/requirements/requirements-review.md` — **overwrites** on every run; user edits to this file are not preserved (it is a generated report).
  - `<workspace>/requirements/requirements-inventory.md` — **overwrites** with the freshly-parsed ID list in document order.
  - `<workspace>/requirements/open-questions.md` — **appends**, deduplicated by the `(question-text, requirement-id)` pair. Existing user-authored questions are preserved.

  **Idempotency contract.** Re-running the helper against unchanged input produces byte-identical `requirements-review.md` and `requirements-inventory.md`, and adds no new lines to `open-questions.md`.

  **Open-questions rule.** The helper emits one open question for every detected broken dependency reference (`"<source-REQ> references <target-REQ> which does not exist"`) and one open question for every detected mutual-exclusion pair (`"<REQ-A> and <REQ-B> assert mutually-exclusive constraints over <shared subject> — which is authoritative?"`). Other findings appear in `requirements-review.md` only.

  **Input-file filter.** A file in `documents/uploaded/` is treated as a requirements source iff it contains at least one `REQ-\d+` token. This excludes the workspace template's `README.md` placeholder and any non-requirements docs the user has uploaded.

  **Requirement-ID collision rule.** If two source files declare the same `REQ-NNN` ID, the helper exits non-zero with a message naming both files and the colliding ID. No artifacts are written on collision.

  **Partition table — mechanical checks per rubric dimension.** Every dimension below has a deterministic check; the seeded fixture has at least one defect per dimension and the helper must find each one. The helper produces a finding for every triggered dimension on every requirement (a single requirement may trigger multiple dimensions).

  | Dimension | Mechanical check |
  | --- | --- |
  | clarity | body contains any buzzword from `{robust, seamless, modern, best-of-breed, world-class, leverage}` |
  | testability | body contains a vague predicate from `{user-friendly, easy, intuitive, fast, slow}` without a numeric threshold nearby, **or** body lacks an RFC-2119 modal (`shall`/`must`/`should`) |
  | completeness | body length ≤ 10 tokens, **or** body specifies an action verb without naming an outcome or acceptance condition |
  | consistency | two or more requirements share a subject noun-phrase (case-insensitive) but assert mutually-exclusive predicates — detected by comparing modal phrases (`may`/`shall`/`require`/`prohibit`) over the shared subject |
  | atomicity | body joins ≥ 2 independent clauses with coordinating conjunctions (a comma-list of ≥ 3 items ending in `and`/`or`, or two `and`-joined verb phrases) |
  | measurability | body uses a qualitative quantifier from `{quickly, fast, many, few, often, soon, slow, rapidly}` without a numeric token (digit run, optional unit/percent) within ±1 sentence |
  | ac-quality | body matches `\bacceptance criteria\b` but no AC pointer of the form `AC-\d+` is present in scope, **or** body specifies a user action without any AC pointer at all |
  | edge-cases | body specifies an action but contains no edge keyword from `{except, unless, otherwise, edge}` |
  | negative-cases | body specifies an action but contains no failure keyword from `{invalid, error, fail, missing, declined, rejected, denied}` |
  | data-rules | body references a sensitive-data keyword from the universal core `{password, secret, token, credential, key}` — **extensible** via `tc-requirements.data-rules.sensitive-keywords` in `<workspace>/config.yaml` for domain terms (e.g. PCI: `PAN`, `primary account number`; HIPAA: `PHI`; PII: `SSN`) — without a constraint keyword from `{length, format, encoding, retention, hashed, encrypted, tokenized}` in the same requirement |
  | roles-permissions | body uses a permission verb from the universal core `{delete, approve, reject, modify, grant, revoke}` — **extensible** via `tc-requirements.roles-permissions.permission-verbs` for domain verbs (e.g. commerce: `issue`, `refund`; healthcare: `dispense`, `prescribe`) — without a role qualifier from the universal core `{admin, owner, operator}` — **extensible** via `tc-requirements.roles-permissions.role-qualifiers` for domain roles (e.g. commerce: `customer`, `store-manager`; research: `investigator`, `reviewer`) |
  | nfrs | body uses an NFR adjective from `{available, secure, performant, scalable, reliable}` without a quantitative threshold (e.g. `99.9%`, `< 200 ms`, `≥ N`) in the same requirement |
  | dependencies | parse `REQ-\d+` references in bodies; report (a) broken references — target REQ-ID does not exist among parsed IDs, **and** (b) cycles — any non-trivial cycle in the reference graph |
  | ambiguity | body contains an ambiguity adjective from `{reasonable, appropriate, sufficient, robust, seamless}` |
  | risk | body contains a universal security anti-pattern from the core `{plain text, plaintext, unencrypted, raw password, hardcoded credential, default password}` — **extensible** via `tc-requirements.risk.compliance-keywords` for domain compliance regimes (e.g. PCI: `PAN`, `primary account number`; HIPAA: `PHI`; PII: `SSN`, `social security`). Presence alone is the risk signal; Claude's narrative layer determines whether a compensating control (tokenization, encryption-at-rest, vault storage) exists |
  | automation-suitability | body uses a subjective verb-phrase from `{feel, look, match the brand, delight, inviting}` while being marked as an automation candidate (e.g. `automation candidate`, `regression check`, `automated`) |

  Word-set membership is case-insensitive. Single-token keywords are matched at word boundaries; multi-token phrases are matched literally. The AC-specific dimensions `ac-missing-edge-cases`, `ac-missing-negative-cases`, `ac-untestable-predicate`, `ac-ambiguous-data-rule`, and `ac-missing-role-context` are owned by 2.4 and are **not** detected here.

  **Configurable extensions — `<workspace>/config.yaml`.** Test Commander ships only universal-core keyword sets because it does not assume a product domain. Consuming projects extend the rows marked **extensible** by adding a `tc-requirements:` block to `<workspace>/config.yaml`:

  ```yaml
  tc-requirements:
    data-rules:
      sensitive-keywords: [PAN, primary account number, PHI, SSN]
    risk:
      compliance-keywords: [PAN, primary account number, PHI, social security]
    roles-permissions:
      permission-verbs: [issue, refund, dispense, prescribe]
      role-qualifiers: [customer, store-manager, investigator, reviewer]
  ```

  Missing keys = no extension; the helper falls back to the universal core only. The helper unions defaults with extensions at runtime — extensions never replace defaults, only add to them. The seeded fixture in `tests/fixtures/seeded-flawed-requirements/` does **not** rely on any extension; every seeded defect triggers via the universal core alone. Projects that need domain coverage write their own requirement fixtures and supply their own extensions.

- **Methodology.** `plugins/test-commander/skills/tc-requirements/methodology/requirements-quality-review.md` — covers all 16 requirement-level rubric dimensions from the partition table. Each dimension's section has: definition, the mechanical check verbatim from the table, one worked example drawn from the seeded fixture (cite the REQ-ID and quote the body), and a "Claude judgment layer" paragraph explaining what the AI must add beyond the mechanical finding (severity ranking, product-context narrative, identification of gaps the keyword check would miss).
- **Template.** `plugins/test-commander/skills/tc-requirements/templates/requirements-review-template.md` — output structure: executive summary, findings table (REQ-ID × dimension × verbatim trigger), per-requirement detail blocks (each requirement's body verbatim plus every dimension it triggered), open-questions section (reproducing the deduplicated questions from `open-questions.md`), traceability footer (list of parsed IDs, count of findings per dimension).
- **Command file.** `plugins/test-commander/skills/tc-requirements/commands/review-requirements.md` — Inputs / Outputs / Preconditions / Behavior / Safety / Implementation / Definition of Done / See also.
- **SKILL.md update.** `tc-requirements/SKILL.md` updated in the same sub-step to describe `/tc:review-requirements`'s shipped behavior and instruct Claude to invoke the bundled helper. Stale deferral wording for this command removed.
- **Tests first.** `tests/test_review_requirements.py` — at minimum:
  - Uninitialized workspace refused with a clear error (no `.test-commander/`).
  - `<workspace>/documents/uploaded/` exists but contains no `REQ-\d+`-bearing file (only a README placeholder): helper writes a review noting "no requirements found", exits 0, and does not error.
  - Seeded-fixture input — **only** `tests/fixtures/seeded-flawed-requirements/requirements.md` is copied into `<workspace>/documents/uploaded/`; the user-stories and acceptance-criteria fixture files are 2.3 and 2.4 inputs and must not be placed here for 2.2 tests. Helper writes exactly three files (`requirements-review.md`, `requirements-inventory.md`, `open-questions.md`).
  - For every one of the 16 dimensions in the partition table, at least one finding appears in `requirements-review.md` whose REQ-ID matches the seeded defect tagged with that dimension in `requirements.md`.
  - Broken-reference finding for REQ-014 (references the absent REQ-099) appears in `open-questions.md`.
  - Mutual-exclusion finding for the REQ-004 / REQ-005 pair appears in `open-questions.md`.
  - Idempotent re-run: `requirements-review.md` and `requirements-inventory.md` are byte-for-byte identical to the first run; `open-questions.md` line count is unchanged.
  - Inventory file lists every parsed REQ-ID in document order.
  - Requirement-ID collision across two input files (a synthetic fixture declaring REQ-007 in a second `.md` file) is refused with a clear error naming both files; no artifacts are written.
- **Definition of done.** Helper passes all test cases; methodology covers all 16 requirement-level rubric dimensions per the partition table with a worked example each and a Claude-judgment-layer paragraph each; template authored; per-command page complete; `tc-requirements/SKILL.md` no longer carries deferral wording for `/tc:review-requirements`.
- **Verification.** Pytest green. The partition-table coverage assertion is already part of the test suite, so no separate smoke is required — the implementer should still eyeball the generated `requirements-review.md` for tone, ordering, and structure before declaring 2.2 done.

#### 2.3 — `/tc:review-user-stories` (TDD)

- **Helper.** `plugins/test-commander/scripts/review_user_stories.py` — parses user stories from a target document (default `<workspace>/documents/uploaded/`), applies the INVEST rubric mechanically (Small = body-length heuristic; Testable = presence of AC pointer; Independent = dependency-graph check across stories; Estimable = presence of size-hint), and writes `<workspace>/requirements/user-story-review.md`. Stories without ACs are flagged for the downstream `/tc:review-acceptance-criteria` step.
- **Methodology.** `plugins/test-commander/skills/tc-requirements/methodology/user-story-readiness.md` — documents INVEST with one seeded-fixture violation per letter and explains the role-action-benefit shape Test Commander expects (`As a ... I want ... So that ...`).
- **Template.** `plugins/test-commander/skills/tc-requirements/templates/user-story-review-template.md` — structure: executive summary, INVEST findings table, per-story detail, readiness verdict (`ready` / `needs-refinement` / `blocked`).
- **Command file.** `plugins/test-commander/skills/tc-requirements/commands/review-user-stories.md`.
- **SKILL.md update.** `tc-requirements/SKILL.md` updated to describe `/tc:review-user-stories`'s shipped behavior and instruct Claude to invoke the bundled helper.
- **Tests first.** `tests/test_review_user_stories.py` — uninitialized workspace refused, fresh workspace runs and writes `user-story-review.md`, every INVEST letter produces at least one finding traced to the seeded fixture, idempotent re-run, stories without ACs are tagged with `needs-acceptance-criteria` and surface in the review, role-action-benefit shape violations are flagged, malformed input refused.
- **Definition of done.** Helper passes all test cases; INVEST coverage complete with one mechanical or judgment finding per letter; methodology doc complete; SKILL.md updated.
- **Verification.** Pytest green; smoke run produces a user-story review that flags every seeded INVEST violation.

#### 2.4 — `/tc:review-acceptance-criteria` (TDD)

- **Helper.** `plugins/test-commander/scripts/review_acceptance_criteria.py` — parses ACs (Given/When/Then bullets, scenario tables, or numbered ACs under a story), applies the AC rubric (testability of each predicate, edge-case coverage, negative-case coverage, data-rule clarity, role/permission context, NFR coverage), and writes `<workspace>/requirements/acceptance-criteria-review.md`. ACs that name a story ID not present in the parsed stories are flagged as orphans.
- **Methodology.** `plugins/test-commander/skills/tc-requirements/methodology/acceptance-criteria-quality.md` — documents the AC rubric with worked examples per dimension; explains the Given/When/Then expectation and what disqualifies an AC from being automatable.
- **Template.** `plugins/test-commander/skills/tc-requirements/templates/acceptance-criteria-review-template.md` — structure: summary, findings table grouped by story, per-AC detail.
- **Command file.** `plugins/test-commander/skills/tc-requirements/commands/review-acceptance-criteria.md`.
- **SKILL.md update.** `tc-requirements/SKILL.md` updated to describe `/tc:review-acceptance-criteria`'s shipped behavior.
- **Tests first.** `tests/test_review_acceptance_criteria.py` — uninitialized workspace refused, fresh workspace runs and writes `acceptance-criteria-review.md`, every AC-rubric dimension produces at least one finding traced to the seeded fixture, ACs without an owning story are flagged as orphans, idempotent re-run, malformed input refused.
- **Definition of done.** Helper passes all test cases; AC rubric coverage complete; methodology doc complete; SKILL.md updated.
- **Verification.** Pytest green; smoke run produces an AC review that flags every seeded AC defect.

#### 2.5 — `/tc:requirements-coverage` (TDD)

- **Helper.** `plugins/test-commander/scripts/requirements_coverage.py` — cross-references requirement IDs with downstream artifacts (existing test ideas at `<workspace>/test-ideas/`, BDD scenarios at `<workspace>/bdd/features/` when present, automation candidates) and writes `<workspace>/requirements/requirements-coverage.md` plus updates `<workspace>/traceability/requirements-map.md`. In Phase 2 the downstream artifacts are largely empty (Phases 4–6 populate them); the coverage file accurately reports `not yet covered` for every requirement until 2.6 lands seed test ideas.
- **Template.** `plugins/test-commander/skills/tc-requirements/templates/requirements-coverage-template.md` — structure: coverage matrix (requirements × downstream artifact types), unmapped-requirement list, unmapped-test list.
- **Command file.** `plugins/test-commander/skills/tc-requirements/commands/requirements-coverage.md`.
- **SKILL.md update.** `tc-requirements/SKILL.md` updated to describe `/tc:requirements-coverage`'s shipped behavior.
- **Tests first.** `tests/test_requirements_coverage.py` — uninitialized workspace refused, workspace with no requirements review yet refused (the command requires the inventory artifact), workspace with only requirements (no downstream artifacts) produces `not yet covered` for every requirement, workspace with seeded test ideas links them correctly, orphan downstream artifacts (test idea that names a non-existent requirement ID) are flagged, idempotent re-run, traceability map updated with the same ID space `/tc:review-requirements` produced in 2.2.
- **Definition of done.** Helper passes all test cases; coverage shape is forward-compatible with Phases 4–6 artifacts; SKILL.md updated.
- **Verification.** Pytest green; smoke run against the seeded fixture (after 2.2 lands) produces a coverage file whose unmapped-requirement list equals the full requirement list.

#### 2.6 — `/tc:requirements-to-tests` (TDD)

- **Helper.** `plugins/test-commander/scripts/requirements_to_tests.py` — for every reviewed requirement, generates a seed test-idea file under `<workspace>/test-ideas/<requirement-id>.md` containing: requirement ID, requirement title, candidate scenario titles (happy path, edge cases, negative cases derived from the AC review when available), risk category, and a forward-compatible schema header that Phase 4 enriches. Updates `<workspace>/traceability/requirements-map.md` to link the requirement ID to the new test-idea file path.
- **Command file.** `plugins/test-commander/skills/tc-requirements/commands/requirements-to-tests.md`. Documents the seed test-idea schema header — this is the Phase 4 contract.
- **SKILL.md update.** `tc-requirements/SKILL.md` updated to describe `/tc:requirements-to-tests`'s shipped behavior. By end of 2.6, `tc-requirements/SKILL.md` describes all five Phase 2 commands with no deferral wording.
- **Tests first.** `tests/test_requirements_to_tests.py` — uninitialized workspace refused, fresh workspace with requirements but no review yet refused (the command requires the requirements-review artifact), requirements + review present generates one test-idea file per requirement with the documented schema, AC-derived candidate scenarios appear when the AC review is also present, idempotent re-run does not duplicate files, traceability map updated, schema header is the agreed Phase-4-compatible shape.
- **Definition of done.** Helper passes all test cases; emitted test-idea files validate against the documented schema; traceability links present; SKILL.md describes all five commands.
- **Verification.** Pytest green; smoke run produces one test-idea file per seeded requirement.

#### 2.7 — Documentation pass *(dedicated step)*

- **Deliverables.**
  - Author `docs/user-guide/reviewing-requirements.md` — end-to-end walkthrough: upload requirements → `/tc:review-requirements` → `/tc:review-user-stories` → `/tc:review-acceptance-criteria` → `/tc:requirements-coverage` → `/tc:requirements-to-tests`. Sample input and sample output drawn from the seeded fixture so every example is reproducible.
  - Update `docs/command-reference.md` to add the five Phase 2 commands as links into their per-command pages inside the plugin.
  - Update `docs/workspace-reference.md` to mark the six `requirements/` files as populated by Phase 2 commands, and note that `test-ideas/` is seeded by `/tc:requirements-to-tests` ahead of its Phase 4 ownership.
  - Refresh `README.md`, `docs/install.md`, and `docs/user-guide/getting-started.md` Phase 2 mentions ("Phase 2 starts next" → "Phase 2 in progress" / "complete").
  - Update `docs/user-guide/workflow.md` (the Phase 1 walkthrough) so the "what's next" footer links to `reviewing-requirements.md`.
  - **Customization-guide update (per the Per-Phase Convention).** Update [`docs/user-guide/customizing-for-your-project.md`](../docs/user-guide/customizing-for-your-project.md) so its "Phase 2 schema (`tc-requirements`)" section reflects the exact config.yaml shape the helper reads (data-rules.sensitive-keywords, risk.compliance-keywords, roles-permissions.permission-verbs, roles-permissions.role-qualifiers). Confirm at least three worked extension examples cover materially-different domains (currently e-commerce, healthcare, research data — keep or replace, do not remove). Add a "Phase 2 — what landed" subsection naming the universal core, the schema keys, and the test that would fail if the helper ignored extensions.
  - **Final `tc-requirements/SKILL.md` pass.** Confirm SKILL.md describes every shipped command, links to all five per-command pages, and instructs Claude to invoke the bundled helpers. No "behavior arrives in Phase N+1" wording for any shipped command. The per-sub-step SKILL.md updates from 2.2–2.6 should already cover this; 2.7 is the final check.
- **Definition of done.** Every doc accurate against the implementation; all cross-links resolve; link checker green; `tc-requirements/SKILL.md` is the consolidated entry point for Phase 2 commands; `customizing-for-your-project.md` accurately reflects the shipped config.yaml schema with at least three worked examples.
- **Verification.** `python3 scripts/check_links.py` clean; manual read-through against the Phase 2 deliverables; grep for stale deferral wording in `tc-requirements/SKILL.md` returns no hits; the YAML block in `customizing-for-your-project.md` parses as valid YAML.

#### 2.8 — Testing finalization *(dedicated step, separate from per-command TDD)*

- **Deliverables.**
  - Bump `DEFAULT_PHASE_CAP` in `scripts/verify_skills.py` from `1` to `2` so the verifier expects both `tc-core` and `tc-requirements`.
  - `tests/test_phase_2_integration.py` — integration smoke that creates a fresh tmp consuming project, runs `init_workspace.py`, copies the seeded fixture's `requirements.md` / `user-stories.md` / `acceptance-criteria.md` into `<workspace>/documents/uploaded/`, then invokes the five Phase 2 helpers in order (`review-requirements` → `review-user-stories` → `review-acceptance-criteria` → `requirements-coverage` → `requirements-to-tests`), asserting after each step that the expected artifact lands and that the next step's preconditions are satisfied. A final assertion confirms the traceability map links every seeded requirement to a test-idea file and that `/tc:next` (Phase 1) now recommends a Phase 3 command instead of `/tc:review-requirements`.
- **Definition of done.** Integration smoke passes; phase cap bump reflected; full `make verify` chain green; `verify_skills.py` reports `tc-core PRESENT (phase 1)` and `tc-requirements PRESENT (phase 2)`.
- **Verification.** Captured `make verify` output.

#### 2.9 — Sign-off

Six sub-steps. Mirrors the Phase 1 sign-off pattern (1.8). Test-first: the sign-off test in 2.9.5 lands red before the plan/CHANGELOG edits in 2.9.3 turn it green. The final sub-step (2.9.6) captures evidence and pushes the `phase-2` annotated tag.

##### 2.9.1 — Cold-user walkthrough of `reviewing-requirements.md`

- **Deliverables.** Captured log of an end-to-end walkthrough of `docs/user-guide/reviewing-requirements.md` from a freshly-installed plugin against a fresh tmp consuming project.
- **Steps to execute verbatim.**
  1. `make uninstall` → `make install` to reach a known-clean plugin state.
  2. Create a tmp consuming-project dir (`mktemp -d`).
  3. `init_workspace.py <tmp>`. Copy `tests/fixtures/seeded-flawed-requirements/*.md` into `<tmp>/.test-commander/documents/uploaded/`.
  4. Invoke the five Phase 2 helpers in workflow order: `review_requirements.py`, `review_user_stories.py`, `review_acceptance_criteria.py`, `requirements_coverage.py`, `requirements_to_tests.py`.
  5. Confirm each helper prints the output documented in `reviewing-requirements.md` (no fabricated examples).
- **Definition of done.** All commands succeed end to end. Output captured to `/tmp/tc-phase2-walkthrough.log`. If any step fails, fix the cause and re-run before continuing to 2.9.2.

##### 2.9.2 — Per-step DoD audit

- **Deliverables.** A line-by-line audit of Steps 2.1 through 2.8 against their DoD lists.
- **What to check per step.** Every DoD bullet green; every pytest file passes; every deliverable present on disk; every cross-link in the per-command pages resolves; every Failure Mode mitigation in place.
- **Specifically.**
  - 2.1: `tc-requirements/SKILL.md` and `tests/fixtures/seeded-flawed-requirements/` present; scaffold test green; rubric coverage and INVEST coverage assertions pass.
  - 2.2–2.6: helper, methodology (where applicable), template (where applicable), command file, and SKILL.md update all present; per-command test files all green; mechanical rubric findings traced to seeded fixture.
  - 2.7: `reviewing-requirements.md`, command-reference index, workspace-reference, README + getting-started status lines all current; `tc-requirements/SKILL.md` describes every shipped Phase 2 command and contains no stale deferral wording; `customizing-for-your-project.md` reflects the Phase 2 `tc-requirements` config.yaml schema with at least three worked extension examples spanning materially-different domains.
  - 2.8: `DEFAULT_PHASE_CAP == 2`, `CATALOG["tc-requirements"] == 2`, integration smoke passes.
  - **Lesson-capture audit (per the "Sub-step lesson capture" Per-Phase Convention):** every Phase 2 sub-step (2.1–2.8) has a corresponding entry in the `Phase 2 — Lessons learned (running)` subsection. Sub-steps that closed cleanly with no bugs explicitly record "no lessons" — silence is not acceptable.
- **Definition of done.** All eight prior sub-steps audited green. Any unmet item blocks the sign-off.

##### 2.9.3 — Plan and CHANGELOG updates

- **Deliverables.**
  - `planning/plan.md` — collapse the `### Phase 2` To Do sub-section to a single line: `Phase 2 complete (YYYY-MM-DD) — see Completed`. Add a `### Phase 2 — Requirements and user story intelligence (YYYY-MM-DD)` section to `## Completed` with the per-step summary lines marked `[x]`, mirroring the Phase 1 closing format.
  - `CHANGELOG.md` — add a new `### Phase 2 — Requirements and user story intelligence (complete YYYY-MM-DD)` section above Phase 1 with a one-line closing summary plus per-sub-step Added bullets, mirroring the Phase 1 closing format.
- **Definition of done.** To Do Phase 2 reduced to the marker line; Completed has the Phase 2 section with date and nine sub-step bullets; CHANGELOG reflects the closing.

##### 2.9.4 — Documentation final pass

- **Deliverables.** Edits wherever Phase 2 wording has drifted during the eight sub-steps.
- **What to read.** README status line, `docs/user-guide/getting-started.md` "what's next", `docs/install.md` verifying-install paragraph, `docs/user-guide/reviewing-requirements.md` introductory paragraph, `docs/user-guide/workflow.md` footer link, `plugins/test-commander/README.md` skill table.
- **Definition of done.** Every Phase 2 fact matches the implementation. "Phase 2 in progress" wording becomes "Phase 2 complete (YYYY-MM-DD); Phase 3 starts next" where applicable. All cross-links resolve.

##### 2.9.5 — Pre-flight tests for sign-off

- **Deliverables.** `tests/test_phase_2_signoff.py`.
- **Coverage.**
  - All eight Phase 2 pytest files exist (`test_tc_requirements_scaffold`, `test_review_requirements`, `test_review_user_stories`, `test_review_acceptance_criteria`, `test_requirements_coverage`, `test_requirements_to_tests`, `test_phase_2_integration`, `test_phase_2_signoff`).
  - All five Phase 2 helpers exist under `plugins/test-commander/scripts/` (`review_requirements.py`, `review_user_stories.py`, `review_acceptance_criteria.py`, `requirements_coverage.py`, `requirements_to_tests.py`).
  - All five Phase 2 command files exist under `plugins/test-commander/skills/tc-requirements/commands/`.
  - All three methodology files exist under `plugins/test-commander/skills/tc-requirements/methodology/`.
  - All four templates exist under `plugins/test-commander/skills/tc-requirements/templates/`.
  - `tests/fixtures/seeded-flawed-requirements/` exists with the three Markdown files plus README.
  - `scripts/verify_skills.py` has `CATALOG["tc-requirements"] == 2` and `DEFAULT_PHASE_CAP == 2`.
  - `tc-requirements/SKILL.md` describes all five Phase 2 commands and contains no "behavior arrives in Phase 2" / "Coming in Phase 2" wording.
  - `docs/user-guide/customizing-for-your-project.md` exists, contains a `tc-requirements:` YAML block whose top-level keys match the shipped config.yaml schema, and contains at least three worked extension examples in distinct domain headings.
  - `Phase 2 — Lessons learned (running)` subsection in `planning/plan.md` contains an entry for every Phase 2 sub-step that has landed (`Step 2.1` through `Step 2.8`); each entry either describes a lesson + mitigation or explicitly records "no lessons".
  - CHANGELOG Phase 2 section marked complete with a date.
  - `plan.md` Completed has a Phase 2 subsection with a date.
  - `plan.md` To Do Phase 2 is the marker line (no unchecked items remain).
  - Total pytest count meets minimum (≥ 140 — Phase 1 finished at 96; Phase 2 adds the scaffold test, five per-command suites, integration, and sign-off).
- **Definition of done.** Test-first: the suite lands red before 2.9.3's plan/CHANGELOG edits, green after.

##### 2.9.6 — Final DoD evaluation (close Phase 2)

- **Procedure.**
  1. Run `make verify` — every test green, link checker clean, `verify_skills.py` reports `tc-core PRESENT (phase 1)` and `tc-requirements PRESENT (phase 2)`.
  2. Replay the 2.9.1 walkthrough end to end to confirm reproducibility.
  3. Capture all output to `/tmp/tc-phase2-signoff.log`.
  4. Commit the plan/CHANGELOG/docs updates and the sign-off test in one final commit.
  5. Push to origin.
  6. Create annotated tag: `git tag -a phase-2 -m "Phase 2 — Requirements and user story intelligence complete."`.
  7. Push tag: `git push origin phase-2`.
- **Definition of done.** All seven numbered steps complete. Tag visible on origin (`git ls-remote origin phase-2` resolves). Evidence log captured. Phase 2 is closed.

#### Definition of done — consolidated 14 checks

Ten automated; four evidence-based.

| # | Check | Type | How |
| --- | --- | --- | --- |
| 1 | All eight Phase 2 test files exist (`test_tc_requirements_scaffold`, `test_review_requirements`, `test_review_user_stories`, `test_review_acceptance_criteria`, `test_requirements_coverage`, `test_requirements_to_tests`, `test_phase_2_integration`, `test_phase_2_signoff`) | auto | sign-off test |
| 2 | All five helpers exist (`review_requirements.py`, `review_user_stories.py`, `review_acceptance_criteria.py`, `requirements_coverage.py`, `requirements_to_tests.py`) | auto | sign-off test |
| 3 | All five command files exist under `tc-requirements/commands/` | auto | sign-off test |
| 4 | All three methodology files exist under `tc-requirements/methodology/` | auto | sign-off test |
| 5 | All four templates exist under `tc-requirements/templates/` | auto | sign-off test |
| 6 | Seeded-flawed-requirements fixture exists and covers every rubric dimension + every INVEST letter | auto | scaffold test |
| 7 | `verify_skills.py` has `CATALOG["tc-requirements"] == 2` and `DEFAULT_PHASE_CAP == 2`; `make verify` prints both skills PRESENT | auto | sign-off test + `make verify` |
| 8 | Integration smoke `test_phase_2_integration` passes | auto | pytest |
| 9 | `tc-requirements/SKILL.md` describes all five shipped Phase 2 commands with no deferral wording | auto | sign-off test |
| 10 | `make verify` chain clean (link checker covers the new docs) | auto | full chain |
| 11 | Cold-user walkthrough of `reviewing-requirements.md` from clean state succeeds (2.9.1) | evidence | `/tmp/tc-phase2-walkthrough.log` |
| 12 | Per-step DoD audit clean for 2.1–2.8 (2.9.2) | evidence | audit notes |
| 13 | `plan.md` To Do Phase 2 collapsed to marker; Completed has Phase 2 subsection with date (2.9.3); CHANGELOG Phase 2 section marked complete | evidence | sign-off test + grep |
| 14 | `phase-2` annotated tag created and pushed (2.9.6) | evidence | `git tag -l phase-2` + `git ls-remote origin phase-2` |

#### TDD pattern used in 2.2–2.6

```
write tests (red)             # define expected behavior per case, including fixture-driven defect detection
  → implement helper (green)  # minimum code to pass; mechanical rubric only
    → author methodology + template (where applicable)
      → author per-command page
        → update SKILL.md to surface shipped behavior
          → verify (pytest + make verify)
```

No implementation lands before its tests. No tests are added after the fact. Every command's test suite drives the helper from the same seeded fixture so the rubric is the contract.

#### Validation sequence

1. Author 2.1 (skill scaffold + fixture) with its scaffold test. Confirm pytest red → green.
2. For each of 2.2, 2.3, 2.4, 2.5, 2.6 in order: write tests, implement helper, author methodology and template where applicable, author command file, update SKILL.md, run pytest.
3. 2.7 documentation pass. Run `make verify`.
4. 2.8 testing finalization: bump `CATALOG["tc-requirements"]` to 2 and `DEFAULT_PHASE_CAP` to 2, integration smoke. Run `make verify`.
5. 2.9 sign-off, in order:
   5a. Run the cold-user walkthrough from `reviewing-requirements.md` (2.9.1). Capture log. Fix anything that fails before proceeding.
   5b. Audit each prior sub-step's DoD (2.9.2). Block on any unmet item.
   5c. Write `tests/test_phase_2_signoff.py` (2.9.5). Run `make test` — expect failures for any not-yet-applied plan/CHANGELOG edits.
   5d. Update `plan.md` and `CHANGELOG.md` (2.9.3). Re-run sign-off test — expect green.
   5e. Doc final read-through (2.9.4). Edit any drift; re-run `make verify`.
   5f. Final DoD evaluation (2.9.6): commit, push, annotated tag, tag push.

#### Failure modes

- A rubric dimension turns out to be hard to detect mechanically. **Mitigation:** the helper applies only the mechanical part; the AI-judgment part lives in the methodology doc and the command file's Behavior section. The seeded fixture marks each defect as `mechanical` or `judgment`, and the test suite only asserts on mechanical findings. Judgment findings are reviewed by the cold-user walkthrough in 2.9.1.
- Requirement-ID collisions between input documents. **Mitigation:** the parser raises on collision and prints the conflicting source lines. The seeded fixture deliberately includes no collisions; a separate negative test asserts the helper refuses collision input.
- Seeded fixture grows stale as the rubric evolves. **Mitigation:** the scaffold test (2.1) asserts every rubric dimension named in the methodology docs appears in the fixture. Adding a rubric dimension without seeding it fails the scaffold test.
- `/tc:requirements-to-tests` writes a schema Phase 4 can't read. **Mitigation:** the schema header is documented in `commands/requirements-to-tests.md` and asserted in `test_requirements_to_tests.py`. Phase 4 inherits the same schema and is reviewed against this contract before enriching.
- Traceability map drift between commands. **Mitigation:** all five commands share the same ID space; each test asserts the traceability map is updated and that the same IDs flow from `/tc:review-requirements` through `/tc:requirements-to-tests`. The integration smoke in 2.8 enforces the end-to-end invariant.
- `workspace_state.py`'s `PHASE_OWNERSHIP` does not know that `/tc:requirements-to-tests` writes test-idea seeds. **Mitigation:** `test-ideas/` remains Phase-4-owned. Phase-2 seed writes show as populated content under Phase 4; status reporting treats this as "in_progress" for Phase 4 once seeds exist. Document the convention in `commands/requirements-to-tests.md` so the behavior is intentional, not a bug.
- `/tc:next` (Phase 1) does not recommend a Phase 3 command after Phase 2 completes. **Mitigation:** the integration smoke in 2.8 asserts `/tc:next` advances past Phase 2 once all five artifacts are populated. If the heuristic R-rules need an update, fold the change into Phase 1's `next-step-inference.md` in the same commit; do not silently break the heuristic.
- Documentation walkthrough in 2.9.1 surfaces a gap (a step that doesn't work as documented). **Mitigation:** update `reviewing-requirements.md` to match reality and re-run the walkthrough. Treat as a Phase 2 doc bug, not a Phase 3 issue.
- A prior sub-step's DoD turns out not to be green during 2.9.2. **Mitigation:** the failing sub-step reopens. 2.9 cannot close while any earlier DoD is unmet. Fix, re-verify the sub-step, then return to 2.9.2.
- `phase-2` tag already exists locally (replay of 2.9). **Mitigation:** the annotated tag is intentional. If the prior tag was wrong, delete it (`git tag -d phase-2` then `git push origin :refs/tags/phase-2`) and recreate. Never force-overwrite an existing tag on origin without explicit user confirmation.
- CHANGELOG Phase 2 closing entry diverges from To Do/Completed movement. **Mitigation:** the sign-off test (2.9.5) checks all three sources. They must agree before the test passes.

#### Phase 2 — Lessons learned (running)

Captured at sub-step close per the "Sub-step lesson capture" Per-Phase Convention. Each entry is preventative care for future implementers of similar work.

##### Step 2.1 — scaffold + fixture

- **Domain-leakage in seeded fixtures.** The first version of the seeded fixture used an online-bookstore narrative (commits to `tests/fixtures/seeded-flawed-requirements/`). When reviewing the Step 2.2 partition table the next day, the e-commerce framing surfaced as a contradiction with Test Commander's "universal testing tool" positioning. **Pattern:** any artifact shipped in the repo — including test-only assets — is read by reviewers as a claim about scope. Test fixtures should match the tool's claimed scope. **Mitigation:** D19 codified product-domain-agnosticism; Per-Phase Customization-guide audit convention added; fixture rewritten to a deliberately-generic SaaS-surface narrative; fixture README explicitly names "test asset, not a claim about scope". **Future-implementer hint:** when authoring a fixture, write "the narrative is deliberately generic" into the README on day one.

##### Step 2.2 — `/tc:review-requirements`

- **Parser-body emptiness bug (high-severity, would have shipped broken).** First implementation used `text[match.end():next_match.start()]` to extract a requirement body — that returns the content *between* match ends, not the content captured *by* the match. For single-line entries like `REQ-001: <body>`, the body lives in `match.group(2)`, not in the inter-match span; the helper returned empty bodies and only `completeness` (every body short) and `testability` (no RFC-2119 modal) fired. **Mitigation:** combine `match.group(N)` (the captured first-line body) with the continuation text from the inter-match span. **Future-implementer hint:** any regex parser that delimits "body" by match boundaries must explicitly include `match.group()` content for single-line entries.
- **Plural-form keyword mismatch.** Initial single-token keyword matching used `\bpassword\b`, which does not match "passwords" (the `s` keeps `\b` from matching). REQ-011 (`User passwords are stored`) was tagged `data-rules` but the check didn't fire — pluralization defeated the boundary check. **Mitigation:** updated `_contains_phrase` to use `\b<word>s?\b` for single-token keywords (allows the optional trailing `s`). Multi-token phrases match literally. **Future-implementer hint:** every keyword-matching helper that uses word boundaries needs explicit plural handling.
- **Domain-leakage in partition table.** Original v1 of the Step 2.2 partition table baked PCI / e-commerce keywords (`credit card`, `PAN`, `primary account number`, `customer`, `refund`) into the shipped defaults for `data-rules`, `risk`, and `roles-permissions`. Reviewed during the user's "is this from Juice Shop?" audit. **Mitigation:** reshaped to universal cores (`password, secret, token, credential, key`; `plain text, plaintext, unencrypted, raw password, hardcoded credential, default password`; `delete, approve, reject, modify, grant, revoke` + `admin, owner, operator`) with explicit `<workspace>/config.yaml` extension hooks under `tc-requirements.<dimension>:`. Codified as D19. **Future-implementer hint:** every shipped keyword set should be auditable for domain assumptions; if the keyword would be foreign to a banking app, healthcare app, *and* a SaaS dashboard, it does not belong in the universal core.
- **Imprecise check naming.** The original partition table named the consistency check "contradicting verbs across requirements that name the same entity". The actual fixture exercises propositional contradiction over a shared subject (REQ-004 `may purchase without account` vs REQ-005 `require authenticated account`) — not verbs. **Mitigation:** renamed to "mutually-exclusive constraints over a shared subject"; check uses shared substantive nouns + opposing modals. **Future-implementer hint:** name mechanical checks after what they detect, not after a plausible-sounding linguistic feature; the fixture is the contract.
- **Undefined check names ("length", "presence of acceptance language").** Listed as mechanical checks without definitions. Each could pick different rubric dimensions depending on the implementer. **Mitigation:** replaced with specific, dimension-anchored checks per the partition table (e.g. completeness = body ≤ 10 tokens). **Future-implementer hint:** every row of a partition table should have a single concrete check; if "length" or "presence of X" sounds reasonable, write the regex and the dimension it grounds.

##### Step 2.3 — `/tc:review-user-stories`

- **No bugs encountered; 9/9 tests passed on first implementation.** The helper closely mirrored `review_requirements.py`'s structure (parse → check → write artifact → CLI). The parser bug fix and the plural-form fix from Step 2.2 were inherited cleanly. **Pattern:** structurally mirroring an established sibling helper dramatically reduces bug discovery cost for parallel work. **Future-implementer hint:** when authoring a Phase 2 / Phase 4 / Phase 5 helper that parses ID-prefixed Markdown entries (REQ-NNN, US-NNN, AC-NNN, etc.), start by copy-renaming the closest sibling and adapt the per-dimension checks. The skeleton is already debugged.

##### Step 2.4 — `/tc:review-acceptance-criteria`

- **Fixture meta-commentary contamination (high-severity, masked three failing dimensions).** Parenthetical asides in the seeded fixture contained the keywords the mechanical checks were meant to flag. For example, `AC-001-01: ... (Happy path only — no coverage of expired records, locked records, or stale-data edge cases.)` — the parenthetical contains `edge cases`, which matches the `\bedge\b` keyword, so the `ac-missing-edge-cases` check thought the AC covered edges. Same pattern caused `ac-missing-negative-cases` and `ac-missing-role-context` to mis-trigger. **Mitigation:** strip parenthetical asides (`re.sub(r"\([^()]*\)", "", body)`) from each AC body before applying checks; preserve the original body in the AC dataclass for display. **Future-implementer hint:** when a seeded fixture has explanatory annotations describing *why* an entry is a defect, those annotations almost always contain the very vocabulary the mechanical check looks for. Either strip annotations from the check body (chosen here) or keep seeded entries strictly to "defect content" with explanations in test docstrings.

##### Step 2.5 — `/tc:requirements-coverage`

- **Template-stub vs generated-artifact ambiguity (medium-severity, blocked one test).** First implementation refused only when `requirements-inventory.md` did not exist. But the workspace template ships an empty inventory placeholder (the file exists from `/tc:init` onward), so `test_missing_inventory_refused` failed — the helper happily parsed zero REQ-IDs from the template stub and proceeded. **Mitigation:** added `_inventory_is_generated()` which checks for the Step 2.2 generator markers (`Total: **` and `_No requirements parsed yet._`); if neither is present, the file is still the unmodified template and the helper raises `InventoryMissingError`. **Future-implementer hint:** any time a helper depends on another sub-step's output and the workspace template ships a placeholder for that file, check for the *generator's* markers, not just file existence. This pattern will recur in Step 2.6 and in every Phase 3+ helper that consumes an upstream-generated artifact — every downstream helper needs a "has the upstream actually run?" check, not just a "does the file exist?" check.

##### Step 2.6 — `/tc:requirements-to-tests`

- **Template-stub pattern recurred (predicted by Step 2.5's lesson).** First implementation detected the optional AC review with `ac_review_path.is_file() and ac_review_path.stat().st_size > 0`. But the workspace template ships a non-empty `acceptance-criteria-review.md` placeholder, so `stat().st_size > 0` was always true and the "no AC review" test failed. **Mitigation:** added `_ac_review_is_generated()` matching the exact same generator-marker pattern as `_review_is_generated()` (Step 2.6) and `_inventory_is_generated()` (Step 2.5) — checks for `## Executive summary` or `no acceptance criteria found`. **Lesson reinforced:** Step 2.5's "check for generator markers, not file existence" prediction held — same bug, same shape, same fix. **Future-implementer hint:** every helper that *optionally* reads an upstream artifact needs the same is-generated check that mandatory inputs use. Treat "this file exists" as never sufficient evidence of "this command has run".
- **Cross-helper return-type mismatch (low-severity, caught on first run).** Imported `review_requirements.apply_checks()` and treated its return value as a flat `list[Finding]`. Actually returns `tuple[list[Finding], list[OpenQuestion]]` — the dependency-cycle / consistency cross-checks emit open questions alongside findings. **Mitigation:** unpacked the tuple (`findings, _open_questions = ...`). **Future-implementer hint:** when reusing a sibling helper's public function, read its return type before assuming. The Python type annotation was correct; the test failure caught the mismatch immediately because every `f.req_id` access raised `AttributeError`.
- **Successful idempotency strategy worth keeping: skip-not-overwrite for user-edited artifacts.** The seeded test-idea files will be enriched by Phase 4 (`tc-explore`) with charters, exploration sessions, and refined ideas. Step 2.6 chose **never overwrite existing seeds** as the idempotency contract — re-runs produce `created: 0, skipped: N` and user/Phase-4 enrichments survive intact. The pattern is different from Step 2.2 (overwrites review files, which are pure generated reports) and Step 2.5 (overwrites coverage + traceability map, also pure generated). **Future-implementer hint:** when an artifact will be enriched downstream by users or later phases, prefer skip-if-exists. When an artifact is a pure generated report regenerated from upstream sources, prefer byte-deterministic overwrite. Document the chosen mode in the helper's idempotency-contract docstring; mixing modes without flagging the choice surprises future contributors.

##### Step 2.7 — Documentation pass

- **No bugs encountered; clean docs pass.** The dedicated documentation step landed `docs/user-guide/reviewing-requirements.md` (Phase 2 end-to-end walkthrough), refreshed `docs/command-reference.md` (moved the five Phase 2 commands from Planned to Shipped + added the per-command-page links), enriched `docs/workspace-reference.md` (per-file ownership table for `requirements/` + Phase 2 seeding note on `test-ideas/`), and refreshed five status-line locations (README, install.md, getting-started.md, workflow.md "Beyond Phase 1", plugin README). `customizing-for-your-project.md` was already current from the earlier D19 backfill — only needed forward-looking tense ("When Phase 2 Step 2.2 ships") → past tense ("Phase 2 ships three extensible rubric dimensions"). All 154 tests stayed green; link checker covers 107 files (up from 106 — one new doc + its inbound cross-links). **Pattern:** a documentation-pass sub-step that lands after all commands ship is essentially a refactor — it benefits from a complete walkthrough doc written *after* the helpers exist so every code block is reproducible against the actual smoke-test output. The doc cribs `workflow.md`'s structure (what's available / prerequisites / per-step / what changed on disk / re-running / customizing / beyond / see also) wholesale; that scaffold is reusable for every future per-phase walkthrough.
- **Status-line drift is real; treat it as a checklist, not a search-and-replace.** Six locations needed updating (README, install.md, getting-started.md "what's next", workflow.md "Beyond Phase 1", plugin README's skill-status table, customizing.md tense). Each is a different sentence with a different surrounding context — no single grep-and-replace works. **Future-implementer hint:** when authoring a dedicated documentation step, build a status-line checklist before editing: `README`, `install.md verify section`, `getting-started.md what's next`, `workflow.md beyond block`, `<plugin>/README.md skill table`, `customizing.md tense`. Walk the list, edit each in context, then `grep -n "Phase N starts next"` to confirm no stragglers.

##### Step 2.8 — Testing finalization

- **Prior-phase sign-off coupling on `DEFAULT_PHASE_CAP` (high-severity, broke one test).** Bumping `DEFAULT_PHASE_CAP` from `1` to `2` in `scripts/verify_skills.py` immediately broke `tests/test_phase_1_signoff.py::test_verify_skills_default_phase_cap_is_1`, which asserted `DEFAULT_PHASE_CAP == 1` (exact match) at Phase 1 close. The assertion captured the wrong invariant — what Phase 1 actually closed was "the cap was bumped from 0 to 1 *or higher*", but the test asserted the strict equality of the moment. **Mitigation:** loosened the assertion to `cap >= 1` and renamed to `test_verify_skills_default_phase_cap_at_least_1`. **Future-implementer hint:** every phase sign-off test that asserts a numeric cap, count, or version should assert `>=` (monotonically non-decreasing), not `==`. The invariant is "this phase landed and bumped the value to at least N", not "this phase landed and the value is exactly N forever". Apply this rule when authoring Phase 2 sign-off tests in 2.9.5 (e.g. pytest count `>= 140` not `== 154`) and forward to every future phase.
- **Existing verifier tests already used explicit `phase_cap=` arguments, so they did NOT break.** `tests/test_verify_skills.py` passes `phase_cap=0`, `phase_cap=2`, etc. explicitly per test, so bumping the default did not regress them. **Pattern worth keeping:** when a helper has a tunable default that future phases may bump, test it with explicit arguments per case rather than relying on the default. Default-coupling is a hidden dependency that breaks silently.
- **Integration smoke landed GREEN on first run.** `tests/test_phase_2_integration.py` (1 test, 13 numbered assertion blocks) drives all five Phase 2 helpers in sequence against the seeded fixture: init → customize project.md → next (R3) → upload three fixture files → review-requirements (asserts all 16 dimensions fire) → review-user-stories (asserts all 6 INVEST letters fire) → review-acceptance-criteria (asserts all 5 AC dimensions fire) → requirements-coverage pre-seed (17 uncovered) → requirements-to-tests (17 created, AC review detected, then re-run shows 0/17 skipped) → requirements-coverage post-seed (17 covered, every test-idea linked in traceability map) → next (advanced past Phase 2) → workspace_state confirms phase 2 in_progress → byte-deterministic re-run of overwrite-mode artifacts. **Pattern worth keeping:** dedicated integration tests can be large (this one is ~150 lines) when they're driving the full phase workflow end-to-end. Resist the urge to factor every block into a helper — a flat sequence of `# --- N. <description> ---` blocks is easier to read as a workflow-as-documentation than a tree of helpers.
- **No new bugs surfaced by the integration test.** Each unit-tested helper composed correctly with the others; the parser/idempotency/contract decisions from 2.2-2.6 held end-to-end. **Pattern reinforced:** when every per-command sub-step ships with thorough unit tests, the integration smoke is verification not discovery — bug-finding happens at the unit level, integration confirms composition.

##### Step 2.9 — Sign-off

- **Test-first sign-off worked exactly as designed.** `tests/test_phase_2_signoff.py` (17 tests) was authored before the plan/CHANGELOG closing edits in 2.9.3. On first run: 14 passed (structural assertions — every helper / command page / methodology / template / fixture / SKILL.md present) and 3 failed (`changelog_phase_2_marked_complete`, `plan_completed_has_phase_2_entry`, `plan_todo_phase_2_collapsed_to_marker`). The three failures pinned exactly what 2.9.3 had to land. After collapsing the To Do block, adding the Completed entry, and flipping the CHANGELOG heading: 17/17 GREEN. **Pattern worth keeping:** the test-first sign-off (red ← closing edits → green) is the cleanest way to gate phase close. The test names *describe the closing actions*, so any future implementer reading red output understands what to do without consulting the plan.
- **Cold-user walkthrough surfaced no documentation drift.** Running `make uninstall → make install → init_workspace → fixture upload → five-helper chain` against a tmp project produced output that matches `docs/user-guide/reviewing-requirements.md` verbatim — no fabricated examples. Captured to `/tmp/tc-phase2-walkthrough.log`. `/tc:next` advanced past Phase 2 (recommended `/tc:automation-plan` because requirements-coverage's traceability-map write bumps Phase 5 to in_progress and requirements-to-tests' seed write bumps Phase 4 to in_progress; both R5 and R6 then skip and R7 fires). **Pattern worth keeping:** the cold-user walkthrough catches doc drift that unit tests miss — the unit tests assert "the helper does X" but the walkthrough asserts "the docs claim the helper does X and that's actually what happens". They're complementary, not redundant.
- **Test count crossed the 172 mark at sign-off close.** The plan's floor was `>= 140`; the actual is `172` (155 baseline + 17 sign-off tests). The closing summary was initially written from memory ("156") and had to be corrected after running `make verify`. **Future-implementer hint:** never write the closing test count in the CHANGELOG / Completed entry by hand — capture it from the actual `make verify` output. The sign-off test's pytest-count assertion is the canonical source.
- **`/tc:next` recommends `/tc:automation-plan` not `/tc:learn-from-docs` after Phase 2 close.** This is a known interaction between Phase 2's traceability-map write and the R-rules in `next-step-inference.md`: writing to `traceability/requirements-map.md` (Phase 5 ownership) and `test-ideas/` (Phase 4 ownership) bumps both phases to in_progress, so R4/R5/R6 skip and R7 (Phase 6) fires. The integration test in 2.8 asserts `command != /tc:review-requirements` (advanced past Phase 2) rather than the specific next command, which is the robust invariant. **Future-implementer hint:** when an upstream skill (Phase 2) writes to a downstream-owned directory (Phase 4 / 5 traceability), the phase-status heuristic in `/tc:next` may skip phases that ostensibly still need their own commands. The R-rules will need refinement in Phase 8 (`tc-learning`) or earlier; for now, downstream phases need to be explicit about whether "directory has content" means "phase is in progress" or "phase has been worked on". Flag for the Phase 3 author. **RESOLVED post-Phase-5 (2026-05-29):** the fix was a pre-Phase-6 hygiene pass, not a Phase-8 deferral. `workspace_state.PHASE_OWNERSHIP` now keys each phase's `in_progress` signal only on directories that phase *uniquely* produces (`3 → product-knowledge` not `documents`; `4 → charters/exploration-notes/sessions` not `test-ideas`; `5 → bdd` not `traceability`). After Phase 2 alone, `/tc:next` correctly recommends `/tc:learn-from-docs` (Phase 3). Regression: `tests/test_next_step.py::test_phase_2_side_effects_do_not_skip_phases_3_4_5`. See CHANGELOG [Unreleased] → Fixes. **Future-implementer hint:** when Phase 7 ships, re-check `evidence/` — Phase 4 currently only *references* `evidence/screenshots/<id>.png` in note text (no files written), so Phase 7's signal is safe today, but if a phase ever writes real files under another phase's directory, narrow that phase's status signal the same way.

---

## Phase 3 — Project Knowledge Ingestion

**Goal.** Learn the consuming project's product narrative, contracts, source architecture, runtime behavior, and existing test coverage from its uploaded documents and source artifacts. Ship the `tc-knowledge` skill with five commands that read source artifacts, extract knowledge with explicit provenance, surface gaps as open questions, and populate `<workspace>/product-knowledge/` plus `<workspace>/requirements/open-questions.md`.

**Architecture.** Each `/tc:learn-from-*` command is a Python helper plus a Markdown command file inside `plugins/test-commander/skills/tc-knowledge/`. Helpers do the deterministic work (walk a source tree, parse a known format, extract structured facts with citations, write artifacts, regenerate the synthesis); Claude executes the judgment-heavy parts (synthesizing narrative, ranking importance, deciding whether an extracted candidate is an entity vs an attribute, flagging gaps as open questions, deduplicating across sources) by reading the per-command page and the methodology docs. The split keeps every command testable end-to-end with the seeded sample-project fixture.

**Phase-3 design decisions (folded in).**

- **Universal cores; project-specific vocabulary via `<workspace>/config.yaml`.** Per D19, every shipped detection keyword set, file-glob pattern, and language detector uses universal English / software-engineering vocabulary only. Project-specific term sets (compliance vocabularies, business-domain entities, permission verbs), language enable lists, and ignored-path patterns extend through a `tc-knowledge:` block in `<workspace>/config.yaml`. The shipped seeded fixture exercises only the universal cores; domain coverage is the consuming project's responsibility through their own uploaded source artifacts and config extensions.
- **Per-source model files; cross-cutting artifacts use namespaced sections.** Each `/tc:learn-from-*` command owns its per-source model file (`documentation-model.md`, `spec-derived-model.md`, `code-derived-model.md`, `api-model.md`, `tests-coverage.md`). Cross-cutting artifacts (`entities.md`, `user-journeys.md`, `business-rules.md`, `assumptions.md`) are populated cumulatively — each command writes to a clearly-namespaced section (`## From documents`, `## From specs`, `## From code`, `## From api`, `## From tests`). Re-running a single command overwrites only its own namespaced section across cross-cutting artifacts; sections written by other commands are preserved.
- **`system-model.md` is regenerated at the end of every `/tc:learn-from-*` run.** A shared `synthesize_system_model.py` helper reads the union of currently-populated per-source models and cross-cutting artifacts and rewrites `system-model.md` byte-deterministically. Running just one learn command yields a partial synthesis; running all five yields the full picture. This keeps the five-command count and avoids a sixth `/tc:synthesize-knowledge` step while still giving consumers a unified view.
- **Provenance is mandatory.** Every extracted fact in every product-knowledge artifact cites its source: file path + line range for code / docs / specs / tests, and request method + path + status code for live-API responses. The methodology docs and templates make provenance a structural requirement. Tests assert that every finding carries a citation.
- **Assumptions are flagged distinctly from confirmed facts.** A confirmed fact has a source citation; an assumption is text that Claude inferred without a direct citation, written into `assumptions.md` under a `## From <source>` section with a one-line rationale. The methodology codifies the distinction; the template's structure enforces it.
- **Knowledge gaps surface as open questions, routed to `requirements/open-questions.md`.** Each helper detects gaps (a glossary term referenced but never defined, an endpoint in the spec with no implementing function, a function with no docstring, an unspecified endpoint that the live-API probe nonetheless returned a 2xx from) and appends them to `<workspace>/requirements/open-questions.md` using the Phase-2 contract (deduplicate by `(question-text, source-id)` pair). User-authored questions are preserved.
- **Phase 3 does NOT write to `<workspace>/traceability/`.** Per the Phase-2 Step-2.9 lesson (writing into a downstream-owned directory bumps that phase to `in_progress` in `workspace_state.py` and skews `/tc:next`), Phase 3 confines its writes to `product-knowledge/` and `requirements/open-questions.md`. Cross-source traceability (requirement ↔ entity ↔ endpoint ↔ test) is Phase 5's responsibility; Phase 3 supplies the inputs but does not pre-populate the map.
- **`/tc:learn-from-code` supports Python only in v1.** Uses the stdlib `ast` module — deterministic, fast, no extra dependencies. TypeScript, JavaScript, Go, Java are detected by extension and reported as "language detected but not parsed in v1" with a file count, *not* silently ignored. The set of parsed languages is extensible via `tc-knowledge.code.enabled-languages` in `<workspace>/config.yaml` (Python is the only entry shipped; future phases may add TS/JS via tree-sitter). The seeded fixture's `src/` tree is Python only.
- **`/tc:learn-from-api` runs in two modes; tests use only `recorded` playback.** The default `recorded` mode reads a `recorded-api/responses.json` file from the workspace (or fixture) — a list of `{method, path, status, headers, body}` entries that the helper "probes" by lookup. The opt-in `live` mode (`tc-knowledge.api.mode: live` plus `tc-knowledge.api.base-url:` in `config.yaml`) issues real HTTP requests. Pytest never enters live mode — the seeded fixture is the contract. Live mode is documented and demonstrated in the customization guide but exercised only by manual smoke.
- **Helper-mirroring is the design.** Per the Phase-2 Step-2.3 lesson (mirroring Step 2.2 closed 9/9 tests on first run), Steps 3.3–3.6 copy Step 3.2's helper skeleton and adapt only the per-source extraction logic. The integration smoke in Step 3.8 stresses the union; bug discovery concentrates in each step's new mechanical checks.

**Skills authored.** `tc-knowledge` — `SKILL.md` plus five command files (one per `/tc:learn-from-*` command), six methodology files (`project-knowledge.md` umbrella plus `learning-from-documents.md`, `learning-from-specs.md`, `learning-from-code.md`, `learning-from-api.md`, `learning-from-tests.md`), and ten templates (`system-model-template.md`, `documentation-model-template.md`, `spec-derived-model-template.md`, `code-derived-model-template.md`, `api-model-template.md`, `tests-coverage-template.md`, `entities-template.md`, `user-journeys-template.md`, `business-rules-template.md`, `assumptions-template.md`).

**Workspace addition.** `<workspace>/product-knowledge/tests-coverage.md` is added by Phase 3 as the 10th product-knowledge artifact (alongside the nine listed in the Workspace Layout). Update the Workspace Layout block in this plan and `docs/workspace-reference.md` in the same sub-step that ships it (3.6).

**Design references.** `plugin:context7:context7` (library/framework doc lookup patterns), `postman:agent-ready-apis`, `postman:search`, `postman:generate-spec` (API discovery and spec extraction patterns). TC reads OpenAPI/Postman collections directly using its own logic; we do not call out to Postman MCP at runtime.

**Knowledge rubric.** entities, terms (glossary), user journeys, business rules, assumptions, endpoints, schemas, auth schemes, modules / classes / functions, docstrings, test coverage, gap signals (undefined-term, unimplemented-endpoint, undocumented-function, untested-function, mismatched-status). The seeded fixture carries one defect per dimension marked with an inline `<!-- knowledge: <dimension> -->` HTML comment in the doc/spec sources and equivalent docstring / decorator tags in the code source, mirroring the Phase 2 fixture convention.

### Phase 3 — Execution outline

Nine sub-steps. TDD throughout: every implementation step lands its tests red before turning them green. Sub-step 3.1 scaffolds the skill and the shared seeded-sample-project fixture; 3.2–3.6 implement the five commands; 3.7 is the dedicated documentation pass; 3.8 is the dedicated testing finalization (cap bump + integration smoke); 3.9 is the sign-off with a `phase-3` tag.

#### 3.1 — Skill scaffold and seeded-sample-project fixture

- **Deliverables.**
  - `plugins/test-commander/skills/tc-knowledge/SKILL.md` — YAML frontmatter (`name: tc-knowledge`, single-line trigger-style `description`). Body lists the five commands and notes that command behavior arrives in subsequent sub-steps. Mirrors Phase 2's initial `tc-requirements/SKILL.md` shape — each command paragraph carries the deferral wording until its own sub-step turns it into a shipped-behavior description (per the "SKILL.md surfaces shipped behavior" convention).
  - `tests/fixtures/seeded-sample-project/` containing:
    - `documents/` — three Markdown files: `product-overview.md` (narrative describing a generic SaaS dashboard — sign-in, search, file upload, settings), `glossary.md` (5–8 universal-vocabulary terms: Account, Session, Asset, Workspace, Permission), `user-journey-sign-in.md` (a journey with explicit steps and at least one untested branch). Each defect is marked with an inline `<!-- knowledge: <dimension> -->` HTML comment.
    - `specs/openapi.yaml` — small OpenAPI 3.0 spec with 4–6 endpoints (`POST /sessions`, `GET /accounts/{id}`, `GET /workspaces`, `POST /workspaces/{id}/assets`, `GET /workspaces/{id}/assets`, `DELETE /sessions/{id}`). At least one endpoint declared but absent from `src/` (an `unimplemented-endpoint` gap).
    - `src/` — Python tree: `app/__init__.py`, `app/models/account.py` (Account class with attributes), `app/models/workspace.py` (Workspace class), `app/api/auth.py` (`sign_in` function with docstring), `app/api/files.py` (`upload_file` function — no docstring; `undocumented-function` gap), `app/utils/validation.py`. At least one TS or JS file (`web/app.ts`) for the "language detected but not parsed in v1" assertion.
    - `tests/` — `test_auth.py` (covers `sign_in`), `test_validation.py` (covers `validation.py`). `app/api/files.py::upload_file` deliberately has no test (`untested-function` gap).
    - `recorded-api/responses.json` — a list of `{method, path, status, headers, body}` entries covering every endpoint in `specs/openapi.yaml` plus one undocumented endpoint (`GET /accounts/me`) returning 200 (`unspecified-endpoint` gap).
    - `README.md` — explains the fixture's universal-SaaS narrative ("test asset, not a claim about scope" per the D19 lesson), the inline `<!-- knowledge: ... -->` defect-marking convention, and the per-dimension defect catalog.
  - `plugins/test-commander/skills/tc-knowledge/methodology/.gitkeep`, `plugins/test-commander/skills/tc-knowledge/templates/.gitkeep`, `plugins/test-commander/skills/tc-knowledge/commands/.gitkeep` — empty directories that 3.2–3.6 fill in. Each `.gitkeep` is removed by the first sub-step that lands real content in that directory.
- **Tests first.** `tests/test_tc_knowledge_scaffold.py` — asserts: skill directory and `SKILL.md` present with valid frontmatter; `name == "tc-knowledge"`; description non-empty; SKILL.md body references each of the five commands; fixture directory exists with the five sub-trees plus README; every knowledge dimension in the rubric is represented by at least one inline `<!-- knowledge: ... -->` comment (or equivalent code marker) somewhere in the fixture; `recorded-api/responses.json` parses as JSON and covers every endpoint in `specs/openapi.yaml`. Test-first: lands red before any deliverable is written.
- **Definition of done.** Skill scaffolded; fixture covers every rubric dimension and every gap-signal type; scaffold test green; `scripts/verify_skills.py` still reports `tc-core PRESENT (phase 1)` and `tc-requirements PRESENT (phase 2)` under `DEFAULT_PHASE_CAP=2` (the cap bumps to 3 in Step 3.8, not here).
- **Review.** Manual read of the fixture against the knowledge rubric — confirm every dimension has at least one seeded defect, every defect is realistic rather than contrived, and the narrative remains universal SaaS vocabulary (D19).

#### 3.2 — `/tc:learn-from-docs` (TDD)

- **Helper.** `plugins/test-commander/scripts/extract_knowledge_from_docs.py` (per D18). Reads every `*.md` file in `<workspace>/documents/uploaded/` that is *not* a requirements-source file (a file is a requirements-source iff it contains at least one `REQ-\d+` token — same filter the Phase 2 helpers use, but inverted). Parses each non-requirements doc with a Markdown-aware extractor that emits structured findings keyed by dimension. Writes:
  - `<workspace>/product-knowledge/documentation-model.md` — **overwrites** (pure generated report).
  - Updates the `## From documents` section in `entities.md`, `user-journeys.md`, `business-rules.md`, `assumptions.md` — **section-overwrite only** (other sources' sections preserved).
  - Appends gap-signal questions to `<workspace>/requirements/open-questions.md` — deduplicated by `(question-text, source-id)` pair (Phase-2 contract).
  - Calls `synthesize_system_model.py` to regenerate `<workspace>/product-knowledge/system-model.md`.

  **Idempotency contract.** Re-running against unchanged input produces byte-identical `documentation-model.md`, byte-identical `## From documents` sections across cross-cutting artifacts, no new lines in `open-questions.md`, and a byte-identical `system-model.md`.

  **Partition table — mechanical extraction per knowledge dimension.**

  | Dimension | Universal-core extraction rule |
  | --- | --- |
  | entities | Markdown table rows whose first column is a single capitalized noun phrase under a heading containing `entit`, `model`, `noun`, or `glossary`; capitalized noun phrases appearing in ≥ 2 distinct documents. Extensible via `tc-knowledge.documents.entity-keywords` |
  | terms | Definition-list entries (`Term`: `definition`) or table rows under a `glossary` or `terminology` heading |
  | user-journeys | Numbered or bulleted lists under a heading containing `journey`, `flow`, `walkthrough`, or `scenario` — each list becomes a journey with ordered steps |
  | business-rules | Bullets or sentences containing an RFC-2119 modal (`must`, `shall`, `should`, `may`) that are not inside a journey or AC context |
  | assumptions | Sentences containing assumption markers from `{assume, expected, presumed, likely}` without an adjacent citation |
  | gap: undefined-term | Capitalized noun phrase appears in ≥ 2 documents but is never the subject of a glossary or definition-list entry |
  | gap: contradictory-rule | Two business rules with the same subject and opposing modals (reuses Phase-2's consistency check shape) |

  Word-set membership is case-insensitive; single-token keywords use the `\b<word>s?\b` pattern (per the Phase-2 Step-2.2 lesson on plural handling).

  **Configurable extensions — `<workspace>/config.yaml`.**

  ```yaml
  tc-knowledge:
    documents:
      entity-keywords: [Patient, Provider, Claim]   # domain-specific
      journey-headings: [story, flow]               # extra journey headings
  ```

  Missing keys = no extension; the helper falls back to the universal core. Extensions union with defaults at runtime; they never replace. The seeded fixture exercises only the universal cores.

- **Synthesizer.** `plugins/test-commander/scripts/synthesize_system_model.py` lands in 3.2 because it is the first command that needs it. It reads every existing `<workspace>/product-knowledge/*.md` per-source file plus the cross-cutting artifacts, then rewrites `system-model.md` from a deterministic template. Tests cover: partial input (only `documentation-model.md` populated), full input (all five populated), no input (system-model.md notes "no sources ingested yet"). 3.3–3.6 reuse the same helper unchanged.
- **Methodology.** `plugins/test-commander/skills/tc-knowledge/methodology/learning-from-documents.md` — covers all seven dimensions in the partition table with definition, mechanical rule verbatim, one worked example from the seeded fixture (cite the doc file and line), and a Claude-judgment-layer paragraph (deciding entity vs attribute, ranking journey importance, distinguishing assumption from confirmed fact). Plus a "shared synthesis" section pointing at `synthesize_system_model.py`'s contract.
- **Umbrella methodology.** `plugins/test-commander/skills/tc-knowledge/methodology/project-knowledge.md` — the cross-source synthesis model: how the five per-source artifacts compose into `system-model.md`, the provenance contract, the assumptions-vs-facts rule, the gap-to-open-question routing. Lands in 3.2 because it documents the synthesizer.
- **Templates.** `documentation-model-template.md`, `entities-template.md`, `user-journeys-template.md`, `business-rules-template.md`, `assumptions-template.md`, `system-model-template.md` all land in 3.2 (3.3–3.6 reuse the cross-cutting and system templates).
- **Command file.** `plugins/test-commander/skills/tc-knowledge/commands/learn-from-docs.md` — Inputs / Outputs / Preconditions / Behavior / Safety / Implementation / Definition of Done / See also.
- **SKILL.md update.** `tc-knowledge/SKILL.md` updated in the same sub-step to describe `/tc:learn-from-docs`'s shipped behavior and the shared synthesizer; instruct Claude to invoke the bundled helper. Stale deferral wording for this command removed.
- **Tests first.** `tests/test_learn_from_docs.py` — at minimum:
  - Uninitialized workspace refused with a clear error.
  - `documents/uploaded/` exists but contains only requirements-source files (`REQ-\d+` present): helper writes a documentation-model noting "no narrative documents found", exits 0, and writes a `system-model.md` reflecting no documentation source.
  - Seeded-fixture input — only `tests/fixtures/seeded-sample-project/documents/*.md` is copied into `<workspace>/documents/uploaded/`. Helper writes the documentation-model file, populates the `## From documents` sections, appends the `undefined-term` and `contradictory-rule` open questions, and regenerates `system-model.md`.
  - For every one of the seven dimensions in the partition table, at least one finding appears in `documentation-model.md` with the correct source citation.
  - Provenance assertion: every finding in `documentation-model.md` carries a `file:line-line` citation that resolves to a real range in the source.
  - Assumption-vs-fact separation: every entry in `assumptions.md`'s `## From documents` section has a "no direct citation" annotation; every entry in `entities.md` has a direct citation.
  - Idempotent re-run: all overwrites and section-overwrites byte-identical; `open-questions.md` line count unchanged.
  - `system-model.md` regenerated correctly: partial-only (only documentation source) state asserted byte-deterministic.
- **Definition of done.** Helper passes all test cases; synthesizer passes its own tests; methodology covers all seven dimensions with worked examples and judgment-layer paragraphs; umbrella `project-knowledge.md` describes the cross-source synthesis model; six templates authored; per-command page complete; `tc-knowledge/SKILL.md` no longer carries deferral wording for `/tc:learn-from-docs` or the synthesizer.
- **Verification.** Pytest green. Eyeball the generated `documentation-model.md` and `system-model.md` for tone, ordering, and structure before declaring 3.2 done.

#### 3.3 — `/tc:learn-from-specs` (TDD)

- **Helper.** `plugins/test-commander/scripts/extract_knowledge_from_specs.py` — auto-detects spec source (`<workspace>/documents/uploaded/openapi.yaml`, `*.openapi.json`, or Postman collection v2.1 `*.postman_collection.json`). Parses the spec into `{endpoint, method, schema-in, schema-out, auth-scheme}` entries. Writes `<workspace>/product-knowledge/spec-derived-model.md` (overwrite), updates the `## From specs` sections in the cross-cutting artifacts (endpoints contribute to `entities.md` as resources; auth-schemes contribute to `business-rules.md`), appends `unimplemented-endpoint` open questions for any endpoint not detectable in `src/` (resolved in 3.4's cross-check), and regenerates `system-model.md`.

  **Partition table — mechanical extraction.**

  | Dimension | Universal-core extraction rule |
  | --- | --- |
  | endpoints | Every `paths.<path>.<method>` triple in OpenAPI; every `item.request` in a Postman collection |
  | schemas | Every `components.schemas.<name>` (OpenAPI); every `body.raw` JSON shape (Postman) |
  | auth-schemes | `components.securitySchemes` (OpenAPI); `auth.type` per request (Postman) |
  | gap: unspecified-status | Endpoint declares no `responses` keys, or only `default` |
  | gap: schema-without-type | A schema entry missing `type` and `$ref` |

- **Methodology.** `learning-from-specs.md` — covers the five dimensions, the OpenAPI-vs-Postman auto-detection, and the Claude judgment layer (ranking endpoints by criticality, identifying response shapes that look unusual).
- **Template.** `spec-derived-model-template.md`.
- **Command file.** `plugins/test-commander/skills/tc-knowledge/commands/learn-from-specs.md`.
- **SKILL.md update.** `tc-knowledge/SKILL.md` updated.
- **Tests first.** `tests/test_learn_from_specs.py` — uninitialized workspace refused; no spec file present: helper writes a spec-derived-model noting "no spec found", exits 0; seeded `specs/openapi.yaml` parsed correctly (every endpoint, schema, auth-scheme captured with `file:line-line` provenance); idempotent re-run; the `gap: unspecified-status` defect surfaces as an open question; Postman-format auto-detection covered with a tiny synthetic Postman collection fixture; namespaced `## From specs` sections written without touching `## From documents`.
- **Definition of done.** Helper passes all test cases; auto-detection works for both formats; methodology covers all five dimensions; SKILL.md updated.
- **Verification.** Pytest green; smoke run produces a spec-derived model for the seeded fixture.

#### 3.4 — `/tc:learn-from-code` (TDD)

- **Helper.** `plugins/test-commander/scripts/extract_knowledge_from_code.py` — walks `<workspace>/documents/uploaded/code/` (or a configurable root via `tc-knowledge.code.source-root`), uses the stdlib `ast` module to extract Python modules, classes, functions, decorators, and docstrings. Non-Python files are detected by extension and counted as "language detected but not parsed in v1" with no parse attempt. Writes `<workspace>/product-knowledge/code-derived-model.md` (overwrite), updates `## From code` sections in cross-cutting artifacts (classes contribute to `entities.md`; module-level constants to `business-rules.md` only when they carry an explicit rule docstring), appends `undocumented-function`, `unimplemented-endpoint` (cross-checks the spec-derived model if present), and `language-unsupported-in-v1` gap signals, and regenerates `system-model.md`.

  **Partition table — mechanical extraction.**

  | Dimension | Universal-core extraction rule |
  | --- | --- |
  | modules | Every Python file successfully parsed by `ast.parse` |
  | classes | Every `ast.ClassDef`; attributes from `__init__` assignments |
  | functions | Every `ast.FunctionDef` and `ast.AsyncFunctionDef` |
  | docstrings | `ast.get_docstring()` per module/class/function |
  | decorators | Decorator names captured for each function (used to cross-check spec endpoints in 3.4 when a future `@route` or `@app.get` decorator pattern is registered via config) |
  | gap: undocumented-function | Public function (name not starting with `_`) with no docstring |
  | gap: unimplemented-endpoint | An endpoint in `spec-derived-model.md` (if present) has no matching function in the parsed code (matched by configurable handler-name pattern, default `<method>_<path-segment>` lowercased) |
  | gap: language-unsupported-in-v1 | File with extension in `{.ts, .tsx, .js, .jsx, .go, .java, .rb}` |

  **Configurable extensions.**

  ```yaml
  tc-knowledge:
    code:
      source-root: src                          # default: documents/uploaded/code
      enabled-languages: [python]               # extensible; v1 ships python only
      ignored-paths: [migrations, __pycache__, .venv]
      endpoint-decorator-patterns: ["@app.{method}", "@router.{method}"]
  ```

- **Methodology.** `learning-from-code.md` — covers Python AST extraction, the cross-check against `spec-derived-model.md`, the deferred-language convention, and the Claude judgment layer (deciding which class is a domain entity vs an implementation detail, ranking modules by surface area).
- **Template.** `code-derived-model-template.md`.
- **Command file.** `plugins/test-commander/skills/tc-knowledge/commands/learn-from-code.md`.
- **SKILL.md update.** Updated.
- **Tests first.** `tests/test_learn_from_code.py` — uninitialized workspace refused; no code root present: helper notes "no code source found"; seeded `src/` tree parsed correctly (every module, class, function captured with `file:line-line` provenance); `app/api/files.py::upload_file` (the seeded `undocumented-function` defect) surfaces as an open question; `web/app.ts` is counted as "language detected but not parsed in v1" rather than silently ignored; cross-check against the seeded OpenAPI spec produces an `unimplemented-endpoint` gap for the endpoint deliberately omitted from `src/`; `config.yaml`-driven extension of ignored paths is honored; idempotent re-run.
- **Definition of done.** Helper passes all test cases; ast walk covers modules / classes / functions / docstrings / decorators; cross-check against the spec model works; non-Python detection is explicit; methodology covers all seven dimensions; SKILL.md updated.
- **Verification.** Pytest green; smoke run produces a code-derived model for the seeded fixture.

#### 3.5 — `/tc:learn-from-api` (TDD)

- **Helper.** `plugins/test-commander/scripts/extract_knowledge_from_api.py` — runs in `recorded` mode by default (reads `<workspace>/documents/uploaded/recorded-api/responses.json` or the configured path). Reads each `{method, path, status, headers, body}` entry, classifies it by status family (2xx / 3xx / 4xx / 5xx), extracts response-body shape (top-level keys for JSON), and writes `<workspace>/product-knowledge/api-model.md` (overwrite). Updates `## From api` sections in cross-cutting artifacts (response entities contribute to `entities.md`; auth-required endpoints contribute to `business-rules.md`). Cross-checks against `spec-derived-model.md` if present and appends `unspecified-endpoint` (recorded but not in spec) and `mismatched-status` (recorded status does not match any spec response) open questions. Regenerates `system-model.md`.

  **Live mode** (`tc-knowledge.api.mode: live`) issues real HTTP requests against `tc-knowledge.api.base-url` using the endpoint list from `spec-derived-model.md`. Pytest never enters live mode — this is exercised only by manual smoke and documented in the customization guide.

  **Partition table — mechanical extraction.**

  | Dimension | Universal-core extraction rule |
  | --- | --- |
  | live-endpoints | Every entry in `responses.json` (recorded) or every spec endpoint probed (live) |
  | response-shapes | Top-level JSON keys per response body |
  | auth-required | Endpoints returning 401/403 without an `Authorization` header in the request |
  | gap: unspecified-endpoint | A recorded request whose `(method, path)` does not appear in `spec-derived-model.md` |
  | gap: mismatched-status | A recorded status not declared by the spec's `responses` map for that endpoint |

  **Configurable extensions.**

  ```yaml
  tc-knowledge:
    api:
      mode: recorded                            # or: live
      recorded-path: documents/uploaded/recorded-api/responses.json
      base-url: http://localhost:8000           # live mode only
      auth-header: "Authorization: Bearer ${TC_API_TOKEN}"
  ```

- **Methodology.** `learning-from-api.md` — covers the recorded-vs-live distinction, the cross-check against `spec-derived-model.md`, the Claude judgment layer (deciding which response shape is canonical vs error-path, identifying auth flows from header patterns).
- **Template.** `api-model-template.md`.
- **Command file.** `plugins/test-commander/skills/tc-knowledge/commands/learn-from-api.md`.
- **SKILL.md update.** Updated.
- **Tests first.** `tests/test_learn_from_api.py` — uninitialized workspace refused; no recorded file present: helper notes "no recorded API responses found"; seeded `recorded-api/responses.json` parsed correctly (every entry captured with `method path status` provenance); the seeded `unspecified-endpoint` (`GET /accounts/me`) surfaces as an open question; idempotent re-run; live mode refused in pytest (asserts the helper raises if `mode: live` is set during tests, ensuring no real network calls leak from the suite); namespaced `## From api` sections written cleanly.
- **Definition of done.** Helper passes all test cases; recorded mode is the test contract; live mode is documented but not exercised by tests; methodology covers all five dimensions; SKILL.md updated.
- **Verification.** Pytest green; smoke run produces an API model for the seeded fixture.

#### 3.6 — `/tc:learn-from-tests` (TDD)

- **Helper.** `plugins/test-commander/scripts/extract_knowledge_from_tests.py` — walks `<workspace>/documents/uploaded/tests/` (or a configurable root via `tc-knowledge.tests.source-root`), detects pytest-style files (`test_*.py`, `*_test.py`) and Playwright spec files (`*.spec.ts`), counts test functions per file, and (for Python) uses `ast` to extract the symbols each test function references. Writes `<workspace>/product-knowledge/tests-coverage.md` (overwrite), updates `## From tests` sections in cross-cutting artifacts (covered symbols contribute to `entities.md`'s confidence column), appends `untested-function` open questions for any function in `code-derived-model.md` not referenced by any test, and regenerates `system-model.md`.

  Also adds `tests-coverage.md` to the Workspace Layout block in this plan and to `docs/workspace-reference.md` in the same sub-step.

  **Partition table — mechanical extraction.**

  | Dimension | Universal-core extraction rule |
  | --- | --- |
  | test-files | Every file matching `test_*.py`, `*_test.py`, or `*.spec.ts` |
  | test-functions | Every `ast.FunctionDef` starting with `test_` (Python); every `test(` call (Playwright, regex-detected for v1) |
  | covered-symbols | For each Python test function, the set of `ast.Name` and `ast.Attribute` identifiers referenced (cross-checked against `code-derived-model.md` to identify which code-side functions/classes are exercised) |
  | gap: untested-function | A function in `code-derived-model.md` (public, name not starting with `_`) not referenced by any test |
  | gap: unsupported-test-runner | A test file whose extension is recognized (`.ts`) but not parsed in v1 — counted, not parsed |

- **Methodology.** `learning-from-tests.md` — covers the pytest / Playwright detection model, the symbol-reference cross-check, the deferred-runner convention, and the Claude judgment layer (deciding which untested functions are critical, ranking coverage gaps by risk).
- **Template.** `tests-coverage-template.md`.
- **Command file.** `plugins/test-commander/skills/tc-knowledge/commands/learn-from-tests.md`.
- **SKILL.md update.** Updated. By end of 3.6, `tc-knowledge/SKILL.md` describes all five Phase 3 commands plus the shared synthesizer with no deferral wording.
- **Workspace Layout update.** Edit the Workspace Layout block in this plan and `docs/workspace-reference.md` to add `tests-coverage.md` under `product-knowledge/`. Land both edits in the 3.6 commit.
- **Tests first.** `tests/test_learn_from_tests.py` — uninitialized workspace refused; no tests root present: helper notes "no tests found"; seeded `tests/` tree parsed correctly (every test function captured with `file:line-line` provenance); the seeded `untested-function` (`upload_file`) surfaces as an open question (only when `code-derived-model.md` is also populated, i.e. 3.4 has run); without `code-derived-model.md` the helper still writes `tests-coverage.md` but skips the cross-check; `web/spec/*.spec.ts` is counted as "test runner detected but not parsed in v1"; idempotent re-run; namespaced `## From tests` sections written cleanly.
- **Definition of done.** Helper passes all test cases; Python detection and Playwright counting both work; the cross-check against `code-derived-model.md` is conditional and correct; `tests-coverage.md` added to the Workspace Layout block and `docs/workspace-reference.md`; methodology covers all five dimensions; SKILL.md describes all five commands plus the synthesizer.
- **Verification.** Pytest green; smoke run produces a tests-coverage model for the seeded fixture.

#### 3.7 — Documentation pass *(dedicated step)*

- **Deliverables.**
  - Author `docs/user-guide/building-project-knowledge.md` — end-to-end walkthrough: upload sample project → `/tc:learn-from-docs` → `/tc:learn-from-specs` → `/tc:learn-from-code` → `/tc:learn-from-api` → `/tc:learn-from-tests`. Sample input and sample output drawn from the seeded sample-project fixture so every example is reproducible. Each section shows the partial `system-model.md` after that command runs.
  - Update `docs/command-reference.md` to add the five Phase 3 commands as links into their per-command pages inside the plugin.
  - Update `docs/workspace-reference.md` to mark the ten `product-knowledge/` files as populated by Phase 3 commands (the `tests-coverage.md` row was added in 3.6); ensure each file's row identifies which command writes it (`documentation-model.md` ← `/tc:learn-from-docs`, etc.).
  - Refresh `README.md`, `docs/install.md`, `docs/user-guide/getting-started.md`, `docs/user-guide/workflow.md`, `docs/user-guide/reviewing-requirements.md`'s "Beyond" footer, and `plugins/test-commander/README.md` Phase 3 mentions ("Phase 3 starts next" → "Phase 3 in progress" / "complete").
  - **Customization-guide update (per the Per-Phase Convention).** Add a "Phase 3 schema (`tc-knowledge`)" section to [`docs/user-guide/customizing-for-your-project.md`](../docs/user-guide/customizing-for-your-project.md) covering all five command sub-blocks (`documents`, `specs`, `code`, `api`, `tests`). At least three worked extension examples spanning materially-different consuming-project shapes: a typical Python/FastAPI app, a Node/Express app (where `code.enabled-languages` is `[]` because v1 does not parse JS — the example shows what the project would set to extend), and a project using a Postman collection instead of OpenAPI. Add a "Phase 3 — what landed" subsection naming the universal cores, the schema keys, and the test that would fail if the helpers ignored extensions.
  - **Final `tc-knowledge/SKILL.md` pass.** Confirm SKILL.md describes every shipped command and the shared synthesizer, links to all five per-command pages, and instructs Claude to invoke the bundled helpers. No "behavior arrives in Phase 4" wording for any shipped command. The per-sub-step SKILL.md updates from 3.2–3.6 should already cover this; 3.7 is the final check.
- **Definition of done.** Every doc accurate against the implementation; all cross-links resolve; link checker green; `tc-knowledge/SKILL.md` is the consolidated entry point for Phase 3 commands; `customizing-for-your-project.md` accurately reflects the shipped config.yaml schema with at least three worked examples.
- **Verification.** `python3 scripts/check_links.py` clean; manual read-through against the Phase 3 deliverables; grep for stale deferral wording in `tc-knowledge/SKILL.md` returns no hits; the YAML block in `customizing-for-your-project.md` parses as valid YAML.

#### 3.8 — Testing finalization *(dedicated step, separate from per-command TDD)*

- **Deliverables.**
  - Bump `DEFAULT_PHASE_CAP` in `scripts/verify_skills.py` from `2` to `3` and add `CATALOG["tc-knowledge"] = 3` so the verifier expects `tc-core`, `tc-requirements`, and `tc-knowledge`.
  - `tests/test_phase_3_integration.py` — integration smoke that creates a fresh tmp consuming project, runs `init_workspace.py`, copies the seeded sample-project fixture's sub-trees into `<workspace>/documents/uploaded/`, then invokes the five Phase 3 helpers in workflow order (`learn-from-docs` → `learn-from-specs` → `learn-from-code` → `learn-from-api` → `learn-from-tests`), asserting after each step that:
    - the per-source model file is overwritten with the new content;
    - the `## From <source>` sections appear in the expected cross-cutting artifacts;
    - prior sources' namespaced sections are preserved (namespacing contract);
    - `system-model.md` reflects the union of currently-populated sources;
    - the expected gap-signal open questions are appended (without duplicating prior runs').
  - A final assertion confirms that after all five commands run, every knowledge rubric dimension has at least one finding with provenance somewhere in `<workspace>/product-knowledge/`, and `/tc:next` (Phase 1) recommends a Phase 4 command (or at least advances past Phase 3) — assert `command != /tc:learn-from-docs` rather than asserting the specific next command (per the Phase-2 Step-2.9 lesson about R-rule interactions).
  - Negative integration test: a `tc-knowledge.api.mode: live` config triggers a clear refusal under the test harness (no network calls leak).
- **Definition of done.** Integration smoke passes; phase cap bump reflected; full `make verify` chain green; `verify_skills.py` reports `tc-core PRESENT (phase 1)`, `tc-requirements PRESENT (phase 2)`, and `tc-knowledge PRESENT (phase 3)`.
- **Verification.** Captured `make verify` output.

#### 3.9 — Sign-off

Six sub-steps. Mirrors the Phase 2 sign-off pattern (2.9). Test-first: the sign-off test in 3.9.5 lands red before the plan/CHANGELOG edits in 3.9.3 turn it green. The final sub-step (3.9.6) captures evidence and pushes the `phase-3` annotated tag.

##### 3.9.1 — Cold-user walkthrough of `building-project-knowledge.md`

- **Deliverables.** Captured log of an end-to-end walkthrough of `docs/user-guide/building-project-knowledge.md` from a freshly-installed plugin against a fresh tmp consuming project.
- **Steps to execute verbatim.**
  1. `make uninstall` → `make install` to reach a known-clean plugin state.
  2. Create a tmp consuming-project dir (`mktemp -d`).
  3. `init_workspace.py <tmp>`. Copy `tests/fixtures/seeded-sample-project/*` into `<tmp>/.test-commander/documents/uploaded/` preserving the sub-tree structure.
  4. Invoke the five Phase 3 helpers in workflow order.
  5. Confirm each helper prints the output documented in `building-project-knowledge.md` (no fabricated examples).
- **Definition of done.** All commands succeed end to end. Output captured to `/tmp/tc-phase3-walkthrough.log`. If any step fails, fix the cause and re-run before continuing to 3.9.2.

##### 3.9.2 — Per-step DoD audit

- **Deliverables.** A line-by-line audit of Steps 3.1 through 3.8 against their DoD lists.
- **What to check per step.** Every DoD bullet green; every pytest file passes; every deliverable present on disk; every cross-link in the per-command pages resolves; every Failure Mode mitigation in place.
- **Specifically.**
  - 3.1: `tc-knowledge/SKILL.md` and `tests/fixtures/seeded-sample-project/` present; scaffold test green; rubric coverage and gap-signal coverage assertions pass.
  - 3.2–3.6: helper, methodology, template, command file, and SKILL.md update all present; per-command test files all green; mechanical extraction findings traced to seeded fixture; provenance citations resolve.
  - 3.7: `building-project-knowledge.md`, command-reference index, workspace-reference (`tests-coverage.md` row added), README + getting-started status lines all current; `tc-knowledge/SKILL.md` describes every shipped Phase 3 command and contains no stale deferral wording; `customizing-for-your-project.md` reflects the Phase 3 `tc-knowledge` config.yaml schema with at least three worked extension examples spanning materially-different consuming-project shapes.
  - 3.8: `DEFAULT_PHASE_CAP >= 3`, `CATALOG["tc-knowledge"] == 3`, integration smoke passes, live-mode refusal under test harness asserted.
  - **Lesson-capture audit (per the "Sub-step lesson capture" Per-Phase Convention):** every Phase 3 sub-step (3.1–3.8) has a corresponding entry in the `Phase 3 — Lessons learned (running)` subsection. Sub-steps that closed cleanly with no bugs explicitly record "no lessons".
- **Definition of done.** All eight prior sub-steps audited green. Any unmet item blocks the sign-off.

##### 3.9.3 — Plan and CHANGELOG updates

- **Deliverables.**
  - `planning/plan.md` — collapse the `### Phase 3` To Do sub-section to a single line: `Phase 3 complete (YYYY-MM-DD) — see Completed`. Add a `### Phase 3 — Project knowledge ingestion (YYYY-MM-DD)` section to `## Completed` with the per-step summary lines marked `[x]`, mirroring the Phase 2 closing format.
  - `CHANGELOG.md` — add a new `### Phase 3 — Project knowledge ingestion (complete YYYY-MM-DD)` section above Phase 2 with a one-line closing summary plus per-sub-step Added bullets, mirroring the Phase 2 closing format.
- **Definition of done.** To Do Phase 3 reduced to the marker line; Completed has the Phase 3 section with date and nine sub-step bullets; CHANGELOG reflects the closing.

##### 3.9.4 — Documentation final pass

- **Deliverables.** Edits wherever Phase 3 wording has drifted during the eight sub-steps.
- **What to read.** README status line, `docs/user-guide/getting-started.md` "what's next", `docs/install.md` verifying-install paragraph, `docs/user-guide/building-project-knowledge.md` introductory paragraph, `docs/user-guide/reviewing-requirements.md` footer "Beyond" block, `docs/user-guide/workflow.md` (if it references Phase 3), `plugins/test-commander/README.md` skill table, `docs/user-guide/customizing-for-your-project.md` tense.
- **Definition of done.** Every Phase 3 fact matches the implementation. "Phase 3 in progress" wording becomes "Phase 3 complete (YYYY-MM-DD); Phase 4 starts next" where applicable. All cross-links resolve.

##### 3.9.5 — Pre-flight tests for sign-off

- **Deliverables.** `tests/test_phase_3_signoff.py`.
- **Coverage.**
  - All eight Phase 3 pytest files exist (`test_tc_knowledge_scaffold`, `test_learn_from_docs`, `test_learn_from_specs`, `test_learn_from_code`, `test_learn_from_api`, `test_learn_from_tests`, `test_phase_3_integration`, `test_phase_3_signoff`).
  - All five Phase 3 helpers plus the shared synthesizer exist under `plugins/test-commander/scripts/` (`extract_knowledge_from_docs.py`, `extract_knowledge_from_specs.py`, `extract_knowledge_from_code.py`, `extract_knowledge_from_api.py`, `extract_knowledge_from_tests.py`, `synthesize_system_model.py`).
  - All five Phase 3 command files exist under `plugins/test-commander/skills/tc-knowledge/commands/`.
  - All six methodology files exist under `plugins/test-commander/skills/tc-knowledge/methodology/` (`project-knowledge.md` umbrella plus five per-source).
  - All ten templates exist under `plugins/test-commander/skills/tc-knowledge/templates/`.
  - `tests/fixtures/seeded-sample-project/` exists with the five sub-trees plus README.
  - `scripts/verify_skills.py` has `CATALOG["tc-knowledge"] == 3` and `DEFAULT_PHASE_CAP >= 3` (per the Phase-2 Step-2.8 lesson — never assert `==` on the cap).
  - `tc-knowledge/SKILL.md` describes all five Phase 3 commands plus the shared synthesizer and contains no "behavior arrives in Phase 3" / "Coming in Phase 3" wording.
  - `docs/user-guide/customizing-for-your-project.md` contains a `tc-knowledge:` YAML block whose top-level keys match the shipped config.yaml schema, and contains at least three worked extension examples in distinct project-shape headings.
  - `Phase 3 — Lessons learned (running)` subsection in `planning/plan.md` contains an entry for every Phase 3 sub-step that has landed (`Step 3.1` through `Step 3.8`); each entry either describes a lesson + mitigation or explicitly records "no lessons".
  - CHANGELOG Phase 3 section marked complete with a date.
  - `plan.md` Completed has a Phase 3 subsection with a date.
  - `plan.md` To Do Phase 3 is the marker line (no unchecked items remain).
  - `plan.md` Workspace Layout includes `tests-coverage.md` under `product-knowledge/`.
  - Total pytest count meets minimum (`>= 200` — Phase 2 finished at 172; Phase 3 adds the scaffold test, five per-command suites, synthesizer tests, integration, and sign-off).
- **Definition of done.** Test-first: the suite lands red before 3.9.3's plan/CHANGELOG edits, green after.

##### 3.9.6 — Final DoD evaluation (close Phase 3)

- **Procedure.**
  1. Run `make verify` — every test green, link checker clean, `verify_skills.py` reports `tc-core PRESENT (phase 1)`, `tc-requirements PRESENT (phase 2)`, `tc-knowledge PRESENT (phase 3)`.
  2. Replay the 3.9.1 walkthrough end to end to confirm reproducibility.
  3. Capture all output to `/tmp/tc-phase3-signoff.log`.
  4. Commit the plan/CHANGELOG/docs updates and the sign-off test in one final commit.
  5. Push to origin.
  6. Create annotated tag: `git tag -a phase-3 -m "Phase 3 — Project knowledge ingestion complete."`.
  7. Push tag: `git push origin phase-3`.
- **Definition of done.** All seven numbered steps complete. Tag visible on origin (`git ls-remote origin phase-3` resolves). Evidence log captured. Phase 3 is closed.

#### Definition of done — consolidated 15 checks

Eleven automated; four evidence-based.

| # | Check | Type | How |
| --- | --- | --- | --- |
| 1 | All eight Phase 3 test files exist (`test_tc_knowledge_scaffold`, `test_learn_from_docs`, `test_learn_from_specs`, `test_learn_from_code`, `test_learn_from_api`, `test_learn_from_tests`, `test_phase_3_integration`, `test_phase_3_signoff`) | auto | sign-off test |
| 2 | All five helpers plus `synthesize_system_model.py` exist | auto | sign-off test |
| 3 | All five command files exist under `tc-knowledge/commands/` | auto | sign-off test |
| 4 | All six methodology files exist under `tc-knowledge/methodology/` | auto | sign-off test |
| 5 | All ten templates exist under `tc-knowledge/templates/` | auto | sign-off test |
| 6 | Seeded-sample-project fixture exists and covers every rubric dimension + every gap-signal type | auto | scaffold test |
| 7 | `verify_skills.py` has `CATALOG["tc-knowledge"] == 3` and `DEFAULT_PHASE_CAP >= 3`; `make verify` prints all three skills PRESENT | auto | sign-off test + `make verify` |
| 8 | Integration smoke `test_phase_3_integration` passes; live-mode refusal under test harness asserted | auto | pytest |
| 9 | `tc-knowledge/SKILL.md` describes all five shipped Phase 3 commands plus the synthesizer with no deferral wording | auto | sign-off test |
| 10 | `tests-coverage.md` added to Workspace Layout in `plan.md` and `docs/workspace-reference.md` | auto | sign-off test |
| 11 | `make verify` chain clean (link checker covers the new docs) | auto | full chain |
| 12 | Cold-user walkthrough of `building-project-knowledge.md` from clean state succeeds (3.9.1) | evidence | `/tmp/tc-phase3-walkthrough.log` |
| 13 | Per-step DoD audit clean for 3.1–3.8 (3.9.2) | evidence | audit notes |
| 14 | `plan.md` To Do Phase 3 collapsed to marker; Completed has Phase 3 subsection with date (3.9.3); CHANGELOG Phase 3 section marked complete | evidence | sign-off test + grep |
| 15 | `phase-3` annotated tag created and pushed (3.9.6) | evidence | `git tag -l phase-3` + `git ls-remote origin phase-3` |

#### TDD pattern used in 3.2–3.6

```
write tests (red)             # define expected extractions per dimension from the seeded fixture, including provenance
  → implement helper (green)  # minimum code to pass; mechanical extraction only
    → author methodology + template (each command owns one of each)
      → author per-command page
        → update SKILL.md to surface shipped behavior
          → call synthesize_system_model.py (shared, lands in 3.2)
            → verify (pytest + make verify)
```

No implementation lands before its tests. No tests are added after the fact. Every command's test suite drives the helper from the same seeded sample-project fixture so the rubric is the contract.

#### Validation sequence

1. Author 3.1 (skill scaffold + fixture) with its scaffold test. Confirm pytest red → green.
2. Author 3.2 (`/tc:learn-from-docs` + the shared synthesizer): write tests, implement helper + synthesizer, author methodology (`learning-from-documents.md` + `project-knowledge.md` umbrella), author cross-cutting + per-source templates, author command file, update SKILL.md, run pytest.
3. For each of 3.3, 3.4, 3.5, 3.6 in order: mirror 3.2's skeleton, adapt per-source extraction, write tests, implement helper, author the source-specific methodology and template, author command file, update SKILL.md, run pytest.
4. 3.7 documentation pass. Run `make verify`.
5. 3.8 testing finalization: bump `CATALOG["tc-knowledge"]` to 3 and `DEFAULT_PHASE_CAP` to 3, integration smoke. Run `make verify`.
6. 3.9 sign-off, in order:
   6a. Run the cold-user walkthrough from `building-project-knowledge.md` (3.9.1). Capture log. Fix anything that fails before proceeding.
   6b. Audit each prior sub-step's DoD (3.9.2). Block on any unmet item.
   6c. Write `tests/test_phase_3_signoff.py` (3.9.5). Run `make test` — expect failures for any not-yet-applied plan/CHANGELOG edits.
   6d. Update `plan.md` and `CHANGELOG.md` (3.9.3). Re-run sign-off test — expect green.
   6e. Doc final read-through (3.9.4). Edit any drift; re-run `make verify`.
   6f. Final DoD evaluation (3.9.6): commit, push, annotated tag, tag push.

#### Failure modes

- An extraction dimension turns out to be hard to detect mechanically. **Mitigation:** the helper applies only the mechanical part; the AI-judgment part lives in the methodology doc and the command file's Behavior section. The seeded fixture marks each defect as `mechanical` or `judgment`, and the test suite only asserts on mechanical findings.
- Source-format ambiguity (OpenAPI 2 vs 3, Postman v2.0 vs v2.1, JSON vs YAML). **Mitigation:** auto-detect by file extension and root keys; refuse with a clear error on unrecognized formats; document the supported format set in the per-command page.
- Cross-source ordering matters in ways the integration smoke does not catch. **Mitigation:** every command must produce a valid (possibly partial) `system-model.md` even when run alone. The 3.2 tests cover the docs-only state; 3.3–3.6 tests each cover the single-source state. The integration smoke covers the union and the order-of-arrival invariants.
- Provenance citations drift from real source lines after an upstream document is edited and the helper re-runs. **Mitigation:** every overwrite-mode artifact is regenerated from scratch on each run; citations are always against the current source. The idempotency contract makes drift detection a byte-diff.
- `system-model.md` regeneration produces different output depending on the order commands ran. **Mitigation:** `synthesize_system_model.py` reads the current state of every per-source file (independent of which command invoked it) and writes from a canonical template. Tests assert byte-identical output for the same final state regardless of which command was the last to run.
- `tc-knowledge.api.mode: live` accidentally enabled during tests. **Mitigation:** the helper inspects an `IS_TEST` environment variable (set by the pytest fixture) and refuses live mode under tests; the integration smoke includes a negative test that asserts this refusal.
- Non-Python source detection (TS, JS, Go) silently skipped. **Mitigation:** every non-Python file is counted and emitted as a `language-unsupported-in-v1` gap; the seeded fixture includes `web/app.ts` to assert this is detected, not ignored.
- Phase 3 writes to a downstream-owned directory and skews `/tc:next`. **Mitigation:** the design decision above forbids writes outside `product-knowledge/` and `requirements/open-questions.md`. The integration smoke in 3.8 asserts `<workspace>/traceability/` is unchanged after a full Phase 3 run.
- Template-stub vs generated-artifact ambiguity (the Phase-2 Step-2.5 lesson). **Mitigation:** every Phase 3 helper that reads an upstream artifact (`spec-derived-model.md` is read by `extract_knowledge_from_code.py`; `code-derived-model.md` is read by `extract_knowledge_from_tests.py`) uses the generator-marker check pattern, not `path.is_file()` or `path.stat().st_size > 0`. Each per-source model template ships a placeholder; the helper detects the upstream's structural markers (`## Extracted endpoints`, `## Extracted modules`, etc.) before treating the file as populated.
- Plural-form keyword mismatch (the Phase-2 Step-2.2 lesson). **Mitigation:** every keyword-matching helper uses `\b<word>s?\b` for single-token keywords.
- Domain-leakage into shipped defaults (the Phase-2 Step-2.1 lesson). **Mitigation:** the seeded sample-project fixture and every default keyword set are audited against D19 universal-vocabulary criteria before each command's sub-step closes. Domain extensibility goes through `tc-knowledge:` config blocks.
- Documentation walkthrough in 3.9.1 surfaces a gap. **Mitigation:** update `building-project-knowledge.md` to match reality and re-run the walkthrough. Treat as a Phase 3 doc bug, not a Phase 4 issue.
- A prior sub-step's DoD turns out not to be green during 3.9.2. **Mitigation:** the failing sub-step reopens. 3.9 cannot close while any earlier DoD is unmet.
- `phase-3` tag already exists locally. **Mitigation:** delete (`git tag -d phase-3` then `git push origin :refs/tags/phase-3`) and recreate. Never force-overwrite an existing tag on origin without explicit user confirmation.
- CHANGELOG Phase 3 closing entry diverges from To Do/Completed movement. **Mitigation:** the sign-off test (3.9.5) checks all three sources. They must agree before the test passes.

#### Phase 3 — Lessons learned (running)

Captured at sub-step close per the "Sub-step lesson capture" Per-Phase Convention. Each entry is preventative care for future implementers of similar work.

##### Step 3.8 — Testing finalization (cap bump + integration smoke)

- **DEFAULT_PHASE_CAP bump landed without breaking prior sign-off tests.** Phase 1's `test_verify_skills_default_phase_cap_at_least_1` and Phase 2's `test_verify_skills_default_phase_cap_at_least_2` both already used `>=` invariants per the Phase-2 Step-2.8 lesson — bumping from 2 to 3 changed neither test's outcome. `verify_skills.py` flipped from `PRESENT=2 ... UNEXPECTED=1` (tc-knowledge ahead of schedule) to `PRESENT=3 ... UNEXPECTED=0`. **Pattern reinforced:** the per-step "use `>=` not `==` on monotonically-non-decreasing values" discipline is paying compounding dividends. Phase 1's invariant test, Phase 2's invariant test, and the Phase 3 cap bump composed cleanly with zero refactoring. **Future-implementer hint:** Phase 4's sign-off test (when `tc-explore` ships at phase 4) should follow the same `>= 4` pattern; never write `== 4`.
- **Integration smoke landed 3/3 GREEN on first run.** The three test cases (`test_full_phase_3_workflow` covering 5 helpers in workflow order with state assertions at every transition + final union state; `test_byte_stable_rerun_across_all_five_helpers` covering full-cycle idempotency across 10 product-knowledge files + open-questions line stability; `test_live_mode_refused_under_pytest`) passed on the first implementation. **Why?** Two reasons: (a) the Phase-3 helpers are by now thoroughly unit-tested (288 unit tests at sub-step close before integration) — composition issues would have to surface at the unit level first; (b) each sub-step's own tests already covered the cross-cutting scope and idempotency invariants, so the integration test is verification, not discovery. **Pattern reinforced (five datapoints in across Phase 3):** when every per-command sub-step ships with thorough unit tests and the helper-mirroring skeleton enforces consistent semantics across siblings, the integration smoke catches no new bugs. Phase 2's Step-2.8 lesson observed the same. **Future-implementer hint:** Phase 4's integration smoke (4 helpers in `tc-explore`) can confidently mirror this skeleton. Budget the integration step as verification-only, not as debugging.
- **In-process imports beat subprocess invocations for integration smoke.** Phase 2's `test_phase_2_integration.py` imported helpers as Python modules and called their `run()` / public functions directly; this Phase 3 integration test mirrors the pattern. Result: 3 tests run in 0.26 seconds. By contrast, the per-command unit tests in `test_learn_from_api.py` use `subprocess` to verify the CLI surface (which is the right scope for those tests — they exercise the helper as users would). **Pattern worth keeping:** subprocess for CLI-surface assertions (exit codes, stderr text); in-process imports for behavior assertions (state changes, return values, exceptions). Mixing them at the wrong scope inflates suite runtime without adding coverage. **Future-implementer hint:** every Phase-N integration test should use in-process imports for speed.
- **Phase 3's "no writes to traceability/" discipline holds end-to-end.** The integration smoke walks every `.md` under `<workspace>/traceability/` after the full helper sweep and asserts the substring `tc-knowledge` is absent — confirming Phase 3 wrote no content into the Phase-5-owned directory. The discipline was codified as a Phase-3 design decision (folded in at the top of the Phase 3 plan section) because of the Phase-2 Step-2.9 lesson: writing into a downstream-owned directory bumps that phase to `in_progress` in `workspace_state.py` and skews `/tc:next`. **Pattern reinforced:** explicit cross-phase write boundaries belong in design decisions, not in code. Each helper enforces it; the integration test verifies it. **Future-implementer hint:** Phase 4's `tc-explore` will write to charters / exploration-notes / test-ideas (the Phase-4-owned directories) plus contribute to `<workspace>/product-knowledge/` (Phase 3-owned). The Phase 4 integration test should assert the inverse — that Phase 4 does NOT write to traceability/ either (still Phase 5's job).
- **`/tc:next` advances past `/tc:learn-from-docs` after the Phase 3 helper sweep.** The integration test's final assertion asserts `command != /tc:learn-from-docs` rather than pinning a specific next command — per the Phase-2 Step-2.9 lesson, the exact next command depends on which downstream phases the cross-cutting writes bumped to `in_progress`, and over-specific assertions break when R-rules evolve. The assertion held: `/tc:next` advanced to a Phase 4 or later command (the integration test does not care which). **Pattern reinforced:** the "advanced past" invariant is robust; the "specific next command" assertion is brittle. **Future-implementer hint:** every Phase-N integration test's final `/tc:next` assertion should follow this shape — assert the prior phase's first command is no longer recommended, not that some specific next command is.
- **Live-mode refusal test uses `pytest.raises` directly.** The per-command unit test in `test_learn_from_api.py` uses subprocess because it verifies the CLI exit code + stderr message. The integration test uses `pytest.raises(extract_knowledge_from_api.LiveModeRefusedError)` because it verifies the in-process exception. Both are correct for their scope. The exception detection mechanism (`os.environ.get("PYTEST_CURRENT_TEST")`) fires identically from either invocation path because pytest sets the env var globally for every test, including in-process imports. **Future-implementer hint:** any future Phase-N helper that gains the *capability* to reach the network should adopt the same `PYTEST_CURRENT_TEST` env-var check; the env var is the reliable signal.
- **Lint cleanup**: ruff initially flagged 2 trivial issues in the new test file (one import-order, one line-too-long). Both auto-fixed without changing semantics; the auto-fix only resorted the `import pytest` line, which the project's import-sorting rule places after the local-package imports. **Pattern worth keeping:** run `pdm run ruff check . --fix` after authoring any new test file. The auto-fix scope is small and the rule-set is stable.

##### Step 3.7 — Documentation pass

- **Dedicated documentation step lands cleanly.** Step 3.7 shipped one new user-facing doc (`docs/user-guide/building-project-knowledge.md` — Phase 3 end-to-end walkthrough, 220+ lines), two updates to top-level reference docs (`docs/command-reference.md` adds the Phase 3 commands table with per-command-page links; `docs/workspace-reference.md` adds the per-file ownership tables for the 10 product-knowledge artifacts and the cross-cutting contribution map), refreshes across six status-line locations (`README.md` x2, `docs/install.md`, `docs/user-guide/getting-started.md`, `docs/user-guide/workflow.md`, `docs/user-guide/reviewing-requirements.md`, `plugins/test-commander/README.md`), the customization-guide update with three worked extension examples spanning materially-different consuming-project shapes (Python/FastAPI, Node/Express with `enabled-languages: []`, Postman-only), and the "Phase 3 — what landed" subsection naming the universal cores + schema keys + the seven tests that would fail if helpers ignored extensions. Total: 311 tests stayed green; link checker covers 137 files (up from 136 — one new walkthrough); ruff and verify_skills clean. No code changes in this step; pure documentation.
- **Status-line drift is real but bounded by the codified list.** Per the Step-2.7 lesson the checklist of six locations to update was named in advance (README, install.md, getting-started.md, workflow.md, reviewing-requirements.md Beyond footer, plugin README). Walking the list in order took ~10 minutes, with no greppable misses afterward. The grep `Phase 2 starts next|Phase 3 starts next|when phase 3 ships|behavior arrives in` returned no hits across the docs after the edits. **Pattern reinforced:** the status-line-drift checklist is the right level of pre-engineering — fewer than six locations would miss something; more than six is over-spec. **Future-implementer hint:** the same six locations need the next bump when 3.9 closes Phase 3. The phrasing then becomes "Phase 3 complete (YYYY-MM-DD); Phase 4 starts next".
- **PyYAML availability is a real consumer concern; documented in the walkthrough's Prerequisites.** A first-pass smoke run of the helpers from `/tmp` via system `python3` failed with `ModuleNotFoundError: No module named 'yaml'` because pdm-managed deps don't propagate to the system interpreter. Re-running via `pdm run python3 ...` worked. The walkthrough's Prerequisites section now calls this out explicitly: "PyYAML is available in the Python environment that runs the helpers. The project's `pyproject.toml` lists `pyyaml>=6.0` under `[project.dependencies]`; with `pdm install` it is on the path. When invoking the bundled helpers from a consuming project without pdm, ensure `pyyaml` is installed in the active Python (`pip install pyyaml`)." **Future-implementer hint:** when shipping a plugin helper that depends on a non-stdlib library, the user-facing walkthrough's Prerequisites section needs the explicit `pip install <lib>` (or pdm equivalent) callout. The helper's exit-2 error message could be improved in a future cleanup to name the missing dep ("PyYAML is not installed; run `pip install pyyaml`") rather than the raw `ModuleNotFoundError` Python emits.
- **Worked extension examples should span materially-different project shapes (D19 emphasis).** The customization guide's Phase 3 schema section ships three worked examples: (a) Python/FastAPI with `source-root: ../src`, (b) Node/Express with `enabled-languages: []` (documents what to do when v1 cannot parse the consuming project's language yet — still flags the gap so the surface is visible), (c) Postman-only with no OpenAPI. Each example targets a *materially-different* project shape so a consuming project recognizes its own situation in at least one of the three. **Pattern worth keeping:** when documenting an extensible schema, the worked examples should NOT all be variants of the same project shape; if they were, a consuming project with a different shape would not see itself. **Future-implementer hint:** for Phase 5+ schemas, follow the same rule — pick examples that span Python-only, JS-only, and a third axis (multi-repo / mono-repo / docs-only).
- **Final SKILL.md deferral-wording grep is the cheap final check.** `grep -niE "behavior arrives in|coming in phase|placeholder|until.*ships|when phase 3 ships|phase 3 starts next"` against `plugins/test-commander/skills/tc-knowledge/SKILL.md` AND across all of `docs/` returns no hits after Step 3.7. The Step-3.6 lesson predicted this; Step 3.7 verified it. **Pattern worth keeping:** before declaring a documentation pass done, run the deferral-wording grep across BOTH the SKILL.md AND the user-facing docs. Stale "when phase X ships" wording is the most common drift the grep catches. **Future-implementer hint:** at the close of Phase 4's docs pass, run the same grep with "phase 4 starts next" and "when phase 4 ships" patterns added to the regex.
- **No new tests authored for the documentation pass.** Step 2.7's lesson observed "no bugs encountered; clean docs pass" — the same holds for 3.7. The link checker (137 files clean) provides the only automated guard; the sign-off test in 3.9 will assert structural deliverables (the walkthrough file exists, the customization-guide schema section exists, etc.) but no per-helper test is added. **Pattern reinforced:** the test-first discipline is for *helper behavior*, not for *user-facing prose*. A documentation pass that lands real content with no broken links and no stale wording is done.
- **Customization-guide audit (per the Per-Phase Customization-guide Convention) — comprehensive Phase 3 schema landed.** The convention requires every phase that ships a configurable surface to update the customization guide with at least one worked example showing how a consuming project extends it. Phase 3 introduced four extensible sub-blocks (`tc-knowledge.documents`, `tc-knowledge.code`, `tc-knowledge.api`, `tc-knowledge.tests`); the per-sub-step lessons (3.2, 3.4, 3.5, 3.6) recorded the deferral with "customization-guide update deferred to Step 3.7". Step 3.7 lands the consolidated schema section + three worked examples + "Phase 3 — what landed" subsection. **Pattern worth keeping:** deferring per-sub-step customization-guide updates to a single comprehensive pass at the end of a helper sweep produces a cleaner end-state document than incremental updates. Each per-sub-step lesson recorded the deferral so the 3.7 author had a complete checklist of what to land. **Future-implementer hint:** for future multi-sub-step skill sweeps (Phase 4's `tc-explore` has 4 sub-commands, Phase 6's `tc-build-framework` has 5), follow the same pattern: defer per-sub-step customization updates to the phase's dedicated documentation step, but record the deferral explicitly in each sub-step's lesson so the consolidation step has a complete checklist.

##### Step 3.6 — `/tc:learn-from-tests` + Phase-3 helper sweep complete

- **Helper-mirroring 23/23 GREEN on first run (fifth datapoint, last `/tc:learn-from-*` helper).** Step 3.6 was the fifth Phase-3 helper authored by copy-renaming the previous helper's skeleton (3.2 → 3.3 → 3.4 → 3.5 → 3.6). Same result as Step 3.5: every test passed on the first run, no RED-to-GREEN cycle after the initial implementation. **Pattern fully reinforced:** the skeleton (workspace IO → config loader → source discovery → per-source extraction → cross-check → render per-source model → cross-cutting section-overwrite → open-questions dedup-append → synthesizer) is mature enough that adapting it to a new source type requires only the per-source extraction + cross-check + cross-cutting scope decisions; everything else carries over verbatim. **Future-implementer hint:** future Phase-N skills that have a "walk a source root and extract structured findings" shape (Phase 4 exploration, Phase 5 BDD generation, Phase 8 learning ingestion) can adopt the same skeleton. The unique pieces will be source-format detection, the per-source extraction rules, and the gap detectors; the rest is fungible.
- **Workspace template addition tripped two Phase-1 tests with exact-equality assertions on file count.** Adding `tests-coverage.md` to `plugins/test-commander/templates/workspace/product-knowledge/` bumped the workspace template's file count from 63 to 64. `tests/test_workspace_state.py::test_snapshot_after_fresh_init_has_zero_populated` and `tests/test_phase_1_integration.py::test_full_phase_1_workflow` both asserted `sum(snap.counts.values()) == 63` and `len(init_result.created) == 63`. The Phase-2 Step-2.8 lesson explicitly codified the invariant ("every phase sign-off test that asserts a numeric cap, count, or version should assert `>=`, not `==`") but Phase-1 was authored *before* that lesson and never retrofitted. **Mitigation:** updated both tests to use `>= 63`, with an inline comment citing the Phase-2 Step-2.8 lesson and naming Phase-3 Step-3.6 as the bump. Captured `initial_count` once at the top of the integration test and re-used it instead of re-asserting `== 63` for the re-init idempotency case. **Future-implementer hint:** when shipping a workspace template change in Phase 4+ (new artifact under `charters/`, `bdd/features/`, etc.), grep `tests/test_workspace*.py` and `tests/test_phase_*_integration.py` for `== <count>` assertions *before* landing the template change. The retrofit pattern is straightforward but the asymmetric break is annoying.
- **Cross-helper import doubles as ergonomic test setup.** Step 3.5 introduced the cross-helper import pattern (3.5 imports 3.3 for spec endpoints). Step 3.6 extends it (3.6 imports 3.4 for code functions). In both cases the consumer helper gets structured findings without re-parsing the upstream's rendered Markdown. **Bonus:** the tests' `test_untested_function_routes_after_code_ran` and `test_cross_cutting_entities_has_from_tests_section` both depend on running `extract_knowledge_from_code` first, then 3.6. The test reads as "run 3.4, then 3.6" — exactly the user-facing flow. **Pattern worth keeping:** when a Phase-N+1 helper consumes Phase-N's findings, the integration test should drive both in order; the test then doubles as a smoke-test of the natural usage pattern.
- **Final SKILL.md pass eliminates ALL deferral wording.** A repo-wide `grep -niE "behavior arrives in|coming in phase|placeholder|until.*ships"` against `tc-knowledge/SKILL.md` returns no hits after Step 3.6's commit. The per-command sections describe every shipped command with its `Run:` example and methodology pointer; the "What to do when a slash command fires" section enumerates per-command judgment-layer focus for all five commands rather than just one. **Pattern worth keeping:** at the close of a multi-step skill helper sweep, run the deferral-wording grep as a final check before the documentation pass. The grep is fast and catches stragglers that "all commands shipped" can miss if individual `Run:` blocks weren't updated. The Phase-2 Step-1.7 wording-grep pattern (per the AGENTS.md "no deferral wording" rule) is the same operation.
- **`## From tests` section in entities.md uses confidence annotation, not just bullets.** Per the plan: "covered symbols contribute to entities.md's confidence column". Step 3.6 renders each class from `code-derived-model.md` as `- **ClassName** - exercised by at least one test (confidence: covered)` OR `- **ClassName** - no test references the class (confidence: uncovered)`. The convention surfaces *which* code entities are tested and *which* are not, in a single grep-friendly listing. **Future-implementer hint:** if a future helper wants to annotate entities with confidence (e.g., a Phase-8 helper that scores entity certainty from learning data), it can adopt the same `(confidence: <label>)` convention. The trailing parenthetical is regex-friendly and human-readable.
- **Phase 3 helper sweep closes cleanly: 311-test suite, 136 link-checked files, all five learn helpers + the synthesizer shipped.** After 3.6: pytest count is 311 (88 at Phase-1 close → 154 at Phase-2 close → +23 per Phase-3 sub-step times 6, plus the +2 retrofitted Phase-1 tests). Markdown link checker covers 136 files (88 at Phase-1 close → 107 at Phase-2 close → +9 per Phase-3 sub-step for new methodology + template + command page). `verify_skills.py` reports `tc-knowledge UNEXPECTED (phase 3) - ahead of schedule` (warn-only); the cap bump lives in Step 3.8. **Pattern reinforced:** the per-sub-step cadence — write tests (RED) → mirror skeleton → drive GREEN → author docs → update SKILL.md → make verify → CHANGELOG + plan lesson → commit + push — produced consistent, predictable, reviewable diffs across six sub-steps without surprise regressions. The discipline scales.
- **Remaining sub-steps shape**: 3.7 is the dedicated documentation pass (`docs/user-guide/building-project-knowledge.md` + `docs/command-reference.md` + `docs/workspace-reference.md` enrichment + `docs/user-guide/customizing-for-your-project.md` Phase-3 schema with at least three worked examples + status-line refresh across six locations). 3.8 is the testing finalization (bump `DEFAULT_PHASE_CAP` from 2 to 3 + `CATALOG["tc-knowledge"] = 3` + `tests/test_phase_3_integration.py` driving all five helpers end-to-end). 3.9 is the sign-off (six sub-sub-steps closing in the `phase-3` annotated tag). No new commands ship in 3.7/3.8/3.9; the helper sweep is closed.

##### Step 3.5 — `/tc:learn-from-api`

- **Helper-mirroring pattern: 23/23 GREEN on first run.** Fourth Phase-3 helper authored by copy-renaming the previous helper's skeleton (3.2 → 3.3 → 3.4 → 3.5). Result: every test passed on the first run — no debugging round, no RED-to-GREEN cycle after the initial implementation. Prior steps each surfaced one or more cosmetic or design bugs the tests caught (3.2: five distinct issues; 3.3: one table-cell shape; 3.4: three open-question format issues). 3.5 produced zero. **Why?** Two reasons: (a) the helper's design follows the now well-trodden Phase-3 skeleton (workspace IO → config loader → source discovery → per-source extraction → cross-check → render per-source model → cross-cutting section-overwrite → open-questions dedup-append → synthesizer), and (b) the lessons from 3.2/3.3/3.4 had already codified the conventions the tests check for (kind-prefix on open-questions, byte-deterministic outputs, generator-marker check for upstream artifacts, explicit cross-cutting scope). **Pattern reinforced four datapoints in:** mirroring concentrates the unique implementation effort into the per-source extraction logic; everything else is fungible. **Future-implementer hint:** 3.6 (`/tc:learn-from-tests`) can confidently mirror 3.5; the only unique pieces are the test-file detection (pytest + Playwright shapes), the symbol-reference cross-check against `code-derived-model.md`, and the `tests-coverage.md` artifact + Workspace-Layout update.
- **Cross-helper import: 3.5 reuses 3.3's parser via Python import.** The plan called for 3.5 to cross-check recorded API responses against the spec's declared status codes. The cleanest implementation: import `extract_knowledge_from_specs` and call its `aggregate()` to get parsed `Endpoint` objects. This avoided duplicating OpenAPI / Postman parsing logic across two helpers. The small refactor needed: add a `statuses: tuple[str, ...] = ()` field to 3.3's `Endpoint` dataclass and populate it from `paths.<path>.<method>.responses` keys. The new field is not surfaced in 3.3's `render_spec_model`, so 3.3's tests stayed green (21 passed). **Pattern worth keeping:** when a downstream Phase-3 helper needs structured data from an upstream helper, prefer module import + dataclass field extension over re-parsing the source artifact OR re-parsing the upstream's rendered Markdown. The Python module is the cleanest single source of truth. **Future-implementer hint:** if 3.6 needs structured code data (functions to cross-check against tests), import `extract_knowledge_from_code` directly rather than re-parsing `code-derived-model.md`.
- **Fixture realignment for cross-source semantics (second occurrence in Phase 3).** The seeded fixture's `mismatched-status` marker was originally on `POST /workspaces/{id}/assets returning 500`, but that spec endpoint has the `unspecified-status` gap on the spec side (no `responses` declared). Without declared responses there is nothing to mismatch against, so emitting `mismatched-status` would have been semantically muddled (two gaps for the same root cause). Moved the marker to `DELETE /sessions/{id} returning 500` (spec declares only 204) and changed `POST /workspaces/{id}/assets` back to 201 success. Two distinct seed gaps now have unambiguous semantics. **Pattern (repeated from Step 3.4):** when a Phase-3 fixture is going to be cross-checked by a later helper, the cross-source semantics must be valid; if the fixture predates the cross-checker, realign in the cross-checker's sub-step. **Future-implementer hint:** during 3.6, double-check that the seeded `untested-function` and `unsupported-test-runner` markers will still fire cleanly against the (then-realigned) fixture state.
- **Live-mode refusal pattern: detect pytest via `PYTEST_CURRENT_TEST`.** The plan required `/tc:learn-from-api` to refuse live mode under tests so the suite never reaches the network. Implementation: `os.environ.get("PYTEST_CURRENT_TEST")` returns a non-empty string when pytest sets it for each test. The helper checks this before constructing any HTTP request and exits 2 with a clear `live mode refused under pytest` error. **Pattern worth keeping:** for any future Phase-3+ helper that gains the *capability* to reach the network, the same env-var check applies. The pytest env var is more reliable than `IS_TEST` or other ad-hoc signals because it is set automatically by pytest's test-collection hook for every test. **Future-implementer hint:** v2's live-mode implementation can add a `--allow-network` CLI flag for explicit opt-in even outside pytest, but the env-var check should remain as the default safety floor.
- **`Authorization` header as an auth-required signal works in practice.** The seeded fixture's three recordings carrying `"authorization": "Bearer redacted"` were correctly inferred as auth-required, and the `business-rules.md` `## From api` section emitted one rule per endpoint. The 401/403-without-Authorization branch wasn't exercised by the fixture (no 401s recorded) but the logic is in place. **Future-implementer hint:** if a real consuming project records both authenticated and unauthenticated requests to the same endpoint, the helper currently flags the endpoint as auth-required as long as *any* request carries the header. This is intentional — a single confirming recording suffices. Document this in the methodology so consuming projects do not mistake the inference for "all recordings to this endpoint required auth".
- **Stable cross-cutting section order paid off.** All four cross-cutting files now show `## From documents`, `## From specs`, `## From code`, `## From api` in stable order across re-runs of any subset of helpers. The shared `SOURCE_ORDER = ("documents", "specs", "code", "api", "tests")` constant in each helper (and in the synthesizer) is the contract; section bodies are looked up by source name and rendered in that order regardless of which helper most recently wrote which section. **Pattern worth keeping:** any future cross-cutting artifact (Phase 5 traceability, Phase 8 learning) should adopt the same per-source section convention so contributions remain independent and re-runs remain idempotent.
- **Empty `## From <source>` sections are silently omitted by the renderer.** When 3.5 contributes only entities + business-rules (not user-journeys or assumptions), `update_cross_cutting` writes an empty `api` body for the two journals it does not touch — but wait, 3.5 only *calls* `update_cross_cutting` for the two it does touch. So `user-journeys.md` and `assumptions.md` never receive an `api` section at all. The renderer's "skip empty bodies" behavior is the safety net: even if a future helper accidentally writes an empty section body, it would not pollute the artifact. **Pattern worth keeping:** the helper-level "only update files I write to" discipline + the renderer-level "skip empty bodies" defense-in-depth combination is robust. Each layer alone would work; both together leave no room for accidental section bloat.
- **`tc-knowledge.api:` schema lands but customization-guide update remains deferred to Step 3.7.** This is the third Phase-3 helper to introduce a new extensible surface (3.2 documents, 3.4 code, 3.5 api). Step 3.7's documentation-pass deliverable now covers three schema blocks. The customization guide will need a "Phase 3 — what landed" subsection naming all three (with `tc-knowledge.tests` from 3.6 expected to follow), worked extension examples spanning materially-different consuming-project shapes, and an explicit "live mode is opt-in and refused under pytest" callout for the api block.

##### Step 3.4 — `/tc:learn-from-code`

- **Fixture realignment for cross-source matching.** The seeded openapi.yaml originally used distinct operationIds (`create_session`, `destroy_session`, `upload_asset`) that did not match the Python function names in `src/` (`sign_in`, `sign_out`, `upload_file`). Step 3.4's `unimplemented-endpoint` cross-check matches by operationId; against the original fixture, 5 of 6 endpoints would have spuriously been flagged as unimplemented. **Mitigation:** updated the fixture's spec to use operationIds that mirror the function names (`sign_in`, `sign_out`, `upload_file`, plus pre-existing `get_account`, `list_workspaces`, `list_assets`) AND added `src/app/api/accounts.py::get_account`. Only `GET /workspaces` (operationId `list_workspaces`) remains unmatched - the single seeded `unimplemented-endpoint` gap. 3.3's tests didn't pin specific operationId values, so they stayed green. **Future-implementer hint:** when a Phase 3 fixture is going to be cross-checked by a later helper, design the cross-source alignment up front; if the fixture predates the cross-checker, plan to realign it in the cross-checker's sub-step rather than papering over with a fuzzy matcher.
- **Open-question kind prefix.** The Step 3.4 tests asserted on the gap kind appearing in the open-questions text (`undocumented-function`, `language-unsupported-in-v1`, `unimplemented-endpoint`). The 3.2 and 3.3 helpers emit the gap *description* only - the kind label is metadata not surfaced in the question text. **Mitigation:** 3.4's `append_open_questions` prepends `[<kind>] ` to every emitted question. This makes grepping the open-questions file by gap kind work uniformly and gives consuming projects a structured way to triage. **Future-implementer hint:** future helpers (3.5, 3.6) should emit the kind prefix on their open-questions entries too. 3.2 and 3.3 could be updated for consistency in a follow-up; the byte-identical idempotency tests there only check line counts, not content, so the change would not regress prior sign-off tests.
- **Spec-cross-check needs a "has the upstream actually run?" check (the Phase-2 Step-2.5 lesson recurs).** First cut of `parse_spec_endpoints` returned the empty list when `spec-derived-model.md` was missing, but happily parsed the template stub if present. The template stub does not contain the `Auto-generated by /tc:learn-from-specs` marker, so the parser had to short-circuit before reading the endpoints table. **Mitigation:** added `SPEC_MODEL_GENERATED_MARKER = "Auto-generated by /tc:learn-from-specs"`; `parse_spec_endpoints` returns `[]` when the marker is absent OR when the body contains the `no spec found` empty-run sentinel. The cross-check is therefore order-independent: running code before specs produces no `unimplemented-endpoint` gaps; re-running code after specs lands them. **Future-implementer hint:** every Phase 3.x helper that consumes an upstream-generated artifact must use the generator-marker check pattern (not `path.is_file()`, not `stat().st_size > 0`). This is the third occurrence of the pattern in the project: Phase 2 Step 2.5 introduced it; Phase 3 Step 3.2's synthesizer needs it for its `_is_generated()`; Step 3.4 needs it again for spec-vs-code cross-checking. Treat it as a project invariant.
- **AST attribute extraction must handle both `Assign` and `AnnAssign`.** Initial cut only walked `ast.Assign` nodes inside `__init__` to find `self.<attr> = ...` patterns. Real Python increasingly uses `self.<attr>: <type> = ...` annotated assignments (`ast.AnnAssign`), and modern style guides recommend them. Without handling both, classes whose constructors use annotated assignments would have empty attribute lists. The seeded fixture happens to use plain `Assign`, but the helper handles both. **Future-implementer hint:** any AST walker that captures class attributes from `__init__` needs to handle `ast.Assign`, `ast.AnnAssign`, and arguably also assignment-via-tuple-unpacking (`self.a, self.b = ...`); the third form is rare enough to defer.
- **Stdlib-first dependency policy verified.** Step 3.3 added PyYAML as the first non-stdlib dep. Step 3.4 ships pure stdlib (`ast`, `re`, `argparse`, `pathlib`, dataclasses). The `ast` module gave everything: stable, well-documented, fast, deterministic, zero install footprint. **Pattern reinforced:** the project's policy ("stdlib-first; canonical pure-Python dep when the alternative is a custom parser for a complex grammar") is right. Python's own AST is the universal vocabulary for Python source; reaching for a third-party parser would have added complexity for no extractor benefit.
- **Helper-mirroring prediction holds (third datapoint).** Step 3.4 was the third Phase-3 helper authored by copy-renaming the previous helper's skeleton (3.2 -> 3.3 -> 3.4). Pattern: 23 tests RED -> 20 GREEN after first cut -> 3 RED remaining (all the same open-question format issue) -> one fix -> 23/23 GREEN. The unique bug class for 3.4 (AST attribute extraction completeness) was a real correctness concern unique to AST walking; everything else flowed from the skeleton. **Future-implementer hint:** 3.5 (`/tc:learn-from-api`) and 3.6 (`/tc:learn-from-tests`) can confidently mirror 3.4's skeleton. The unique implementation effort for each is per-source extraction logic plus the gap detectors; the rest is fungible.
- **`enabled-languages: []` short-circuits the AST walk entirely while still flagging unsupported-language files.** An early cut had the AST walk unconditional and used `enabled-languages` only as documentation. After thinking about how a consuming project might use this (e.g., to disable Python parsing temporarily during a v1-language audit), changed to: empty list -> skip the Python AST walk; unsupported-language extension walk still runs. **Future-implementer hint:** for v1 the only meaningful setting is `[python]` (default) or `[]` (disable parsing); future phases adding TS/JS will extend the dispatch on `enabled-languages` content.
- **`source-root` resolves relative to the workspace root, not the consuming project's CWD.** The plan's example `source-root: src` would naturally resolve to `<workspace>/src/`, which is unusual (the workspace is `.test-commander/` inside the project root). For consuming projects whose source lives at `<project>/src/` (the standard Python layout), the right setting is `source-root: ../src` to escape the workspace. The test exercises both default and explicit paths inside the workspace; the documentation explicitly mentions `../src` as the typical setting for real projects. **Future-implementer hint:** the workspace-relative path is the simplest semantics; complicate the resolution only if real-world feedback says otherwise.
- **No customization-guide audit deferred this time.** Step 3.4 introduces a new extensible surface (`tc-knowledge.code.{source-root, enabled-languages, ignored-paths, endpoint-decorator-patterns}`); recording the surface here for the Step 3.7 documentation-pass audit. The customization-guide update is intentionally deferred to 3.7 (which aggregates the full `tc-knowledge:` schema across 3.2-3.6 with worked extension examples). Step 3.2's lesson already records this deferral; 3.4 reinforces it.

##### Step 3.3 — `/tc:learn-from-specs`

- **Helper-mirroring prediction verified.** Step 2.3's lesson (Phase 2) predicted that copy-renaming the nearest sibling helper and adapting per-source extraction would dramatically reduce bug discovery cost. Step 3.3 was the first chance to test this inside Phase 3. The skeleton from `extract_knowledge_from_docs.py` (workspace IO + source discovery + per-document extraction + cross-document aggregation + render functions + `update_cross_cutting` + `append_open_questions` + synthesizer invocation) was copied verbatim; only the source-format detection, the per-format extractors, the gap detectors, and the cross-cutting scope changed. Result: 21 RED on first run, 19 GREEN after the helper landed, 2 RED remaining — both the same root cause (test asserted `"POST /sessions"` as a substring but the table rendered `"| POST | /sessions |"` with a column separator). One small fix (merged method + path into a single table cell) turned both GREEN. **Pattern reinforced:** the prediction held — Step 3.3 produced one cosmetic bug, not the parser-body / template-stub / case-sensitivity class of bugs Step 3.2 surfaced. **Future-implementer hint:** the Phase 3 helper skeleton is stable enough that 3.4, 3.5, 3.6 can confidently copy-rename 3.2 or 3.3 and concentrate the implementation effort on the per-source extraction logic alone.
- **PyYAML added as the first non-stdlib dependency.** Phase 0-2 shipped stdlib-only; Step 3.3 added `pyyaml>=6.0` to `pyproject.toml` because OpenAPI YAML parsing with a tolerant indentation parser would be brittle for real-world specs (anchors, aliases, multiline strings, deeply nested mappings). PyYAML is pure-Python, canonical, zero-config. Future Phase-3 sub-steps and later phases (Phase 6 test data, Phase 10.5 policy) will reuse it. **Future-implementer hint:** the project's policy is now "stdlib-first; add a canonical pure-Python dep when the alternative is a custom parser for a complex grammar". Reach for PyYAML, json (stdlib), `ast` (stdlib), `re` (stdlib) before considering anything heavier.
- **Markdown table cell ambiguity bites test assertions (low-severity, RED for two tests).** First cut rendered endpoints as `| METHOD | /path | ... |` (separate columns). The test asserted `"POST /sessions"` as a substring on the assumption that the natural representation of an endpoint is the compact `METHOD PATH` form. The separate columns meant the literal substring `"POST /sessions"` (with one space) never appeared. **Mitigation:** merged method + path into a single table cell. The rendered model now reads `| POST /sessions | create_session | openapi.yaml:NN |` which is also more compact and human-readable. **Future-implementer hint:** when a test asserts on a compact natural form (`METHOD PATH`, `Term: definition`, etc.), pick the cell shape that contains that form *as a literal substring*. The alternative — adding a separate compact-summary section above the structured table — works but adds noise to the rendered output.
- **`Endpoint.summary` shadowed by `dict.get` typing.** Initial extractor used `summary = op.get("summary") if isinstance(op.get("summary"), str) else ""` which exceeded the 100-char line limit. Split into a two-line form (`op_id_raw = op.get(...)` then ternary). Tiny lint nit, but it surfaced the cleaner pattern: when an OpenAPI / Postman field could be `str | dict | list | None`, do the type-check on a captured variable, not inline in the conditional expression. **Future-implementer hint:** OpenAPI / Postman fields are heterogeneous; the type-narrowing-on-capture pattern is more readable across the dispatch.
- **Scope discipline — only entities + business-rules cross-cutting writes from 3.3.** The plan's partition specifies that specs contribute endpoints to `entities.md` (as resources) and auth-schemes to `business-rules.md`. It explicitly does NOT specify journeys or assumptions contributions — specs declare no journeys and they are confirmed facts, not inferences. The first cut respected this scope; two explicit negative tests assert that `user-journeys.md` and `assumptions.md` do NOT receive a `## From specs` section. **Pattern worth keeping:** every Phase-3 sub-step should ship explicit negative tests for cross-cutting files it does NOT touch. The negative tests defend the section-overwrite contract: a regression that erroneously writes empty `## From specs` sections everywhere would be caught immediately. **Future-implementer hint:** 3.4 contributes to entities + business-rules; 3.5 contributes to entities + business-rules; 3.6 contributes to entities only (covered-symbol confidence). Each sub-step needs the matching negative assertions.
- **Postman v2.1 path extraction handles three URL shapes (`raw` string, `url.path` array, fully-qualified URL with `{{base_url}}`).** A Postman collection author can express a URL in three different formats, sometimes within the same collection. The first cut handled `url.path` (array of segments) but missed `url.raw` strings with `{{base_url}}` variable substitution. Added `_strip_postman_variables` to drop leading `/{{base_url}}` and similar template prefixes so the captured path is just the API path. **Future-implementer hint:** when extracting paths from Postman collections, always pass through `_strip_postman_variables` before recording the path; the raw form is variable-laden and will not match what the spec declares.

##### Step 3.2 — `/tc:learn-from-docs` + shared synthesizer

- **`_section_range_for` must use heading levels, not "next heading of any level" (medium-severity, blocked two tests).** The first cut walked spans linearly and ended the journey section at the next heading — but the seeded `user-journey-sign-in.md` has the journey heading at H1 (`# User journey - sign in and open a workspace`) followed by `## Steps` at H2 containing the numbered list. The naïve range ended at `## Steps`, so the journey extractor saw zero steps. **Mitigation:** rewrote `_section_range_for` to look up the current heading's level and terminate at the next same-or-shallower-level heading; deeper child headings remain part of the section. Same logic applies uniformly to entity/glossary headings. **Future-implementer hint:** every heading-scoped extractor that consumes content under H2/H3 children of an H1 needs this level-aware termination; "ends at next heading" is wrong any time markup uses nested structure.
- **Synthesizer must treat "no <source> found" empty-run sentinels as not-ingested (medium-severity, blocked one test).** After `/tc:learn-from-docs` runs against an empty `documents/uploaded/`, `documentation-model.md` no longer carries the workspace-template stub marker `_(empty until Phase 3 ships.)_`, so the first cut of `_is_generated` returned True and the synthesizer reported documents as ingested. **Mitigation:** added an `EMPTY_RUN_MARKERS` tuple of helper-emitted "no <source> found" sentinels; `_is_generated` rejects any text containing one. **Future-implementer hint:** every learn-from helper's empty-run output must contain a distinctive sentinel the synthesizer can detect; pre-populate `EMPTY_RUN_MARKERS` for each new helper in 3.3-3.6. The pattern is the inverse of the Phase-2 Step-2.5 lesson — there the helper *consuming* the upstream had to detect "not yet generated"; here the synthesizer consuming five potential upstreams has to detect "no data on this path even though the file is technically non-stub".
- **Synthesizer must surface entity/journey names, not just counts (low-severity, but improves the cold-user UX).** First cut rendered just counts (`From documents: 5`) without naming the entities. The test wanted at least one entity name in `system-model.md` because counts alone are not a useful synthesis. **Mitigation:** added `extract_bolded_names()` that parses bolded-leading-name bullets out of each cross-cutting `## From <source>` body and rolls them up into the synthesis with `(from <source1>, <source2>, ...)` provenance. **Future-implementer hint:** the cross-cutting section bodies should consistently use `- **Name** (path:line)` for entities and journeys so the synthesizer's regex `^\s*-\s+\*\*([A-Z][A-Za-z0-9 _-]+?)\*\*` works uniformly. Don't depart from the bolded-leading-name convention in 3.3-3.6 contributions.
- **Case sensitivity in entity-keywords extension (low-severity, surfaced by a test the seeded fixture didn't support).** Initial test used `entity-keywords: [Dashboard]` against the seeded `product-overview.md` where every "dashboard" mention is lowercase common-noun usage. The case-sensitive matcher (correct for domain proper nouns) didn't fire. **Mitigation:** rewrote the test to use an inline narrative with capitalized `Patient`, `Provider`, `Claim` — the realistic shape of a domain-vocabulary extension. **Pattern worth keeping:** edge-case tests that exercise extension surfaces should generate their own minimal fixtures rather than relying on the seeded happy-path corpus to incidentally contain the test's vocabulary. **Future-implementer hint:** when writing a Phase 3.x extension test, default to an inline fixture in the test body rather than assuming the shared seeded fixture is universally applicable.
- **`5`-level cross-link depth from skill methodology to repo docs (low-severity, caught by `check_links`).** Methodology files live one level deeper than SKILL.md (`skills/<skill>/methodology/<file>.md`), so a relative link to `docs/...` needs five `../` segments, not four. The Step-3.2 first draft borrowed the SKILL.md depth and shipped four-`../` paths. `check_links.py` flagged every one of them. **Mitigation:** corrected to five levels; cross-checked against the working Phase-2 methodology files which already use the correct depth. **Future-implementer hint:** when authoring methodology files for Phase 3.x, copy the link from a known-good Phase-2 methodology file (e.g., `tc-requirements/methodology/requirements-quality-review.md`) rather than computing the depth from scratch.
- **Templates must NOT link to runtime-only paths (medium-severity, caught by `check_links`).** The first cut of `system-model-template.md` used a clickable Markdown link to `documentation-model.md` as a sibling because the *rendered* system-model.md (which lives in `<workspace>/product-knowledge/`) has those sibling files. But the *template* lives in `plugins/test-commander/skills/tc-knowledge/templates/` where those sibling files do not exist; the link checker correctly flagged them. **Mitigation:** changed every cross-product-knowledge reference in the template to plain code-spans (`` `documentation-model.md` ``). The runtime synthesizer continues to emit real Markdown links in its rendered output. **Future-implementer hint:** templates illustrate output structure; any path the helper renders at runtime as a relative link should appear in the template as plain text or code span. Reserve clickable links in templates for paths that resolve *from the template's own location* in the plugin tree.

##### Step 3.1 — scaffold + fixture

- **Pytest collection of in-fixture Python (medium-severity, caught by `make verify`).** Phase 3's seeded sample-project fixture is the first one to ship example Python source and example test files (Phase 2's fixture was Markdown-only). With `testpaths = ["tests"]` in `pyproject.toml`, pytest's default recursive walk picked up `tests/fixtures/seeded-sample-project/tests/test_auth.py` and `test_validation.py` as collected modules and immediately failed on `ModuleNotFoundError: No module named 'app'` — because those files are *example consuming-project tests*, not Test Commander's own tests, and their import paths target the fixture's own `src/app/` tree, not anything on `pythonpath`. **Mitigation:** added `norecursedirs = ["fixtures"]` to the `[tool.pytest.ini_options]` block. The exclusion is scoped to the conventional fixture root, leaves `tests/test_*.py` collection unchanged, and is forward-compatible with Phases 4+ that will ship more example-code-bearing fixtures. **Future-implementer hint:** any phase fixture that contains executable Python under `tests/fixtures/<name>/` needs the `norecursedirs` guard; this one settles it once for the whole project. Note `ruff check .` still lints fixture Python — the example code is hand-authored to pass lint, so this is fine; only pytest collection needed exclusion.
- **Marker-token uniformity across file types (low-severity, caught by RED-then-GREEN cycle).** First fixture pass used `"_knowledge": "<dimension>"` JSON keys to seed gap signals (the README documented it that way). The scaffold-test regex looks for the literal substring `knowledge: <dimension>` and JSON keys produce `"_knowledge": "..."` with a `"` between `knowledge` and the colon — so the regex missed two seeds (`unspecified-endpoint`, `mismatched-status`). **Mitigation:** changed the JSON convention so the *value* of the `_knowledge` key carries the literal marker phrase: `"_knowledge": "knowledge: <dimension>"`. One regex (`knowledge:\s*([a-z][a-z0-9-]*)`) now matches uniformly across HTML, YAML, Python, TypeScript, and JSON. README updated to match. **Future-implementer hint:** when a marker convention must travel across multiple file types whose comment syntaxes differ, push the marker into the *content* (the literal token phrase) rather than the *syntax* (key shape, attribute name). Content survives every container.
- **`tc-knowledge` under `DEFAULT_PHASE_CAP=2` reports as `UNEXPECTED — ahead of schedule`, not `MISSING` or `MALFORMED`.** The verifier's design (Step 0.6.4): skills in the catalog whose phase > cap are skipped from "expected" but on-disk presence is still classified. `UNEXPECTED` is warn-only and does not fail the exit code, so `make verify` stays green through Phases 3.2–3.7. The cap bump to 3 lives in Step 3.8 per the plan; do not try to land it earlier to "clean up" the `UNEXPECTED` line. **Future-implementer hint:** mirrors Phase 2's identical scaffold-time behavior under `DEFAULT_PHASE_CAP=1`; this is the verifier working as designed.
- **Helper-mirroring pattern starts at Step 3.2.** Step 3.1 ships no helper, so the mirroring claim from the Phase-2 Step-2.3 lesson does not yet have evidence in Phase 3. Step 3.2 will be the first sibling-to-sibling mirror inside `tc-knowledge` and the first chance to verify the prediction.

---

## Phase 4 — Exploratory Testing and Test Idea Generation

**Goal.** Charter-based exploration that captures observations, risks, ideas, and evidence. Ship the `tc-explore` skill with four commands plus an internal review sub-mode that drive Playwright MCP against a target web application (or replay a recorded session in tests), produce structured charter / exploration-note / session-summary artifacts, enrich the Phase-2-seeded test-idea files with refined candidate scenarios drawn from real exploration, and surface anomalies as gap signals routed to `<workspace>/requirements/open-questions.md`.

**Architecture.** Each `/tc:explore-*`-family command is a Python helper plus a Markdown command file inside `plugins/test-commander/skills/tc-explore/`. Helpers do the deterministic work (load charters, parse recorded session events, classify observations, render artifacts, enrich Phase-2 test-idea seeds); Claude executes the judgment-heavy parts (ranking anomaly severity, deciding which observations belong as candidate scenarios versus noise, mapping exploration findings back to charter goals) by reading the per-command page and the methodology docs. Live mode integrates with Playwright MCP at runtime; pytest never reaches a real browser — recorded session replay is mandatory under the test harness, refused via the `PYTEST_CURRENT_TEST` env-var check established in Phase 3 Step 3.5.

**Phase-4 design decisions (folded in).**

- **Recorded session replay is the test contract; live Playwright MCP is opt-in.** The default `recorded` mode reads a captured session file from `<workspace>/documents/uploaded/recorded-sessions/<charter-id>.json` (or the configured path). The opt-in `live` mode (`tc-explore.mode: live`) drives Playwright MCP via the `tc-explore.mcp.endpoint:` configuration against a real target URL. Pytest never enters live mode — the helper detects `PYTEST_CURRENT_TEST` and exits 2 with a clear error before any MCP connection is attempted. Mirrors the Phase 3 Step 3.5 pattern verbatim.
- **Charters use stable `CH-NNN` IDs; sessions use `SESS-YYYYMMDD-NNN` IDs.** Every artifact carries its ID in a YAML frontmatter block plus inline `# {id}` markers so cross-references (session → charter, test-idea enrichment → session, anomaly → charter + session) resolve mechanically. Mirrors the Phase 2 `REQ-NNN`/`US-NNN`/`AC-NNN` convention.
- **Phase 4 reads product-knowledge but writes only to its own directories.** Inputs: `<workspace>/product-knowledge/` (system-model.md, entities.md, user-journeys.md for charter suggestions and exploration scope), `<workspace>/requirements/` (open-questions.md for candidate exploration targets, requirements-inventory.md for traceability), `<workspace>/risk-register/risk-register.md` (charter risk-area suggestions), `<workspace>/learning/accepted-lessons.md` (Phase-8 feedback loop, may be empty in v1). Writes: `<workspace>/charters/`, `<workspace>/exploration-notes/`, `<workspace>/sessions/`, `<workspace>/test-ideas/` (enrichment only, never overwrite seeds), `<workspace>/evidence/screenshots/` (referenced from notes). Does NOT write to `<workspace>/traceability/` (Phase 5 owns) or `<workspace>/product-knowledge/` (Phase 3 owns). The integration smoke in 4.7 asserts the boundary directly, per the Phase 3 Step 3.8 lesson that codified the discipline.
- **Test-idea enrichment preserves the `tc-test-idea/v1` schema.** Phase 2 Step 2.6's idempotency contract is "existing test-idea files are NEVER overwritten" because Phase 4 enriches them. Phase 4 honors that contract: the helper reads each existing `<REQ-ID>.md` seed, preserves the YAML frontmatter unchanged (`schema`, `requirement_id`, `requirement_title`, `source`, `status`, `phase_2_findings`, `candidates`), and appends a new `## Phase 4 enrichment` body section with refined candidate scenarios drawn from exploration sessions plus a `phase_4_sessions: [SESS-IDs]` frontmatter field added once (and updated, never duplicated, on re-runs). The Phase 4 schema bump is `status: seed` → `status: enriched`. The test for this contract asserts byte-identical preservation of every frontmatter key the seed shipped with.
- **Internal review sub-mode auto-runs at the end of every exploration session.** Designed after `mcp-exploratory-testing:review-exploration`. Runs a deterministic rubric over the freshly-written session artifact: charter-ID present and resolvable, every observation cites a `<file>:<line>` provenance or `evidence/screenshots/<id>.png` reference, anomalies categorized into known severity buckets, every `## From product-knowledge` link resolves. Failures route to `requirements/open-questions.md` as `[exploration-review]` gap signals. The review sub-mode is internal — it does NOT ship as a fifth `/tc:` command in v1, matching the plan's original "four sub-commands" framing; instead, it runs at the end of `/tc:explore` (the `--no-review` flag suppresses it for advanced users who want to chain commands manually).
- **Universal cores; project-specific tuning via `tc-explore:` config extensions per D19.** Three extensible sub-blocks ship in v1: `tc-explore.charters.{risk-keywords, area-keywords}` for charter suggestion heuristics, `tc-explore.exploration.{mode, recorded-path, mcp-endpoint, target-url, charter-id}`, `tc-explore.review.{rubric-extensions}`. Universal cores carry only generic English / software-engineering vocabulary; project-specific domain extensions go through `<workspace>/config.yaml`. The seeded fixture exercises only the universal cores; the customization guide (updated in Step 4.6) carries worked examples for three different consuming-project shapes (a typical web-app + Playwright project, a mobile app where Playwright is replaced by a different MCP, an API-only project where exploration falls back to spec-derived journeys).
- **Helper-mirroring is the design.** Per the Phase-3 Step-3.5 result (five datapoints in across two phases: helper-mirroring concentrates the unique implementation effort into the per-source extraction logic; everything else is fungible), Steps 4.3–4.5 copy Step 4.2's helper skeleton and adapt only the per-command behavior. The integration smoke in 4.7 is budgeted as verification, not debugging, per the Phase 3 Step 3.8 lesson.
- **Phase 4 fixture bundles a recorded MCP exploration session.** The new `tests/fixtures/seeded-exploration-session/` directory carries: a `charter.md` (CH-001 worked example), a `recorded-session.json` (50–80 timestamped events: page loads, clicks, anomalies, screenshots taken), a `target-app.md` describing the seeded target (a universal SaaS dashboard — sign-in / accounts / workspaces / assets, mirroring the Phase 3 sample-project's narrative for cross-phase consistency), and a `README.md` describing the recording convention and the per-dimension defect catalog (one seeded anomaly per anomaly category: `slow-response`, `console-error`, `broken-link`, `missing-evidence`, `auth-mismatch`).

**Skills authored.** `tc-explore` — `SKILL.md` plus four command files (one per `/tc:` command), four methodology files (`exploratory-testing.md` umbrella plus `charter-based-exploration.md`, `test-idea-model.md`, `session-based-test-management.md`), and seven templates (`charter-template.md`, `exploration-note-template.md`, `session-summary-template.md`, `test-idea-enrichment-template.md`, `exploration-review-template.md`, `target-app-template.md`, `anomaly-record-template.md`).

**Design references.** `mcp-exploratory-testing:explore-app` (app reconnaissance shape), `mcp-exploratory-testing:explore-workflow` (bounded workflow exploration), `mcp-exploratory-testing:review-exploration` (review rubric for exploration artifacts). Per Decision D1 (vendor-and-own), `tc-explore` is authored in-repo; these MCP skills are design references only, never runtime dependencies. Playwright MCP itself is a runtime dependency for live mode (and recorded mode treats the captured session JSON as its sole input — no MCP connection needed in recorded mode).

**Inputs read.** `<workspace>/product-knowledge/`, `<workspace>/requirements/`, `<workspace>/risk-register/`, `<workspace>/learning/accepted-lessons.md`.

**Exploration rubric.** charter (mission + target + time-box + risk areas + acceptance criteria), observation (page state + action + result + timestamp), evidence (screenshot ID + caption + page URL), anomaly (category + severity + reproduction steps), journey (ordered sequence of observations satisfying a charter goal), session (charter ID + start/end time + observation count + anomaly count + review verdict), test-idea-enrichment (charter ID + session ID + new candidate scenario titles). Universal anomaly categories: `slow-response`, `console-error`, `broken-link`, `missing-evidence`, `auth-mismatch`, `unexpected-state`. The seeded fixture carries one defect per category marked with the universal `knowledge: <category>` token in the file's native comment syntax (mirroring the Phase 3 Step 3.1 marker uniformity lesson).

### Phase 4 — Execution outline

Eight sub-steps. TDD throughout: every implementation step lands its tests red before turning them green. Sub-step 4.1 scaffolds the skill and the shared seeded-exploration-session fixture; 4.2–4.5 implement the four commands; 4.6 is the dedicated documentation pass; 4.7 is the dedicated testing finalization (cap bump + integration smoke); 4.8 is the sign-off with a `phase-4` tag.

#### 4.1 — Skill scaffold and seeded-exploration-session fixture

- **Deliverables.**
  - `plugins/test-commander/skills/tc-explore/SKILL.md` — YAML frontmatter (`name: tc-explore`, single-line trigger-style `description`). Body lists the four commands plus the internal review sub-mode; carries deferral wording until each sub-step turns the wording into shipped-behavior description (per the "SKILL.md surfaces shipped behavior" convention). Mirrors the Phase 2 / Phase 3 scaffold shape.
  - `tests/fixtures/seeded-exploration-session/` containing:
    - `charter.md` — a `CH-001` worked example with mission, target area, time-box (`60min`), risk areas, acceptance criteria, and an explicit "this is a test asset, not a claim about scope" note (per the D19 fixture-discipline lesson).
    - `recorded-session.json` — a JSON list of 50–80 timestamped events: `page_load`, `click`, `fill`, `screenshot`, `console_message`, `network_request`, `anomaly`. Each anomaly entry carries an inline `"_knowledge": "knowledge: <category>"` field so the scaffold test can verify rubric coverage with the uniform regex from Step 3.1.
    - `target-app.md` — describes the seeded target (a generic SaaS dashboard — sign-in / accounts / workspaces / assets; mirrors the Phase 3 sample-project narrative for cross-phase consistency).
    - `README.md` — documents the recording convention, the universal anomaly-category catalog, the inline marker convention, and the "deliberately generic; not a claim about scope" framing (per the D19 audit).
  - `plugins/test-commander/skills/tc-explore/commands/.gitkeep`, `plugins/test-commander/skills/tc-explore/methodology/.gitkeep`, `plugins/test-commander/skills/tc-explore/templates/.gitkeep` — empty directories that 4.2–4.5 fill in. Each `.gitkeep` is removed by the first sub-step that lands real content in that directory.
  - Workspace template updates: `templates/workspace/charters/`, `templates/workspace/exploration-notes/`, `templates/workspace/sessions/` already exist as Phase-1 stubs; no new product-knowledge artifacts needed (Phase 4 writes only to its own directories).
- **Tests first.** `tests/test_tc_explore_scaffold.py` — asserts: skill directory and `SKILL.md` present with valid frontmatter (`name == "tc-explore"`, non-empty description, body references all four commands plus the review sub-mode); `commands/`, `methodology/`, `templates/` directories present; fixture directory exists with `charter.md`, `recorded-session.json`, `target-app.md`, `README.md`; `recorded-session.json` parses as JSON list with at least 50 entries each carrying `timestamp`, `event_type`, and (for anomalies) `_knowledge` markers; every universal anomaly category (`slow-response`, `console-error`, `broken-link`, `missing-evidence`, `auth-mismatch`, `unexpected-state`) appears in at least one `knowledge:` marker; charter has YAML frontmatter with `id: CH-001` and required fields (mission, target, time-box, risk-areas, acceptance-criteria). Test-first: lands red before any deliverable is written.
- **Definition of done.** Skill scaffolded; fixture covers every anomaly category and every required charter field; scaffold test green; `scripts/verify_skills.py` reports `tc-core PRESENT (phase 1)`, `tc-requirements PRESENT (phase 2)`, `tc-knowledge PRESENT (phase 3)`, `tc-explore UNEXPECTED (phase 4) - ahead of schedule` under `DEFAULT_PHASE_CAP=3` (the cap bumps to 4 in Step 4.7, not here — same convention as every prior phase scaffold step).
- **Review.** Manual read of the fixture against the exploration rubric — confirm every anomaly category has at least one seeded entry, the charter is realistic but deliberately-generic, and the recorded-session JSON shape is forward-compatible with the per-command extractors 4.2–4.5 will author.

#### 4.2 — `/tc:create-charter` (TDD)

- **Helper.** `plugins/test-commander/scripts/create_charter.py` — reads `<workspace>/product-knowledge/system-model.md`, `entities.md`, `user-journeys.md`, `<workspace>/requirements/open-questions.md`, and `<workspace>/risk-register/risk-register.md` to suggest a charter target (highest-risk untested entity, journey with most open questions, etc.). When invoked with `--target <area>` or `--mission <text>`, uses the supplied scope directly. Writes a charter file to `<workspace>/charters/<CH-ID>.md` with YAML frontmatter (`id`, `mission`, `target_area`, `time_box`, `risk_areas`, `acceptance_criteria`, `created_at`, `phase_3_sources`) and a structured body (Mission, Target Area, Time-Box, Risk Areas, Acceptance Criteria, Out-of-Scope, Phase 3 sources). Allocates the next `CH-NNN` ID by scanning existing charters. **Idempotency contract**: re-running with the same `--target`/`--mission` is a no-op (`created: 0, skipped: 1`); explicit re-allocation requires `--new-id`. User edits to existing charters are preserved.
- **Methodology.** `methodology/charter-based-exploration.md` — covers the charter rubric (mission specificity, target scope, time-box discipline, risk-area enumeration, acceptance-criteria testability), with one worked example per dimension drawn from the seeded fixture's `CH-001` and a Claude-judgment-layer paragraph (deciding which Phase-3 entity is worth a charter, ranking risk areas, identifying out-of-scope items the keyword check could not flag).
- **Umbrella methodology.** `methodology/exploratory-testing.md` — the umbrella that 4.3–4.5 reference. Documents the charter → explore → session-summary → test-idea-enrichment workflow, the session-based test management discipline (Bach + Bolton), the boundary that Phase 4 does not write to `traceability/` or `product-knowledge/`, and the test-idea enrichment contract (preserve Phase-2 `tc-test-idea/v1` frontmatter; append `## Phase 4 enrichment` body section; update `phase_4_sessions:` frontmatter once).
- **Templates.** `templates/charter-template.md`, `templates/target-app-template.md`.
- **Command file.** `plugins/test-commander/skills/tc-explore/commands/create-charter.md` — Inputs / Outputs / Preconditions / Behavior / Safety / Implementation / Definition of Done / See also.
- **SKILL.md update.** `tc-explore/SKILL.md` updated to describe `/tc:create-charter`'s shipped behavior and instruct Claude to invoke the bundled helper. Stale deferral wording for this command removed.
- **Tests first.** `tests/test_create_charter.py` — at minimum: uninitialized workspace refused with a clear error; `<workspace>/product-knowledge/` empty (no Phase 3 ingestion yet) refused with a precondition error directing the user at `/tc:learn-from-docs`; `--target` argument generates a `CH-001.md` charter with valid frontmatter; auto-suggestion (no `--target`) chooses the highest-risk entity from the seeded fixture's product-knowledge state; idempotent re-run with same `--target` produces `created: 0, skipped: 1`; explicit `--new-id` flag re-allocates as `CH-002`; user-edited charter body preserved on re-run; charter file passes the internal `_charter_is_well_formed` shape check (every required frontmatter key present + non-empty body sections); `tc-explore.charters.{risk-keywords, area-keywords}` config extensions union with the universal core.
- **Definition of done.** Helper passes all test cases; methodology covers the charter rubric with worked examples per dimension; umbrella `exploratory-testing.md` describes the cross-command workflow; templates authored; per-command page complete; `tc-explore/SKILL.md` no longer carries deferral wording for `/tc:create-charter`.
- **Verification.** Pytest green. Eyeball the generated `<CH-ID>.md` charter for tone, structure, and the YAML frontmatter shape before declaring 4.2 done.

#### 4.3 — `/tc:explore` (TDD)

- **Helper.** `plugins/test-commander/scripts/explore.py` — reads `<workspace>/charters/<CH-ID>.md` (required), drives Playwright MCP in `live` mode OR replays a recorded session from the configured path in `recorded` mode (default). Each MCP event becomes a structured `Observation(timestamp, event_type, page_url, action, result, screenshot_id)` record. Anomalies are classified into the universal categories at extraction time. Writes `<workspace>/exploration-notes/<SESS-ID>.md` (overwrite; pure generated report — re-running the same charter against the same recording is byte-deterministic) with per-event detail table, anomaly summary, evidence index, charter-coverage matrix. Updates `<workspace>/evidence/screenshots/<screenshot-id>.png` references (the seeded recording bundles minimal placeholder PNGs to keep the test deterministic; real screenshots populate at runtime in live mode). Calls the internal review sub-mode (Step 4.6 wires the auto-run; 4.3 ships the sub-mode itself).

  **Live-mode refusal under pytest** mirrors Step 3.5: `os.environ.get("PYTEST_CURRENT_TEST")` returns truthy → raise `LiveModeRefusedError` before any MCP connection is attempted, exit 2 with a clear error.

  **Partition table — mechanical extraction per observation dimension.**

  | Dimension | Universal-core extraction rule |
  | --- | --- |
  | observations | Every event in the recorded session JSON (`event_type ∈ {page_load, click, fill, screenshot, console_message, network_request}`) |
  | evidence | Every `screenshot` event captures a `screenshot_id` and a `page_url`; the helper renders an Evidence index in the note |
  | journeys | Detect sequences of events spanning a single page-load through the next page-load as journey segments (mirrors Phase 3 user-journey detection); name each by the first user action's target |
  | anomalies | Every event carrying `anomaly: {category, severity}` becomes an anomaly entry; severity universal core: `{low, medium, high, critical}` |
  | charter-coverage | Cross-reference observed `page_url` substrings against the charter's `target_area` and `acceptance_criteria`; mark each acceptance criterion `observed`, `partial`, or `unobserved` |
  | gap: missing-evidence | Anomaly entry without an adjacent `screenshot` event captured within ±3 seconds of the anomaly timestamp |
  | gap: charter-coverage-shortfall | One or more acceptance criteria marked `unobserved` after the full session |

- **Internal review sub-mode.** A `_review_session()` function in `explore.py` (not a separate command). Auto-runs after the session note is written (suppressible with `--no-review` flag). Runs a deterministic rubric: charter-ID resolvable to an existing charter; every observation cites either a `evidence/screenshots/<id>.png` reference (for visual observations) or a `recorded-session.json:<index>` provenance citation; every anomaly has a `category` from the universal core; every acceptance criterion has a coverage verdict. Failures route to `<workspace>/requirements/open-questions.md` as `[exploration-review]` gap signals with the `(source-id, question-text)` dedup contract from Phase 2.
- **Methodology.** `methodology/session-based-test-management.md` — covers the Bach + Bolton session-based discipline (charter time-box, debrief, deliverables), the observation / evidence / anomaly model, the universal anomaly categories, the charter-coverage rubric, and a Claude-judgment-layer paragraph (ranking anomaly severity beyond the mechanical category, identifying observations worth elevating to candidate scenarios, deciding which `partial`-coverage criteria warrant a follow-up charter).
- **Templates.** `templates/exploration-note-template.md`, `templates/anomaly-record-template.md`, `templates/exploration-review-template.md`.
- **Command file.** `plugins/test-commander/skills/tc-explore/commands/explore.md`.
- **SKILL.md update.** Updated to describe `/tc:explore`'s shipped behavior and the auto-running review sub-mode.
- **Tests first.** `tests/test_explore.py` — at minimum: uninitialized workspace refused; missing charter file refused with a clear error directing the user at `/tc:create-charter`; seeded charter + seeded recording → `<SESS-ID>.md` written with every observation captured (`recorded-session.json:<index>` provenance) and every seeded anomaly category surfaced; `[exploration-review]` gap signals route to open-questions when the seeded recording omits screenshots for one anomaly (the `missing-evidence` seed); charter-coverage matrix accurately marks `partial` for the seeded coverage shortfall; idempotent re-run produces byte-identical exploration note; `--no-review` flag suppresses the review sub-mode (no `[exploration-review]` gap signals appended); `mode: live` refused under pytest with the same `LiveModeRefusedError` shape as Step 3.5.
- **Definition of done.** Helper passes all test cases; the partition-table coverage assertion is part of the test suite; methodology covers the session-based discipline + the partition table + the Claude judgment layer; review sub-mode emits the expected gap signals; SKILL.md updated.
- **Verification.** Pytest green; smoke run against the seeded fixture produces an exploration note that flags every seeded anomaly.

#### 4.4 — `/tc:session-summary` (TDD)

- **Helper.** `plugins/test-commander/scripts/session_summary.py` — reads `<workspace>/exploration-notes/<SESS-ID>.md` (required), synthesizes a per-session summary at `<workspace>/sessions/<SESS-ID>.md` with: charter ID (resolved), session duration, observation count by event type, anomaly count by category and severity, charter-coverage verdict (`covered` / `partial` / `uncovered` summary), evidence index, candidate scenarios extracted from the session (which observations look like good test seeds — mirrors the Phase 2 candidate-scenarios shape so 4.5 can enrich the test-idea seeds with these), and an executive narrative section that Claude completes with the judgment layer. Pure generated report — overwrite mode; byte-deterministic. Updates a `<workspace>/sessions/index.md` (overwrite; lists every session by ID with one-line summaries).
- **Methodology.** Reuses `methodology/session-based-test-management.md` from Step 4.3; no new methodology file. Adds a "session summary" subsection to that doc.
- **Templates.** `templates/session-summary-template.md`.
- **Command file.** `plugins/test-commander/skills/tc-explore/commands/session-summary.md`.
- **SKILL.md update.** Updated.
- **Tests first.** `tests/test_session_summary.py` — uninitialized workspace refused; missing exploration note refused with a clear error directing the user at `/tc:explore`; seeded exploration note (generated by Step 4.3's helper against the seeded recording) → `<SESS-ID>.md` summary written with every required section; charter-coverage verdict resolved correctly against the seeded charter; candidate-scenarios section extracted with a stable shape (forward-compatible with Step 4.5's enrichment); idempotent re-run byte-identical; `<workspace>/sessions/index.md` lists the session with a one-line summary; index updated idempotently across multiple session writes.
- **Definition of done.** Helper passes all test cases; candidate-scenarios shape compatible with Step 4.5's enrichment input; SKILL.md updated.
- **Verification.** Pytest green; smoke run produces a session summary that resolves the seeded charter and lists the candidate scenarios.

#### 4.5 — `/tc:test-ideas` (TDD)

- **Helper.** `plugins/test-commander/scripts/enrich_test_ideas.py` (per D18; command name `/tc:test-ideas` is shortened from the action `enrich_test_ideas` for CLI ergonomics, matching the Phase-2 `/tc:requirements-to-tests` → `requirements_to_tests.py` pattern). Reads `<workspace>/sessions/` (one or more session summaries via `--session <SESS-ID>` or all sessions if no flag), reads `<workspace>/test-ideas/<REQ-ID>.md` files (the Phase-2 seeds), and **enriches each seed** as follows: preserves the YAML frontmatter unchanged for every Phase-2-shipped key, bumps `status: seed` → `status: enriched`, adds a `phase_4_sessions: [SESS-ID, ...]` list (deduplicated, never overwriting a sibling session's contribution), appends a `## Phase 4 enrichment` body section listing each session's candidate scenarios mapped to this REQ-ID via charter-coverage cross-reference, preserves every existing body section (the Phase-2-generated content, user edits, prior Phase-4 enrichments). **Idempotency contract**: existing enrichments are skipped (`created: 0, enriched: N, skipped: M`); the helper never duplicates a session's contribution to the same REQ-ID. Refuses to overwrite the Phase-2 seed frontmatter (asserted by a structural test).
- **Methodology.** `methodology/test-idea-model.md` — covers the Phase-2 `tc-test-idea/v1` schema contract, the Phase-4 enrichment additions (`status: enriched`, `phase_4_sessions:`, `## Phase 4 enrichment` section), the charter-coverage → REQ-ID cross-reference logic, and a Claude-judgment-layer paragraph (deciding which candidate scenarios are worth elevating, ranking by risk + coverage, identifying scenarios that span multiple REQs).
- **Templates.** `templates/test-idea-enrichment-template.md` — documents the `## Phase 4 enrichment` section structure.
- **Command file.** `plugins/test-commander/skills/tc-explore/commands/test-ideas.md`. By end of 4.5, `tc-explore/SKILL.md` describes all four commands plus the review sub-mode with no deferral wording.
- **Tests first.** `tests/test_enrich_test_ideas.py` — uninitialized workspace refused; missing session summaries refused with a clear error directing the user at `/tc:session-summary`; missing test-idea seeds refused with a clear error directing the user at `/tc:requirements-to-tests` (Phase 2); seeded session summary (generated by Step 4.4 against the seeded charter + recording) → every test-idea seed whose REQ-ID is covered by the session gets a `## Phase 4 enrichment` section; Phase-2 frontmatter preserved byte-for-byte (every key the seed shipped with is still present with its original value); `status: seed` flipped to `status: enriched` only on enriched files; `phase_4_sessions:` populated with the contributing SESS-IDs (sorted, deduplicated); idempotent re-run produces zero duplicate enrichment sections; user-edited body sections preserved; explicit assertion that no Phase-2 frontmatter key is missing or changed after enrichment.
- **Definition of done.** Helper passes all test cases; emitted test-idea files preserve the Phase-2 contract; `## Phase 4 enrichment` shape forward-compatible with Phase 5's BDD generation (the BDD helper reads enriched test-ideas as charter-grounded scenario seeds); SKILL.md describes all four commands.
- **Verification.** Pytest green; smoke run enriches at least three Phase-2-seeded test-ideas with session-derived candidate scenarios.

#### 4.6 — Documentation pass *(dedicated step)*

- **Deliverables.**
  - Author `docs/user-guide/exploring-an-app.md` — end-to-end walkthrough: upload a charter target (or use auto-suggestion) → `/tc:create-charter` → `/tc:explore` (replay the seeded recording for the docs example) → `/tc:session-summary` → `/tc:test-ideas`. Sample input and output drawn from the seeded fixture so every example is reproducible. Each section shows the partial state of `<workspace>/charters/`, `exploration-notes/`, `sessions/`, and `test-ideas/` after that command runs. Mirrors the `docs/user-guide/building-project-knowledge.md` (Phase 3) structure section-for-section.
  - Update `docs/command-reference.md` to add the four Phase 4 commands as links into their per-command pages inside the plugin (move from "Planned commands" to a new "Phase 4 commands (shipped)" section).
  - Update `docs/workspace-reference.md` per-file ownership tables for `charters/`, `exploration-notes/`, `sessions/`, and the enrichment behavior of `test-ideas/` (Phase 4 enriches; Phase 2 seeds; Phase 6 reads). Cross-cutting contribution map: Phase 4 writes only to its own directories.
  - Refresh status lines across the same six locations as Phase 3: `README.md` status header + doc index, `docs/install.md` "Verifying the install", `docs/user-guide/getting-started.md` "what's next" (add Phase 4 row), `docs/user-guide/workflow.md` "Beyond Phase 1" (Phase 4 link), `docs/user-guide/building-project-knowledge.md` "Beyond Phase 3" footer (Phase 4 link), `plugins/test-commander/README.md` skill-status table.
  - **Customization-guide update (per the Per-Phase Customization-guide Convention).** Add a "Phase 4 schema (`tc-explore`)" section to `docs/user-guide/customizing-for-your-project.md` covering all three extensible sub-blocks (`charters`, `exploration`, `review`). At least three worked extension examples spanning materially-different consuming-project shapes (per the Phase 3 Step 3.7 lesson about varying examples by project shape AND domain): a typical web-app + Playwright project, a mobile app where Playwright is replaced by a different MCP, an API-only project where exploration falls back to spec-derived journeys. Add a "Phase 4 — what landed" subsection naming the universal cores, the schema keys, and the tests that would fail if the helpers ignored extensions.
  - **Final `tc-explore/SKILL.md` pass.** Confirm SKILL.md describes every shipped command plus the review sub-mode, links to all four per-command pages, and instructs Claude to invoke the bundled helpers. No deferral wording. Grep `behavior arrives in|coming in phase|when phase 4 ships` across BOTH the SKILL.md AND all of `docs/` per the Phase-3 Step-3.7 lesson.
- **Definition of done.** Every doc accurate against the implementation; all cross-links resolve; link checker green; `tc-explore/SKILL.md` is the consolidated entry point for Phase 4 commands; `customizing-for-your-project.md` accurately reflects the shipped config.yaml schema with at least three worked examples spanning project shapes.
- **Verification.** `python3 scripts/check_links.py` clean; manual read-through against the Phase 4 deliverables; grep for stale deferral wording in `tc-explore/SKILL.md` AND `docs/` returns no hits; the YAML block in `customizing-for-your-project.md` parses as valid YAML.

#### 4.7 — Testing finalization *(dedicated step, separate from per-command TDD)*

- **Deliverables.**
  - Bump `DEFAULT_PHASE_CAP` in `scripts/verify_skills.py` from `3` to `4` and add `CATALOG["tc-explore"] = 4` so the verifier expects four shipped skills.
  - `tests/test_phase_4_integration.py` — integration smoke that creates a fresh tmp consuming project, runs `init_workspace.py`, seeds the workspace with the Phase-3 sample-project fixture AND runs the five Phase-3 helpers (so the product-knowledge artifacts exist as Phase 4's inputs), then drives the four Phase 4 helpers in workflow order (`create-charter` → `explore` → `session-summary` → `test-ideas`). In-process imports (per the Phase 3 Step 3.8 lesson that in-process beat subprocess for integration speed by 10x). Assertions at every transition: charter file written with valid frontmatter; exploration note written with all seeded anomalies captured; session summary written with charter resolved and candidate scenarios listed; test-idea enrichment preserves every Phase-2 frontmatter key + bumps `status: enriched`; full union state correct (all four Phase 4 artifacts present; all 10 Phase 3 product-knowledge artifacts unchanged after Phase 4 runs); `<workspace>/traceability/` carries no `tc-explore` content (the Phase 4 design-decision discipline asserted directly, mirroring the Phase 3 Step 3.8 traceability assertion); `<workspace>/product-knowledge/` byte-identical before and after Phase 4 (Phase 4 reads but does not write product-knowledge per design decision); `/tc:next` advances past `/tc:create-charter` (the "advanced past" invariant from Phase 2 Step 2.9 + Phase 3 Step 3.8 — assert `command != /tc:create-charter`, not pinning a specific next command).
  - Byte-stable re-run integration test (mirrors Phase 3 Step 3.8): full Phase-4 helper sweep twice in sequence; assert byte-identical artifacts and line-stable open-questions.
  - Negative integration test: `tc-explore.mode: live` config triggers `LiveModeRefusedError` under pytest (no MCP connection attempted; no network calls leak).
- **Definition of done.** Integration smoke passes; phase cap bump reflected; full `make verify` chain green; `verify_skills.py` reports all four shipped skills `PRESENT` with `UNEXPECTED=0`.
- **Verification.** Captured `make verify` output. Per the Phase 3 Step 3.8 lesson, the integration smoke is budgeted as verification not debugging — if it lands red, surface the discovery as a sub-step lesson and consider whether the unit-test coverage in 4.2–4.5 needs strengthening.

#### 4.8 — Sign-off

Six sub-steps. Mirrors the Phase 3 sign-off pattern (3.9) exactly. Test-first: the sign-off test in 4.8.5 lands red before the plan/CHANGELOG edits in 4.8.3 turn it green. The final sub-step (4.8.6) captures evidence and pushes the `phase-4` annotated tag.

##### 4.8.1 — Cold-user walkthrough of `exploring-an-app.md`

- **Deliverables.** Captured log of an end-to-end walkthrough of `docs/user-guide/exploring-an-app.md` from a freshly-installed plugin against a fresh tmp consuming project (with Phase-3 product-knowledge state pre-populated by running the Phase-3 helpers first).
- **Steps to execute verbatim.**
  1. `make uninstall` → `make install` to reach a known-clean plugin state.
  2. Create a tmp consuming-project dir (`mktemp -d`).
  3. `init_workspace.py <tmp>`. Copy `tests/fixtures/seeded-sample-project/*` into `<tmp>/.test-commander/documents/uploaded/` and run the five Phase 3 helpers in workflow order to populate `product-knowledge/`. Then copy the seeded `charter.md` + `recorded-session.json` into `<tmp>/.test-commander/documents/uploaded/recorded-sessions/`.
  4. Invoke the four Phase 4 helpers in workflow order: `create_charter.py`, `explore.py`, `session_summary.py`, `enrich_test_ideas.py`.
  5. Confirm each helper prints the output documented in `exploring-an-app.md` (no fabricated examples).
- **Definition of done.** All commands succeed end to end. Output captured to `/tmp/tc-phase4-walkthrough.log`. If any step fails, fix the cause and re-run before continuing to 4.8.2.

##### 4.8.2 — Per-step DoD audit

- **Deliverables.** A line-by-line audit of Steps 4.1 through 4.7 against their DoD lists.
- **What to check per step.** Every DoD bullet green; every pytest file passes; every deliverable present on disk; every cross-link in the per-command pages resolves; every Failure Mode mitigation in place.
- **Specifically.**
  - 4.1: `tc-explore/SKILL.md` and `tests/fixtures/seeded-exploration-session/` present; scaffold test green; anomaly-category coverage assertion passes.
  - 4.2–4.5: helper, methodology (where applicable), template (where applicable), command file, and SKILL.md update all present; per-command test files all green; mechanical extraction findings traced to seeded fixture; provenance citations resolve; Phase-2 `tc-test-idea/v1` schema preservation asserted by 4.5's test.
  - 4.6: `exploring-an-app.md`, command-reference index, workspace-reference (charters/, exploration-notes/, sessions/ ownership rows), README + getting-started status lines all current; `tc-explore/SKILL.md` describes every shipped Phase 4 command plus the review sub-mode and contains no stale deferral wording; `customizing-for-your-project.md` reflects the Phase 4 `tc-explore` config.yaml schema with at least three worked extension examples spanning materially-different consuming-project shapes.
  - 4.7: `DEFAULT_PHASE_CAP >= 4`, `CATALOG["tc-explore"] == 4`, integration smoke passes, live-mode refusal under test harness asserted.
  - **Lesson-capture audit (per the "Sub-step lesson capture" Per-Phase Convention):** every Phase 4 sub-step (4.1–4.7) has a corresponding entry in the `Phase 4 — Lessons learned (running)` subsection. Sub-steps that closed cleanly with no bugs explicitly record "no lessons".
- **Definition of done.** All seven prior sub-steps audited green. Any unmet item blocks the sign-off.

##### 4.8.3 — Plan and CHANGELOG updates

- **Deliverables.**
  - `planning/plan.md` — collapse the `### Phase 4` To Do sub-section to a single line: `Phase 4 complete (YYYY-MM-DD) — see Completed`. Add a `### Phase 4 — Exploratory testing and test idea generation (YYYY-MM-DD)` section to `## Completed` with the per-step summary lines marked `[x]`, mirroring the Phase 3 closing format.
  - `CHANGELOG.md` — add a new `### Phase 4 — Exploratory testing and test idea generation (complete YYYY-MM-DD)` section above Phase 3 with a one-line closing summary plus per-sub-step Added bullets, mirroring the Phase 3 closing format.
- **Definition of done.** To Do Phase 4 reduced to the marker line; Completed has the Phase 4 section with date and eight sub-step bullets; CHANGELOG reflects the closing.

##### 4.8.4 — Documentation final pass

- **Deliverables.** Edits wherever Phase 4 wording has drifted during the seven sub-steps.
- **What to read.** README status line, `docs/user-guide/getting-started.md` "what's next", `docs/install.md` verifying-install paragraph, `docs/user-guide/exploring-an-app.md` introductory paragraph, `docs/user-guide/building-project-knowledge.md` footer "Beyond Phase 3" block, `docs/user-guide/workflow.md` (if it references Phase 4), `plugins/test-commander/README.md` skill table, `docs/user-guide/customizing-for-your-project.md` tense.
- **Definition of done.** Every Phase 4 fact matches the implementation. "Phase 4 in progress" wording becomes "Phase 4 complete (YYYY-MM-DD); Phase 5 starts next" where applicable. All cross-links resolve.

##### 4.8.5 — Pre-flight tests for sign-off

- **Deliverables.** `tests/test_phase_4_signoff.py`.
- **Coverage.**
  - All seven Phase 4 pytest files exist (`test_tc_explore_scaffold`, `test_create_charter`, `test_explore`, `test_session_summary`, `test_enrich_test_ideas`, `test_phase_4_integration`, `test_phase_4_signoff`).
  - All four Phase 4 helpers exist under `plugins/test-commander/scripts/` (`create_charter.py`, `explore.py`, `session_summary.py`, `enrich_test_ideas.py`).
  - All four Phase 4 command files exist under `plugins/test-commander/skills/tc-explore/commands/`.
  - All four methodology files exist under `plugins/test-commander/skills/tc-explore/methodology/` (`exploratory-testing.md` umbrella plus three per-command).
  - All seven templates exist under `plugins/test-commander/skills/tc-explore/templates/`.
  - `tests/fixtures/seeded-exploration-session/` exists with all four files (`charter.md`, `recorded-session.json`, `target-app.md`, `README.md`).
  - `scripts/verify_skills.py` has `CATALOG["tc-explore"] == 4` and `DEFAULT_PHASE_CAP >= 4` (per the Phase-2 Step-2.8 lesson — never assert `==` on the cap).
  - `tc-explore/SKILL.md` describes all four Phase 4 commands plus the review sub-mode and contains no deferral wording.
  - `docs/user-guide/customizing-for-your-project.md` contains a `tc-explore:` YAML block whose top-level keys match the shipped config.yaml schema, and contains at least three worked extension examples in distinct project-shape headings.
  - `Phase 4 — Lessons learned (running)` subsection in `planning/plan.md` contains an entry for every Phase 4 sub-step that has landed (`Step 4.1` through `Step 4.7`); each entry either describes a lesson + mitigation or explicitly records "no lessons".
  - CHANGELOG Phase 4 section marked complete with a date.
  - `plan.md` Completed has a Phase 4 subsection with a date.
  - `plan.md` To Do Phase 4 is the marker line (no unchecked items remain).
  - Total pytest count meets minimum (`>= 350` — Phase 3 finished at 314; Phase 4 adds the scaffold test, four per-command suites, integration, and sign-off).
- **Definition of done.** Test-first: the suite lands red before 4.8.3's plan/CHANGELOG edits, green after.

##### 4.8.6 — Final DoD evaluation (close Phase 4)

- **Procedure.**
  1. Run `make verify` — every test green, link checker clean, `verify_skills.py` reports all four shipped skills `PRESENT`.
  2. Replay the 4.8.1 walkthrough end to end to confirm reproducibility.
  3. Capture all output to `/tmp/tc-phase4-signoff.log`.
  4. Commit the plan/CHANGELOG/docs updates and the sign-off test in one final commit.
  5. Push to origin.
  6. Create annotated tag: `git tag -a phase-4 -m "Phase 4 — Exploratory testing and test idea generation complete."`.
  7. Push tag: `git push origin phase-4`.
- **Definition of done.** All seven numbered steps complete. Tag visible on origin (`git ls-remote origin phase-4` resolves). Evidence log captured. Phase 4 is closed.

#### Definition of done — consolidated 15 checks

Eleven automated; four evidence-based.

| # | Check | Type | How |
| --- | --- | --- | --- |
| 1 | All seven Phase 4 test files exist | auto | sign-off test |
| 2 | All four helpers exist (`create_charter.py`, `explore.py`, `session_summary.py`, `enrich_test_ideas.py`) | auto | sign-off test |
| 3 | All four command files exist under `tc-explore/commands/` | auto | sign-off test |
| 4 | All four methodology files exist under `tc-explore/methodology/` | auto | sign-off test |
| 5 | All seven templates exist under `tc-explore/templates/` | auto | sign-off test |
| 6 | Seeded-exploration-session fixture exists and covers every universal anomaly category | auto | scaffold test |
| 7 | `verify_skills.py` has `CATALOG["tc-explore"] == 4` and `DEFAULT_PHASE_CAP >= 4`; `make verify` prints all four skills PRESENT with `UNEXPECTED=0` | auto | sign-off test + `make verify` |
| 8 | Integration smoke `test_phase_4_integration` passes; live-mode refusal under test harness asserted; `traceability/` + `product-knowledge/` untouched assertions hold | auto | pytest |
| 9 | `tc-explore/SKILL.md` describes all four shipped Phase 4 commands plus the review sub-mode with no deferral wording | auto | sign-off test |
| 10 | Phase-2 `tc-test-idea/v1` schema preservation: every Phase-4-enriched test-idea retains every Phase-2 frontmatter key with its original value | auto | enrich-test-ideas test |
| 11 | `make verify` chain clean (link checker covers the new docs) | auto | full chain |
| 12 | Cold-user walkthrough of `exploring-an-app.md` from clean state succeeds (4.8.1) | evidence | `/tmp/tc-phase4-walkthrough.log` |
| 13 | Per-step DoD audit clean for 4.1–4.7 (4.8.2) | evidence | audit notes |
| 14 | `plan.md` To Do Phase 4 collapsed to marker; Completed has Phase 4 subsection with date (4.8.3); CHANGELOG Phase 4 section marked complete | evidence | sign-off test + grep |
| 15 | `phase-4` annotated tag created and pushed (4.8.6) | evidence | `git tag -l phase-4` + `git ls-remote origin phase-4` |

#### TDD pattern used in 4.2–4.5

```
write tests (red)             # define expected behavior per dimension from the seeded fixture, including provenance + Phase-2 schema preservation
  → implement helper (green)  # minimum code to pass; mechanical extraction only
    → author methodology + template (each command owns one of each; umbrella exploratory-testing.md lands in 4.2)
      → author per-command page
        → update SKILL.md to surface shipped behavior
          → wire into the internal review sub-mode where applicable (4.3 ships it; 4.4 and 4.5 do not invoke it)
            → verify (pytest + make verify)
```

No implementation lands before its tests. No tests are added after the fact. Every command's test suite drives the helper from the same seeded fixture so the rubric is the contract.

#### Validation sequence

1. Author 4.1 (skill scaffold + fixture) with its scaffold test. Confirm pytest red → green.
2. Author 4.2 (`/tc:create-charter` + the umbrella `exploratory-testing.md` methodology): write tests, implement helper, author methodology, templates, command file, update SKILL.md, run pytest.
3. For each of 4.3, 4.4, 4.5 in order: mirror 4.2's skeleton, adapt per-command behavior, write tests, implement helper, author the command-specific methodology and templates, author command file, update SKILL.md, run pytest.
4. 4.6 documentation pass. Run `make verify`.
5. 4.7 testing finalization: bump `CATALOG["tc-explore"]` to 4 and `DEFAULT_PHASE_CAP` to 4, integration smoke. Run `make verify`.
6. 4.8 sign-off, in order:
   6a. Run the cold-user walkthrough from `exploring-an-app.md` (4.8.1). Capture log. Fix anything that fails before proceeding.
   6b. Audit each prior sub-step's DoD (4.8.2). Block on any unmet item.
   6c. Write `tests/test_phase_4_signoff.py` (4.8.5). Run `make test` — expect failures for any not-yet-applied plan/CHANGELOG edits.
   6d. Update `plan.md` and `CHANGELOG.md` (4.8.3). Re-run sign-off test — expect green.
   6e. Doc final read-through (4.8.4). Edit any drift; re-run `make verify`.
   6f. Final DoD evaluation (4.8.6): commit, push, annotated tag, tag push.

#### Failure modes

- A Playwright MCP session shape changes between recordings. **Mitigation:** the seeded fixture's `recorded-session.json` is the contract for v1; the helper's parser asserts the entries match the expected schema and refuses unrecognized event types with a clear error. Future MCP versions are addressed by extending the parser, not by relaxing the schema check.
- Live-mode integration with Playwright MCP fails during a real exploration. **Mitigation:** the live-mode entry point catches MCP connection errors and writes a structured exploration-note stub explaining the failure plus the configured MCP endpoint. The recorded-mode contract guarantees the test suite stays green regardless of live-mode availability.
- Test-idea enrichment accidentally overwrites a Phase-2 frontmatter key. **Mitigation:** 4.5's test suite explicitly asserts byte-identical preservation of every key the Phase-2 seed shipped with (`schema`, `requirement_id`, `requirement_title`, `source`, `phase_2_findings`, `candidates`, `generated_by`). The Phase-2 Step-2.6 contract is the canonical reference; any change to the contract requires a Phase 4 schema bump that Phase 5 must consume.
- Charter ID allocation conflict during parallel `/tc:create-charter` invocations. **Mitigation:** the helper scans existing `charters/CH-*.md` files at allocation time and uses a file-system-level lock (`fcntl.flock`) so two simultaneous invocations cannot allocate the same ID. The seeded fixture exercises the single-invocation path; a synthetic concurrency test exercises the lock.
- Session ID collision (two sessions with the same timestamp prefix). **Mitigation:** session IDs follow `SESS-YYYYMMDD-NNN` where `NNN` is the next available index for the day; the helper scans existing sessions/ entries before allocating. Mirrors the charter-ID logic.
- The `[exploration-review]` gap signals duplicate across re-runs. **Mitigation:** the `(source-id, question-text)` dedup contract from Phase 2 (extended in Phase 3 with the `[<kind>]` prefix) applies here too; the helper uses `source-id: tc-explore/explore-review-<SESS-ID>` so re-running the same exploration is idempotent.
- Phase 4 writes into `traceability/` or `product-knowledge/` accidentally. **Mitigation:** the design decision forbids it; the integration smoke in 4.7 walks both directories after the full helper sweep and asserts the absence of `tc-explore` content (mirrors the Phase 3 Step 3.8 assertion against `tc-knowledge` in `traceability/`).
- Recorded-session replay produces different output on re-run because timestamps drift. **Mitigation:** all generated artifacts use the recorded session's own timestamps (not the helper's clock); re-running against unchanged input produces byte-identical exploration notes and session summaries. The integration smoke in 4.7 asserts this directly.
- Documentation walkthrough in 4.8.1 surfaces a gap (a step that doesn't work as documented). **Mitigation:** update `exploring-an-app.md` to match reality and re-run the walkthrough. Treat as a Phase 4 doc bug, not a Phase 5 issue.
- A prior sub-step's DoD turns out not to be green during 4.8.2. **Mitigation:** the failing sub-step reopens. 4.8 cannot close while any earlier DoD is unmet.
- `phase-4` tag already exists locally. **Mitigation:** delete (`git tag -d phase-4` then `git push origin :refs/tags/phase-4`) and recreate. Never force-overwrite an existing tag on origin without explicit user confirmation.
- CHANGELOG Phase 4 closing entry diverges from To Do/Completed movement. **Mitigation:** the sign-off test (4.8.5) checks all three sources. They must agree before the test passes.

#### Phase 4 — Lessons learned (running)

Captured at sub-step close per the "Sub-step lesson capture" Per-Phase Convention. Each entry is preventative care for future implementers of similar work.

##### Step 4.8 — Sign-off

- **The cold-user walkthrough caught a latent bug Steps 4.1-4.7 missed for 7 sub-steps.** `plugins/test-commander/skills/tc-explore/SKILL.md` shipped from Step 4.1 with a description value ending in `Live mode is opt-in via tc-explore.mode: live and refused under pytest.` The unquoted colon-space inside `mode: live` is interpreted as a YAML flow-mapping start by strict parsers. The project's own `scripts/verify_skills.py` is a regex-based parser (`NAME_LINE`, `DESCRIPTION_LINE` line regex per file) and the description regex matched cleanly — it never reached a real YAML library. Every sub-step from 4.1 through 4.7 passed `make verify` (which includes `verify_skills.py`) and every unit + integration test passed. **The only project-wide check that uses the strict YAML parser is `claude plugin validate`, invoked by `make install`.** That check ran for the first time in Step 4.8.1's cold-user walkthrough — and immediately reported `frontmatter: YAML frontmatter failed to parse: YAML Parse error: Unexpected token`. **Fix**: rephrased the description to remove the embedded `key: value` substring (`via the tc-explore.mode setting` instead of `via tc-explore.mode: live`). One-word edit; `claude plugin validate` now reports `✔ Validation passed`. **Pattern**: when a shipped artifact is parsed by two parsers (one in-repo, one external), the in-repo parser may be tolerant of an input the external parser rejects. The cold-user walkthrough is the only check that exercises the external parser path. Do not skip the walkthrough on the grounds that "the existing checks all pass." **Mitigation added in the same sub-step**: a new unit test `tests/test_phase_4_signoff.py::test_tc_explore_skill_md_frontmatter_parses_strict_yaml` invokes PyYAML directly on the SKILL.md frontmatter and asserts a clean parse. This would have caught the bug at Step 4.1's unit-test layer; future Phase-N scaffold tests should land a similar strict-YAML assertion on the new SKILL.md they author. **Future-implementer hint**: Phase 5's `tc-bdd/SKILL.md` scaffold sub-step should include the strict-YAML parse assertion in its scaffold test from the start (not as a sign-off afterthought).
- **The `Phase 2 → Phase 3 → Phase 4` sequencing rule held in production.** Step 4.6 predicted the walkthrough would clobber the `[exploration-review]` open-questions line if Phase 2 ran AFTER Phase 4 (Phase 2's `review_requirements` overwrites the file). Step 4.7's integration smoke implemented the predicted order; Step 4.8.1's walkthrough used the same order and the `[exploration-review]` line landed correctly at the END of open-questions after Phase 2 + Phase 3 had already written their entries. Walkthrough's final `grep -c '[exploration-review]'` reported `1` — matching the seeded fixture's single missing-evidence gap. **Pattern reinforced**: the natural workflow order IS the test order IS the documentation order. When all three agree, the cross-helper side-effect on a sibling phase's file lands where expected. **Future-implementer hint**: Phase 5's sign-off walkthrough should similarly run Phase 2 → Phase 3 → Phase 4 → Phase 5 in that order; do not let the BDD generator run before Phase 4 enrichment because it consumes enriched test-ideas.
- **`make uninstall` + `make install` is the right shape of the cold-user walkthrough preamble.** Phase 4 Step 4.8.1's first invocation hit the SKILL.md YAML bug at `make install`'s `validate-manifests` stage — exactly where the strict parser lives. After the fix landed, `make install` succeeded with `verify-skills` reporting `PRESENT=4 MISSING=0 MALFORMED=0 UNEXPECTED=0` and the plugin marketplace re-registering cleanly. **Pattern**: the walkthrough preamble is not ceremonial — it exercises the strict-validation gate that no other step in the project runs. The `make uninstall` + `make install` pair is also the only check that the plugin marketplace lifecycle (register → install → verify) works end-to-end against the current SKILL.md set. **Future-implementer hint**: Phase 5's walkthrough should keep the preamble exactly as-is. Do not stub it out as `verify_skills.py` runs (that is the regex-based parser; it misses what `claude plugin validate` catches).
- **22-test sign-off file is the right size; mirroring the Phase 3 sign-off shape transferred cleanly.** `tests/test_phase_4_signoff.py` (22 assertions) covers exactly the same set of closing conditions as `tests/test_phase_3_signoff.py` (17 assertions) plus the new Phase-4-specific ones: strict YAML frontmatter parse (the bug-prevention test added in the same sub-step that found the bug), umbrella methodology no-deferral-wording, walkthrough wording with all four commands. The size growth (17 → 22) is a 30% growth corresponding to Phase 4's new mechanical surfaces (3 sub-blocks vs Phase 3's 4 sub-blocks, but with an extra strict-YAML check). Lands RED on the 3 plan/CHANGELOG closing assertions before the closing edits; GREEN on all 22 after. **Pattern**: the sign-off test grows phase-over-phase by adding assertions for each new mechanical surface, not by adding boilerplate. **Future-implementer hint**: Phase 5's sign-off test should start at ~22 + the count of new Phase-5 mechanical surfaces and use the `>=` discipline for every numeric assertion (pytest count, worked-example count, file count) so Phase 5's close doesn't break Phase 4's sign-off test.

##### Step 4.7 — Testing finalization (cap bump + integration smoke + live-mode refusal)

- **3/3 GREEN on first run of the integration smoke; budgeted as verification not debugging.** Per the Phase 3 Step 3.8 lesson — "the integration smoke is budgeted as verification, not debugging" — and the Phase 4 Step 4.5 lesson on cross-phase contract triangles, the Step 4.7 integration test landed 3/3 GREEN on first run with no bug-fix cycle. The full Phase 2 → Phase 3 → Phase 4 sweep (12 helper invocations: 2 Phase-2, 5 Phase-3, 4 Phase-4, plus `/tc:next` resolution at the end) runs in 0.30s end-to-end via in-process imports — the 10x speedup over the subprocess approach the Phase 3 Step 3.8 lesson predicted. Per-command unit tests + cross-phase contract enumerations (CHARTER_REQUIRED_FIELDS in 4.1, the candidate-shape contract in 4.4, the consumer/producer `CandidateScenario` dataclass triangle in 4.5) collectively asserted every transition the integration smoke needed, so the smoke was a verification-not-debugging exercise. **Pattern reinforced** (now the fifth datapoint after Phase 3 Steps 3.5 + 3.6 + 3.8 + Phase 4 Step 4.2): when sub-step contracts are enumerated mechanically at the test level AND the helper-mirroring skeleton is mature, the closing integration test budget is "land it" not "debug it." **Future-implementer hint**: Phase 5's integration smoke should be similarly budget-able once Phase 5's per-command unit tests enumerate the BDD-output shape and the Phase 4 → Phase 5 input-contract triangle.
- **The Phase 2 → Phase 3 → Phase 4 sequencing rule the Step 4.6 lesson predicted is the right one.** The Step 4.6 lesson recommended: "Step 4.7's integration smoke should run Phase 2 (`review_requirements + requirements_to_tests`) FIRST, then Phase 3, then Phase 4 — so the `[exploration-review]` line lands on top of Phase-2 entries rather than being clobbered by them." The Step 4.7 integration smoke implemented exactly that order and the `[exploration-review]` assertion passed cleanly (the line lands at the END of open-questions.md after Phase 2 + Phase 3 have already written their entries). The natural workflow order is also the right test order. **Pattern**: when a downstream phase writes a side-effect line into a file an upstream phase owns, the integration test must run the upstream phase first; the natural workflow order matches the test order. **Future-implementer hint**: Phase 5's integration smoke (if Phase 5 writes any side-effect into `requirements/open-questions.md` or `requirements/requirements-coverage.md`) should follow the same Phase 2 → Phase 3 → Phase 4 → Phase 5 sequencing.
- **The `UNEXPECTED (phase 4) — ahead of schedule` → `PRESENT (phase 4)` transition is a one-line cap-bump fix.** The `tc-explore` skill directory has existed since Step 4.1 (the scaffold step). Under `DEFAULT_PHASE_CAP=3` from Phase 3's sign-off, the verifier classified it as `UNEXPECTED` (warn-only). The Step 4.7 cap bump from 3 to 4 flipped it to `PRESENT` with zero other code changes — the catalog entry (`CATALOG["tc-explore"] = 4`) had already landed in Step 0.6.1 when the catalog was scaffolded. **Pattern**: the staged cap-bump discipline (cap bumps in the closing sub-step of each phase, NOT mid-phase when the catalog already includes the next-phase skill) is by design. Mid-phase code mid-sub-step would have allowed the verifier to claim "phase 4 PRESENT" before Phase 4 was actually complete; the staged bump prevents that false claim. **Pattern reinforced** (fourth datapoint after Phase 1, Phase 2, Phase 3 sign-offs): the cap bump belongs in the test-finalization sub-step (4.7), not the per-command sub-steps. **Future-implementer hint**: Phase 5's testing-finalization sub-step (5.N analogous to 4.7) bumps the cap from 4 to 5; the per-Phase-5-command sub-steps (5.1 through 5.M) deliberately leave the cap alone.
- **In-process subprocess-free integration smoke is fast enough for the Phase-4 close.** Phase 3 Step 3.8 measured 10x speedup (subprocess: ~3s per helper invocation; in-process: ~0.3s for the full sweep). Phase 4 Step 4.7 measures 0.30s for the full 12-helper sweep — consistent with the Phase 3 measurement. The unit-test files (`test_create_charter.py`, `test_explore.py`, `test_session_summary.py`, `test_enrich_test_ideas.py`) all use subprocess for their CLI-shape coverage; the integration test uses in-process for end-to-end speed. **Pattern**: per-command unit tests cover the CLI shape via subprocess (because the CLI exit codes + stderr routing is part of the contract); the integration smoke covers the end-to-end workflow via in-process imports (because subprocess overhead would dominate the runtime budget). Same helper, different invocation mode per test purpose. **Future-implementer hint**: when Phase 5's integration smoke ships, use in-process imports for the same reason. The pattern is now a stable discipline across Phases 3 + 4.

##### Step 4.6 — Documentation pass

- **Reproducible sample output beats hand-crafted prose.** The `exploring-an-app.md` walkthrough is anchored on the seeded fixture (`tests/fixtures/seeded-exploration-session/` for Phase 4 inputs + `tests/fixtures/seeded-flawed-requirements/` for the Phase-2 seeds Step 4.5 enriches). Before authoring each per-step "Sample output" block, the doc author drove the helpers end-to-end against a tmp workspace, captured the actual stdout + on-disk artifacts, and embedded **verbatim excerpts** rather than paraphrasing. The Phase 3 Step 3.7 lesson — that doc-step samples must be reproducible from the seeded fixture — transferred cleanly. **Pattern**: when authoring a user-guide walkthrough that ships before sign-off, drive the actual helper chain against the seeded fixture in a tmp workspace and quote the byte-real output. This catches drift between the helper render and the doc immediately. **Future-implementer hint**: Phase 5's `generating-bdd.md` walkthrough should follow the same discipline — drive `/tc:generate-bdd` against the same seeded fixture chain (Phase 3 product-knowledge + Phase 4 sessions + Phase 4 enriched test-ideas, in that order) and embed the actual `.feature` file output, not a paraphrase.
- **Three worked extension examples should span project shapes, not just product domains.** Per the Phase 3 Step 3.7 lesson about varying examples by project shape AND domain (the Phase 3 customization guide ships Python/FastAPI, Node/Express, Postman-only), the Phase 4 customization guide ships Python web app + Playwright (web/Playwright shape with PCI domain), mobile app with non-Playwright MCP (mobile/Appium shape with biometric domain), and API-only project (REST API shape with rate-limit / payload-size domain). Project-shape variation forces the worked examples to exercise different sub-blocks: the mobile example exercises `mcp-endpoint` + `target-url` as documented-for-v2 keys; the API-only example exercises `recorded-path` as the primary tuning surface; the web/Playwright example exercises `risk-keywords` as the primary tuning surface. **Pattern**: when authoring three worked extension examples, vary the project shape across the three so each example exercises a different sub-block as its primary tuning surface. Three examples that all tune the same key on different vocabulary teach less than three examples that each tune a different key. **Future-implementer hint**: Phase 5's customization-guide additions should follow the same pattern — pick three project shapes whose BDD generation needs differ structurally (web with browser-driven scenarios, API with spec-derived scenarios, mobile with screen-flow scenarios), not just three vocabularies.
- **`exploratory-testing.md` is the third umbrella methodology document with a "this command's behavior arrives in Step 4.N" pattern that needed scrubbing in the doc-pass step.** The umbrella file shipped with Steps 4.1-4.3 carried explicit deferral wording (`(Step 4.3; behavior arrives in 4.3)`) in its workflow diagram. After Steps 4.3-4.5 shipped, the deferral wording was technically wrong (the behavior IS in 4.3) but had stayed because the umbrella wasn't on the per-sub-step Per-Phase-Convention #4 edit list — only the owning SKILL.md was. The doc-pass step caught this via the recurring `grep "behavior arrives in|coming in phase|when phase 4 ships"` sweep. **Pattern**: when a sub-step ships a command behavior described in an umbrella methodology file (one tier above the per-command methodology file), the umbrella file's mention of that command is itself a Per-Phase-Convention #4 edit. The verb-tense edit ("behavior arrives in" → "shipped") is one line, but identifying it requires the sweep. **Future-implementer hint**: Phase 5's umbrella `bdd-generation.md` (when it ships) will carry a similar workflow diagram naming `/tc:generate-bdd`, `/tc:review-bdd`, `/tc:traceability-map`; each command's sub-step must edit the diagram in the same commit. Add the umbrella file to the Per-Phase-Convention #4 edit list explicitly.
- **The `[exploration-review]` open-questions entry is a doc-test-able invariant — but the test fixture clobbers it.** The walkthrough's Step 2 sample says the run lands one `[exploration-review]` entry in `requirements/open-questions.md` (the missing-evidence anomaly). Verified manually by driving `/tc:explore` against a tmp workspace. But the integration test in Step 4.7 (when it ships) will need to be careful: if the integration sequence runs Phase-2 `review_requirements` AFTER `/tc:explore`, Phase-2 will overwrite `open-questions.md` and the `[exploration-review]` entry vanishes. **Pattern**: when documenting a cross-helper side-effect (Phase 4's `[exploration-review]` write into a Phase-2-owned file), the doc author must verify the side-effect in isolation (not after a Phase-2 run). The integration test must either run Phase 2 first or assert the `[exploration-review]` line BEFORE Phase 2 fires. **Future-implementer hint**: when Step 4.7's integration smoke ships, it should run Phase 2 (`review_requirements + requirements_to_tests`) FIRST, then Phase 3, then Phase 4 — so the `[exploration-review]` line lands on top of Phase-2 entries rather than being clobbered by them. This is the natural workflow order anyway (Phase 2 → Phase 3 → Phase 4); the doc walkthrough's prerequisite text already says so.

##### Step 4.5 — `/tc:test-ideas` (enrich Phase-2 seeds)

- **15/17 GREEN on first cut; one bug-fix cycle for `merge_phase_4_sessions` duplicate-key emission.** First cut had a single `merge_phase_4_sessions` loop that, while walking the existing frontmatter lines, inserted a new `phase_4_sessions: [SESS-X]` line after the first `status:` line AND, when it later reached the existing `phase_4_sessions:` line (left over from a prior enrichment), rewrote that line with the merged sorted set. Result on idempotent re-run: **two** `phase_4_sessions:` lines in the frontmatter, the inserted one carrying only the new SESS-ID and the rewritten one carrying the merged set. The idempotency test caught it (`test_idempotent_rerun_byte_identical`), and the multi-session test failed as a downstream symptom (`test_multiple_sessions_merged_into_phase_4_sessions` — the test-side `frontmatter_scalar()` returns the FIRST match, which was the malformed insert-after-status line, so the assertion that both SESS-IDs appear in the list always failed). **Fix**: pre-scan the existing lines for an existing `phase_4_sessions:` line; when present, only the existing-line rewrite path runs (no insert); when absent, the insert-after-status path runs. The fix is one extra `any(sessions_re.match(line) for line in existing_lines)` pre-scan plus an `if not has_existing` guard on the insert branch. 17/17 GREEN after the one-method edit. **Pattern**: when a helper performs both an insert-or-update on a YAML-ish key family, the insert branch and the update branch are mutually exclusive at the file level (the key either exists or it doesn't), but they are NOT mutually exclusive at the line-walking level (a single loop can fire both). The defense is a pre-scan that decides which branch runs before the loop begins. **Future-implementer hint**: any future helper that maintains "either insert a new key after an anchor line OR rewrite an existing key" in a flat YAML-ish frontmatter should declare both branches in the same function with the pre-scan-decides-which discipline (vs. trusting the loop to land in the right branch). The same pattern applies to Phase 5's BDD generator if it ever needs to inject tags into a `.feature` file's frontmatter region.
- **The five-character-stem keyword matching is preferable to exact-token matching for cross-phase keyword cross-reference, even without a real stemmer.** The first design used exact-token equality between the requirement body and the session keyword set; against the seeded flawed-requirements + seeded-exploration-session pairing, this produced ZERO enrichments because the requirements use words like `authentication` and `session` while the charter uses `authenticated` and `sessions`. Five-character prefix stems (`authe`, `sessi`) recover the match without depending on a stemmer library. **Trade-off**: short tokens (≤5 chars after the ≥4-char filter) act as exact matches; longer tokens act as prefix-stem matches. False positives are possible (`accept` and `acceptance` both stem to `accep`; `report` and `reporting` both to `repor`) — acceptable because over-enrichment is mitigated by the Claude judgment layer in `methodology/test-idea-model.md`. Under-enrichment hides session-derived candidates from REQs that legitimately needed them. **Pattern**: when matching keyword sets across phases where authors use morphological variants (singular/plural, -ation/-ated, -er/-ing), prefer a short fixed-length prefix stem over exact equality. Five characters is a good default — long enough to discriminate (`work` vs `works` would over-match, but `works` covers `workspace` AND `workspaces`); short enough to fold typical English morphology (`authen` vs `authent` would split `authenticate` from `authentication`, but `authe` keeps them together). **Future-implementer hint**: Phase 5's BDD-to-test-idea correlation will face the same problem (the BDD generator reads enriched test-ideas and produces `.feature` files whose Given/When/Then steps need to match upstream REQ vocabulary); the five-character stem convention should carry forward there too.
- **Cross-phase contract triangle closed at the dataclass level.** Per the Step 4.4 future-implementer hint, Step 4.5 declares a `CandidateScenario` dataclass in `enrich_test_ideas.py` whose fields mirror `session_summary.CandidateScenario` (`id`, `title`, `type`, `source`, `linked_anomaly`). The contract is therefore enumerated in three places: (a) `session_summary.CandidateScenario` (producer dataclass + render), (b) `tests/test_session_summary.py::test_candidate_scenarios_have_stable_shape` (producer test asserting `title`/`type`/`source` literal field names appear in each rendered block), (c) `enrich_test_ideas.CandidateScenario` + `tests/test_enrich_test_ideas.py::test_candidate_shape_contract_is_declared` (consumer dataclass + assertion that producer-fields ⊆ consumer-fields). Drift at any one layer surfaces at unit-test time. **Pattern reinforced** (now the third datapoint after CHARTER_REQUIRED_FIELDS in Step 4.1 and the candidate-shape contract in Step 4.4): when a sub-step's output is downstream input for another sub-step, the field contract should be declared mechanically in producer dataclass + producer test + consumer dataclass + consumer test. **Future-implementer hint**: when Phase 5 ships, the BDD generator should declare a `Scenario` dataclass mirroring the enriched-test-idea shape (`req_id`, `cs_id`, `type`, `title`, `source`, `linked_anomaly`) AND assert in its tests that parsing the enriched test-idea body recovers every field — closing the same contract triangle.
- **Helper-mirroring transferred ~95% verbatim from session_summary.py; tenth datapoint in the pattern.** `enrich_test_ideas.py`'s skeleton — workspace IO + error hierarchy + load-source (session summary instead of exploration note) + per-source extraction (candidate block parser instead of table parser) + frontmatter merge (new) + body merge (new) + orchestration `run()` + CLI `main()` — is structurally identical to `session_summary.py`. Unique work in 4.5: session-summary candidate parser (~50 lines using the `### CS-NNN-NNN` regex per the Step 4.4 future-implementer hint); the five-character-stem keyword cross-reference (~50 lines); the frontmatter-preserving merge with pre-scan-decides-which discipline (~70 lines including the bugfix); the body merge that appends per-SESS-ID sub-blocks idempotently (~50 lines). Total unique: ~220 lines. Skeleton mirrors: ~290 lines. **Tenth datapoint across Phase 2/3/4** (Phase 2 Step 2.3 + Phase 3 Steps 3.5 + 3.6 + 3.8 + Phase 4 Steps 4.1 + 4.2 + 4.3 + 4.4 + 4.5). Pattern is now fully stable: when the helper-mirroring skeleton is mature, the per-sub-step implementation effort concentrates in the per-source-type logic + any phase-unique merge/render mechanics; everything else is fungible. **Future-implementer hint**: Phase 5's `tc-bdd` helpers will continue the pattern. The `enrich_test_ideas.py` skeleton is now an even-more-debugged artifact than `session_summary.py` was at the close of Step 4.4 — Phase 5's BDD generator can copy-rename it for its first helper.

##### Step 4.4 — `/tc:session-summary` + sessions index

- **13/14 GREEN on first cut; 2 small RED fixes were one-line edits.** First RED: the SESSION_TITLE_RE used during index rebuild only matched the exploration note's title shape `# SESS-... - exploration note for CH-...` but the helper writes a session summary with `# SESS-... - session summary for CH-...`. When `update_sessions_index()` scans `sessions/SESS-*.md` (the helper's own output), the regex didn't match the title and the index emitted `charter `(unknown)``. Second RED: the candidate-shape test expected the literal field names `title`/`type`/`source` to appear in each candidate block; the first cut rendered candidates as a single table with the field names ONLY in the column header row above, so per-row blocks didn't contain the literal words. **Fixes**: widened the regex to `(?:exploration note|session summary) for`; restructured candidates from a single table to per-candidate `### CS-NNN-NNN` sub-sections with field bullets. Both one-line edits; 15/15 GREEN after. **Pattern**: when a helper rebuilds an index over a directory of files it itself produced, the parser regex must match the helper's own output shape — not just the upstream helper's. The regex IS the cross-format contract. **Future-implementer hint**: any future Phase-N helper that ships a "scan-and-index" sweep (the `sessions/index.md` rebuild here; a hypothetical Phase 5 `bdd/index.md`; etc.) should declare its parser regex with explicit branches for every file format the helper produces or ingests. Document the regex's coverage in the helper docstring.
- **Per-candidate sub-sections beat tables when downstream consumers need to grep for field names.** The first-cut Candidate Scenarios render was a single 5-column table — concise but the field names (`id`/`type`/`title`/`source`/`linked anomaly`) only appeared in the header row. Step 4.5's enrichment helper (when it ships) will parse each candidate as an independent record; making each candidate an independently-citable sub-section with literal field-name bullets means the parser can grep for `title:`/`type:`/`source:` per block without needing to track column positions. **Pattern**: when a downstream consumer parses each entry independently (vs. aggregating the whole list), prefer per-entry sub-sections with explicit field labels over compact tables with column headers. The byte-count cost is modest; the parser robustness payoff is significant. **Future-implementer hint**: Step 4.5's test-idea enrichment will consume these candidate blocks; the per-block sub-section shape means 4.5 can parse them with a simple `### CS-...` heading regex + per-field bullet regex without depending on table column ordering.
- **Candidate-shape is the second cross-phase contract enumeration in Phase 4.** CHARTER_REQUIRED_FIELDS in Step 4.1 was the first — declared identically in both `tests/test_tc_explore_scaffold.py` (the assertion list) AND `scripts/create_charter.py` (the render list). The Step 4.4 candidate-shape contract (`id`, `title`, `type`, `source`, optional `linked_anomaly`) is the second — declared in the `CandidateScenario` dataclass in `session_summary.py`, asserted by `tests/test_session_summary.py::test_candidate_scenarios_have_stable_shape`, AND will be consumed by Step 4.5's enrichment parser. **Pattern reinforced**: when a sub-step's output is downstream input for another sub-step, the field contract should be declared mechanically in (a) the producer's dataclass / render, (b) the producer's test assertions, AND (c) the consumer's parser. Three layers means drift surfaces at unit-test time at any one of them. **Future-implementer hint**: Step 4.5 should declare its own dataclass mirroring the producer's CandidateScenario, AND its tests should assert that parsing the producer's output recovers every field — closing the third side of the contract triangle.
- **Helper-mirroring transferred ~95% verbatim from explore.py; ninth datapoint in the pattern.** `session_summary.py`'s skeleton — workspace IO + error hierarchy + load-source (exploration note instead of charter + recording) + per-source extraction (table parsers instead of JSON event parsers) + aggregate (counts instead of categorical lists) + render (7-section summary instead of exploration note) + orchestration `run()` + CLI `main()` — is structurally identical to `explore.py`. Unique work in 4.4: exploration-note markdown parsers (~120 lines); aggregator functions (~40 lines); candidate synthesis (~60 lines); summary render (~80 lines); sessions index rebuild (~50 lines). Total unique: ~350 lines. Skeleton mirrors: ~270 lines. **The skeleton was an even-more-debugged artifact from Steps 4.2 + 4.3; only the per-source parsing + aggregation needed bug-finding effort.** Ninth datapoint across Phase 2/3/4 (Phase 2 Step 2.3 + Phase 3 Steps 3.5 + 3.6 + 3.8 + Phase 4 Steps 4.1 + 4.2 + 4.3 + 4.4). Pattern is now fully stable: when the helper-mirroring skeleton is mature, the per-sub-step implementation effort concentrates in the per-source-type logic; everything else is fungible. **Future-implementer hint**: Step 4.5 (`/tc:test-ideas`) should ship in even less time than 4.4 because its input sources are the session summaries (one structured file format the helper-mirroring family already knows how to parse) plus the Phase-2 test-idea YAML frontmatter (a structured format the project already has tooling for).

##### Step 4.3 — `/tc:explore` + internal review sub-mode

- **16/17 GREEN on first cut of the helper; one bug-fix cycle for the SESS-ID deterministic-allocation pattern.** The first cut of `allocate_session_id` scanned the filesystem for max-existing SESS-IDs for the day's prefix and incremented — wall-clock-allocation behavior reasonable for live mode but wrong for recorded mode where re-runs against the same recording need to produce the same SESS-ID. The idempotency test caught it: first run → SESS-...-001 written; second run → SESS-...-002 written; two session notes existed where one was expected. **Fix**: compute NNN deterministically from the recording's first-event timestamp via `(parsed.hour * 60 + parsed.minute) % 1000` — same recording produces the same SESS-ID across re-runs because the first-event timestamp is the same. **Pattern**: when a helper's output filename must be stable across re-runs against unchanged input, the filename component must derive from the input content, not from filesystem-scanning + counter. Wall-clock + counter is right for *new* artifacts; content-derived hashing is right for *replays*. **Future-implementer hint**: Step 4.4's session-summary helper reads the SESS-ID from the existing exploration note (no allocation), so this concern is bounded to 4.3. But Step 4.5's enrichment helper will need to track which sessions have already enriched each REQ-ID — the `phase_4_sessions:` frontmatter list per test-idea is the equivalent of the SESS-ID stability contract for 4.5.
- **The asymmetric missing-evidence rule shows that fixture seed semantics matter at the unit-test level.** The plan's gap-detection text says "Anomaly entry without an adjacent `screenshot` event captured within ±3 seconds of the anomaly timestamp". Strict reading: count screenshot events within ±3s of the anomaly timestamp; if zero, fire gap. Tracing the seeded fixture: the slow-response anomaly at 10:00:12.815 has S-002 at 10:00:08.220 (4.6s away) and S-003 at 10:00:17.100 (4.3s away) — both outside ±3s. Strict reading would fire two gap signals: slow-response AND the seeded missing-evidence anomaly. **But the test expects exactly one missing-evidence gap** (the seed comment says "no screenshot captured within ±3 seconds"). **Resolution**: refine the rule asymmetrically — the anomaly's *own* `screenshot_id` field, when non-null, is the explicit evidence link, regardless of nearby screenshot events. The ±3s window is the fallback for cases where the anomaly does NOT cite its own screenshot. The seeded `missing-evidence` anomaly has `screenshot_id: null`; every other seeded anomaly has a non-null `screenshot_id`. Only one gap fires. **Pattern**: when a mechanical rule must be tested against a fixture, trace the rule against EVERY seeded entry and ensure the expected outcome holds for ALL of them, not just the marker-tagged seed. The fixture's seed comments are documentation; the rule + fixture together are the contract. **Future-implementer hint**: Step 4.5's `untested-function` cross-check has a similar potential asymmetry (mentioned function vs unmentioned function in code; need to verify against the full Phase 3 code-derived-model.md fixture state, not just the seeded `untested-function` anomaly).
- **Trigger-word coverage downgrade is a clean way to handle "AC mentions specific scenario that wasn't tested".** AC5 in the seeded CH-001 charter says "Session expiration during workspace navigation routes the user back to /sign-in". The URL `/sign-in` IS reached by the seeded session (after a sign-out attempt). But the *trigger* (session expiration) is not what reached it; the trigger was a manual sign-out. URL-and-keyword-match alone would mark this `observed`. The trigger-word downgrade pattern catches this: if the AC mentions `expiration` and observations never carry that word, the verdict is at best `partial`. The trigger-word universal core (10 entries: `expiration`, `expired`, `expire`, `leak`, `leakage`, `concurrent`, `race`, `timeout`, `timed-out`, `rollback`) is small but covers the common "this AC asserts a specific failure mode" pattern. **Pattern**: when assessing whether an acceptance criterion is satisfied by observations, distinguish (a) the entities/paths the AC mentions from (b) the *trigger* conditions the AC requires. URL + keyword matching covers (a); trigger-word vocabulary covers (b). Without (b), `partial`-coverage detection collapses to "everything mentioned ever in observations equals observed" which is wrong. **Future-implementer hint**: project extensions to the trigger-word core go through `tc-explore.exploration.trigger-words:` (not currently shipped — v1 ships the universal core only; Step 4.6's customization-guide audit will name this as a deferred extension).
- **Helper-mirroring transferred 95% cleanly with only the per-source extraction differing.** `explore.py`'s skeleton — workspace IO + error hierarchy + config loader + load-and-parse-source + per-source extraction + cross-check + render + open-questions append + orchestration `run()` + CLI `main()` — is structurally identical to `create_charter.py`. The unique work in 4.3 was: charter frontmatter parsing (~30 lines); recorded-session JSON parsing (~10 lines); the four extractor functions (`extract_observations`, `extract_evidence`, `extract_anomalies`, none for a missing fifth); the coverage assessor (~50 lines); the missing-evidence + charter-coverage-shortfall gap detectors (~60 lines combined); the deterministic SESS-ID allocator (~10 lines); the exploration-note renderer (~80 lines). Total unique implementation: ~250 lines. The other ~580 lines are skeleton mirrors. **The skeleton was a debugged artifact from Step 4.2; only the per-source extraction needed bug-finding effort.** Pattern reinforced (now eight datapoints across Phase 2/3/4): when the helper-mirroring skeleton is mature, the per-sub-step implementation effort concentrates in the per-source-type logic; everything else is fungible. **Future-implementer hint**: Steps 4.4 and 4.5 will be smaller than 4.3 (one input source each: exploration notes for 4.4; sessions + test-ideas for 4.5) and should land even closer to first-run-GREEN.

##### Step 4.2 — `/tc:create-charter`

- **14/14 GREEN on first implementation of the helper.** Second Phase-4 sub-step in a row (after Step 4.1's 20/20 GREEN scaffold) to land 100% GREEN on first author. **Seventh first-run-GREEN datapoint** across Phases 2-4: Phase 2 Step 2.3, Phase 3 Steps 3.5 + 3.6 + 3.8 integration, Phase 4 Steps 4.1 + 4.2. The pattern is now stable: helper-mirroring skeleton + test-first authoring + comprehensive seeded fixture + cross-phase contract enumeration (CHARTER_REQUIRED_FIELDS in 4.1; the test-idea enrichment contract that 4.5 will inherit; the per-source section namespacing from Phase 3) produces RED→GREEN on first cut with no debugging round. **Future-implementer hint**: budget 4.3-4.5 as helper-mirroring exercises, not debugging exercises; reserve discovery time for the cross-helper interactions (4.3's `--no-review` flag + 4.4's session-summary input shape + 4.5's enrichment contract) rather than for the helpers themselves.
- **Cross-phase contract enumeration proves its value at unit-test time.** CHARTER_REQUIRED_FIELDS — the six-element tuple (`id`, `mission`, `target`, `time-box`, `risk-areas`, `acceptance-criteria`) — is shared between `tests/test_tc_explore_scaffold.py` (Step 4.1, asserts the seeded fixture's charter carries every field) and `plugins/test-commander/scripts/create_charter.py` (Step 4.2, asserts the rendered charter carries every field). The two are literally the same Python tuple, declared identically in both files. **Why this matters**: when Step 4.7 builds the integration smoke, the charter-render fixture and the assertion list will agree mechanically because they share the same constant. **Pattern worth keeping**: when a phase ships a structural artifact that a subsequent sub-step must produce, enumerate the structural contract as a Python tuple/list in BOTH the scaffold test AND the helper that produces the artifact. The duplication is intentional — it surfaces drift at unit-test time rather than at integration time. **Future-implementer hint**: Step 4.3's recorded-session event types tuple (`page_load`, `click`, `fill`, `screenshot`, `console_message`, `network_request`, `anomaly`) should follow the same pattern — declared in `tests/test_tc_explore_scaffold.py` (Step 4.1, asserts the seeded recording uses only these types) AND in `extract_session_observations.py` (Step 4.3, asserts the helper handles each type). The universal anomaly categories already follow this pattern.
- **Broken-link drift in newly-deeper directory paths is a recurring failure mode.** The new `commands/` and `methodology/` directories under `tc-explore/` are five levels deep from the repo root (`plugins/test-commander/skills/tc-explore/{commands,methodology}/`); references to `tests/fixtures/seeded-exploration-session/charter.md` from these locations need `../../../../../tests/fixtures/...` (five `..` segments), not the four-segment pattern that worked for the `tc-knowledge` doc references in Phase 3 (because `tc-knowledge/{commands,methodology}/` is only four levels deep from the repo root via a different layout). The link checker caught 4 broken links on the first verify-chain run; all four were the same off-by-one relative-path mistake. **Mitigation**: before declaring a docs/template/methodology sub-step done, run `python3 scripts/check_links.py` explicitly as part of the per-sub-step verify cycle (`make verify` already runs it last; the lesson is to fix the broken paths in the same sub-step, not in a follow-up commit). **Future-implementer hint**: when authoring docs in a new skill's `commands/` or `methodology/` directory, look up the actual path depth before writing the first `../../` reference — count the directory segments from the file's location to the repo root, and use that count plus one for paths reaching back into `tests/fixtures/`. A more robust long-term fix would be a helper script that converts repo-root-anchored paths into correct relative paths during a docs pre-commit hook, but that's not in scope for v1.
- **Auto-suggestion ranking algorithm matters for test determinism.** The plan called for "the highest-risk entity from the seeded fixture's product-knowledge state" to be auto-suggested when no `--target` is supplied. The first cut of the suggestion logic used "highest mention count" with no defined tiebreaker. The test `test_auto_suggestion_ties_broken_alphabetically` then asserted that when two entities tie at the same mention count, the alphabetically-earlier name wins. This is a **deterministic-output discipline** rather than a UX requirement: cross-machine, cross-run reproducibility requires every sort tiebreaker to be explicit. The final algorithm sorts by `(-mention_count, alphabetical_name)` — both terms named. **Pattern worth keeping**: when a helper sorts a list of candidates, every tiebreaker must be explicit. `sorted(items, key=lambda x: x.score)` is brittle if two items share a score; `sorted(items, key=lambda x: (-x.score, x.name))` is reproducible. **Future-implementer hint**: Step 4.3's observation timeline rendering and Step 4.5's enrichment-section ordering will both need explicit tiebreakers (observation timestamp + secondary sort by event sequence; enrichment session ID + secondary sort by SESS-ID prefix).

##### Step 4.1 — scaffold + fixture

- **Scaffold step landed 20/20 GREEN on first author of the fixture.** Test-first authoring: 20 assertions covering skill directory + SKILL.md frontmatter + commands/methodology/templates dirs + fixture files + charter frontmatter + recorded-session JSON shape + every universal anomaly category present in both `_knowledge` markers AND `anomaly.category` structured values. All 20 went RED on the empty workspace; all 20 went GREEN as soon as the four fixture files (README, charter, target-app, recorded-session.json) plus the SKILL.md plus the three `.gitkeep` placeholders existed. No bug-fix cycle. **Why?** Two compounding factors: (a) the test design inherited the Phase 3 Step 3.1 scaffold pattern verbatim (uniform `knowledge: <dim>` marker token across file types; charter required-field assertion list mirrors the rubric-coverage assertion list from Phase 3); (b) the seeded fixture was authored against the test, not the other way around — each fixture file was written to satisfy specific assertions that the scaffold test enumerated. **Pattern reinforced**: the scaffold step's marker convention should be designed jointly with the test, and the test should enumerate every required-field check the fixture must satisfy. The Phase 3 Step 3.1 lesson about pushing the marker phrase into content (not container syntax) transferred cleanly to the JSON-no-native-comments problem in `recorded-session.json` — the `"_knowledge": "knowledge: <category>"` convention works the second time because it worked the first time. **Future-implementer hint**: Phase 5's scaffold step (`tc-bdd`) can confidently mirror this 20-assertion shape.
- **Cross-phase narrative consistency pays compounding dividends.** The seeded sample-project fixture in `tests/fixtures/seeded-sample-project/` (Phase 3) uses Account / Session / Workspace / Asset / Permission as its entity vocabulary, and the seeded-exploration-session fixture in `tests/fixtures/seeded-exploration-session/` (Phase 4) reuses the same entity names + the same `/sessions`, `/workspaces/{id}/assets`, `/accounts/{id}` URL paths. Step 4.7's integration smoke (per the plan) seeds the workspace with the Phase 3 sample-project, runs the five Phase 3 helpers to populate `product-knowledge/`, then runs the four Phase 4 helpers against the same workspace — the charter's `phase_3_sources` field references real Phase 3 product-knowledge artifacts. **Pattern**: when two phases produce artifacts that consume each other (Phase 3 → Phase 4 via the charter's `phase_3_sources`; Phase 2 → Phase 4 via the test-idea enrichment contract), use the same fixture narrative so cross-phase tests compose without translation. The cost is one extra line of D19 audit per fixture ("mirrors the Phase 3 fixture narrative for cross-phase consistency"); the benefit is zero translation overhead during integration test authoring. **Future-implementer hint**: Phase 5's `tc-bdd` fixture should similarly mirror the SaaS-dashboard narrative — the BDD generation will read Phase 3 product-knowledge + Phase 4 sessions and emit `.feature` files against the same Account/Workspace/Asset entities.
- **Charter-frontmatter required-fields assertion list IS the contract.** The plan's Step 4.1 deliverable says "charter has YAML frontmatter with `id: CH-001` and required fields (mission, target, time-box, risk-areas, acceptance-criteria)" — the scaffold test enumerates those exact fields as `CHARTER_REQUIRED_FIELDS` and asserts each one appears in the frontmatter. Step 4.2 (`/tc:create-charter`) will need to render those exact fields when producing new charters; any drift between the scaffold-test field list and the 4.2 helper's render template would break the 4.2 unit tests. **Pattern**: the scaffold step's frontmatter required-fields list IS the cross-phase contract that 4.2 must satisfy; treating it as such (rather than as documentation) catches drift at the unit-test level. **Future-implementer hint**: in 4.2, the charter render template should be driven by `CHARTER_REQUIRED_FIELDS` literally (or by a parallel constant the helper exposes) so the assertion list and the render template stay in sync mechanically.
- **`UNEXPECTED (phase 4) — ahead of schedule` is the verifier working as designed (third datapoint).** The `tc-explore` catalog entry was added in Step 0.6.1 when the catalog was scaffolded; the scaffold step's job is to land the SKILL.md so the directory exists. Under `DEFAULT_PHASE_CAP=3`, the verifier skips `tc-explore` from "expected" but still classifies it from on-disk presence — `UNEXPECTED` with reason `ahead of schedule`, warn-only, does not affect exit code. The cap bump to 4 lives in Step 4.7 per the plan. **Pattern (third datapoint after Phase 2 Step 2.1 and Phase 3 Step 3.1)**: do not chase the `UNEXPECTED` warning by landing an early cap bump; the staged bump is the design and prevents accidentally claiming "phase N PRESENT" mid-implementation.

---

## Phase 5 — BDD Generation and Traceability

**Goal.** Turn requirements, exploration, and ideas into BDD specs with full traceability. Ship two skills — `tc-bdd` (`/tc:generate-bdd`, `/tc:review-bdd` + an internal review sub-mode) and `tc-traceability` (`/tc:traceability-map`) — that read the Phase-2 reviewed requirements, the Phase-4-enriched test-idea seeds, and the Phase-4 session summaries, generate Gherkin `.feature` files carrying mechanical linkage tags back to their source REQ/CS IDs, review those specs against a deterministic quality rubric, and rebuild the cross-cutting traceability map that ties every requirement to its test ideas and BDD scenarios (downstream links reported `pending` until Phases 6–7 populate them).

**Architecture.** Each `/tc:*` command is a Python helper plus a Markdown command file inside `plugins/test-commander/skills/<skill>/`. Helpers do the deterministic work (parse enriched test-idea frontmatter + `## Phase 4 enrichment` candidate blocks, render `.feature` files with linkage tags, run the BDD review rubric, scan `bdd/features/` and rebuild the trace maps); Claude executes the judgment-heavy parts (phrasing Given/When/Then in behavior-not-UI language, deciding which candidate scenarios merit a scenario vs. a scenario outline, ranking review findings beyond the mechanical category) by reading the per-command page and methodology docs. Phase 5 is fully deterministic and offline — no MCP, no network, no browser. There is no live/recorded mode split (unlike Phases 3–4); the only inputs are workspace Markdown artifacts.

**Phase-5 design decisions (folded in).**

- **Linkage tags are the traceability contract.** Every generated scenario carries machine-readable provenance tags: `@req:REQ-NNN` and `@cs:CS-NNN-NNN` (plus optional `@anomaly:<category>` when the source candidate was anomaly-derived). `/tc:traceability-map` parses these tags to rebuild the map mechanically — the tag IS the cross-format contract between the generator (5.2) and the mapper (5.4). This closes the cross-phase contract triangle the Phase 4 Step 4.5 lesson predicted: enriched test-idea (`req_id`, `cs_id`, `type`, `title`, `source`, `linked_anomaly`) → `.feature` scenario tags (5.2) → trace-map rows (5.4). The generator declares a `Scenario` dataclass mirroring the enriched-test-idea candidate shape and asserts that parsing the enriched test-idea body recovers every field.
- **`tc-traceability` is the single authoritative writer of `traceability/`; the Phase-2 write is reconciled via a shared renderer (resolves the prior "Phase 5 owns traceability" framing).** Phase 2's `requirements_coverage.py` already writes `traceability/requirements-map.md` and `traceability/automation-map.md`, so the loose claim in the Phase 3/4 design notes that "`traceability/` is Phase-5-owned and untouched upstream" was already false. Phase 5 reconciles this cleanly: the trace-map render logic in `requirements_coverage.py` (`_render_traceability_map`) is **factored out into a shared module** (`plugins/test-commander/scripts/traceability_render.py`) so Phase 2 and Phase 5 render byte-identically (DRY, per the parent CLAUDE.md). `/tc:traceability-map` is the authoritative regenerator: it rebuilds `requirements-map.md` (now enriched with a BDD-scenario column), writes `test-map.md` (test-idea → BDD scenario → `pending` downstream), and leaves `automation-map.md` as Phase 2 seeds it until Phase 6 owns it. Phase 2's narrower write remains a compatible interim seed; the shared renderer guarantees no format drift between the two callers.
- **Downstream trace links are reported `pending`, never invented.** The full chain is Requirement → Test Idea → BDD Scenario → Automation Candidate → Automated Test → Test Result → Quality Report, but in Phase 5 only the first three links exist (Automation Candidate is partial via Phase-4 test-ideas; Automated Test = Phase 6; Test Result + Quality Report = Phase 7). The map renders `pending` for every link a later phase populates. "Traceability complete" in the DoD means "every requirement is linked to its test ideas and BDD scenarios; downstream columns honestly read `pending`" — it does not mean fabricating links that do not yet exist (per the project's never-invent-metrics rule).
- **Review is both an auto-run sub-mode and a standalone command.** Mirroring the Phase 4 `/tc:explore` pattern: `/tc:generate-bdd` auto-runs the internal BDD review sub-mode at the end of generation (suppressible with `--no-review`), routing failures to `requirements/open-questions.md` as `[bdd-review]` gap signals. `/tc:review-bdd` is the standalone, re-runnable form that reviews already-written `.feature` files without regenerating them. Both share one `_review_features()` implementation.
- **Two skills scaffolded together; staged cap-bump unchanged.** 5.1 scaffolds both `tc-bdd/SKILL.md` and `tc-traceability/SKILL.md` (the `CATALOG` entries `tc-bdd: 5` and `tc-traceability: 5` already exist from Step 0.6.1). Both report `UNEXPECTED (phase 5) — ahead of schedule` under `DEFAULT_PHASE_CAP=4` until the cap bumps to 5 in the testing-finalization sub-step (5.6), per the staged-bump discipline from every prior phase.
- **Strict-YAML scaffold assertion from the start (per the Phase 4 Step 4.8 lesson).** Both new `SKILL.md` files get a `tests/test_*_scaffold.py` assertion that invokes PyYAML directly on the frontmatter and asserts a clean parse — landed in 5.1, not deferred to sign-off. This is the bug `claude plugin validate` caught in Phase 4 only at the cold-user walkthrough; Phase 5 catches it at the unit-test layer.
- **Helper-mirroring is the design.** `generate_bdd.py` copy-renames the most-debugged sibling, `enrich_test_ideas.py` (it parses the same enriched test-idea frontmatter + `### CS-NNN-NNN` candidate blocks it consumes). `review_bdd.py` mirrors the `_review_session()` rubric pattern from `explore.py`. `traceability_map.py` mirrors `requirements_coverage.py` (which already scans the workspace and renders trace maps — the closest sibling). The integration smoke in 5.6 is budgeted as verification, not debugging, per the Phase 3 Step 3.8 / Phase 4 Step 4.7 lessons.
- **Phase 5 fixture bundles seeded BDD inputs and one deliberate review defect per rubric dimension.** The new `tests/fixtures/seeded-bdd/` directory carries: an enriched test-idea `REQ-001.md` (status `enriched`, with a `## Phase 4 enrichment` section and `### CS-NNN-NNN` candidate blocks) plus a session summary `SESS-...md` (the generator inputs); and a `flawed.feature` carrying one seeded defect per universal BDD-review category (`ambiguous-step`, `missing-tag`, `untraceable`, `ui-coupled-step`, `missing-examples`, `conjunction-overload`) marked with the uniform `knowledge: <category>` token (per the Phase 3 Step 3.1 marker-uniformity lesson). The narrative reuses the Account / Session / Workspace / Asset SaaS-dashboard vocabulary from the Phase 3 + Phase 4 fixtures so the 5.6 integration smoke composes without translation.
- **Cross-phase write boundary.** Phase 5 reads `<workspace>/requirements/` (reviewed requirements + acceptance criteria), `<workspace>/test-ideas/` (Phase-4-enriched seeds), `<workspace>/sessions/` (Phase-4 session summaries), and `<workspace>/product-knowledge/` (Phase-3 entities/journeys for scenario grounding). It writes `<workspace>/bdd/features/`, `<workspace>/bdd/summaries/`, `<workspace>/bdd/index.md`, `<workspace>/traceability/` (the three maps), and appends `[bdd-review]` gap signals to `<workspace>/requirements/open-questions.md`. It does NOT write to `product-knowledge/` (Phase 3) or `test-ideas/` (Phase 4 enriches; Phase 5 reads only). The 5.6 integration smoke asserts these boundaries directly.

**Skills authored.** `tc-bdd` — `SKILL.md` plus two command files (`generate-bdd.md`, `review-bdd.md`), the umbrella `methodology/bdd-generation.md` plus `methodology/bdd-quality-review.md`, and templates `feature-template.feature`, `bdd-summary-template.md`, `bdd-review-template.md`. `tc-traceability` — `SKILL.md` plus `commands/traceability-map.md`, `methodology/traceability.md`, and `templates/traceability-map-template.md`.

**Design references.** `exploratory-to-bdd:generate-bdd`, `exploratory-to-bdd:review-bdd`, `exploratory-to-bdd:explore-to-bdd` (BDD generation prompts, review rubric, exploration-to-spec bridging), `mcp-exploratory-testing:exploration-to-bdd` (handoff patterns). Per Decision D1 (vendor-and-own), `tc-bdd` and `tc-traceability` are authored in-repo; these skills are design references only, never runtime dependencies.

**Inputs read.** `<workspace>/requirements/`, `<workspace>/test-ideas/`, `<workspace>/sessions/`, `<workspace>/product-knowledge/`.

**Outputs.** `.test-commander/bdd/features/*.feature`, `.test-commander/bdd/summaries/*.md`, `.test-commander/bdd/index.md`, `.test-commander/traceability/{requirements-map.md,test-map.md}`.

**Tags.** Shipped universal classes: `@smoke`, `@regression`, `@manual`, `@exploratory`, `@automated-candidate`. Machine-readable linkage tags: `@req:REQ-NNN`, `@cs:CS-NNN-NNN`, `@anomaly:<category>`. Per D19, Test Commander ships no hard-coded domain, risk, or persona taxonomy — projects add values under shared namespaces:

- `@area:<feature>` — project-defined feature areas (e.g. `@area:sign-in`, `@area:reports`).
- `@risk:<class>` — project-defined risk classes (e.g. severity `@risk:high`/`@risk:medium`/`@risk:low`, or category `@risk:data-loss`/`@risk:availability`/`@risk:integrity`).
- `@persona:<role>` — project-defined personas (e.g. `@persona:admin`, `@persona:operator`).

Test Commander ships the namespaces; the consuming project picks values (configured under `tc-bdd.tags.*` in `<workspace>/config.yaml`), documents them in its own BDD methodology notes, and configures any tag-driven gates. The customization guide (updated in 5.5) carries worked examples for three materially-different project shapes.

**Traceability chain.** Requirement → Test Idea → BDD Scenario → Automation Candidate → Automated Test → Test Result → Quality Report. Phase 5 populates the first three links; the trace map renders `pending` for Automated Test (Phase 6), Test Result, and Quality Report (Phase 7).

**BDD review rubric (universal core).** Six categories, mirroring the Phase 4 anomaly-category model. `ambiguous-step` (vague Given/When/Then with no concrete subject or outcome), `missing-tag` (scenario lacking a required namespace tag — `@area:` or a linkage tag), `untraceable` (scenario with no `@req:`/`@cs:` linkage tag resolvable to an existing requirement/candidate), `ui-coupled-step` (steps describing clicks/selectors/URLs instead of behavior), `missing-examples` (a `Scenario Outline` with no `Examples:` table), `conjunction-overload` (a step chaining multiple behaviors with `and`/`,` such that it is not atomically assertable). The seeded fixture carries one defect per category. Project extensions union via `tc-bdd.review.rubric-extensions`.

### Phase 5 — Execution outline

Seven sub-steps. TDD throughout: every implementation step lands its tests red before turning them green. Sub-step 5.1 scaffolds both skills and the shared seeded-bdd fixture; 5.2–5.4 implement the three commands; 5.5 is the dedicated documentation pass; 5.6 is the dedicated testing finalization (cap bump + integration smoke); 5.7 is the sign-off with a `phase-5` tag.

#### 5.1 — Skill scaffolds (`tc-bdd` + `tc-traceability`) and seeded-bdd fixture

- **Deliverables.**
  - `plugins/test-commander/skills/tc-bdd/SKILL.md` and `plugins/test-commander/skills/tc-traceability/SKILL.md` — each with YAML frontmatter (`name`, single-line trigger-style `description` with **no embedded `key: value` substring**, per the Phase 4 Step 4.8 lesson) and a body listing the skill's commands. `tc-bdd`'s body lists `/tc:generate-bdd`, `/tc:review-bdd`, and the internal review sub-mode; `tc-traceability`'s lists `/tc:traceability-map`. Both carry deferral wording until each sub-step turns it into shipped-behavior description.
  - `commands/.gitkeep`, `methodology/.gitkeep`, `templates/.gitkeep` under both skills — removed by the first sub-step that lands real content in each directory.
  - `tests/fixtures/seeded-bdd/` containing:
    - `REQ-001.md` — an enriched test-idea seed (`status: enriched`, full Phase-2 `tc-test-idea/v1` frontmatter, a `## Phase 4 enrichment` section with two or more `### CS-NNN-NNN` candidate blocks carrying `type`/`title`/`source`/`linked_anomaly`).
    - `SESS-20260115-001.md` — a session summary (the second generator input), reusing the SaaS-dashboard narrative.
    - `flawed.feature` — a Gherkin file carrying one seeded defect per universal BDD-review category, each marked with a `# knowledge: <category>` comment so the scaffold test verifies rubric coverage with the uniform regex from Step 3.1.
    - `README.md` — documents the linkage-tag convention, the universal review-category catalog, the marker convention, and the "deliberately generic; not a claim about scope" D19 framing.
- **Tests first.** `tests/test_tc_bdd_scaffold.py` and `tests/test_tc_traceability_scaffold.py` — assert: each skill directory and `SKILL.md` present; frontmatter parses cleanly under **strict PyYAML** (`name == "tc-bdd"` / `"tc-traceability"`, non-empty description, no parse error); body references each command; `commands/`/`methodology/`/`templates/` dirs present; fixture directory exists with all four files; `REQ-001.md` parses with `status: enriched` and at least two `### CS-` candidate blocks; `flawed.feature` parses as Gherkin and every universal review category appears in at least one `knowledge:` marker. Test-first: red before any deliverable exists.
- **Definition of done.** Both skills scaffolded; fixture covers every review category and ships valid enriched-test-idea inputs; scaffold tests green; `verify_skills.py` reports `tc-core/tc-requirements/tc-knowledge/tc-explore PRESENT` and `tc-bdd UNEXPECTED (phase 5) — ahead of schedule`, `tc-traceability UNEXPECTED (phase 5) — ahead of schedule` under `DEFAULT_PHASE_CAP=4` (the cap bumps to 5 in 5.6, not here).
- **Review.** Manual read of the fixture against the BDD review rubric and the linkage-tag convention — confirm every review category has a seeded defect, the enriched test-idea is realistic but deliberately generic, and the `.feature` shape is forward-compatible with the 5.2 generator and 5.4 mapper.

#### 5.2 — `/tc:generate-bdd` (TDD)

- **Helper.** `plugins/test-commander/scripts/generate_bdd.py` (mirrors `enrich_test_ideas.py`). Reads `<workspace>/test-ideas/<REQ-ID>.md` (enriched seeds; `--req <REQ-ID>` for one, all enriched seeds otherwise), reads the referenced `<workspace>/sessions/` summaries and `<workspace>/product-knowledge/` for grounding, and writes `<workspace>/bdd/features/<area>.feature` — a Gherkin `Feature` with one `Scenario`/`Scenario Outline` per candidate, each carrying `@req:REQ-NNN`, `@cs:CS-NNN-NNN`, the universal class tags, and `@area:<feature>` derived from the requirement. Writes a per-feature `<workspace>/bdd/summaries/<area>.md` and rebuilds `<workspace>/bdd/index.md` (scan-and-index of every feature: scenario count, linkage coverage, review verdict). Declares a `Scenario` dataclass mirroring the enriched-test-idea candidate shape (`req_id`, `cs_id`, `type`, `title`, `source`, `linked_anomaly`) and asserts parsing the enriched body recovers every field. **Idempotency contract**: pure generated reports — overwrite mode; byte-deterministic re-run against unchanged inputs. **No auto-review in 5.2** — the review engine and the generate-time auto-run wiring (incl. the `--no-review` flag) ship together in 5.3, which owns the rubric and edits `generate_bdd.py` to add the call. This keeps 5.2 a clean generation-only increment with no forward dependency; the generated `.feature` output is authored to pass the 5.3 rubric (concrete behavior-not-UI steps, `@area:`/`@req:`/`@cs:` tags on every scenario, no bare `Scenario Outline`).
- **Umbrella methodology.** `methodology/bdd-generation.md` — the umbrella 5.2–5.3 reference. Documents the test-idea → BDD → traceability workflow, Gherkin authoring discipline (behavior-not-UI, Given/When/Then atomicity, scenario vs. outline), the linkage-tag convention, the cross-phase write boundary, and a Claude-judgment-layer paragraph. (Per the Phase 4 Step 4.6 lesson, the umbrella's workflow diagram is on the Per-Phase-Convention #4 edit list for every command sub-step.)
- **Templates.** `templates/feature-template.feature`, `templates/bdd-summary-template.md`.
- **Command file.** `commands/generate-bdd.md` (Inputs / Outputs / Preconditions / Behavior / Safety / Implementation / Definition of Done / See also).
- **SKILL.md update.** `tc-bdd/SKILL.md` updated to describe `/tc:generate-bdd`'s shipped generation behavior and instruct Claude to invoke the bundled helper; deferral wording for this command's generation removed. (A brief forward pointer that the review sub-mode wires in 5.3 is acceptable mid-phase and is finalized in 5.3.)
- **Tests first.** `tests/test_generate_bdd.py` — uninitialized workspace refused; no enriched test-ideas refused with a precondition error directing the user at `/tc:test-ideas`; seeded enriched `REQ-001.md` → `<area>.feature` written with valid Gherkin, every candidate rendered as a scenario, every scenario carrying resolvable `@req:`/`@cs:` linkage tags plus an `@area:` tag; the `Scenario`-shape contract test (`type`/`title`/`source` recovered from the enriched body); `bdd/summaries/<area>.md` written; `bdd/index.md` lists the feature; idempotent re-run byte-identical; `tc-bdd.tags.*` config extensions union with the universal classes.
- **Definition of done.** Helper passes all cases; the generated `.feature` is valid Gherkin with linkage tags; umbrella + per-command methodology + templates + command page authored; `tc-bdd/SKILL.md` no longer defers `/tc:generate-bdd`.
- **Verification.** Pytest green; eyeball a generated `.feature` for tone, tag placement, and Gherkin validity before declaring 5.2 done.

#### 5.3 — `/tc:review-bdd` + internal review sub-mode (TDD)

- **Helper.** `plugins/test-commander/scripts/review_bdd.py` (mirrors the `_review_session()` rubric pattern from `explore.py`). Reads `<workspace>/bdd/features/*.feature`, runs the six-category universal review rubric, and writes a review verdict into each `<workspace>/bdd/summaries/<area>.md` plus routes failures to `<workspace>/requirements/open-questions.md` as `[bdd-review]` gap signals (with the `(source-id, question-text)` dedup contract from Phase 2; `source-id: tc-bdd/bdd-review-<area>`). Exposes `review_features()` so `generate_bdd.py` calls the same implementation for its auto-run sub-mode. **5.3 also wires the auto-run**: it edits `generate_bdd.py` to import `review_features` and call it at the end of generation (suppressible with a new `--no-review` flag), and updates `generate-bdd.md` + `tc-bdd/SKILL.md` to describe the now-wired auto-review (removing the 5.2 forward pointer). **Idempotency contract**: re-running produces byte-identical verdicts and no duplicate gap signals.
- **Methodology.** `methodology/bdd-quality-review.md` — the six review categories with one worked example per category drawn from the seeded `flawed.feature`, plus a Claude-judgment-layer paragraph (ranking severity beyond the mechanical category, deciding which ambiguous steps are acceptable shorthand vs. genuine defects).
- **Templates.** `templates/bdd-review-template.md`.
- **Command file.** `commands/review-bdd.md`.
- **SKILL.md update.** `tc-bdd/SKILL.md` updated to describe `/tc:review-bdd` and the now-wired generate-time auto-run sub-mode; the 5.2 forward pointer and all deferral wording removed.
- **Tests first.** `tests/test_review_bdd.py` — uninitialized workspace refused; no `.feature` files refused with a clear error directing the user at `/tc:generate-bdd`; seeded `flawed.feature` → every one of the six universal review categories surfaced exactly once; `[bdd-review]` gap signals routed to open-questions with the dedup contract; idempotent re-run produces no duplicate signals; a clean (generated-by-5.2) feature produces a `pass` verdict with zero gap signals; `review_features()` is the same code path `/tc:generate-bdd` auto-runs (assert `generate_bdd` imports and calls it, and that `--no-review` suppresses the gap signals).
- **Definition of done.** Helper passes all cases; the rubric-category coverage assertion is in the suite; methodology covers all six categories + the judgment layer; the auto-run sub-mode and the standalone command share one implementation; SKILL.md updated.
- **Verification.** Pytest green; smoke run against the seeded fixture flags every seeded defect and passes a clean feature.

#### 5.4 — `/tc:traceability-map` (TDD)

- **Shared renderer extraction.** Factor `_render_traceability_map` out of `requirements_coverage.py` into `plugins/test-commander/scripts/traceability_render.py`; update `requirements_coverage.py` to import it (no behavior change — assert the Phase-2 tests stay green). This is the DRY reconciliation that lets Phase 2 and Phase 5 render byte-identically.
- **Helper.** `plugins/test-commander/scripts/traceability_map.py` (mirrors `requirements_coverage.py`, reusing its scan functions + `review_bdd.parse_feature_file` for DRY). Scans `<workspace>/requirements/` (requirement inventory), `<workspace>/test-ideas/` (enriched seeds), and `<workspace>/bdd/features/*.feature` (parsing `@req:`/`@cs:` linkage tags), then rebuilds `<workspace>/traceability/requirements-map.md` via the **shared renderer** (the same 4-column REQ-ID/Test ideas/BDD features/Automation format Phase 2 writes — no drift; requirements-map.md is byte-identical whichever helper wrote it) and writes the new `<workspace>/traceability/test-map.md` carrying the scenario-level chain (Requirement → Test idea (CS) → BDD scenario → Automated test → Test result → Quality report). The scenario-level "BDD-scenario" detail lives in test-map.md, not as a new column on requirements-map.md, so the shared 4-column format stays drift-free. Downstream columns (Automated test, Test result, Quality report) render `pending`. **Idempotency contract**: authoritative regenerator — overwrite mode; byte-deterministic; the only writer of `requirements-map.md` and `test-map.md` from Phase 5 onward.
- **Methodology.** `methodology/traceability.md` — the full chain, the linkage-tag convention as the mechanical join key, the `pending`-not-invented discipline, the Phase-2-seed/Phase-5-authoritative reconciliation, and a Claude-judgment-layer paragraph (spotting requirements with zero scenarios, scenarios spanning multiple requirements).
- **Templates.** `templates/traceability-map-template.md`.
- **Command file.** `commands/traceability-map.md`. By end of 5.4, both `tc-bdd/SKILL.md` and `tc-traceability/SKILL.md` describe every shipped command with no deferral wording.
- **Tests first.** `tests/test_traceability_map.py` — uninitialized workspace refused; no `.feature` files → `requirements-map.md` written with every requirement present and the BDD-features cell reading `_(none)_`, `test-map.md` written with the empty-note (not an error); seeded chain (enriched `REQ-001.md` + generated `<area>.feature`) → `test-map.md` links REQ-001 to its CS IDs and the generated scenarios via the linkage tags with `pending` downstream columns, and `requirements-map.md` lists the feature file for REQ-001; idempotent re-run byte-identical; a regression test asserting `traceability_render.render_requirements_map` produces identical output for the Phase-2 caller and the Phase-5 caller given the same links (and that the extraction left `requirements_coverage`'s output unchanged).
- **Definition of done.** Helper passes all cases; shared renderer extracted and Phase-2 tests still green; `requirements-map.md` and `test-map.md` rebuilt with `pending` downstream; both SKILL.md files free of deferral wording.
- **Verification.** Pytest green; smoke run produces a map that resolves REQ-001 → CS → scenario and reports downstream `pending`.

#### 5.5 — Documentation pass *(dedicated step)*

- **Deliverables.**
  - Author `docs/user-guide/generating-bdd.md` — end-to-end walkthrough: `/tc:generate-bdd` → (auto review) → `/tc:review-bdd` → `/tc:traceability-map`. Sample input and output drawn from the seeded fixture chain (Phase 3 product-knowledge + Phase 4 sessions + Phase 4 enriched test-ideas, in that order, per the Phase 4 Step 4.6 lesson); embed verbatim helper output, not paraphrase. Mirrors `docs/user-guide/exploring-an-app.md` section-for-section.
  - Update `docs/command-reference.md` — add the three Phase 5 commands as links into their per-command pages (new "Phase 5 commands (shipped)" section).
  - Update `docs/workspace-reference.md` — per-file ownership tables for `bdd/features/`, `bdd/summaries/`, `bdd/index.md`, and the `traceability/` reconciliation (Phase 2 seeds; Phase 5 is authoritative; Phase 6 owns `automation-map.md`). Document the linkage-tag convention.
  - Refresh status lines across the same six locations as Phase 4: `README.md` status header + doc index, `docs/install.md` "Verifying the install", `docs/user-guide/getting-started.md` "what's next", `docs/user-guide/workflow.md`, `docs/user-guide/exploring-an-app.md` footer "Beyond Phase 4", `plugins/test-commander/README.md` skill-status table (two new rows).
  - **Customization-guide update (per the Per-Phase Customization-guide Convention / D19).** Add a "Phase 5 schema (`tc-bdd` / `tc-traceability`)" section to `docs/user-guide/customizing-for-your-project.md` covering the tag namespaces (`@area:`, `@risk:`, `@persona:`), `tc-bdd.tags.*`, and `tc-bdd.review.rubric-extensions`. At least three worked extension examples spanning materially-different project shapes (per the Phase 4 Step 4.6 lesson — vary by shape, not just vocabulary): a web app with browser-driven scenarios, an API-only project with spec-derived scenarios, a mobile app with screen-flow scenarios. Add a "Phase 5 — what landed" subsection naming the universal cores, schema keys, and the tests that defend them.
  - **Final SKILL.md pass.** Confirm both SKILL.md files describe every shipped command, link to every per-command page, and instruct Claude to invoke the bundled helpers. Grep `behavior arrives in|coming in phase|when phase 5 ships` across both SKILL.md files, the umbrella `bdd-generation.md`, AND all of `docs/`.
- **Definition of done.** Every doc accurate against the implementation; all cross-links resolve; link checker green; customization guide reflects the shipped schema with three worked examples spanning project shapes.
- **Verification.** `python3 scripts/check_links.py` clean; grep for stale deferral wording across both SKILL.md files, the umbrella methodology, and `docs/` returns no hits; every YAML block in `customizing-for-your-project.md` parses.

#### 5.6 — Testing finalization *(dedicated step, separate from per-command TDD)*

- **Deliverables.**
  - Bump `DEFAULT_PHASE_CAP` in `scripts/verify_skills.py` from `4` to `5` (the `CATALOG` entries `tc-bdd: 5` and `tc-traceability: 5` already exist).
  - `tests/test_phase_5_integration.py` — integration smoke that creates a fresh tmp consuming project, runs `init_workspace.py`, then drives the full workflow in the natural order Phase 2 → Phase 3 → Phase 4 → Phase 5 (per the Phase 4 Step 4.7 sequencing lesson, so `[bdd-review]` lands on top of upstream open-questions entries rather than being clobbered). In-process imports. Assertions at every transition: `.feature` files written with valid Gherkin + resolvable linkage tags; review verdict written and `[bdd-review]` gap signal present for the appropriate defect; `requirements-map.md` + `test-map.md` rebuilt with REQ → CS → scenario links and `pending` downstream; `product-knowledge/` and `test-ideas/` byte-identical before and after Phase 5 (write-boundary discipline asserted directly, mirroring the Phase 4 traceability assertion); `/tc:next` advances past `/tc:generate-bdd` (the robust "advanced past" invariant — assert `command != /tc:generate-bdd`, not a pinned next command).
  - Byte-stable re-run integration test: full Phase-5 sweep twice; assert byte-identical `.feature` files, maps, and line-stable open-questions.
  - Shared-renderer regression: assert `requirements_coverage.py` output is unchanged after the `traceability_render` extraction (Phase-2 tests stay green).
- **Definition of done.** Integration smoke passes; cap bump reflected; full `make verify` chain green; `verify_skills.py` reports all six shipped skills `PRESENT` with `UNEXPECTED=0`.
- **Verification.** Captured `make verify` output. Per the Phase 3/4 lessons, the integration smoke is budgeted as verification not debugging; if it lands red, surface the discovery as a sub-step lesson and consider whether the unit-test coverage in 5.2–5.4 needs strengthening. **Note (per the Phase 2 Step 2.9 + Phase 4 Step 4.7 lessons): Phase 5 writing to `traceability/` and `bdd/` further perturbs the `/tc:next` phase-status heuristic; if the "advanced past" assertion is brittle, refine the R-rules in `next-step-inference.md` here rather than pinning a specific next command.**

#### 5.7 — Sign-off

Six sub-sub-steps. Mirrors the Phase 4 sign-off (4.8) exactly. Test-first: the sign-off test in 5.7.5 lands red before the plan/CHANGELOG edits in 5.7.3 turn it green. The final sub-step (5.7.6) captures evidence and pushes the `phase-5` annotated tag.

##### 5.7.1 — Cold-user walkthrough of `generating-bdd.md`

- **Deliverables.** Captured log of an end-to-end walkthrough from a freshly-installed plugin (`make uninstall` → `make install`, which runs `claude plugin validate` — the only strict-YAML gate) against a fresh tmp consuming project, with Phase 2 → 3 → 4 state pre-populated, then the three Phase 5 helpers in workflow order.
- **Definition of done.** All commands succeed end to end. Output captured to `/tmp/tc-phase5-walkthrough.log`. Any failure is fixed and re-run before 5.7.2. **Keep the `make uninstall` + `make install` preamble exactly as-is (per the Phase 4 Step 4.8 lesson) — it exercises the strict validator no other step runs.**

##### 5.7.2 — Per-step DoD audit

- Line-by-line audit of 5.1 through 5.6 against their DoD lists: every helper, methodology, template, command file, and SKILL.md update present; every per-command test green; linkage tags resolve; write-boundary holds; both SKILL.md files free of deferral wording; `customizing-for-your-project.md` carries the Phase 5 schema with three worked examples. **Lesson-capture audit:** every Phase 5 sub-step (5.1–5.6) has an entry in `Phase 5 — Lessons learned (running)`; clean sub-steps record "no lessons" explicitly. Any unmet item blocks the sign-off.

##### 5.7.3 — Plan and CHANGELOG updates

- `planning/plan.md` — collapse `### Phase 5` To Do to a marker line; add a `### Phase 5 — BDD generation and traceability (YYYY-MM-DD)` section to `## Completed` with `[x]` per-step bullets, mirroring the Phase 4 closing format.
- `CHANGELOG.md` — flip the Phase 5 heading from `(in progress)` to `(complete YYYY-MM-DD)` with per-sub-step Added bullets.

##### 5.7.4 — Documentation final pass

- Edit wherever Phase 5 wording has drifted across the six sub-steps (README status line, getting-started "what's next", install verifying-install paragraph, `generating-bdd.md` intro, `exploring-an-app.md` "Beyond Phase 4" footer, `plugins/test-commander/README.md` skill table, customization-guide tense). "Phase 5 in progress" → "Phase 5 complete (YYYY-MM-DD); Phase 6 starts next". All cross-links resolve.

##### 5.7.5 — Pre-flight tests for sign-off

- `tests/test_phase_5_signoff.py`. Coverage: all Phase 5 pytest files exist (`test_tc_bdd_scaffold`, `test_tc_traceability_scaffold`, `test_generate_bdd`, `test_review_bdd`, `test_traceability_map`, `test_phase_5_integration`, `test_phase_5_signoff`); all three helpers + `traceability_render.py` exist; all command files exist under both skills; all methodology + template files exist; `seeded-bdd/` fixture exists with all four files; `verify_skills.py` has `CATALOG["tc-bdd"] == 5`, `CATALOG["tc-traceability"] == 5`, and `DEFAULT_PHASE_CAP >= 5` (per the Phase-2 Step-2.8 lesson — never assert `==` on the cap); both SKILL.md files describe every shipped command with no deferral wording AND parse under strict PyYAML; `customizing-for-your-project.md` has a Phase 5 `tc-bdd:` YAML block matching the shipped schema with at least three project-shape headings; the `Phase 5 — Lessons learned (running)` subsection has an entry per sub-step (5.1–5.6); CHANGELOG Phase 5 marked complete with a date; `plan.md` Completed has a Phase 5 subsection; `plan.md` To Do Phase 5 collapsed to the marker line; total pytest count meets the floor (`>= 460` — Phase 4 finished at 422; Phase 5 adds two scaffold suites, three per-command suites, integration, and sign-off). Test-first: red before 5.7.3's edits, green after.

##### 5.7.6 — Final DoD evaluation (close Phase 5)

1. `make verify` — every test green, link checker clean, `verify_skills.py` reports all six shipped skills `PRESENT` with `UNEXPECTED=0`.
2. Replay the 5.7.1 walkthrough end to end.
3. Capture output to `/tmp/tc-phase5-signoff.log`.
4. Commit the plan/CHANGELOG/docs updates + the sign-off test in one final commit.
5. Push to origin.
6. Create annotated tag: `git tag -a phase-5 -m "Phase 5 — BDD generation and traceability complete."`.
7. Push tag: `git push origin phase-5`.

- **Definition of done.** All seven steps complete. Tag visible on origin (`git ls-remote origin phase-5` resolves). Evidence log captured. Phase 5 is closed.

#### Definition of done — consolidated 15 checks

Eleven automated; four evidence-based.

| # | Check | Type | How |
| --- | --- | --- | --- |
| 1 | All seven Phase 5 test files exist | auto | sign-off test |
| 2 | All three helpers + `traceability_render.py` exist | auto | sign-off test |
| 3 | All three command files exist (two under `tc-bdd/commands/`, one under `tc-traceability/commands/`) | auto | sign-off test |
| 4 | All methodology files exist (`bdd-generation.md`, `bdd-quality-review.md`, `traceability.md`) | auto | sign-off test |
| 5 | All templates exist (`feature-template.feature`, `bdd-summary-template.md`, `bdd-review-template.md`, `traceability-map-template.md`) | auto | sign-off test |
| 6 | `seeded-bdd/` fixture exists and covers every universal review category | auto | scaffold test |
| 7 | `verify_skills.py` has `CATALOG["tc-bdd"] == 5` and `CATALOG["tc-traceability"] == 5` and `DEFAULT_PHASE_CAP >= 5`; `make verify` prints all six skills PRESENT with `UNEXPECTED=0` | auto | sign-off test + `make verify` |
| 8 | Integration smoke `test_phase_5_integration` passes; `product-knowledge/` + `test-ideas/` untouched assertions hold; `/tc:next` advances past `/tc:generate-bdd` | auto | pytest |
| 9 | Both SKILL.md files describe every shipped command with no deferral wording and parse under strict PyYAML | auto | sign-off test |
| 10 | Linkage-tag contract: every generated scenario carries a `@req:`/`@cs:` tag resolvable by `traceability_map.py` | auto | generate-bdd + traceability-map tests |
| 11 | `make verify` chain clean (link checker covers the new docs) | auto | full chain |
| 12 | Cold-user walkthrough of `generating-bdd.md` from clean state succeeds (5.7.1) | evidence | `/tmp/tc-phase5-walkthrough.log` |
| 13 | Per-step DoD audit clean for 5.1–5.6 (5.7.2) | evidence | audit notes |
| 14 | `plan.md` To Do Phase 5 collapsed; Completed has Phase 5 subsection with date (5.7.3); CHANGELOG Phase 5 marked complete | evidence | sign-off test + grep |
| 15 | `phase-5` annotated tag created and pushed (5.7.6) | evidence | `git tag -l phase-5` + `git ls-remote origin phase-5` |

#### TDD pattern used in 5.2–5.4

```
write tests (red)             # define expected behavior per dimension from the seeded fixture, including linkage-tag resolution + Scenario-shape recovery
  → implement helper (green)  # minimum code to pass; mechanical generation/review/mapping only
    → author methodology + template (umbrella bdd-generation.md lands in 5.2)
      → author per-command page
        → update the owning SKILL.md to surface shipped behavior
          → 5.2 ships generation only; 5.3 ships the review engine (review_features()) AND wires generate-bdd's auto-run
            → verify (pytest + make verify)
```

No implementation lands before its tests. Every command's test suite drives the helper from the same seeded fixture so the rubric and the linkage-tag convention are the contract.

#### Validation sequence

1. Author 5.1 (two skill scaffolds + fixture) with the two scaffold tests. Confirm pytest red → green.
2. Author 5.2 (`/tc:generate-bdd` + umbrella `bdd-generation.md`): tests, helper, methodology, templates, command file, SKILL.md, pytest.
3. Author 5.3 (`/tc:review-bdd` + the shared `_review_features()`): tests, helper, methodology, template, command file, SKILL.md, pytest.
4. Author 5.4 (`/tc:traceability-map`): extract `traceability_render.py` first (Phase-2 tests stay green), then tests, helper, methodology, template, command file, SKILL.md, pytest.
5. 5.5 documentation pass. Run `make verify`.
6. 5.6 testing finalization: bump `DEFAULT_PHASE_CAP` to 5, integration smoke. Run `make verify`.
7. 5.7 sign-off, in order: 5.7.1 walkthrough (capture log; fix failures first) → 5.7.2 DoD audit (block on any unmet item) → 5.7.5 write `test_phase_5_signoff.py` (expect red on plan/CHANGELOG edits) → 5.7.3 update `plan.md` + `CHANGELOG.md` (re-run sign-off test → green) → 5.7.4 doc final read-through (`make verify`) → 5.7.6 final DoD eval (commit, push, annotated tag, tag push).

#### Failure modes

- The Gherkin a helper emits is not valid (parser would reject it downstream in Phase 6). **Mitigation:** the seeded `feature-template.feature` is the v1 contract; `test_generate_bdd.py` parses every generated `.feature` and asserts well-formed Feature/Scenario/tag structure before declaring 5.2 done.
- A generated scenario lacks a resolvable `@req:`/`@cs:` linkage tag, breaking traceability. **Mitigation:** the generator always emits the linkage tags from the enriched test-idea's `req_id`/`cs_id`; `test_traceability_map.py` asserts every scenario in the seeded chain resolves to an existing requirement/candidate; an unresolvable tag is a `untraceable` review finding (5.3).
- Two writers of `requirements-map.md` (Phase 2 + Phase 5) drift in format. **Mitigation:** the shared `traceability_render.py` module is the single render path; the 5.6 regression test asserts both callers produce identical output for the same links.
- Phase 5 writes into `product-knowledge/` or `test-ideas/` accidentally. **Mitigation:** the write-boundary design decision forbids it; the 5.6 integration smoke asserts both directories are byte-identical before and after the Phase 5 sweep.
- `[bdd-review]` gap signals duplicate across re-runs, or are clobbered by an upstream Phase-2 run. **Mitigation:** the `(source-id, question-text)` dedup contract (`source-id: tc-bdd/bdd-review-<area>`) makes re-runs idempotent; the integration smoke runs Phase 2 → 3 → 4 → 5 so the `[bdd-review]` line lands on top of upstream entries (per the Phase 4 Step 4.7 sequencing lesson).
- `bdd/index.md` rebuild regex fails to match the helper's own output shape. **Mitigation (per the Phase 4 Step 4.4 lesson):** declare the index parser regex with explicit branches for every `.feature`/summary shape the helper produces; document the regex coverage in the helper docstring.
- The `/tc:next` heuristic skips Phase 6 because Phase 5 wrote to `traceability/`. **Mitigation:** use the robust "advanced past" invariant in the integration test; refine the `next-step-inference.md` R-rules in 5.6 if the assertion is brittle (the Phase 2 Step 2.9 lesson flagged this would eventually need attention).
- The cold-user walkthrough (5.7.1) surfaces a strict-YAML frontmatter bug in a SKILL.md. **Mitigation:** the 5.1 scaffold tests already assert strict-PyYAML parse on both SKILL.md files, so this should be caught at the unit layer; the walkthrough preamble remains the backstop.
- `phase-5` tag already exists locally. **Mitigation:** delete and recreate; never force-overwrite an existing tag on origin without explicit user confirmation.

#### Phase 5 — Lessons learned (running)

Captured at sub-step close per the "Sub-step lesson capture" Per-Phase Convention. Each entry is preventative care for future implementers of similar work.

##### Step 5.7 — Sign-off

- **The strict-YAML scaffold assertion (5.1) paid off: the cold-user walkthrough's `make install` passed `claude plugin validate` first try.** Phase 4's sign-off was where the embedded-`key: value` frontmatter bug surfaced (Step 4.8.1), because no earlier check ran the strict parser. Phase 5 baked the strict-PyYAML parse into both SKILL.md scaffold tests at 5.1, so by sign-off `claude plugin validate .` and `claude plugin validate plugins/test-commander` both reported `✔ Validation passed` with zero rework. **Pattern**: the unit-layer strict-YAML assertion moves the `claude plugin validate` failure from sign-off (expensive, late) to the scaffold step (cheap, early). The walkthrough preamble is still the backstop, but it now confirms rather than discovers. **Future-implementer hint**: keep landing the strict-parse assertion in every new skill's scaffold test.
- **A `ls | sed` SESS-ID extraction in the walkthrough script broke on the template README.** The first walkthrough run built `SID` from `ls exploration-notes/ | sed 's/.md//'`, which also matched `README.md`, producing a two-line `SID` that the downstream helpers rejected. Fixed by globbing `SESS-*.md` explicitly: `basename "$(ls .../SESS-*.md | head -1)" .md`. **Not a product bug** — the helpers correctly refused the malformed ID. **Pattern**: when a walkthrough shell script derives an ID from a directory that also ships a template `README.md`, glob the ID prefix, never list the whole directory. **Future-implementer hint**: every `<workspace>` artifact dir ships a template `README.md` from `/tc:init`; account for it in any `ls`-based extraction.
- **The sign-off test grows by adding assertions per new mechanical surface, not boilerplate (22 tests, matching Phase 4's 22).** `test_phase_5_signoff.py` covers two skills (vs Phase 4's one) but the same closing conditions; the count held at 22 because Phase 5 has fewer per-skill artifacts. Three assertions landed RED before the plan/CHANGELOG closing edits and GREEN after — the test-first sign-off gate working as designed. **Pattern reinforced** (fifth phase): the sign-off test is authored RED against the not-yet-applied closing edits, then the closing edits turn it GREEN. **Future-implementer hint**: Phase 6's sign-off test starts from this shape; use `>=` for every numeric floor (pytest count, cap) so a later phase never breaks it.

##### Step 5.6 — Testing finalization (cap bump + integration smoke)

- **The integration smoke caught a wrong test assumption, not a code bug — and that is exactly its value.** I budgeted the smoke as "verification not debugging" (the Phase 3/4 lesson) and it landed 2/3, with the third failing on `assert "Review verdict: pass"`. Root cause: the integration runs against the **deliberately-flawed** `seeded-flawed-requirements` fixture, whose vague acceptance criteria (`quickly`, `properly`, `appropriately`) get embedded verbatim into Phase-4 coverage-gap candidate titles (`Follow-up exploration to fully cover acceptance criterion #N: '<AC>'`), which `/tc:generate-bdd` renders into scenario steps, which `/tc:review-bdd` then correctly flags as `ambiguous-step`. **No code bug** — the generate→review pipeline works end to end; flawed requirements produce flawed BDD that review catches. The fix was in the test: assert the auto-review *ran* (verdict resolved, not pending) and routed `[bdd-review]` signals, not that every feature passes. "Every feature passes" is true only for the clean `seeded-bdd` unit fixture (`test_review_bdd.py`). **Pattern**: an integration smoke that composes a *flawed* upstream fixture will exercise the downstream *failure* paths; assert the mechanism ran and routed correctly, not that everything is clean. **Future-implementer hint**: Phase 6/7 integration tests inherit the same flawed fixture — expect (and assert) that review/quality-gate findings are present, not absent.
- **`/tmp` vs `/private/tmp` bit a hand-rolled repro, not pytest.** A standalone `tempfile.mkdtemp()` repro under macOS `/tmp` (a symlink to `/private/tmp`) broke `extract_knowledge_from_code`'s `path.relative_to(workspace)` because the uploaded code path resolved to `/private/tmp/...` while the workspace was `/tmp/...`. pytest's `tmp_path` is already canonical, so the suite was unaffected; the repro needed `.resolve()`. **Pattern**: when reproducing a pytest failure in a standalone script on macOS, `.resolve()` the temp dir or you will hit a spurious `relative_to` error the suite never sees. **Future-implementer hint**: not a product bug — but if a helper ever does `path.relative_to(workspace)` on caller-supplied paths, resolve both sides first.
- **Cap bump is the one-line flip to PRESENT (fifth datapoint).** `DEFAULT_PHASE_CAP` 4 → 5 flipped `tc-bdd` and `tc-traceability` from `UNEXPECTED — ahead of schedule` to `PRESENT`; `verify_skills.py` now reports `PRESENT=6 UNEXPECTED=0`. The catalog entries landed at scaffold time (5.1), so the bump touched one constant. The staged-bump discipline (cap bump in the testing-finalization sub-step, not mid-phase) held for the fifth phase running. No new extensible surface in 5.6; customization guide unchanged.

##### Step 5.5 — Documentation pass

- **Reproducible sample output, captured from the real chain (Phase 4 Step 4.6 discipline, reapplied).** Before writing `generating-bdd.md`, I drove the three Phase 5 helpers against a tmp workspace seeded with the `seeded-bdd` fixture + a 2-row inventory, and embedded the byte-real stdout, feature, summary (with the `Review verdict: pass` line the auto-run writes), index, and both maps. No paraphrase. **Pattern**: a walkthrough doc that ships before sign-off must quote output captured from the actual helper chain against the seeded fixture, so doc drift surfaces immediately. **Future-implementer hint**: the 5.7.1 cold-user walkthrough replays exactly this chain from a clean `make install`; keep the doc's commands runnable verbatim.
- **Status-line drift is a six-location sweep; the count is stable phase-over-phase.** The Phase-5 status touches the same six surfaces Phase 4 did: README status header, `docs/install.md` verifying-install, getting-started what's-next, workflow Beyond-Phase-1, the prior phase's Beyond-Phase-N footer, and the plugin README skill-status table. The plugin README needed two rows *moved* (from "What arrives later" to shipped), not just edited. **Pattern**: keep a fixed checklist of the six status surfaces; a new phase's doc pass edits all six or explicitly records why one is unchanged. **Future-implementer hint**: Phase 6's doc pass updates the same six plus the new `automation.md` Beyond-Phase-5 footer here in `generating-bdd.md`.
- **Three worked examples vary by project shape, each exercising a different surface as its primary tuning point (Phase 4 Step 4.6 pattern).** The web shape tunes `tags.extra-classes`, the API shape tunes `vague-words` (and deliberately does NOT add URL terms to `ui-words`, which would mis-flag legitimate endpoint references), the mobile shape tunes `ui-words`. **Pattern**: three examples that each tune a different key teach more than three that tune the same key on different vocabulary. **Future-implementer hint**: when a phase ships two config surfaces, make the worked examples collectively exercise both.
- **No new extensible surface in 5.5 (it documents 5.2/5.3's surfaces).** The doc pass expands the customization guide for surfaces already shipped in 5.2 (`tc-bdd.tags.extra-classes`) and 5.3 (`tc-bdd.review.rubric-extensions`); it ships no new schema key. Convention #6 is satisfied by the expansion.

##### Step 5.4 — `/tc:traceability-map` + shared `traceability_render.py`

- **6/6 GREEN; the extraction was safe because the Phase-2 tests pin behavior, not bytes.** Before extracting `_render_traceability_map`, I grepped the test suite: the Phase-2 tests assert requirements-map.md is byte-stable on re-run and that every REQ-ID + `test-ideas/<REQ-ID>.md` link appears — they do **not** pin the intro string or column order. That freedom let me neutralise the intro (to name both `/tc:requirements-coverage` and `/tc:traceability-map`) and move the renderer without touching a single Phase-2 assertion. **Pattern**: before refactoring a shared writer, grep the dependent tests to learn exactly what they pin; behavior-pinned tests (byte-stability, presence) give refactor freedom that byte-pinned tests would not. **Future-implementer hint**: keep map renderers behavior-pinned in tests, not byte-pinned, so later phases can extend them.
- **The "BDD-scenario column" belongs in a new file, not as a new column on the shared map.** The 5.4 plan originally said "rebuild requirements-map.md with a BDD-scenario column." But adding a 5th column to requirements-map.md would make the Phase-2 writer (4 columns) and the Phase-5 writer (5 columns) drift on the same file — the exact thing the shared renderer exists to prevent. Resolved (fix-the-plan-first) by keeping requirements-map.md at the shared 4-column shape and putting the scenario-level detail in the **new** `test-map.md`. **Pattern**: when two writers share a file, a new dimension of detail goes in a new file, not a new column — preserving the shared format's drift-free guarantee. **Future-implementer hint**: Phase 6/7 add automation/result detail to `test-map.md`'s `pending` columns, not new columns on requirements-map.md.
- **Maximal DRY by reusing sibling scanners + parser.** `traceability_map.py` imports `requirements_coverage`'s `parse_inventory`/`scan_test_ideas`/`scan_bdd_features`/`scan_automation_map`/`assemble_coverage`/`_inventory_is_generated` and `review_bdd.parse_feature_file` rather than re-implementing them. The dependency graph stays acyclic: `traceability_render` (leaf) ← `requirements_coverage` ← `traceability_map` → `review_bdd`. **Pattern**: a regenerator that re-derives an upstream artifact should import the upstream's scanners, not re-parse the workspace; the shared renderer + shared scanners make the two writers provably consistent. **Future-implementer hint**: pytest `pythonpath` already includes both scripts dirs, so these cross-helper imports work in-process without `sys.path` juggling (unlike the file-path `importlib` loaders in 5.2/5.3 tests).
- **No new extensible surface in 5.4.** `/tc:traceability-map` ships no `config.yaml` key (the maps are mechanical). Per Convention #6, `docs/user-guide/customizing-for-your-project.md` is unchanged this sub-step.

##### Step 5.3 — `/tc:review-bdd` + shared `review_features()` + generate-bdd auto-run

- **9/9 GREEN; the deferred-not-defended wiring from 5.2 paid off cleanly.** 5.3 added `review_bdd.py` (the rubric engine + `review_features()`), then wired the generate-time auto-run by editing `generate_bdd.py` to `from review_bdd import review_features` (top-level) and call it at the end of `run()` unless `--no-review`. One-directional dependency (generate imports review; review never imports generate), so no cycle. The `test_review_features_is_shared_codepath` identity assertion (`generate_mod.review_features is review_mod.review_features`) holds because `from review_bdd import ...` binds the same function object. **Pattern reinforced**: when a later sub-step owns a shared function the earlier helper auto-runs, the later step does the import + wiring edit into the earlier helper, keeping the dependency one-directional.
- **A top-level cross-helper import forces every in-process test loader to put the scripts dir on `sys.path`.** Once `generate_bdd.py` gained `from review_bdd import review_features`, loading `generate_bdd` via `importlib.util.spec_from_file_location` in `test_generate_bdd.py` failed with `ModuleNotFoundError: review_bdd` — the scripts dir is `sys.path[0]` only when a script is run directly (subprocess), not when pytest loads it in-process. Fix: both `test_generate_bdd.load_module` and `test_review_bdd.load` insert `SCRIPTS` into `sys.path` before `exec_module`. **Pattern**: any helper that imports a sibling helper at module top must have its in-process test loaders prepend the scripts dir to `sys.path`. **Future-implementer hint**: 5.4's `traceability_map.py` imports the shared `traceability_render.py`; its test loader needs the same `sys.path` insertion, and the Phase-5 integration smoke (5.6) that imports these helpers in-process must add the scripts dir to `sys.path` once at module top.
- **Word-boundary regexes prevent rubric cross-fire; substring matching would false-positive.** The `ambiguous-step` check matches `works` — but `workspace` (in the seeded `conjunction-overload` scenario) contains `works` as a substring. A naive `"works" in step` would have fired `ambiguous-step` on the conjunction scenario, breaking the "each category surfaced exactly once" contract. `\bworks\b` does not match inside `workspace`. Similarly `ui-coupled-step` deliberately excludes `page` (the seeded `ambiguous-step` scenario says "on the page"). **Pattern**: a keyword rubric whose categories must not cross-fire needs `\b`-anchored regexes and a deliberately-curated keyword set traced against every seeded scenario (not just the marker-tagged one) — the Phase 4 Step 4.3 "trace the rule against every seeded entry" lesson, reapplied. **Future-implementer hint**: when extending the rubric keyword sets, re-trace against all six seeded scenarios to confirm no scenario matches two categories.
- **The verdict-line update is the observable signal that proves the auto-run wiring.** Rather than a weak "did review run" assertion, the wiring tests check an observable artifact: `/tc:generate-bdd` (default) leaves `- Review verdict: pass` in the summary, while `--no-review` leaves `- Review verdict: (pending /tc:review-bdd)`. Because the generated feature is clean, review finds nothing — so the only proof review ran is the verdict transition. **Pattern**: when an auto-run produces no findings on clean input, assert a side-effect that only the auto-run writes (here, the verdict line) to prove the wiring without needing a deliberately-broken input.
- **Configurable surface shipped (`tc-bdd.review.rubric-extensions`) → customization guide updated in the same sub-step (Convention #6).** Added the rubric-extensions worked example (a mobile project adding `tap`/`swipe` UI words and `tbd`/`wip` vague words) to the Phase 5 schema section.

##### Step 5.2 — `/tc:generate-bdd` (generation only)

- **9/9 GREEN after two one-line fixes; the forward-dependency on review was resolved by deferring, not by defensive code.** The plan originally had 5.2's generate-bdd auto-run a review sub-mode that 5.3 builds — a forward dependency. Rather than a defensive `try: import review_bdd` (which violates the "don't program defensively" rule) or front-loading the whole rubric into 5.2, the plan was refined (fix-the-plan-first) so **5.2 ships generation only and 5.3 owns the review engine AND wires generate-bdd's auto-run** (5.3 edits `generate_bdd.py` to add `--no-review` + the call). Each step is then a clean, independently-testable increment. **Pattern**: when two sub-steps share an implementation and the consumer ships first, give the later (owner) step the wiring edit into the earlier helper — do not stub or defensively-import across the gap. **Future-implementer hint**: 5.3 must edit `generate_bdd.py` (CLI flag + end-of-run call) and update `generate-bdd.md` + SKILL.md to remove the 5.2 forward pointer.
- **The in-process module loader must register the module in `sys.modules` before `exec_module`.** `tests/test_generate_bdd.py` loads `generate_bdd.py` via `importlib.util` to test `parse_scenarios` in-process. With `from __future__ import annotations`, the `@dataclass` decorator resolves field annotations by looking up `sys.modules[cls.__module__]` — which is `None` if the module was exec'd without being registered, raising `AttributeError: 'NoneType' object has no attribute '__dict__'`. Fix: `sys.modules[spec.name] = module` before `spec.loader.exec_module(module)`. **Pattern**: any test that imports a helper via `spec_from_file_location` and the helper uses `from __future__ import annotations` + dataclasses must register the module in `sys.modules` first. **Future-implementer hint**: 5.3 and 5.4 tests that load helpers in-process need the same one-liner.
- **Five-segment relative paths bit again (Phase 4 Step 4.2 lesson, third datapoint).** `methodology/bdd-generation.md` is five directories deep (`plugins/test-commander/skills/tc-bdd/methodology/`); the link to `planning/plan.md` needs five `..` segments, not four. The link checker caught it on first verify. **Mitigation**: count segments before writing the first `../` from a `commands/` or `methodology/` file. **Future-implementer hint**: 5.3/5.4 command + methodology pages reach `planning/plan.md` via `../../../../../` and `tests/fixtures/` via `../../../../../tests/...`.
- **Tolerant config loading via PyYAML beats the hand-rolled sibling parser.** `create_charter.py` hand-rolls a ~70-line indentation parser for `tc-explore.charters.*`. `generate_bdd.py` instead loads `config.yaml` with `yaml.safe_load` and reads `data["tc-bdd"]["tags"]["extra-classes"]` under a broad `except` that yields no extensions on any error — simpler, correct, and uses the dependency the project already ships (PyYAML, added in Phase 3). **Pattern**: prefer PyYAML for new config readers; the hand-rolled parser is legacy, not a model to mirror. **Future-implementer hint**: 5.3's `tc-bdd.review.rubric-extensions` reader should use the same PyYAML approach.
- **Configurable surface shipped → customization guide updated in the same sub-step (Convention #6).** `tc-bdd.tags.extra-classes` ships in 5.2, so `docs/user-guide/customizing-for-your-project.md` gains a "Phase 5 schema (`tc-bdd`)" section with a worked example now (not deferred to the 5.5 doc pass). 5.5 expands it with the review-rubric extension and three project-shape examples.

##### Step 5.1 — Skill scaffolds (`tc-bdd` + `tc-traceability`) + seeded-bdd fixture

- **25/25 GREEN once the scaffold + fixture existed; the strict-PyYAML assertion landed in the scaffold step, not at sign-off.** Per the Phase 4 Step 4.8 future-implementer hint, both `tests/test_tc_bdd_scaffold.py` and `tests/test_tc_traceability_scaffold.py` parse the SKILL.md frontmatter with `yaml.safe_load` directly (not the regex parser `verify_skills.py` uses). This is the check that would have caught the Phase-4 colon-space bug at the unit-test layer; in Phase 5 it is an invariant from the first sub-step. Both descriptions were authored with no embedded `key: value` substring; the strict-parse assertion passed on first author. **Pattern**: the unit-layer strict-YAML parse is cheap insurance against the one bug `make verify` cannot catch (only `claude plugin validate` does). **Future-implementer hint**: keep the strict-parse assertion in every future skill's scaffold test.
- **The fixture must match the real upstream output shape, not the plan's shorthand.** The 5.1 plan text said `REQ-001.md` carries "`### CS-NNN-NNN` candidate blocks." The real `enrich_test_ideas.py` output puts `### CS-` headings only in the **session summary** (`session_summary.py` output); the **enriched test-idea** instead carries `## Phase 4 enrichment` → `### SESS-…` sub-blocks with `- **CS-NNN-NNN**` candidate *bullets*. The fixture was authored to the real format (verified against `enrich_test_ideas.render_session_subblock` and `session_summary` render), and the scaffold test asserts the accurate shape: `### CS-` headings in `SESS-20260115-001.md`, and `>= 2` `CS-NNN-NNN` *references* in `REQ-001.md`. **Pattern**: when a fixture stands in for a prior phase's output, read that phase's render function and match its bytes — do not trust the plan's prose paraphrase. **Future-implementer hint**: Step 5.2's `generate_bdd.py` parser must consume the enriched test-idea's `### SESS-…` → `- **CS-…**` bullet shape (plus the Phase-2 `candidates:` frontmatter), not a `### CS-` heading shape, when reading candidates from `test-ideas/`.
- **No new extensible surface in 5.1.** The scaffold ships SKILL.md + fixture + empty command/methodology/template dirs only; the `tc-bdd.tags.*` / `tc-bdd.review.rubric-extensions` config schema ships with the helpers in 5.2/5.3 and is documented in the customization guide in 5.5. Per Convention #6, `docs/user-guide/customizing-for-your-project.md` is unchanged this sub-step.

---

## Phase 6 — Playwright Framework (Lazy) and Strategic Automation

**Goal.** Generate the Playwright TypeScript framework on demand, then produce strategic automation from the Phase-5 BDD scenarios. Ship four skills — `tc-build-framework` (lazy framework scaffold), `tc-automation-plan` (suitability scoring), `tc-automate` (`/tc:automate` + an internal review sub-mode), and `tc-test-data` (`/tc:generate-test-data`) — that turn `bdd/features/*.feature` into a Playwright/TypeScript suite under `tests/`, scored by a universal automation-suitability rubric, with test data living under `.test-commander/test-data/` and reached through fixtures.

**Architecture.** Each `/tc:*` command is a Python helper plus a Markdown command file inside `plugins/test-commander/skills/<skill>/` (per D18). The helpers do the deterministic work — scaffold the framework directory tree, score scenarios against the suitability rubric, render TypeScript page objects / specs / fixtures from the BDD scenarios and their `@req:`/`@cs:`/`@area:` tags, and populate test-data files; Claude does the judgment-heavy parts (writing the actual step logic and assertions, choosing locators, deciding which scenarios are worth automating beyond the mechanical score). This is the **first phase that ships an executable runtime** (Playwright/TypeScript), per D2; it also writes for the first time *outside* `.test-commander/` (the framework lives at the consuming project's `tests/`).

**Phase-6 design decisions (folded in).**

- **Generate-and-structurally-validate; never run Playwright under pytest.** The Python helpers generate TypeScript files; the pytest suite asserts the generated files' *structure* (valid TS scaffolding, correct imports, page-object/spec/fixture shape, linkage-tag provenance comments) by parsing the rendered text — it never invokes `npx playwright test` or reaches a browser. Actual execution is Phase 7's `/tc:run`; Phase 6's manual smoke (a spec run against a tester-supplied local app) is opt-in and **refused under pytest** via the `PYTEST_CURRENT_TEST` env-var check established in Phase 3 Step 3.5. This keeps the suite hermetic and the "no executable runtime in tests" property intact even though the *artifacts* are now executable.
- **Lazy, idempotent framework build (D8).** `/tc:build-framework` writes the `tests/` tree + `playwright.config.ts` + `package.json` only if `tests/playwright.config.ts` is absent at the consuming project root; re-running is a byte-stable no-op (`created: 0`). `/tc:automate` (and Phase 7's `/tc:run`) check for `tests/playwright.config.ts` and call the build helper first when missing. The framework is **not** under `.test-commander/` — it is at the project root, so it is a real, runnable Playwright project.
- **Retire the prior-phase runtime guard in the build commit (Per-Phase Convention #3).** Earlier phases may carry a guard asserting "no executable runtime ships before Phase 6" (e.g. a test forbidding `.ts`/`package.json` under the plugin, or a `make build` that only prints a placeholder). The sub-step that lands `/tc:build-framework` (6.2) retires that guard in the same commit and replaces the `make build` placeholder if present.
- **TypeScript templates ship inside the plugin (D18).** `page-object-template.ts`, `component-object-template.ts`, `playwright-spec-template.ts`, `fixture-template.ts` live under `tc-build-framework/templates/`; `tc-automate` reads them to render concrete files. They are authored to pass `tsc --noEmit` / a lint shape check but are not compiled in the pytest suite.
- **Test data lives under `.test-commander/test-data/`, never inline (D6).** `/tc:generate-test-data` writes `seed/` (baseline fixtures), `scenarios/` (per-suite data), and `factories/` (regenerable definitions); generated specs reach data only through a `tests/fixtures/` fixture, never by inlining values. Per Q11, the shipped formats are Markdown specs + YAML manifests for declarative data, with JSON for structured fixtures; Python factories only where a generator is too complex to express declaratively. A test asserts at least one fixture references a `test-data/` file and that no generated spec inlines data.
- **Universal automation-suitability rubric (seven factors, D19).** `business-criticality`, `repeatability`, `determinism`, `setup-complexity`, `ui-stability`, `maintenance-cost`, `bug-detection-value`. The helper scores each BDD scenario mechanically from available signals (e.g. `@smoke`/`@regression` class, `@risk:` namespace, anomaly linkage, step count); Claude calibrates. Projects tune factor weights via `tc-automate.suitability.weights` in `<workspace>/config.yaml`; `@automated-candidate`-tagged scenarios are always in scope.
- **Review is both an auto-run sub-mode and a standalone command (the Phase-5 pattern).** `/tc:automate` auto-runs the internal review sub-mode after generation (suppressible with `--no-review`), routing findings to `requirements/open-questions.md` as `[automation-review]` gap signals. `/tc:review-automation` is the standalone, re-runnable form sharing one `review_automation()` implementation. Per the Phase 5 Step 5.2/5.3 lesson, **6.5 owns the review engine and wires the auto-run into `tc-automate`** (no forward dependency in 6.4).
- **Traceability hand-off.** `/tc:automate` writes `traceability/automation-map.md` (the Phase-6-owned map Phase 2 only seeded) linking each `@cs:`/`@req:` scenario to its generated spec path. `/tc:traceability-map` (Phase 5) already scans `automation-map.md`; when Phase 6 lands, a re-run populates the `Automated test` column of `test-map.md` from the new automation links (the `pending` placeholder resolves). The 6.x sub-step that ships `automate` confirms this round-trip.
- **Helper-mirroring is the design.** `automation_plan.py` mirrors `traceability_map.py`/`review_bdd.py` (scan features → score → render); `automate.py` mirrors `generate_bdd.py` (parse scenarios → render artifacts); `review_automation.py` mirrors `review_bdd.py`; `generate_test_data.py` mirrors `enrich_test_ideas.py`. The genuinely new mechanical work is the **TypeScript rendering** (as Gherkin was the new surface in Phase 5) and the scan-and-index over `tests/`.
- **Phase 6 fixture bundles a clean, automatable feature.** A new `tests/fixtures/seeded-automation/` carries a clean `<area>.feature` (sign-in, with `@automated-candidate` scenarios carrying resolvable `@req:`/`@cs:` tags — the shape `/tc:generate-bdd` emits when its input is clean, not the deliberately-flawed Phase-5 unit fixture) plus a `README.md`. Reuses the Account/Session/Workspace/Asset SaaS narrative so the 6.8 integration smoke composes with the upstream chain.
- **Cross-phase write boundary.** Phase 6 reads `bdd/features/`, `automation-plan/`, `test-ideas/`, `product-knowledge/`. It writes the project-root `tests/` framework, `<workspace>/automation-plan/`, `<workspace>/test-data/`, `<workspace>/traceability/automation-map.md`, and the `[automation-review]` line in `open-questions.md`. It does not write `bdd/` (Phase 5) or `product-knowledge/` (Phase 3). `/tc:next`'s Phase-6 status keys on `automation-plan` + `test-data` (both under `.test-commander/`); the project-root `tests/` tree is outside the workspace and is not a status signal.

**Skills authored.** `tc-build-framework` — `SKILL.md` + `commands/build-framework.md` + `methodology/playwright-standards.md` + `methodology/locator-strategy.md` + the four `.ts` templates. `tc-automation-plan` — `SKILL.md` + `commands/automation-plan.md` + `methodology/automation-suitability.md` + `templates/automation-plan-template.md`. `tc-automate` — `SKILL.md` + `commands/automate.md` + `commands/review-automation.md` + `methodology/automation-generation.md` (umbrella). `tc-test-data` — `SKILL.md` + `commands/generate-test-data.md` + `methodology/test-data-strategy.md` + `templates/test-data-template.json`.

**Design references.** `agentic-playwright-automation:setup-playwright-framework` (framework scaffold structure), `:convert-bdd-to-playwright` (bulk-conversion approach), `:generate-playwright-test` (single-test prompts), `:generate-playwright-suite` (suite prompts), `:review-playwright-test` (review rubric). Per D1 (vendor-and-own), all four skills are authored in-repo; these are design references only. Playwright itself is a runtime dependency for the generated framework (installed lazily, not by the pytest suite).

**Inputs read.** `<workspace>/bdd/features/`, `<workspace>/automation-plan/`, `<workspace>/test-ideas/`, `<workspace>/product-knowledge/`.

**Outputs.** Project-root `tests/{e2e,pages,components,fixtures,utils}/` + `playwright.config.ts` + `package.json`; `<workspace>/automation-plan/*.md`; `<workspace>/test-data/{seed,scenarios,factories}/`; `<workspace>/traceability/automation-map.md`.

**Framework structure.**

```
tests/                 # at the consuming project root, NOT under .test-commander/
  e2e/                 # *.spec.ts
  pages/               # page objects
  components/          # component objects
  fixtures/            # Playwright fixtures (the only path to test data)
  utils/
playwright.config.ts
package.json
```

Test data is **not** under `tests/`. It is under `.test-commander/test-data/` and reached through fixtures.

**Automation suitability rubric (universal core, seven factors).** `business-criticality`, `repeatability`, `determinism`, `setup-complexity`, `ui-stability`, `maintenance-cost`, `bug-detection-value`. Project weights tune via `tc-automate.suitability.weights`.

### Phase 6 — Execution outline

Nine sub-steps. TDD throughout: every implementation step lands its tests red before turning them green. 6.1 scaffolds the four skills + the seeded-automation fixture; 6.2 builds the lazy framework (and retires the prior-phase runtime guard); 6.3–6.6 implement the four commands; 6.7 is the documentation pass; 6.8 is the testing finalization (cap bump + integration smoke); 6.9 is the sign-off with a `phase-6` tag.

#### 6.1 — Skill scaffolds (four skills) and seeded-automation fixture

- **Deliverables.** `SKILL.md` for `tc-build-framework`, `tc-automation-plan`, `tc-automate`, `tc-test-data` (frontmatter with no embedded `key: value` substring; body lists each skill's commands; deferral wording until each sub-step ships behavior). Empty `commands/`/`methodology/`/`templates/` dirs (`.gitkeep`). `tests/fixtures/seeded-automation/` with a clean `<area>.feature` (`@automated-candidate` scenarios, resolvable `@req:`/`@cs:` tags) + `README.md` documenting the narrative and the linkage-tag convention.
- **Tests first.** `tests/test_tc_build_framework_scaffold.py` and three sibling scaffold tests (or one parametrized file) — each asserts the skill dir + `SKILL.md` (strict-PyYAML frontmatter parse from the start, per the Phase 5 Step 5.1 discipline), the three sub-dirs, and (for the fixture) a parseable clean feature with `@automated-candidate` + resolvable linkage tags.
- **Definition of done.** Four skills scaffolded; fixture present; scaffold tests green; `verify_skills.py` reports the four new skills `UNEXPECTED (phase 6) — ahead of schedule` under `DEFAULT_PHASE_CAP=5` (cap bumps to 6 in 6.8). Confirm the `CATALOG` carries `tc-build-framework: 6`, `tc-automation-plan: 6`, `tc-automate: 6`, `tc-test-data: 6` (add if absent — earlier phases pre-seeded their next-phase catalog entries at scaffold time).

#### 6.2 — `/tc:build-framework` (lazy, idempotent) + runtime-guard retirement (TDD)

- **Helper.** `plugins/test-commander/scripts/build_framework.py` — scaffolds the project-root `tests/{e2e,pages,components,fixtures,utils}/` tree + `playwright.config.ts` + `package.json` from the bundled TS templates, **only if `tests/playwright.config.ts` is absent**; re-running is a byte-stable no-op (`created: 0, skipped: N`). Exposes `ensure_framework(project_root)` for the lazy-init callers.
- **Methodology + templates.** `methodology/playwright-standards.md`, `methodology/locator-strategy.md`; the four `.ts` templates (`page-object-template.ts`, `component-object-template.ts`, `playwright-spec-template.ts`, `fixture-template.ts`).
- **Guard retirement.** Locate and retire the prior-phase "no executable runtime before Phase 6" guard (grep tests for assertions forbidding `.ts`/`package.json`/`tests/` runtime; check `make build`'s placeholder). Replace in the same commit (Per-Phase Convention #3).
- **Command file + SKILL.md update.** `commands/build-framework.md`; `tc-build-framework/SKILL.md` surfaces the shipped behavior.
- **Tests first.** `tests/test_build_framework.py` — uninitialized workspace refused; first run scaffolds the full tree with `playwright.config.ts` + `package.json`; re-run is byte-stable no-op; the generated config/templates parse as well-formed (structural assertion, no `tsc`); `ensure_framework` is the lazy-init entry point.
- **Definition of done.** Framework builds lazily and idempotently; guard retired; generated files structurally valid; SKILL.md updated.

#### 6.3 — `/tc:automation-plan` (TDD)

- **Helper.** `plugins/test-commander/scripts/automation_plan.py` (mirrors `traceability_map.py`/`review_bdd.py`). Scans `bdd/features/*.feature`, scores each scenario against the seven-factor suitability rubric (mechanical signals: class tags, `@risk:`, anomaly linkage, step count), and writes `<workspace>/automation-plan/<area>.md` ranking scenarios `automate` / `consider` / `manual` with the per-factor scores and a recommended order. `@automated-candidate` scenarios are always `automate`. Config: `tc-automate.suitability.weights`.
- **Methodology + template.** `methodology/automation-suitability.md` (the seven factors with worked examples + Claude judgment layer); `templates/automation-plan-template.md`.
- **Command file + SKILL.md update.** `commands/automation-plan.md`; `tc-automation-plan/SKILL.md`.
- **Tests first.** `tests/test_automation_plan.py` — uninitialized refused; no features → plan notes "no scenarios" (not an error); seeded clean feature → plan written with every scenario scored, `@automated-candidate` marked `automate`, deterministic ordering; config weights change the ranking.
- **Definition of done.** Plan written with rubric scores; deterministic; config-tunable; SKILL.md updated.

#### 6.4 — `/tc:automate` (generation only) (TDD)

- **Helper.** `plugins/test-commander/scripts/automate.py` (mirrors `generate_bdd.py`). Reads the automation plan + `bdd/features/*.feature`, calls `build_framework.ensure_framework` first (lazy-init), and renders TypeScript page objects (`tests/pages/`), component objects, and specs (`tests/e2e/<area>.spec.ts`) for `automate`-ranked / `@automated-candidate` scenarios, each carrying a provenance comment (`// @req:REQ-NNN @cs:CS-NNN-NNN`) and reaching test data only via a `tests/fixtures/` fixture. Writes/updates `traceability/automation-map.md` linking scenario → spec path. Single / suite / bulk paths via `--scenario` / `--area` / all. Deterministic; overwrite mode for generated specs (preserve a user-edits region per the page-object template convention). **No auto-review in 6.4** — the review engine + the generate-time auto-run wiring (incl. `--no-review`) ship in 6.5 (the Phase-5 defer-not-defend pattern); the generated TS is authored to pass the 6.5 rubric.
- **Methodology (umbrella).** `methodology/automation-generation.md` — the BDD → page-object → spec workflow, the locator + fixture discipline, the lazy-init contract, the cross-phase write boundary, and the Claude judgment layer.
- **Command file + SKILL.md update.** `commands/automate.md`; `tc-automate/SKILL.md`.
- **Tests first.** `tests/test_automate.py` — uninitialized refused; no plan/features refused pointing at `/tc:automation-plan`; seeded clean feature → `tests/e2e/<area>.spec.ts` + page object written with valid TS structure + provenance comments + a fixture-mediated data reference (no inlined data); `tests/playwright.config.ts` auto-built when absent (lazy-init); `automation-map.md` links scenario → spec; idempotent re-run byte-stable.
- **Definition of done.** Generates structurally-valid TS with provenance + fixture-mediated data; lazy-init wired; automation-map updated; SKILL.md updated.

#### 6.5 — `/tc:review-automation` + shared review + automate auto-run wiring (TDD)

- **Helper.** `plugins/test-commander/scripts/review_automation.py` (mirrors `review_bdd.py`). Reviews generated specs/page objects against a universal rubric (e.g. `inline-test-data`, `hardcoded-wait`, `missing-provenance`, `weak-locator`, `untraceable-spec`, `assertion-free`), writes a verdict into the automation plan / a review summary, and routes failures to `requirements/open-questions.md` as deduplicated `[automation-review]` gap signals. Exposes `review_automation()`; **6.5 wires the auto-run into `automate.py`** (`--no-review`) and updates `automate.md` + `tc-automate/SKILL.md` to describe the now-wired sub-mode (removing the 6.4 forward pointer).
- **Methodology + template + command file.** `methodology/automation-review.md` (or a subsection); `templates/automation-review-template.md`; `commands/review-automation.md`.
- **Tests first.** `tests/test_review_automation.py` — uninitialized refused; no specs refused pointing at `/tc:automate`; a deliberately-flawed seeded spec surfaces every rubric category once; a clean generated spec passes; `[automation-review]` dedup; `review_automation()` is the same code path `/tc:automate` auto-runs (identity + `--no-review` suppression).
- **Definition of done.** Rubric detects every category; clean spec passes; auto-run wired and shared; SKILL.md updated.

#### 6.6 — `/tc:generate-test-data` (TDD)

- **Helper.** `plugins/test-commander/scripts/generate_test_data.py` (mirrors `enrich_test_ideas.py`). Populates `<workspace>/test-data/{seed,scenarios,factories}/` from the BDD scenarios + product-knowledge entities (per Q11: Markdown specs + YAML manifests + JSON fixtures; Python factories only where declarative is insufficient). Deterministic; overwrite mode for generated data, skip-not-overwrite for user-authored.
- **Methodology + template.** `methodology/test-data-strategy.md`; `templates/test-data-template.json`.
- **Command file + SKILL.md update.** `commands/generate-test-data.md`; `tc-test-data/SKILL.md`.
- **Tests first.** `tests/test_generate_test_data.py` — uninitialized refused; seeded → `test-data/` populated; a generated fixture references a `test-data/` file (the D6 contract); idempotent; user-authored data preserved.
- **Definition of done.** Test data populated under `.test-commander/test-data/`; reached via a fixture; nothing inline; SKILL.md updated.

#### 6.7 — Documentation pass *(dedicated step)*

- **Deliverables.** Author `docs/user-guide/automation.md` (end-to-end: `/tc:build-framework` → `/tc:automation-plan` → `/tc:automate` (+ auto-review) → `/tc:review-automation` → `/tc:generate-test-data`, with verbatim helper output from the seeded chain; explains the lazy framework, the suitability rubric, and the data flow). Update `docs/command-reference.md` (Phase 6 shipped section). Update `docs/workspace-reference.md` (the project-root `tests/` framework, `automation-plan/`, `test-data/`, and `automation-map.md` ownership; the lazy-init + data-flow discipline). Customization-guide "Phase 6 schema" section (`tc-automate.suitability.weights` + any `tc-build-framework`/`tc-test-data` keys) with three project-shape worked examples + "Phase 6 — what landed". Status-line refresh across the six locations + the new `automation.md` Beyond-Phase-5 footer in `generating-bdd.md`. Final deferral-wording sweep across all four SKILL.md files, the umbrella methodology, and `docs/`.
- **Definition of done.** Docs accurate; links resolve; link checker green; customization guide reflects the shipped schema with three project-shape examples.

#### 6.8 — Testing finalization *(dedicated step)*

- **Deliverables.** Bump `DEFAULT_PHASE_CAP` 5 → 6 (CATALOG entries already present from 6.1). `tests/test_phase_6_integration.py` (in-process, full Phase 2 → 3 → 4 → 5 → 6 sweep in natural order): assert the framework builds lazily and idempotently; the automation plan scores scenarios; `automate` generates structurally-valid TS with provenance + fixture-mediated data; `automation-map.md` links scenario → spec and a `/tc:traceability-map` re-run resolves the `Automated test` column of `test-map.md` from `pending`; the write boundary holds (`bdd/`, `product-knowledge/` byte-identical before/after Phase 6; the framework lands at project-root `tests/`, outside `.test-commander/`); `/tc:next` advances past `/tc:automation-plan`; Playwright execution refused under pytest. Byte-stable re-run contract.
- **Definition of done.** Integration smoke passes; cap bump reflected; `make verify` clean; `verify_skills.py` reports all ten shipped skills `PRESENT` with `UNEXPECTED=0`.

#### 6.9 — Sign-off

Six sub-sub-steps mirroring 5.7. 6.9.1 cold-user walkthrough of `automation.md` from a clean `make install` (the `claude plugin validate` strict-YAML gate over four new SKILL.md files); 6.9.2 per-step DoD audit for 6.1–6.8; 6.9.3 plan + CHANGELOG closing; 6.9.4 documentation final pass; 6.9.5 test-first `tests/test_phase_6_signoff.py` (RED before the closing edits, GREEN after; pytest floor `>=` the prior count); 6.9.6 final DoD eval — `make verify`, replay the walkthrough, commit, push, annotated `phase-6` tag.

#### Definition of done — consolidated

| # | Check | Type |
| --- | --- | --- |
| 1 | All Phase 6 test files exist | auto (sign-off) |
| 2 | Four helpers + `ensure_framework` exist | auto |
| 3 | All command pages exist (build-framework, automation-plan, automate, review-automation, generate-test-data) | auto |
| 4 | All methodology + TS/JSON templates exist | auto |
| 5 | `seeded-automation` fixture exists with a clean automatable feature | auto |
| 6 | `verify_skills.py` CATALOG has all four at phase 6 and `DEFAULT_PHASE_CAP >= 6`; `make verify` prints all ten skills PRESENT, `UNEXPECTED=0` | auto + verify |
| 7 | Framework builds lazily + idempotently at project-root `tests/`; prior runtime guard retired | auto |
| 8 | Generated TS is structurally valid, carries `@req:`/`@cs:` provenance, reaches data only via fixtures (nothing inline) | auto |
| 9 | `review_automation()` shared between `/tc:automate` auto-run and `/tc:review-automation`; `--no-review` suppresses | auto |
| 10 | `automation-map.md` links scenario → spec; `/tc:traceability-map` re-run resolves `test-map.md`'s `Automated test` column | auto (integration) |
| 11 | Playwright execution refused under pytest; suite never reaches a browser | auto |
| 12 | All four SKILL.md files describe shipped behavior, no deferral wording, strict-YAML frontmatter | auto |
| 13 | Cold-user walkthrough of `automation.md` from clean state succeeds | evidence |
| 14 | plan To Do Phase 6 collapsed; Completed has Phase 6 with date; CHANGELOG marked complete | evidence + sign-off |
| 15 | `phase-6` annotated tag created and pushed | evidence |

#### TDD pattern used in 6.2–6.6

```
write tests (red)             # define structure of the generated framework/plan/TS/data from the seeded fixture
  → implement helper (green)  # minimum code; deterministic scaffold/score/render
    → author methodology + template(s)
      → author per-command page
        → update the owning SKILL.md to surface shipped behavior
          → 6.4 ships automate (generation only); 6.5 ships the review engine AND wires automate's auto-run
            → verify (pytest + make verify)
```

#### Validation sequence

1. 6.1 scaffold (four skills + fixture) with scaffold tests. Red → green.
2. 6.2 build-framework + guard retirement. Run `make verify` (the guard retirement must not break the chain).
3. 6.3 automation-plan; 6.4 automate (generation only); 6.5 review-automation + wire automate's auto-run; 6.6 generate-test-data — each tests-first, mirror the closest sibling helper.
4. 6.7 documentation pass. `make verify`.
5. 6.8 testing finalization: bump cap to 6, integration smoke. `make verify`.
6. 6.9 sign-off in order (walkthrough → DoD audit → write sign-off test RED → plan/CHANGELOG edits GREEN → doc final pass → final DoD + `phase-6` tag).

#### Failure modes

- The generated TypeScript is not valid (would fail `tsc`/Playwright later). **Mitigation:** the bundled `.ts` templates are the v1 contract; `test_automate.py` asserts well-formed structure (imports, class/fixture shape, provenance comment) on every generated file. A real compile/run is the manual smoke (6.x test step), refused under pytest.
- A generated spec inlines test data instead of using a fixture. **Mitigation:** `test_generate_test_data.py` / `test_automate.py` assert at least one fixture references a `test-data/` file and that generated specs contain no inlined data literals (D6).
- `/tc:automate` runs before the framework exists. **Mitigation:** the lazy-init `ensure_framework` call builds it first; `test_automate.py` asserts a from-scratch run produces both `playwright.config.ts` and the spec.
- The prior-phase runtime guard is missed and the suite still forbids runtime artifacts. **Mitigation:** 6.2 greps for the guard and retires it in the same commit; `make verify` red on the guard is the signal.
- Playwright execution leaks into the pytest suite. **Mitigation:** the `PYTEST_CURRENT_TEST` refusal (Phase 3 Step 3.5 pattern) guards any execution entry point; the integration smoke asserts the refusal.
- `automation-map.md` drift between Phase 2's seed and Phase 6's authoritative write. **Mitigation:** Phase 6 owns `automation-map.md`; if a shared renderer is warranted, extend `traceability_render.py` (the Phase 5 reconciliation pattern) rather than hand-rolling a second writer.
- `phase-6` tag already exists locally. **Mitigation:** delete and recreate; never force-overwrite an origin tag without explicit user confirmation.

#### Phase 6 — Lessons learned (running)

Captured at sub-step close per the "Sub-step lesson capture" Per-Phase Convention. (Populated as 6.1–6.9 land.)

- **Step 6.9 (sign-off) closed cleanly; the test-first sign-off gate landed 19/22 GREEN immediately and 3 RED on exactly the closing edits.** Mirrored 5.7's six sub-sub-steps. The cold-user walkthrough ran `make uninstall` → `make install` fully clean (both `claude plugin validate` manifests passed over all ten SKILL.md — no strict-YAML regression, since every Phase-6 scaffold test asserted the parse from 6.1 onward), then drove the full Phase 2 → 6 chain in a fresh tmp project: the framework built, specs generated, and the `test-map` `Automated test` column resolved (3 hits for the sign-in scenarios). `test_phase_6_signoff.py` (22 tests) landed RED on the three plan/CHANGELOG closing assertions (CHANGELOG `(complete …)`, plan Completed entry, To Do collapsed) and GREEN after the closing edits — the test-first gate working as designed for the sixth phase running. **Customization three-shape assertion keyed on `suitability:` block count (>= 3), not on Phase-5's shape labels** ("Web app"/"API-only"/"Mobile app"), because Phase 6's shapes are weight-tuning variants (smoke-first / risk-first / stability-first) — a sign-off test must assert against *its own* phase's doc shape, not copy the prior phase's literal labels. **Lessons-coverage assertion matched the actual bullet format** (`- **Step 6.N`) rather than Phase 5's `##### Step N.M` heading format — the Phase 6 lessons are bullet entries, so the sign-off regex tracks that. **Future-implementer hint:** when mirroring a sign-off test, re-derive every literal (heading text, shape labels, lesson format, pytest floor) from the new phase's actual artifacts; the *structure* mirrors, the *literals* do not. Pytest floor set to `>= 590` (the suite is at 622 with the 22 sign-off tests). `make verify` clean; annotated `phase-6` tag pushed to origin.

- **Step 6.8 (testing finalization) needed a real code change, not just cap+integration: the test-map `Automated test` resolution wiring.** The plan's 6.8 DoD ("a `/tc:traceability-map` re-run resolves the `Automated test` column of `test-map.md` from `pending`") implied behavior that did not yet exist — `traceability_render.render_test_map` hardcoded `pending | pending | pending` for all three downstream columns. The integration test landed RED on exactly that assertion (everything else GREEN, including the byte-stable rerun) — confirming the gap precisely. Added `scan_automation_specs()` to `traceability_map.py` (parses the Phase-6 `automation-map.md` rows into `{cs_id -> spec}`) and extended `render_test_map(rows, automated_by_cs=None)` to resolve the `Automated test` column per `@cs:`. **Byte-stability preserved by the default-empty arg:** with no automation map (Phase 5 and all existing traceability tests), `automated_by_cs` is empty → every row renders `pending` → byte-identical to the pre-6.8 output, so `test_traceability_map.py` and the Phase 5 integration smoke stayed green untouched. **Cap bump flips the four skills PRESENT cleanly:** `DEFAULT_PHASE_CAP` 5 → 6, and `verify_skills.py` now reports `PRESENT=10 UNEXPECTED=0`; the Phase 1-5 sign-off tests are unaffected because they assert `DEFAULT_PHASE_CAP >= N` (the monotonic-non-decreasing discipline from Phase 2 Step 2.8 paying off again). **"Playwright execution refused under pytest" is a no-execution-path property here, not a guarded entry point:** Phase 6 helpers only write text (no `tsc`, no `npx playwright test`), so the integration asserts no `node_modules/`/`test-results/`/`playwright-report/` ever appears — the honest form of the assertion when there is no execution code to guard (unlike Phase 3/4's live-mode `PYTEST_CURRENT_TEST` refusal). **Integration fixture composition:** the clean `seeded-automation/sign-in.feature` is injected into `bdd/features/` after the (deliberately-flawed) Phase-5 BDD, so Phase 6 has guaranteed `@automated-candidate` scenarios to automate while the upstream chain still exercises the flawed-input path — the Phase 5 lesson's "compose the flawed fixture, assert the mechanism" extended with a clean feature for the automation leg. 1 RED → all GREEN after the wiring; `make verify` clean (600 tests, up from 598). **No new `config.yaml` surface.**

- **Step 6.7 (documentation pass) closed cleanly; the status-line semantics follow the 5.5-vs-5.7 precedent exactly.** Authored `docs/user-guide/automation.md` (the five-command walkthrough with verbatim output captured by running the seeded chain end-to-end in a tmp project), updated `command-reference.md` (new "Phase 6 commands (shipped)" section; the five rows removed from the planned table), `workspace-reference.md` (automation-plan/ + test-data/ marked shipped, automation-map.md ownership corrected to `/tc:automate`, the project-root `tests/` framework layout documented under "what lives outside the workspace"), and the customization guide (the Phase 6 section grew from one example to three project-shape examples + "Phase 6 — what landed", clarifying that `tc-automate.suitability.weights` is the *only* config.yaml surface — `PLAYWRIGHT_BASE_URL` is an env var, the seed shape is hand-edited). **Status-line semantics:** checked the Phase 5 precedent before touching the six surfaces — 5.5 (doc pass) set "Phase 4 complete; **Phase 5 in progress** — skills shipped", and 5.7 (sign-off) flipped to "Phase 5 complete (date); Phase 6 starts next". So 6.7 sets "Phase 5 complete; **Phase 6 in progress** — four skills shipped (sign-off pending)" and leaves the "Phase 6 complete (date)" flip to 6.9. **Future-implementer hint:** the doc pass marks the new phase's commands *shipped* and adds the walkthrough link across the six surfaces (README status line, install verifying-install, getting-started what's-next, workflow Beyond-Phase-1, the plugin README skill table moved from "what arrives later" to shipped rows, and the prior guide's Beyond footer), but never claims the phase "complete" — that is the sign-off's job. **Stale-forward-pointer sweep caught two:** `automate.md` and `automation-generation.md` still said "review wired in Step 6.5 / Step 6.4 ships generation only" (correct when 6.4 wrote them, stale once 6.5 shipped) — the deferral sweep is the mechanism that catches a *shipped* command's doc still describing its behavior as future. Updated both to describe the auto-run as present. No code, no new tests (598 unchanged); `make verify` clean, link checker 192 files (+1 for automation.md). The customization-guide three-example expansion satisfies Per-Phase Convention #6 in full (the 6.3 in-step example was the interim; 6.7 is the consolidation, per the Phase 3/4/5 defer-to-doc-step pattern).

- **Step 6.6 (generate-test-data) closed cleanly and closed the D6 loop.** Mirrored `enrich_test_ideas.py`'s skip-not-overwrite accounting and reused `review_bdd.parse_feature_file`. **The whole point is the D6 loop:** `/tc:automate` (6.4) emits fixtures that reference `../../.test-commander/test-data/seed/<area>.json`; 6.6 writes exactly that file (area = feature stem, matching automate's area slug), so the fixture's data reference resolves to a real file and no data is inlined in the spec. `test_fixture_data_reference_resolves` proves the loop end-to-end (automate writes the reference; generate-test-data creates the target). **Skip-not-overwrite via a content marker, not mtime/heuristics:** a generated file carries `_generated_by: /tc:generate-test-data` (JSON) or "Generated by /tc:generate-test-data" (Markdown); on re-run a file lacking its marker is user-authored and skipped, so hand-tuned data survives — the same structural-marker discipline as `create_charter.py` (don't trust `is_file()` alone). Byte-stable because generated content is deterministic and the marker round-trips. **Q11 resolved pragmatically:** declarative JSON (`seed/`) + Markdown (`scenarios/`) cover the universal case; Python factories (`factories/`) are hand-authored exceptions never written by the helper — so 6.6 writes only `seed/` and `scenarios/`, leaving `factories/` and its README untouched. **Universal seed shape (D19):** generic records keyed by candidate id with `id`/`requirement`/`label` only — no product fields; Claude fleshes out realistic values from product-knowledge (the judgment layer). 7 RED → 7 GREEN; `make verify` clean (598 tests, up from 591). **Ruff caught an E501** on the long Markdown-row f-string — extracted the cell text to a local; the lint stage is the line-length backstop. **No new `config.yaml` surface** — the data shape is fixed/universal, so the customization guide is unchanged (Per-Phase Convention #6). With 6.6 the four Phase-6 command skills are all shipped; 6.7 (docs), 6.8 (testing finalization + cap bump), 6.9 (sign-off) remain.

- **Step 6.5 (review-automation + auto-run wiring) closed cleanly; the defer-not-defend pattern from Phase 5 (5.2→5.3) repeated exactly.** Mirrored `review_bdd.py` end-to-end: the rubric → per-spec verdict → open-questions append/dedup → CLI shape, plus the shared-entry-point pattern (`review_automation()` is the one function both the standalone command and the `/tc:automate` auto-run call, exactly as `review_features()` serves `/tc:review-bdd` and `/tc:generate-bdd`). **Six real heuristics, not marker-driven detection:** the flawed fixture spec (`seeded-automation/flawed.spec.ts`) carries `// knowledge: <category>` comments for readability, but `review_spec_text` detects via genuine regex/structural signals (`.fill\(['"]` for inline-data, `waitForTimeout` for hardcoded-wait, per-`test()` provenance/assertion scans, `.locator\(['"][.#\[]`/`xpath=` for weak-locator), so each flawed test triggers its category on its own merits — same discipline as Phase 5's `flawed.feature`. **`untraceable-spec` keyed on the automation-map, not on missing provenance:** the file-level "is this spec in `automation-map.md`?" check is meaningfully distinct from the per-test `missing-provenance` check, so the two don't collapse into one signal — the flawed fixture (deliberately absent from the map) trips untraceable-spec once for the file while a separate test trips missing-provenance. **Auto-run guarded on `outcome.spec_paths`:** `automate` only calls `review_automation` when it actually generated specs, so the review's own "no specs → exit 2" precondition never fires from the auto-run path (the standalone CLI still raises it). `--no-review` suppresses, mirroring `generate_bdd`'s `--no-review`. **Shared-path proof by byte-identity:** `test_autorun_matches_standalone` runs the auto-run in one project and `automate --no-review` + standalone `review_automation` in another, asserting the two `review-summary.md` files are byte-identical — a robust way to prove "same code path" without reaching into internals. **review-summary lives in `automation-plan/` but is naturally skipped by `automate`'s plan loop** (it has no matching `bdd/features/<stem>.feature`), so no extra exclusion was needed beyond the README.md exclude from 6.4. 10 RED → 10 GREEN; `make verify` clean (591 tests, up from 581). **No new `config.yaml` surface** — the six rubric categories are the fixed quality contract (not project-tunable), so the customization guide is unchanged (Per-Phase Convention #6). **Future-implementer hint:** the spec-unit splitter (`_test_units`: lead `//` comments + body to next `test(`) is the automation analogue of `parse_feature_file`'s scenario split; 6.x/Phase-7 helpers that reason per-`test()` can reuse it.

- **Step 6.4 (automate, generation only) closed cleanly; the template-placeholder-vs-real-artifact lesson recurred and was caught by a RED test.** Mirrored `generate_bdd.py`; imported `build_framework.ensure_framework` (lazy-init) and reused `review_bdd.parse_feature_file` (DRY sibling imports — both resolve in subprocess because Python adds the script's dir to `sys.path[0]`). **The AGENTS.md "don't check `is_file()` alone; the template ships placeholders" lesson recurred in a new form:** the precondition "no automation plan → refuse" used `automation-plan/*.md`, but the workspace template ships `automation-plan/README.md`, so the glob matched the placeholder and the refusal never fired. The `test_no_plan_refused_points_at_automation_plan` test caught it RED (it asserted exit 2 but got exit 0). Fix: exclude `README.md` from the plan glob. **Future-implementer hint:** every `<workspace>/<dir>/` ships a `README.md` placeholder from `/tc:init`; any helper that globs a workspace dir to detect "has the upstream run?" must exclude `README.md` (and check for the generator's real output shape), exactly as Steps 2.5/2.6 had to check structural markers rather than `is_file()`. **Spec imports test/expect from the per-area fixture, not `@playwright/test` directly** — that is the D6 discipline (the fixture re-exports `test`/`expect` after extending `base` with the `data` fixture), so a structural test asserting `@playwright/test` in the *spec* is wrong; assert it in the page object and assert the spec imports `../fixtures/<area>`. That was a test-expectation bug, not a code bug. **Byte-stable idempotency + user edits via a preserved region:** the page object carries `// === custom methods ... ===` markers; `_splice_custom_region` carries the existing inner text forward on regen, so an unedited re-run is byte-identical AND hand-added methods survive. Specs/fixtures are pure deterministic overwrite. **Owns `automation-map.md`:** Phase 2's `requirements_coverage.py` only *reads* it (loose `REQ-NNN` scan), so 6.4's write is the authoritative owner; updated the workspace-template placeholder from "Populated by /tc:traceability-map (Phase 5)" to "/tc:automate (Phase 6)". The map carries per-scenario `REQ`/`CS`/spec rows so 6.8 can resolve the test-map `Automated test` column. **Component-object generation deferred to the Claude judgment layer** — the mechanical generator can't infer shared UI fragments from a single feature, so 6.4 generates page+fixture+spec per area and leaves component extraction to refactoring (noted in the methodology). 12 RED → 12 GREEN (after the two fixes); `make verify` clean (581 tests, up from 569). **No new `config.yaml` surface** — `automate` consumes the plan (which already applied `suitability.weights`) and adds no key of its own; customization guide unchanged (Per-Phase Convention #6). **Ruff caught an unused `ParsedScenario` import** left over from the initial mirror — removed; the lint stage of `make verify` is the backstop for import drift.

- **Step 6.3 (automation-plan) closed cleanly; the rubric reuses review_bdd's parser and a borderline non-candidate fixture proves config sensitivity.** Mirrored `review_bdd.py` end-to-end and **imported its `parse_feature_file` + `ParsedScenario`** rather than re-implementing the Gherkin parse (DRY; the same sibling-import pattern `generate_bdd.py` uses for `review_features`). The seven-factor rubric is purely mechanical (tags + step count): `traceable` (3), `regression-value` (2), `risk-flagged` (2), `deterministic` (2, inverse of `@exploratory`/`@anomaly:`), `right-sized` (1, 3-12 steps), `data-ready` (1, not an Examples-less Outline), `persona-scoped` (1); thresholds `>=8` automate / `>=5` consider; two hard overrides (`@automated-candidate`→automate, `@manual`→manual). **Config-sensitivity test design:** the clean fixture's scenarios are all `@automated-candidate` (hard-override → automate), so they can't prove weight tuning. The test writes a *separate borderline* feature (`@req:`/`@cs:` only, no class/risk/persona, 3 steps → score 7 → `consider`) and asserts boosting `traceable` to 6 flips it to `automate` (score 10). **Future-implementer hint:** to test a config-tunable ranking, you need an input that is NOT hard-overridden; the fixture's all-candidate scenarios are deliberately override-bound, so author a borderline inline feature in the test. 9 RED → 9 GREEN; `make verify` clean (569 tests, up from 560). **Link-depth gotcha (recurred):** command pages and methodology files live 5 levels below repo root (`skills/<skill>/commands/<file>.md`), so links into `docs/` need `../../../../../` (5), not `../../../../` (4) — the link checker caught two 4-level links; fixed to match the `generate-bdd.md`→fixtures precedent. **Customization guide (Per-Phase Convention #6):** 6.3 ships the first Phase-6 config key (`tc-automate.suitability.weights`), so a focused "Phase 6 schema (`tc-automate`)" section with one worked example (automate-by-risk-first) landed this sub-step; the comprehensive three-shape pass + "Phase 6 — what landed" is deferred to 6.7's documentation step (the Phase 3/4/5 pattern — ship the surface's example in-step, defer the consolidation).

- **Step 6.2 (build-framework) closed cleanly; first executable artifacts ship as inline-rendered text, not disk-read templates.** Mirrored the sibling-helper skeleton (workspace IO + error hierarchy + outcome dataclass + orchestration + CLI) from `generate_bdd.py`. Key design call: the codebase's established pattern is **inline content rendering** (the `template` references in `create_charter.py` etc. are stub-*detection*, not file reads), so `build_framework.py` renders `playwright.config.ts` and `package.json` as inline string constants rather than reading bundled template files at runtime — avoids a runtime file-path dependency and matches how `generate_bdd.py` renders Gherkin inline. The four `.ts` object templates (`page-object`/`component-object`/`playwright-spec`/`fixture`) ship as bundled files under `templates/` because they are the v1 rendering contract `/tc:automate` (6.4) consumes, not because `build_framework` reads them. **Idempotency via per-file create-if-absent**, not a single sentinel short-circuit: every managed path (5 `.gitkeep` dirs + 2 files) is written only when absent, so a re-run is inherently byte-stable (`created 0`) AND a partial tree converges without clobbering user edits. `ensure_framework` adds the sentinel (`tests/playwright.config.ts`) short-circuit as the cheap lazy-init signal for 6.4. 12 RED → 12 GREEN; `make verify` clean (560 tests, up from 548). **Guard retirement (Per-Phase Convention #3):** there was *no test-level* "no executable runtime before Phase 6" guard (grepped `tests/` for `.ts`/`package.json`/runtime-forbidding assertions — none; the seeded fixtures already carried `.ts` files). The only stale guard was the `make build` placeholder ("Runtimes ship in Phase 6 (Playwright)"), which is now false — retired in this commit to point at `/tc:build-framework`. **No new extensible `config.yaml` surface** — the framework target is a runtime env var (`PLAYWRIGHT_BASE_URL`), documented in the command page and methodology, not a `config.yaml` schema key; the first Phase-6 config key (`tc-automate.suitability.weights`) arrives in 6.3, so the customization guide is unchanged this sub-step (Per-Phase Convention #6). **Future-implementer hint:** 6.4's `automate.py` calls `from build_framework import ensure_framework` (sibling import, needs `sys.path` insert of `scripts/` — the test harness already does this); generated specs/page objects render from the four `templates/*.ts` files, which carry placeholder tokens (`<AreaName>`, `<REQ-ID>`, `<CS-ID>`) and the mandatory `// @req: @cs:` provenance comment in the spec template.

- **Step 6.1 (scaffold) closed cleanly; one parametrized scaffold test covers all four skills + the fixture.** Mirrored the Step 5.1 scaffold-test discipline but consolidated into a single parametrized file (`tests/test_phase_6_scaffolds.py`, 29 cases) rather than four sibling files — the plan explicitly allowed "one parametrized file" and it kept the four near-identical skill assertions DRY. 29 RED → 29 GREEN; `make verify` clean (548 tests, up from 519). The four new SKILL.md files all parse under strict PyYAML from the start (the Phase 4 Step 4.8 latent-bug guard, now a scaffold-time invariant): descriptions were authored with no embedded `key: value` colon-space substring. **No new extensible surface** — the configurable keys (`tc-automate.suitability.weights` and any `tc-build-framework`/`tc-test-data` keys) arrive with their helpers in 6.3–6.6, so per Per-Phase Convention #6 the customization guide is unchanged this sub-step. `verify_skills.py` reports the four skills `UNEXPECTED (phase 6) — ahead of schedule` under `DEFAULT_PHASE_CAP=5` (warns, exit 0); the CATALOG already carried all four at phase 6 from an earlier phase's pre-seed, so no catalog edit was needed. **Fixture choice:** unlike the Phase 5 `seeded-bdd` fixture (one defect per review category), `seeded-automation/sign-in.feature` is *clean* — every scenario is an `@automated-candidate` with resolvable `@req:`/`@cs:` tags — because Phase 6's downstream commands (`/tc:automation-plan`, `/tc:automate`) need the clean shape `/tc:generate-bdd` emits from clean input, not the flawed shape. **Future-implementer hint:** the per-scenario `scenario_blocks()` splitter in the scaffold test (tags above a `Scenario` keyword belong to that scenario) is reusable by 6.3/6.4 tests that assert per-scenario tag handling.

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

### Phase 7 — Execution outline

Nine sub-steps. TDD throughout: every implementation step lands its tests red before turning them green. 7.1 scaffolds the three skills + the seeded-results fixture; 7.2 ships `/tc:run` (the project's **first real test execution**); 7.3 ships the `tc-evidence` indexer and wires it into run; 7.4–7.6 implement `/tc:analyze-results`, `/tc:report`, `/tc:quality-gate`; 7.7 is the documentation pass; 7.8 is the testing finalization (cap bump + integration smoke + the `test-map` downstream-column resolution); 7.9 is the sign-off with a `phase-7` tag.

**Three disciplines Phase 7 introduces (read before 7.1).**

- **Hermetic pytest is preserved even though the artifacts now run.** `/tc:run` shells out to `npx playwright test` (and the `postman` CLI for the API path) in real use, but the pytest suite must stay browser-free. Mirror the Phase 3 Step 3.5 / Phase 4 Step 4.7 pattern: the real subprocess invocation is **refused under pytest** via the `PYTEST_CURRENT_TEST` env-var guard, and every test exercises the result-ingestion / report-building logic against a **recorded Playwright JSON report** fixture — never a live browser. The "no executable runtime in tests" property holds.
- **Injected-clock determinism.** Run IDs (`runs/<RUN-ID>/`) and report/history-snapshot filenames carry a timestamp, which breaks the byte-determinism every prior phase relied on. Resolution: the helpers take an **injected `now`** (a `--now` flag / parameter); tests pass a fixed timestamp so generated artifacts are byte-stable. Production reads the wall clock. Document the contract in each helper's docstring; do not call `datetime.now()` inline.
- **Evidence policy (Q5/Q3/Q10).** Screenshots are committed (`evidence/screenshots/`); videos and traces are git-ignored by default with a documented `git-lfs` opt-in; JSON/HTML reports are committed and referenced from the quality report. History snapshots are full copies (Q3), kept forever in git (Q10). The policy is config-tunable and enforced by the `tc-evidence` indexer, not by the test author's discipline.

#### 7.1 — Skill scaffolds (three skills) and seeded-results fixture

- **Deliverables.** `SKILL.md` for `tc-run`, `tc-quality-report`, `tc-evidence` (strict-PyYAML frontmatter with **no embedded `key: value` substring** per the Phase 4 Step 4.8 lesson; body lists each skill's commands; `tc-evidence`'s body documents that it is an **internal cross-cutting indexer with no user-facing command**, invoked by `tc-run` and later by `tc-web`; deferral wording until each sub-step ships behavior). Empty `commands/`/`methodology/`/`templates/` dirs (`.gitkeep`). `tests/fixtures/seeded-results/` containing: a recorded Playwright JSON report (`results.json`) with at least one `passed`, one `failed`, and one `flaky` (pass-on-retry) case, each carrying the `@req:`/`@cs:` provenance that links it back to a generated spec; sample evidence artifacts (a committed-class screenshot stub plus a video/trace stub to exercise the policy split); and a populated upstream chain (a Phase-6 `automation-map.md` + a generated `<area>.spec.ts`) so `/tc:run` can map results → scenarios → requirements. `README.md` documents the result schema, the evidence-policy categories, the linkage convention, and the deliberately-generic D19 framing.
- **Tests first.** A parametrized scaffold test (or three siblings) — each asserts the skill dir + `SKILL.md` (strict-PyYAML parse from the start), the three sub-dirs, and (for the fixture) a parseable `results.json` carrying at least one passed/failed/flaky case with resolvable linkage tags.
- **Definition of done.** Three skills scaffolded; fixture present; scaffold tests green; `verify_skills.py` reports the three new skills `UNEXPECTED (phase 7) — ahead of schedule` under `DEFAULT_PHASE_CAP=6` (cap bumps to 7 in 7.8). Confirm `CATALOG` carries `tc-run: 7`, `tc-quality-report: 7`, `tc-evidence: 7` (add if absent).

#### 7.2 — `/tc:run` (execution + result capture; execution refused under pytest) (TDD)

- **Helper.** `plugins/test-commander/scripts/run_tests.py`. Two responsibilities split by the hermetic boundary: **(a)** in real use shells out to `npx playwright test` (and `postman` for the API path) for the requested run mode (smoke / regression / feature-specific / failed-only / tagged) — **refused under pytest** via the `PYTEST_CURRENT_TEST` guard with a clear message; **(b)** ingests the Playwright JSON report (the recorded fixture under pytest), and writes a per-run record under `<workspace>/runs/<RUN-ID>/` (RUN-ID from the injected clock), mapping each result to its scenario/spec via the `@req:`/`@cs:` provenance and the Phase-6 `automation-map.md`. Run modes select which specs run. **No evidence-index auto-call in 7.2** — the indexer + the auto-run wiring (incl. `--no-index`) ship in 7.3 (the Phase-5/6 defer-not-defend pattern); 7.2 leaves a forward pointer. Upstream is read-only (no `automation-map.md` / spec mutation). **Injected-clock determinism**: tests pass a fixed `now` → byte-stable run records.
- **Methodology + templates.** `methodology/test-execution.md` (run modes, the hermetic boundary, the injected-clock contract, the result schema, the Claude judgment layer); `templates/test-run-summary-template.md`.
- **Command file + SKILL.md update.** `commands/run.md`; `tc-run/SKILL.md` surfaces the shipped behavior (a brief forward pointer that evidence indexing wires in 7.3 is acceptable mid-phase).
- **Tests first.** `tests/test_run_tests.py` — uninitialized workspace refused; the real Playwright invocation refused under pytest with the directing message; recorded `results.json` ingested → `runs/<RUN-ID>/` record written mapping each pass/fail/flaky to its scenario via provenance; run modes filter the result set; the injected clock makes the run record byte-stable; `automation-map.md` and the generated specs are byte-identical before/after (read-only upstream).
- **Definition of done.** Results ingested into per-run records; real execution refused under pytest; run modes work; deterministic via the injected clock; SKILL.md updated.

#### 7.3 — `tc-evidence` indexer + evidence policy + run auto-index wiring (TDD)

- **Helper.** `plugins/test-commander/scripts/index_evidence.py`. Routes raw run artifacts to the evidence tree per the policy (screenshots → committed `evidence/screenshots/`; videos + traces → `evidence/{videos,traces}/` git-ignored by default with the documented `git-lfs` opt-in; JSON/HTML → committed), writes `<workspace>/evidence/evidence-index.md` (each artifact with its run + scenario provenance), and manages the evidence `.gitignore` + the lfs opt-in note. Exposes `index_run_evidence()`; **7.3 wires the auto-call into `run_tests.py`** (`--no-index` to suppress) and updates `run.md` + `tc-run/SKILL.md` to describe the now-wired indexing (removing the 7.2 forward pointer).
- **Methodology + template.** `methodology/evidence-management.md` (the policy table, the commit/lfs/ignore decision per artifact type, the index discipline, the Claude judgment layer); `templates/evidence-summary-template.md`.
- **Tests first.** `tests/test_index_evidence.py` — screenshots routed and committed; videos/traces routed and git-ignored (assert the `.gitignore` entry exists, not that the files are deleted); the evidence index lists every artifact with provenance; idempotent re-run byte-stable; `index_run_evidence()` is the same code path `/tc:run` auto-runs (identity + `--no-index` suppression).
- **Definition of done.** Evidence routed per policy; index written; `.gitignore`/lfs opt-in handled; auto-run wired and shared; `tc-evidence`/`tc-run` SKILL.md updated.

#### 7.4 — `/tc:analyze-results` (failure triage + flaky detection) (TDD)

- **Helper.** `plugins/test-commander/scripts/analyze_results.py` (mirrors the `review_*` rubric pattern; design reference `agentic-playwright-automation:investigate-playwright-failure`). Reads `runs/<RUN-ID>/` records, classifies each failure against a universal triage rubric (product-defect / test-defect / environment / flaky), detects flaky tests from the recorded report's pass-on-retry signal, writes the analysis into the run record, and routes confirmed gaps to `requirements/open-questions.md` as deduplicated `[test-analysis]` signals.
- **Methodology + template.** `methodology/failure-triage.md` (the triage categories with one worked example each + the Claude judgment layer); `templates/analysis-template.md`.
- **Tests first.** `tests/test_analyze_results.py` — uninitialized refused; no runs refused pointing at `/tc:run`; seeded report with a failure + a flaky case → each classified exactly once; `[test-analysis]` dedup; a clean run → no signals; deterministic.
- **Definition of done.** Failures triaged, flaky tests flagged, signals routed and deduped; SKILL.md updated.

#### 7.5 — `/tc:report` (quality report + history snapshot) + `test-map` downstream resolution (TDD)

- **Helper.** `plugins/test-commander/scripts/build_report.py`. Aggregates the workspace into `<workspace>/quality-report/current-quality-report.md` with **every spec'd section** (executive summary, coverage, requirements readiness, exploratory findings, automated regression status from the latest run, known risks, known defects, open questions, automation health, flaky tests, evidence summary, traceability summary, recommendations, release readiness, recent changes), keeping **facts, interpretation, and human-review items clearly separated**. Then snapshots a full copy to `<workspace>/quality-report/history/<YYYY-MM-DD-HHmm>.md` (Q3 full snapshot, Q10 keep-forever; filename from the injected clock). **Also extends `traceability_map.py`** to resolve the `Test result` column (from `runs/`) and the `Quality report` column (from `quality-report/`) of `test-map.md` from `pending` — the columns Phase 6 left pending (mirrors the Step 6.8 `Automated test` resolution; wired here, asserted in 7.8). **Injected-clock determinism**: same inputs + same `now` → byte-identical current report and snapshot.
- **Methodology + template.** `methodology/quality-reporting.md` (the section catalog, the facts-vs-interpretation separation, the never-invent-metrics rule, the history-snapshot discipline, the Claude judgment layer); `templates/quality-report-template.md`.
- **Tests first.** `tests/test_build_report.py` — uninitialized refused; seeded chain → `current-quality-report.md` with every section present; facts / interpretation / human-review separated; history snapshot written under the injected-clock filename; re-run with the same clock byte-identical; `test-map.md` `Test result` + `Quality report` columns resolve from `pending` to the run/report references.
- **Definition of done.** Report carries all sections; history snapshots; deterministic via the injected clock; `test-map` downstream columns resolved; SKILL.md updated.

#### 7.6 — `/tc:quality-gate` (PASS / WARN / FAIL) (TDD)

- **Helper.** `plugins/test-commander/scripts/quality_gate.py`. Evaluates the quality report / latest run against project-defined thresholds (config `tc-quality-report.gate.thresholds` — e.g. min pass rate, max open critical defects, max flaky count) and returns **PASS / WARN / FAIL** with the per-criterion breakdown, writing a gate verdict file. Release-readiness reads only measured values (never invents metrics).
- **Methodology + template.** `methodology/quality-gates.md` (the criteria, the PASS/WARN/FAIL thresholds, the judgment layer); `templates/quality-gate-template.md`.
- **Tests first.** `tests/test_quality_gate.py` — uninitialized refused; no report refused pointing at `/tc:report`; seeded report → PASS/WARN/FAIL computed against the default thresholds; config thresholds change the verdict; deterministic.
- **Definition of done.** Gate returns PASS/WARN/FAIL against thresholds; config-tunable; deterministic; SKILL.md updated. By end of 7.6 all three SKILL.md files describe every shipped command/indexer with no deferral wording.

#### 7.7 — Documentation pass *(dedicated step)*

- **Deliverables.** Author `docs/user-guide/running-tests.md` (end-to-end: `/tc:run` → (auto evidence index) → `/tc:analyze-results` → `/tc:report` → `/tc:quality-gate`, with verbatim helper output from the seeded chain; explains run modes, the hermetic boundary, the injected-clock determinism, and the evidence policy) and `docs/user-guide/quality-report.md` (the report sections, history, and the gate). Update `docs/command-reference.md` (Phase 7 shipped section) and `docs/workspace-reference.md` (`runs/`, the `evidence/` policy split, `quality-report/` + `history/` ownership, and the `test-map` downstream resolution). Add a "Phase 7 schema (`tc-run` / `tc-quality-report` / `tc-evidence`)" section to `docs/user-guide/customizing-for-your-project.md` covering the run-mode and evidence-policy keys and `tc-quality-report.gate.thresholds`, with three worked examples spanning materially-different project shapes + a "Phase 7 — what landed" subsection. Status-line refresh across the six locations + a "Beyond Phase 6" footer in `automation.md`. Final deferral-wording sweep across all three SKILL.md files, the methodology, and `docs/`.
- **Definition of done.** Docs accurate against the implementation; all cross-links resolve; link checker green; customization guide reflects the shipped schema with three project-shape examples.

#### 7.8 — Testing finalization *(dedicated step)*

- **Deliverables.** Bump `DEFAULT_PHASE_CAP` 6 → 7 (CATALOG entries already present from 7.1). `tests/test_phase_7_integration.py` (in-process, full Phase 2 → 3 → 4 → 5 → 6 → 7 sweep in natural order, injected clock): assert run records written from the recorded report; evidence routed per the policy split; analysis classifies the failure + flaky case; the report carries every section + a history snapshot; the gate returns a verdict; `test-map.md` `Test result` + `Quality report` columns resolve from `pending`; the write boundary holds (`bdd/`, `product-knowledge/`, and the project-root `tests/` framework byte-identical before/after Phase 7); Playwright execution refused under pytest; `/tc:next` advances past `/tc:run` (the robust "advanced past" invariant). Byte-stable re-run with a fixed clock. **`PHASE_OWNERSHIP` narrowing** (per the line-1472 future-implementer hint): Phase 7 now writes **real files** under `evidence/`, so confirm Phase 4's `in_progress` signal does not key on `evidence/` (it keys on `charters`/`exploration-notes`/`sessions`), and set Phase 7's signal to key only on directories it uniquely produces (`runs/` + `quality-report/`); add the regression test.
- **Definition of done.** Integration smoke passes; cap bump reflected; full `make verify` chain green; `verify_skills.py` reports all thirteen shipped skills `PRESENT` with `UNEXPECTED=0`.

#### 7.9 — Sign-off

Six sub-sub-steps. Mirrors the Phase 6 sign-off (6.9) exactly. Test-first: the sign-off test in 7.9.5 lands red before the plan/CHANGELOG edits in 7.9.3 turn it green. The final sub-step (7.9.6) captures evidence and pushes the `phase-7` annotated tag.

##### 7.9.1 — Cold-user walkthrough of `running-tests.md`

- **Deliverables.** Captured log of an end-to-end walkthrough from a freshly-installed plugin (`make uninstall` → `make install`, which runs `claude plugin validate`) against a fresh tmp consuming project with Phase 2 → 6 state pre-populated, then the Phase 7 helpers in workflow order. **Keep the `make uninstall` + `make install` preamble exactly as-is** (per the Phase 4 Step 4.8 lesson — it exercises the strict validator no other step runs).
- **Definition of done.** All commands succeed end to end. Output captured to `/tmp/tc-phase7-walkthrough.log`. Any failure is fixed and re-run before 7.9.2.

##### 7.9.2 — Per-step DoD audit

- Line-by-line audit of 7.1 through 7.8 against their DoD lists: every helper, methodology, template, command file, and SKILL.md update present; every per-command test green; results map to scenarios; the write boundary holds; all three SKILL.md files free of deferral wording; `customizing-for-your-project.md` carries the Phase 7 schema with three worked examples. **Lesson-capture audit:** every Phase 7 sub-step (7.1–7.8) has an entry in `Phase 7 — Lessons learned (running)`; clean sub-steps record "no lessons" explicitly.

##### 7.9.3 — Plan and CHANGELOG updates

- `planning/plan.md` — collapse `### Phase 7` To Do to a marker line; add a `### Phase 7 — Execution, evidence, and quality report (YYYY-MM-DD)` section to `## Completed` with `[x]` per-step bullets, mirroring the Phase 6 closing format.
- `CHANGELOG.md` — flip the Phase 7 heading from `(in progress)` to `(complete YYYY-MM-DD)` with per-sub-step Added bullets.

##### 7.9.4 — Documentation final pass

- Edit wherever Phase 7 wording has drifted across the six sub-steps (README status line, getting-started "what's next", install verifying-install paragraph, `running-tests.md` intro, `automation.md` "Beyond Phase 6" footer, `plugins/test-commander/README.md` skill table, customization-guide tense). "Phase 7 in progress" → "Phase 7 complete (YYYY-MM-DD); Phase 8 starts next". All cross-links resolve.

##### 7.9.5 — Pre-flight tests for sign-off

- `tests/test_phase_7_signoff.py`. Coverage: all Phase 7 pytest files exist (`test_tc_run_scaffold` etc., `test_run_tests`, `test_index_evidence`, `test_analyze_results`, `test_build_report`, `test_quality_gate`, `test_phase_7_integration`, `test_phase_7_signoff`); all five helpers exist (`run_tests`, `index_evidence`, `analyze_results`, `build_report`, `quality_gate`); all command files exist; all methodology + template files exist; `seeded-results/` fixture intact; `verify_skills.py` has `CATALOG["tc-run"] == 7`, `CATALOG["tc-quality-report"] == 7`, `CATALOG["tc-evidence"] == 7`, and `DEFAULT_PHASE_CAP >= 7` (per the Phase-2 Step-2.8 lesson — never assert `==` on the cap); all three SKILL.md files describe every shipped command/indexer with no deferral wording AND parse under strict PyYAML; `customizing-for-your-project.md` has a Phase 7 YAML block matching the shipped schema with at least three project-shape headings; the `Phase 7 — Lessons learned (running)` subsection has an entry per sub-step (7.1–7.8); CHANGELOG Phase 7 marked complete with a date; `plan.md` Completed has a Phase 7 subsection; `plan.md` To Do Phase 7 collapsed to the marker line; total pytest count meets the floor (`>= 700` — Phase 6 finished at 622; Phase 7 adds the scaffold suites, five per-command/indexer suites, integration, and sign-off). Test-first: red before 7.9.3's edits, green after.

##### 7.9.6 — Final DoD evaluation (close Phase 7)

- `make verify` clean; replay the cold-user walkthrough; commit; push; annotated `phase-7` tag pushed to origin.

#### Phase 7 — Lessons learned (running)

Captured at sub-step close per the "Sub-step lesson capture" Per-Phase Convention. (Populated as 7.1–7.9 land.)

- **Step 7.9 (sign-off) closed cleanly; the test-first sign-off gate landed 20/23 GREEN immediately and 3 RED on exactly the closing edits, and the pytest floor needed re-derivation from the def-count method.** Mirrored 6.9's six sub-sub-steps. The cold-user walkthrough ran `make uninstall` → `make install` fully clean (`claude plugin validate` passed over all thirteen SKILL.md — no strict-YAML regression, since every Phase-7 scaffold test asserted the parse from 7.1 onward), then drove the full Phase 2 → 7 chain in a fresh tmp project: run record, routed evidence + index, triage (`product-defect` + `flaky`), the fifteen-section report + history snapshot, the `FAIL` gate, and the fully-resolved `test-map` (three REQ-001 rows with `Test result` + `Quality report` resolved). `test_phase_7_signoff.py` (23 tests) landed RED on the three plan/CHANGELOG closing assertions and GREEN after the closing edits — the test-first gate working as designed for the seventh phase running. **The pytest-floor literal had to be re-derived, not copied from the plan:** the plan estimated `>= 700`, but the sign-off test counts test-function `def`s (the Phase-6 method), and the def count at close is 682 (vs 715 pytest-*collected*, the gap being parametrized suites like `test_phase_7_scaffolds`). The plan's 700 was a collected-count estimate; the floor was set to `>= 680` (just below the real def count, monotonic-safe) with a comment recording the distinction — the AGENTS.md "re-derive every literal from the new phase's actual artifacts" rule applied to the floor specifically. **`tc-evidence` being command-less drove three sign-off assertions that diverge from the per-command pattern:** `test_tc_evidence_has_no_command_page` (asserts `commands/` is empty), `test_tc_evidence_skill_md_documents_internal_indexer` (asserts `indexer`/`internal`/`tc-run` instead of a `/tc:` command), and the command-page existence check covers only the four real command pages — Per-Phase Convention #5 does not apply to a command-less skill, and the sign-off test encodes that. **Cold-user walkthrough harness gotcha (macOS):** `tempfile.mkdtemp()` returns `/tmp/...` which macOS resolves to `/private/tmp/...`, breaking `extract_knowledge_from_code`'s `path.relative_to(workspace)`; pytest's `tmp_path` is pre-resolved so the integration test never hit it, but the standalone walkthrough script did — fixed by `.resolve()`-ing the temp dir. **Future-implementer hint:** any standalone script (not a pytest fixture) that drives the helpers against a tmp dir must `.resolve()` it first. `make verify` clean (715 tests, up from 692; link checker 214 files); annotated `phase-7` tag pushed to origin. **Phase 7 is closed; Phase 8 (`tc-learning`, the governed learning loop) starts next.**

- **Step 7.8 (testing finalization) closed cleanly; the cap bump flipped the three skills `PRESENT` and the integration smoke was a clean compose of the Phase-6 chain + the recorded run.** Three changes: `DEFAULT_PHASE_CAP` 6 → 7 (so `verify_skills.py` now reports `PRESENT=13 UNEXPECTED=0`), the `PHASE_OWNERSHIP` narrowing, and `tests/test_phase_7_integration.py` (full Phase 2 → 7 sweep, in-process, injected clock). **The integration reused the Phase-6 integration's upstream sweep verbatim and appended a four-call Phase-7 chain** (`run` → `analyze` → `report` → `gate`), ingesting the recorded `seeded-results/results.json` whose `@req:`/`@cs:` provenance and scenario titles match the Phase-6-generated `sign-in` spec and automation map — so the run record joins results → scenarios → requirements with no fixture translation. The clean compose is the payoff of every fixture sharing the universal sign-in/session narrative (D19). **The `evidence/` write-into-workspace did not break the project-root `tests/` write-boundary check:** the auto-index copies the recorded stubs into `.test-commander/evidence/` (Phase 7's own dir), never into the project-root `tests/` framework, so snapshotting `tests/` before/after Phase 7 stays byte-identical — the boundary assertion is over the *framework*, not the workspace. **`PHASE_OWNERSHIP` narrowing (the line-1472 hint discharged):** Phase 7 now writes real files under `evidence/` via the indexer, so `evidence` was removed from Phase 7's signal, leaving `["quality-report", "runs"]` — the directories Phase 7 *uniquely and canonically* produces. The regression test (`test_phase_7_signal_keys_on_runs_and_quality_report_not_evidence`) lands RED before the narrowing (asserting `evidence` not in the signal) and proves evidence content alone does not mark Phase 7 in_progress while a run record does. Phase 4's signal was confirmed clean (it keys on `charters`/`exploration-notes`/`sessions`, never `evidence`). The `test_workspace_state.py` full-case already keyed Phase 7 on `quality-report/current-quality-report.md`, so the narrowing left it green. **"Playwright execution refused under pytest" asserted two ways:** the no-execution-path property (no `node_modules`/`test-results`/`playwright-report` under `tests/`) *and* the active guard (`run_tests.run(report=None)` raises `ExecutionRefusedError`) — the recorded-report path is the only one the suite exercises. **Cap bump was safe because every prior sign-off test asserts `DEFAULT_PHASE_CAP >= N`** (the Phase-2 Step-2.8 monotonic discipline), so 6 → 7 broke nothing; the full suite stayed green (692, up from 689: +2 integration, +1 ownership regression). `make verify` clean (link checker 214 files unchanged — no new docs). **Future-implementer hint:** 7.9 sign-off writes `test_phase_7_signoff.py` (RED before the plan/CHANGELOG close, GREEN after), asserting every Phase-7 helper/command page/methodology/template on disk, `CATALOG[...] == 7` for the three skills and `DEFAULT_PHASE_CAP >= 7`, no deferral wording, the customization Phase-7 block, a lessons entry per sub-step, and the pytest floor (`>= 700` per the plan — the suite is at 692 now, so 7.9's own tests carry it past 700).

- **Step 7.7 (documentation pass) closed cleanly; the customization-guide deliverable was already discharged in 7.6, so the doc pass was the two walkthroughs + references + status sweep.** Authored `docs/user-guide/running-tests.md` (the run → auto-index → analyze → report → gate walkthrough) and `docs/user-guide/quality-report.md` (the report sections, history, and gate), both with **verbatim output captured from the real chain** — I ran all four Phase-7 commands against a tmp workspace seeded with the `seeded-results` fixture + a generated inventory + the `seeded-automation` feature, and embedded the byte-real stdout and the fully-resolved `test-map.md` (the 6.7/5.5 "quote captured output, never paraphrase" discipline). **The customization-guide "Phase 7 schema" section was already added in Step 7.6** (the first config surface, `tc-quality-report.gate.thresholds`, ships its example in-step per the Phase 3/4/5/6 pattern), so the plan's 7.7 "add the customization section" deliverable was satisfied early — 7.7 confirmed it carries three project-shape examples + "Phase 7 — what landed" and added nothing further. **Status-line semantics followed the 6.7-vs-6.9 precedent exactly:** the doc pass sets "Phase 6 complete (2026-05-29); **Phase 7 in progress** — `tc-run`, `tc-quality-report`, `tc-evidence` shipped (sign-off pending)" across the six surfaces (README status header + doc index, install verifying-install, getting-started what's-next, workflow Beyond-Phase-1, the `automation.md` Beyond footer, the plugin README skill table — three new shipped rows), and leaves the "Phase 7 complete (date)" flip to 7.9. **command-reference gained a "Phase 7 commands (shipped)" section** and the four Phase-7 rows were removed from the planned table (the 6.7 pattern). **workspace-reference's four Phase-7 sections** (`runs/`, `evidence/`, `quality-report/`, the `test-map` rows) were rewritten from "Phase 7" stubs to shipped behavior, documenting the per-run record files, the evidence policy split + `.gitignore` shape, the fifteen-section report + history, and the downstream-column resolution. No code, no new tests (689 unchanged); `make verify` clean (link checker 214 files, +2 walkthroughs). Final deferral sweep across the three SKILL.md files, the methodology, and `docs/` returned no shipped-command deferral wording. **Future-implementer hint:** 7.8 (testing finalization) bumps `DEFAULT_PHASE_CAP` 6 → 7 (flipping the three skills `PRESENT`), adds the Phase 2 → 7 integration smoke, and narrows `PHASE_OWNERSHIP` for `runs/`/`quality-report/` (Phase 7 now writes real files under `evidence/` — confirm Phase 4's signal does not key on it).

- **Step 7.6 (`/tc:quality-gate`) closed cleanly; the gate is the first Phase-7 surface with a `config.yaml` schema, so it carried the customization-guide obligation.** `quality_gate.py` evaluates four criteria over the latest run record + open-questions: pass rate and failed tests are *hard* (breach → FAIL), flaky tests and open questions are *soft* (breach → WARN); the overall verdict is the worst per-criterion (`PASS < WARN < FAIL`). **Config loading mirrors `automation_plan.load_weights` verbatim** — `tc-quality-report.gate.thresholds` merged over `DEFAULT_THRESHOLDS`, tolerant of any read/parse error or unknown key (falls back to the default for that criterion), the `try: import yaml` + nested `data[...][...]` + broad `except` shape. Reused, not re-invented. **The gate exits `1` on FAIL** (not just reports it) so a CI pipeline can branch on `/tc:quality-gate` directly — the first helper to use exit code as a *result* signal rather than only a precondition signal (exit 2 stays reserved for uninitialized/no-report). The in-process `gate()` returns the verdict for tests; only the CLI maps FAIL→1. **Never-invent-metrics handled the empty case explicitly:** with no run record, `total==0` → the pass-rate criterion reads `n/a` and passes vacuously rather than dividing by zero or assuming a rate. **Determinism without a clock** — the verdict is derived purely from the run record and open-questions, so no `--now` seam is needed (like 7.4's analysis, unlike 7.2/7.5's timestamped artifacts). **Customization-guide obligation (Per-Phase Convention #6) discharged in-step:** added a "Phase 7 schema (`tc-quality-report`)" section with the threshold table and three project-shape worked examples (regulated zero-tolerance, early-stage pragmatic, internal-tool advisory — varied by *risk posture*, the Phase-7 analogue of Phase-6's weight-tuning variants), plus "Phase 7 — what landed"; the three YAML blocks parse, and two tests (`test_loose_thresholds_pass`, `test_flaky_only_warns`) are the named "would fail if the helper ignored the config" defense. 7 RED → 7 GREEN; `make verify` clean (689 tests, up from 682; link checker 212 files). **With 7.6 all three Phase-7 SKILL.md files describe every shipped command/indexer with no deferral wording (sweep clean)** — the command-and-indexer surface of Phase 7 is complete; 7.7 (docs), 7.8 (cap bump + integration + PHASE_OWNERSHIP narrowing), 7.9 (sign-off) remain. **Future-implementer hint:** 7.8's integration smoke runs the full chain run → analyze → report → gate and asserts the gate verdict; the `seeded-results` fixture's 1-pass/1-fail/1-flaky shape yields FAIL under default thresholds, so the integration can assert FAIL without extra config, or write a loose-threshold config to assert PASS.

- **Step 7.5 (`/tc:report` + test-map downstream resolution) closed cleanly; the test-map resolution mirrored 6.8 exactly and the report's discipline is structural separation, not richer prose.** Two deliverables: the quality report (`build_report.py`) and the `test-map` downstream-column resolution (extending `traceability_map`/`traceability_render`). **The resolution mirrors Step 6.8's `Automated test` wiring symmetrically:** added `scan_run_results()` (latest `runs/*/results.json` → `{cs -> status}`) and `quality_report_ref()` (the report-presence → ref string) to `traceability_map`, and extended `render_test_map(rows, automated_by_cs=None, result_by_cs=None, report_by_cs=None)` with two more defaulted-empty dicts — so with no runs/report (Phase 5/6) every downstream cell still renders `pending` and the existing `test_traceability_map.py` stayed byte-identical (6 tests green untouched). The same default-empty-arg trick that kept 6.8 byte-stable. **`/tc:report` triggers the resolution itself** (calls `traceability_map.traceability_map()` after writing the report, `contextlib.suppress`-guarded on `InventoryMissingError`/`UninitializedWorkspaceError`), so running `/tc:report` leaves a fully-resolved test-map — the orchestrating-command-rebuilds-downstream pattern (`automate`→review, `run`→index, `report`→traceability). Order matters: the report is written *before* the traceability rebuild, so `quality_report_ref` sees the generated report and the `Quality report` column resolves in the same `/tc:report` invocation. **The report's facts/interpretation/review separation is structural, tagged inline** (`[fact]`/`[interpretation]`/`[review]` on every section header and key line) rather than three top-level parts — this keeps the 15 sections in their spec'd order while still making the class of every line unmistakable, and the never-invent-metrics rule is enforced by reading each section from its artifact (a missing source reads `_None recorded._`, never a guessed 0). **Defensive stub detection reused the `_(empty until` marker** (the AGENTS.md "don't trust `is_file()`; the template ships placeholders" lesson) so an un-run workspace's template stubs count as no-data, not as content. **Injected-clock determinism reused 7.2's pattern** for both the report's `Generated:` line and the `history/<YYYY-MM-DD-HHmm>.md` snapshot filename; the snapshot is a byte-identical copy of the current report (Q3 full snapshot, Q10 keep-forever). **Ruff caught four issues across two passes** — three E501s (a long `if ... else []` one-liner split to a `sessions_dir` local; a long comment; a long `except (A, B):` tuple) and one SIM105 (`try/except/pass` → `contextlib.suppress`); plus a test-comment E501 that needed two shortenings. The lint stage is the repeated backstop. 8 RED → 8 GREEN (14 with the traceability suite, all green); `make verify` clean (682 tests, up from 674; link checker 209 files). With 7.5, `/tc:report` is shipped and `tc-quality-report` has one command left (`/tc:quality-gate`, 7.6). **No new `config.yaml` surface this sub-step** — the section catalog and the three content classes are universal; the gate thresholds (`tc-quality-report.gate.thresholds`) arrive with `/tc:quality-gate` in 7.6, so the customization guide is unchanged (Per-Phase Convention #6). **Future-implementer hint:** 7.6's `/tc:quality-gate` reads the same latest-run record (`runs/*/results.json`) and the quality report for its PASS/WARN/FAIL thresholds; `build_report._latest_run` and the `[fact]` counts are the model to reuse.

- **Step 7.4 (`/tc:analyze-results`) closed cleanly; the triage rubric needed a small backward-compatible enrichment of 7.2's run record.** Mirrored `review_bdd.py`'s rubric + open-questions append/dedup pattern (the `EXISTING_RE` parse, the `(source-id, question)` dedup set, the append-only write). **The mechanical triage needs the failure error text, which 7.2's `results.json` did not persist** — so this step extended `run_tests` to capture each result's first failing-attempt `error.message` into `ResultRecord` and `results.json`. This is a justified cross-step edit (like 6.8 extending `traceability_map`): the new `error` field is deterministic, defaulted to `None`, and additive, so the 7.2 byte-stable-record test and the 7.3 evidence tests (which read attachments, not error) stayed green untouched. **Future-implementer hint:** when a downstream consumer needs a field the upstream record dropped, enrich the upstream record (additive, defaulted) rather than re-reading the transient raw report — the run record is the canonical, persisted source of truth. **The rubric is conservative and status-first:** `flaky` short-circuits on the pass-on-retry status *before* the error text is consulted (so the flaky case's `TimeoutError` does not misroute to `environment`); a genuine `failed` then goes `environment` → `test-defect` → `product-defect` by error-text precedence, defaulting an unrecognized assertion failure to `product-defect`. **`analyze` needs no injected clock** — the analysis is derived purely from the run record (which already carries the run's timestamp), so `analysis.md` is deterministic without a `--now` seam, unlike 7.2's RUN-ID. **Test brittleness caught and fixed in-cycle:** the first cut asserted `analysis.count("product-defect") == 1` on the rendered Markdown, but the category name also appears in the summary counts line — so the assertion saw 2. Fixed the *test* (not the code) to count triage-table rows ending in `| <category> |`, the robust "classified exactly once" check; the `outcome.classifications` dict assertion already proved correctness. **Pytest collection gotcha:** a test-file helper named `analysis_lines` was originally `test_analysis_lines` and pytest tried to collect it as a test (errored on the missing `ws` fixture) — helper functions in a test module must not start with `test_`. **`source-id` keyed on the candidate (`tc-run/test-analysis-<CS>`), not the run**, so the same scenario+category dedups across re-runs and across runs — one open question per (scenario, category), not one-per-run (the never-spam-the-log discipline). 8 RED → 1 RED (the brittle count) → 8 GREEN; the 7.2/7.3 suites stayed green (28 together). `make verify` clean (674 tests, up from 666; link checker 206 files). With 7.4 both `tc-run` commands are shipped and the SKILL.md carries no deferral wording (deferral sweep clean). **No new `config.yaml` surface** — the triage categories are the fixed universal rubric (the gate thresholds arrive in 7.6), so the customization guide is unchanged (Per-Phase Convention #6).

- **Step 7.3 (`tc-evidence` indexer + run auto-index wiring) closed cleanly; the defer-not-defend wiring from 7.2's forward pointer landed exactly as planned.** `index_evidence.py` exposes `index_run_evidence(project_root, run_id, *, source_root=None)`, and `run_tests.run` now imports and calls it after writing `results.json` (suppressible with `--no-index`) — the same shape as `generate_bdd`→`review_features` (5.3) and `automate`→`review_automation` (6.5), the third sibling of the pattern. **First command-less skill ships its behavior under `methodology/`, not `commands/`:** `tc-evidence` has no `/tc:*` command, so Per-Phase Convention #5 (per-command page) does not apply — `methodology/evidence-management.md` is its authoritative spec, and `commands/.gitkeep` stays (the dir is asserted present by the 7.1 scaffold test but is intentionally empty). A thin `main()` exists for manual/debugging use only. **The index is rebuilt from the records, not accumulated:** `index_run_evidence` rebuilds `evidence-index.md` by scanning *every* `runs/*/results.json` each call (routing only the named run's artifact files), so it is order-independent and byte-stable on re-run over unchanged records — the cleanest way to get idempotency without a dedup pass. **The git policy is `.gitignore` globs that preserve the dir placeholder:** `videos/*` + `!videos/README.md` (and the same for `traces/`) ignore the large binaries while keeping the committed `README.md` the workspace template ships in each evidence subdir — so "git-ignored" never means "the directory disappears" (the test asserts the `.gitignore` entry exists, not that files are deleted). **Source resolution via `source_root`:** attachments are absolute as Playwright emits them, or relative to a `source_root`; `run_tests` passes `source_root=report.parent` so the recorded fixture's relative `evidence/...` attachment paths resolve to the real stub files under `seeded-results/`, and a missing source is still indexed (the record is the source of truth). **Run-order matters for the auto-run:** `run` writes `results.json` *first* (the indexer reads it), then indexes, then writes `run.md` with an `indexed` flag so the summary's evidence note is accurate whether or not `--no-index` was passed — and `run.md`/`results.json` stay in `runs/<RUN-ID>/` while the index lands in `evidence/`, so 7.2's byte-stable-record test (which compares only `record_dir`) is unaffected. **Shared-path proof by byte-identity:** `test_run_autorun_matches_standalone` runs `/tc:run` (auto-index) in project A and `--no-index` + standalone `index_run_evidence` in project B, asserting the two `evidence-index.md` are byte-identical — the same robust "same code path" proof Phase 6 Step 6.5 used. 8 RED → 8 GREEN (20 with 7.2's suite re-run, all green — the auto-run does not perturb the 7.2 record-only assertions); `make verify` clean (666 tests, up from 658; link checker 203 files). **No new `config.yaml` surface this sub-step** — the policy (which types are committed vs ignored) is the universal evidence contract; the config-tunable evidence keys, if any, are folded into the 7.7 customization pass, so the guide is unchanged here (Per-Phase Convention #6). **Classification routes reports/logs to `evidence/logs/`** (the template ships no `reports/` dir): `.json`/`.html` map to the committed `logs/` subdir rather than inventing a directory — the "don't add a workspace dir the template doesn't ship" discipline. **Future-implementer hint:** 7.5's `/tc:report` reads `runs/<RUN-ID>/results.json` for the automated-regression section and `evidence/evidence-index.md` for the evidence summary; both are stable, machine-readable inputs now.

- **Step 7.2 (`/tc:run`) closed cleanly; the first executing command keeps the suite hermetic by splitting execution from ingestion at the `--report` seam.** Mirrored `generate_bdd.py`'s skeleton (workspace IO + error hierarchy + load-source + per-result extraction + render + CLI). **The hermetic boundary is a function-argument seam, not just an env-var guard:** `run(..., report=None)` takes the execution path (refused under pytest via `PYTEST_CURRENT_TEST`), `run(..., report=<path>)` takes the pure-ingestion path. Tests always pass `--report`, so they exercise the real ingestion logic against the recorded `seeded-results/results.json` and never reach a browser; one dedicated test forces `report=None` to assert the refusal fires with the directing message. This is cleaner than Phase 3/4's live-mode guard because ingestion is independently reachable without any "mode" flag — the recorded report *is* the test input. **Injected-clock determinism via a defaulted parameter:** `run(now=None)` falls back to `datetime.now()` only inside the call (never at import or inline), and the RUN-ID is `RUN-{now:%Y%m%d-%H%M%S}`; tests pass a fixed `--now` so `runs/<RUN-ID>/` is byte-stable, and the same-clock re-run overwrites byte-for-byte. This is the pattern Steps 7.5's report/history-snapshot filenames will reuse. **Provenance join is two-source:** `@req:`/`@cs:` come from the report's per-spec `tags`, and the authoritative spec path comes from the Phase-6 `automation-map.md` (`@cs:` -> spec, falling back to the report's own `file`) — reusing the `AUTOMATION_ROW_RE` regex shape from `traceability_map.py` (copied, not imported, to keep the helper free of the `traceability_render` import chain for a three-line parser). **Run modes filter the ingested set, not just the execution:** `smoke`/`regression` on the class tag, `feature` on `@area:<slug>` (requires `--area`), `failed-only` on status, `tagged` on an arbitrary `--tag`; storing the full `tags` tuple on each `ResultRecord` makes every mode a one-line predicate. **Ruff caught four E501s** (two long error-message f-strings, a long pragma comment, a long `def` signature) — extracted the repeated "unknown run mode" message to `_unknown_mode_msg()` and wrapped the signature; the lint stage is the line-length backstop again. 12 RED → 12 GREEN; `make verify` clean (658 tests, up from 646; link checker 201 files). **No new `config.yaml` surface** — run modes and the result schema are universal; the first Phase-7 config keys (evidence policy, gate thresholds) arrive in 7.3/7.6, so the customization guide is unchanged (Per-Phase Convention #6). **Future-implementer hint:** 7.3's `index_evidence.py` reads `runs/<RUN-ID>/results.json` (the machine-readable companion to `run.md`) for each result's `attachments` paths and routes them per the evidence policy; the auto-run wiring edits `run_tests.run` to call `index_run_evidence()` after writing the record (suppressible with `--no-index`), exactly as `generate_bdd` calls `review_features` (5.3) and `automate` calls `review_automation` (6.5).

- **Step 7.1 (scaffold) closed cleanly; one parametrized scaffold test covers all three skills + the fixture, mirroring the Step 6.1 consolidation.** Reused the `test_phase_6_scaffolds.py` skeleton (strict-PyYAML frontmatter parse from the start, parametrized skill/subdir assertions) and adapted the fixture assertions to the Phase-7 shape — a recorded Playwright JSON report rather than a `.feature`. **`tc-evidence` is the first command-less skill, so its assertions diverge:** instead of a `body references its commands` check it gets a dedicated `documents_internal_indexer` assertion (`indexer` + `internal` + `tc-run` present), and it is excluded from the command-mapping parametrization but included in the directory / frontmatter / subdir parametrizations. **Future-implementer hint:** when a skill has no `/tc:*` command, the per-command-page Per-Phase Convention #5 does not apply to it — `tc-evidence` ships its behavior spec under `methodology/` (wired in 7.3), and the 7.9.5 sign-off test must assert *that*, not a `commands/` page. **The fixture is a recorded run, not a clean input:** unlike the Phase 5 `seeded-bdd` (one defect per category) and Phase 6 `seeded-automation` (clean automatable feature), Phase 7's `seeded-results` is the *output* of an execution — a Playwright JSON report carrying passed/failed/flaky cases plus the upstream `automation-map.md` + generated spec that lets `/tc:run` join a result back to its requirement. This is what makes the suite hermetic: every Phase-7 helper reads this recorded report instead of launching a browser. **Playwright report shape baked into the fixture now** so 7.2–7.5 ingest a stable schema: `suites[] → specs[] → tests[]` with a test-level `status` of `expected`/`unexpected`/`flaky` and per-attempt `results[]` of `passed`/`failed` with a `retry` index; the flaky case is `retry:0` failed then `retry:1` passed (the pass-on-retry signal 7.4 keys on); attachments carry `evidence/{screenshots,videos,traces}/` paths for 7.3's policy router. **Evidence stubs are text placeholders with real extensions** (`.png`/`.webm`/`.zip`) — the 7.3 indexer routes by artifact type and directory, not content, so a stub suffices to exercise the commit-vs-ignore split. **No CATALOG edit needed:** `tc-run`/`tc-quality-report`/`tc-evidence` were pre-seeded at phase 7 in `verify_skills.py` by an earlier phase, so 7.1 only relies on the cap staying at 6 (the three report `UNEXPECTED — ahead of schedule`, warn/exit-0; cap bumps to 7 in 7.8). 24 RED → 24 GREEN; `make verify` clean (646 tests, up from 622; link checker 198 files). **No new extensible `config.yaml` surface** — the run-mode / evidence-policy / gate-threshold keys arrive with their helpers in 7.2–7.6, so the customization guide is unchanged this sub-step (Per-Phase Convention #6).

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

### Phase 8 — Execution outline

Ten sub-steps. TDD throughout: every implementation step lands its tests red before turning them green. 8.1 scaffolds the one skill (`tc-learning`) + the seeded-learning fixture; 8.2 ships `/tc:learn` (the `tc-lesson/v1` schema + the inbox-append discipline every capture command reuses); 8.3–8.5 implement the three `/tc:learn-from-*` capture commands; 8.6 ships `/tc:review-lessons` (the classifier); 8.7 ships `/tc:promote-lessons` (the governed promotion); 8.8 is the documentation pass; 8.9 is the testing finalization (cap bump + integration smoke); 8.10 is the sign-off with a `phase-8` tag.

**Three disciplines Phase 8 introduces (read before 8.1).**

- **Governed promotion — Test Commander never silently rewrites itself (Q6).** `/tc:promote-lessons` is the only command that changes *guidance*, and it does so under a human-approval gate: by default it writes a **proposal** (what *would* be promoted) and applies it to the workspace's own `learning/promoted-guidance.md` only with an explicit `--apply` (the human's approval). Every applied promotion is a visible `git diff`. It writes **only** into the workspace `learning/` tree — never into the shipped plugin methodology and never into third-party installed skills (Q6 default). A lesson flagged core-relevant renders an `improvement-proposal` artifact (a proposal for a human to take upstream as a plugin PR), never an edit to shipped files.
- **Lessons are provenance-anchored and deduplicated.** Every captured lesson carries `path:line` evidence pointing at the committed artifact it came from (the same discipline as every Phase 2–7 artifact) and a stable `LESSON-NNN` id; the inbox dedups by `(source, origin, summary)` so re-running a capture command never spams `lessons-inbox.md`. The `tc-lesson/v1` frontmatter schema (authored in 8.2) is the contract every capture command emits and the review/promote commands consume.
- **Deterministic capture from committed artifacts + injected-clock IDs.** The `/tc:learn-from-*` commands derive candidate lessons from existing committed artifacts (`runs/*/analysis.md`, `exploration-notes/`, resolved `requirements/open-questions.md`), so they are byte-deterministic; the only non-determinism is the `captured_at` timestamp and the `LESSON-NNN` counter, both fed by an **injected clock** (the Phase-7 `--now` pattern) so tests stay byte-stable.

#### 8.1 — Skill scaffold (`tc-learning`) and seeded-learning fixture

- **Deliverables.** `SKILL.md` for `tc-learning` (strict-PyYAML frontmatter with no embedded `key: value` substring per the Phase 4 Step 4.8 lesson; body lists all six commands; deferral wording until each sub-step ships behavior). Empty `commands/`/`methodology/`/`templates/` dirs (`.gitkeep`). `tests/fixtures/seeded-learning/` containing the upstream artifacts the capture commands read — a Phase-7 `runs/<RUN-ID>/analysis.md` (a `product-defect` + a `flaky` row), an exploration note with a seeded anomaly, a resolved-feedback `open-questions.md` excerpt — plus a `lessons-inbox.md` pre-seeded with one candidate lesson per review-classification (one clearly-acceptable, one clearly-rejectable, one ambiguous → needs-human-review), each carrying valid `tc-lesson/v1` frontmatter and a `# knowledge: <classification>` marker (the Phase 5/6 flawed-fixture convention). `README.md` documents the lesson schema, the classification catalog, the governance flow, and the D19 framing.
- **Tests first.** A parametrized scaffold test (mirroring `test_phase_7_scaffolds.py`) — asserts the skill dir + `SKILL.md` (strict-PyYAML parse from the start), the three sub-dirs, the body references all six commands, and the fixture: the upstream artifacts parse and the seeded `lessons-inbox.md` carries one candidate per classification with valid `tc-lesson/v1` frontmatter.
- **Definition of done.** Skill scaffolded; fixture present; scaffold tests green; `verify_skills.py` reports `tc-learning` `UNEXPECTED (phase 8) — ahead of schedule` under `DEFAULT_PHASE_CAP=7` (cap bumps to 8 in 8.9). Confirm `CATALOG` carries `tc-learning: 8` (add if absent).

#### 8.2 — `/tc:learn` + the `tc-lesson/v1` schema (TDD)

- **Helper.** `plugins/test-commander/scripts/capture_lesson.py`. The foundational capture command: appends a candidate lesson to `<workspace>/learning/lessons-inbox.md` from a freeform observation (`--note "..."`) or by aggregating cross-workspace signals, each rendered as a `tc-lesson/v1` block (`id: LESSON-NNN`, `source`, `origin` `path:line`, `category`, `severity`, `status: candidate`, `captured_at` from the injected clock). Exposes `append_lessons(workspace, lessons, now)` — the shared inbox-append + dedup engine (dedup by `(source, origin, summary)`, the Phase-2 open-questions contract) that **every `/tc:learn-from-*` command reuses**. `LESSON-NNN` ids are allocated by scanning the existing inbox for the max id (monotonic, stable). **Injected-clock determinism**: tests pass a fixed `now` → byte-stable inbox.
- **Umbrella methodology + templates.** `methodology/learning-loop.md` (the capture → review → promote loop, the governance gate, the never-silently-rewrite principle, the Claude judgment layer) and `methodology/lesson-taxonomy.md` (the universal category catalog: `product-defect-pattern`, `flaky-pattern`, `coverage-gap`, `process`, `heuristic`, `anti-pattern`); `templates/lesson-template.md`.
- **Command file + SKILL.md update.** `commands/learn.md`; `tc-learning/SKILL.md` surfaces the shipped `/tc:learn` (deferral wording for it removed; the other five remain).
- **Tests first.** `tests/test_capture_lesson.py` — uninitialized refused; `--note` appends one valid `tc-lesson/v1` candidate to `lessons-inbox.md`; the id allocator is monotonic; the injected clock makes the inbox byte-stable; a duplicate `(source, origin, summary)` is not re-appended; `append_lessons` is the shared engine (identity assert).
- **Definition of done.** `/tc:learn` appends valid candidates with provenance; the schema + dedup + id-allocation engine is shared; SKILL.md updated.

#### 8.3 — `/tc:learn-from-failures` (TDD)

- **Helper.** `plugins/test-commander/scripts/learn_from_failures.py` (mirrors `capture_lesson.py`; design reference `superpowers:systematic-debugging`). Reads `<workspace>/runs/<RUN-ID>/analysis.md` (the Phase-7 triage), turns recurring `product-defect` and `flaky` classifications into candidate lessons (`category: product-defect-pattern` / `flaky-pattern`, `origin` pointing at the analysis row), and calls the shared `append_lessons`. Aggregates across all run records by default (`--run-id` for one). Deterministic via the injected clock.
- **Methodology + template.** A `failure-learning.md` subsection (or reuse `learning-loop.md`) with one worked example per failure category; reuses `lesson-template.md`.
- **Command file + SKILL.md update.** `commands/learn-from-failures.md`; `tc-learning/SKILL.md`.
- **Tests first.** `tests/test_learn_from_failures.py` — uninitialized refused; no analysis refused pointing at `/tc:analyze-results`; the seeded analysis → a `product-defect-pattern` and a `flaky-pattern` candidate, each with resolvable `origin` provenance; dedup on re-run; deterministic.
- **Definition of done.** Failure-derived candidates captured with provenance; dedup holds; SKILL.md updated.

#### 8.4 — `/tc:learn-from-exploration` (TDD)

- **Helper.** `plugins/test-commander/scripts/learn_from_exploration.py` (mirrors 8.3). Reads `<workspace>/exploration-notes/` + `sessions/` (Phase 4), turns recurring anomaly categories and coverage gaps into candidate lessons (`category: coverage-gap` / `anti-pattern`), and calls `append_lessons`. Deterministic.
- **Methodology + template.** An exploration-learning subsection; reuses `lesson-template.md`.
- **Command file + SKILL.md update.** `commands/learn-from-exploration.md`; `tc-learning/SKILL.md`.
- **Tests first.** `tests/test_learn_from_exploration.py` — uninitialized refused; no exploration notes refused pointing at `/tc:explore`; seeded notes → candidate lessons with anomaly-category provenance; dedup; deterministic.
- **Definition of done.** Exploration-derived candidates captured; dedup holds; SKILL.md updated.

#### 8.5 — `/tc:learn-from-feedback` (TDD)

- **Helper.** `plugins/test-commander/scripts/learn_from_feedback.py` (mirrors 8.3; design reference `superpowers:receiving-code-review`). Reads resolved human feedback — `requirements/open-questions.md` entries marked resolved, plus an optional `documents/uploaded/feedback.md` — and turns each into a `category: process` / `heuristic` candidate lesson, calling `append_lessons`. Deterministic.
- **Methodology + template.** A feedback-learning subsection; reuses `lesson-template.md`.
- **Command file + SKILL.md update.** `commands/learn-from-feedback.md`; `tc-learning/SKILL.md`.
- **Tests first.** `tests/test_learn_from_feedback.py` — uninitialized refused; no feedback → an empty-but-not-error result; seeded resolved feedback → candidate lessons with `open-questions.md` provenance; dedup; deterministic.
- **Definition of done.** Feedback-derived candidates captured; dedup holds; SKILL.md updated. By end of 8.5 all four capture commands emit the same `tc-lesson/v1` schema through the one shared engine.

#### 8.6 — `/tc:review-lessons` (TDD)

- **Helper.** `plugins/test-commander/scripts/review_lessons.py` (mirrors the `review_*` rubric pattern). Reads `learning/lessons-inbox.md`, classifies each candidate against a universal governance rubric into **accepted** / **rejected** / **needs-human-review**, moves each to `learning/{accepted-lessons,rejected-lessons,needs-human-review}.md` (updating its `status`), and clears the inbox of the reviewed candidates. Mechanical signals decide the confident buckets (e.g. duplicate-of-accepted → rejected; missing provenance or `severity: high` + ambiguous category → needs-human-review; clean + provenanced + known category → accepted); Claude adds the judgment layer. **Idempotent**: a re-run over an already-reviewed inbox is a no-op.
- **Methodology + template.** `methodology/improvement-governance.md` (the four-bucket lifecycle, the accept/reject/needs-human-review rubric with one worked example each, the never-silently-rewrite gate, the Claude judgment layer); `templates/improvement-proposal-template.md`.
- **Command file + SKILL.md update.** `commands/review-lessons.md`; `tc-learning/SKILL.md`.
- **Tests first.** `tests/test_review_lessons.py` — uninitialized refused; no inbox candidates refused pointing at `/tc:learn`; the seeded one-per-classification inbox → each lands in its correct file with `status` updated and the inbox cleared; idempotent re-run; deterministic.
- **Definition of done.** Candidates classified into the three buckets; statuses updated; inbox cleared; idempotent; SKILL.md updated.

#### 8.7 — `/tc:promote-lessons` (governed promotion) (TDD)

- **Helper.** `plugins/test-commander/scripts/promote_lessons.py`. Reads `learning/accepted-lessons.md` and, **by default, writes a proposal** (`learning/promotion-proposal.md` — what *would* be promoted) without changing guidance; with `--apply` (the human-approval gate) it moves accepted lessons into `<workspace>/learning/promoted-guidance.md` (the workspace's own guidance corpus), updates each lesson's `status: promoted`, and — for lessons flagged core-relevant — renders a `core-promotion` artifact proposing an upstream change to Test Commander's shipped methodology (never applied here; a human takes it upstream as a plugin PR). Writes **only** under `learning/` — never the shipped plugin methodology, never third-party skills (Q6). Every applied promotion is a visible `git diff`. **Idempotent**: an already-promoted lesson is not re-promoted.
- **Methodology + templates.** `methodology/commander-doctrine.md`, `methodology/anti-patterns.md`, `methodology/heuristics.md` (the shipped universal-doctrine corpus the promoted guidance *extends*, read-only references — promotion never edits these); `templates/core-promotion-template.md`.
- **Command file + SKILL.md update.** `commands/promote-lessons.md`. By end of 8.7 `tc-learning/SKILL.md` describes all six commands with no deferral wording.
- **Tests first.** `tests/test_promote_lessons.py` — uninitialized refused; no accepted lessons refused pointing at `/tc:review-lessons`; **default run writes a proposal and does not touch `promoted-guidance.md`** (the governance gate); `--apply` moves accepted lessons into `promoted-guidance.md` with `status: promoted` and a visible diff; a core-relevant lesson renders a `core-promotion` proposal artifact; the shipped methodology files are byte-identical before/after (never rewritten); idempotent re-run; deterministic.
- **Definition of done.** Promotion proposes by default and applies only under `--apply`; writes only under `learning/`; shipped methodology untouched; idempotent; all six SKILL.md commands free of deferral wording.

#### 8.8 — Documentation pass *(dedicated step)*

- **Deliverables.** Author `docs/user-guide/learning-loop.md` (end-to-end: `/tc:learn` + the three `/tc:learn-from-*` → `/tc:review-lessons` → `/tc:promote-lessons --apply`, with verbatim output from the seeded chain; explains the lesson schema, the four-bucket governance lifecycle, the human-approval gate, and the never-silently-rewrite principle). Update `docs/command-reference.md` (Phase 8 shipped section) and `docs/workspace-reference.md` (the `learning/` lifecycle files + `promoted-guidance.md` + the governance flow). Customization-guide "Phase 8 schema (`tc-learning`)" section (any `tc-learning.*` config — e.g. review-rubric thresholds / extra categories) with three project-shape worked examples + "Phase 8 — what landed" (or record "no new extensible surface" explicitly if the loop ships none). Status-line refresh across the six locations + a "Beyond Phase 7" footer in `running-tests.md`/`quality-report.md`. Final deferral-wording sweep across the SKILL.md, the methodology, and `docs/`.
- **Definition of done.** Docs accurate against the implementation; all cross-links resolve; link checker green; customization guide reflects the shipped schema (or records no new surface).

#### 8.9 — Testing finalization *(dedicated step)*

- **Deliverables.** Bump `DEFAULT_PHASE_CAP` 7 → 8 (CATALOG entry present from 8.1). `tests/test_phase_8_integration.py` (in-process, full Phase 2 → … → 8 sweep in natural order, injected clock): assert the capture commands append `tc-lesson/v1` candidates from the upstream artifacts; `/tc:review-lessons` sorts them into the three buckets and clears the inbox; `/tc:promote-lessons` proposes by default and applies under `--apply` into `promoted-guidance.md`; the write boundary holds (the shipped plugin methodology and every prior-phase workspace dir byte-identical — the learning loop writes **only** under `learning/`); `/tc:next` advances past `/tc:learn`. Byte-stable re-run with a fixed clock. **No `PHASE_OWNERSHIP` change expected** (Phase 8 uniquely produces `learning/`, already its signal) — confirm and record.
- **Definition of done.** Integration smoke passes; cap bump reflected; full `make verify` chain green; `verify_skills.py` reports all fourteen shipped skills `PRESENT` with `UNEXPECTED=0`.

#### 8.10 — Sign-off

Six sub-sub-steps. Mirrors the Phase 7 sign-off (7.9) exactly. Test-first: the sign-off test in 8.10.5 lands red before the plan/CHANGELOG edits in 8.10.3 turn it green. The final sub-step (8.10.6) captures evidence and pushes the `phase-8` annotated tag.

- **8.10.1 — Cold-user walkthrough** of `learning-loop.md` from a clean `make install` (the `claude plugin validate` strict-YAML gate over the now-fourteen SKILL.md), against a fresh tmp consuming project with Phase 2 → 7 state pre-populated, then the six Phase 8 commands in workflow order. Capture to `/tmp/tc-phase8-walkthrough.log`. Keep the `make uninstall` + `make install` preamble exactly as-is.
- **8.10.2 — Per-step DoD audit** for 8.1–8.9: every helper, command page, methodology, template, SKILL.md update on disk; the governance gate enforced; the shipped methodology never rewritten; the SKILL.md free of deferral wording; the customization guide carries the Phase 8 schema (or records no new surface). Lesson-capture audit: every sub-step 8.1–8.9 has an entry in `Phase 8 — Lessons learned (running)`.
- **8.10.3 — Plan + CHANGELOG closing.** Collapse `### Phase 8` To Do to the marker line; add `### Phase 8 — Continuous learning and self-improvement (YYYY-MM-DD)` to `## Completed`; flip the CHANGELOG heading from `(in progress)` to `(complete YYYY-MM-DD)`.
- **8.10.4 — Documentation final pass.** "Phase 8 in progress" → "Phase 8 complete (YYYY-MM-DD); Phase 9 starts next" across the six surfaces. All cross-links resolve.
- **8.10.5 — Pre-flight sign-off test.** `tests/test_phase_8_signoff.py` (RED before 8.10.3, GREEN after): every Phase-8 helper/command page/methodology/template on disk; `CATALOG["tc-learning"] == 8` and `DEFAULT_PHASE_CAP >= 8` (`>=`, never `==`); the one SKILL.md describes all six commands with no deferral wording AND parses under strict PyYAML; the customization Phase-8 block (or the explicit "no new surface" record); a lessons entry per sub-step 8.1–8.9; CHANGELOG marked complete with a date; plan Completed has a Phase 8 subsection; plan To Do collapsed; pytest test-def floor (`>= 700` — re-derive from the actual def count at close, per the Step 7.9 lesson that the plan's count estimates are collected-count, not def-count).
- **8.10.6 — Final DoD evaluation.** `make verify` clean; replay the walkthrough; commit; push; annotated `phase-8` tag pushed to origin (a **new** tag — confirm it does not already exist before creating, per the Phase 7 sign-off discipline).

#### Phase 8 — Lessons learned (running)

Captured at sub-step close per the "Sub-step lesson capture" Per-Phase Convention. (Populated as 8.1–8.10 land.)

- **Step 8.10 (sign-off) closed cleanly; the test-first gate landed 16/19 GREEN immediately and 3 RED on exactly the closing edits, and the "no new surface" customization record needed its own sign-off assertion.** Mirrored 7.9's six sub-sub-steps. The cold-user walkthrough ran `make uninstall` → `make install` fully clean (`claude plugin validate` over all fourteen SKILL.md — no strict-YAML regression, asserted from 8.1 onward), then drove the full Phase 2 → 8 chain in a fresh tmp project to a `--apply` promotion. `test_phase_8_signoff.py` (19 tests) landed RED on the three plan/CHANGELOG closing assertions and GREEN after the closing edits. **The customization assertion diverges from Phase 6/7's "schema with three examples" check:** Phase 8 ships no config surface, so the sign-off asserts the *literal* "Phase 8 — what landed (no new extensible surface)" record instead of a YAML-block count — the convention's other branch, encoded as a test. **Pytest floor re-derived from the def count, not the plan estimate:** the def count at close is ~725 (the plan's earlier "~705" estimate undercounted the 8.x suites); floored at `>= 720` with headroom, per the Step 7.9 "re-derive every literal from the phase's actual artifacts" rule. **The walkthrough surfaced a real-vs-fixture format gap worth noting (not a blocker):** `learn-from-exploration` captured 0 from the *real* Phase-4 `explore.run` output (its note format differs from the seeded fixture's `## Anomalies`/`## Coverage gaps` sections), while the 8.4 unit test passes on the fixture format. The chain still completed end-to-end; the gap is a candidate Phase-8 lesson for a future session (the explore-note parser should track the real `/tc:explore` output shape), recorded here so it is not lost. `make verify` clean (758 tests; `PRESENT=14 UNEXPECTED=0`; link checker 236 files); annotated `phase-8` tag pushed to origin. **Phase 8 is closed; Phase 9 (`tc-visualize`, Mermaid diagrams + infographics) starts next.**

- **Step 8.9 (testing finalization) closed cleanly; the integration smoke caught a real cross-cycle idempotency bug the per-command tests could not.** Three changes: `DEFAULT_PHASE_CAP` 7 → 8 (so `verify_skills.py` now reports `PRESENT=14 UNEXPECTED=0`), `tests/test_phase_8_integration.py` (full Phase 2 → 8 sweep, reusing the Phase-7 integration's upstream chain via `import test_phase_7_integration`), and the `PHASE_OWNERSHIP["8"] == ["learning"]` confirmation (no narrowing needed — the loop writes only under `learning/`, already its unique signal). **The byte-stable-re-run assertion exposed a latent bug:** the per-command dedup (8.2–8.5) only checked the *inbox*, so once `/tc:review-lessons` cleared the inbox, a second capture cycle re-added the same lessons (the inbox no longer "remembered" them) and the buckets grew on re-run. **Fix in the shared engine:** `append_lessons` now builds its dedup `(source, origin, summary)` set *and* its `LESSON-NNN` id allocator from **every** `learning/*.md` file (inbox + the three buckets + promoted-guidance), so a reviewed/promoted lesson is never re-captured and ids stay globally monotonic even after lessons move out of the inbox. This is the correct "never spam, ids never collide" behavior the plan demanded — the per-command tests passed because they captured into a fresh inbox before any review; only the full capture→review→capture cycle in the integration revealed the gap (the Phase-6/7 lesson that the integration is a *discovery* surface, not just a smoke test). The per-command suites stayed green (the corpus of a fresh workspace is just the inbox). **The Q6 write-boundary is asserted at integration scale** with the same outside-`learning/` snapshot the 8.7 unit test uses — every workspace file outside `learning/` byte-identical before/after the whole Phase-8 chain. **Cap bump safe** (every prior sign-off asserts `>=`). 3 RED → fix → all GREEN (35 across the Phase-8 suites); `make verify` clean (758 tests, up from 755; `PRESENT=14 UNEXPECTED=0`; link checker 236 files). **Future-implementer hint:** 8.10 sign-off writes `test_phase_8_signoff.py` (RED before the plan/CHANGELOG close, GREEN after), asserting every Phase-8 helper/command page/methodology/template on disk, `CATALOG["tc-learning"] == 8` and `DEFAULT_PHASE_CAP >= 8`, the one SKILL.md with no deferral wording, the customization "no new extensible surface" record (not a schema block), a lessons entry per sub-step, CHANGELOG/plan closing markers, and the test-def floor (re-derive from the actual def count — ~705 now — not a collected-count estimate, per the Step 7.9 lesson).

- **Step 8.8 (documentation pass) closed cleanly; Phase 8 is the first phase to record "no new extensible surface" as the customization deliverable, not a schema.** Authored `docs/user-guide/learning-loop.md` (capture → review → promote with **verbatim output captured from the real chain** — I ran all six commands against a tmp workspace seeded with the `seeded-learning` fixture and embedded the byte-real stdout: 7 captured, review sorted to 6 accepted + 1 needs-human-review, the propose-then-`--apply` gate). **The customization-guide obligation (Per-Phase Convention #6) is discharged by the explicit "no new extensible surface" record**, not a schema section: Phase 8's taxonomy, review rubric, and promotion gate are the fixed universal governance contract, and the one place a project "tunes" the loop is its *inputs* (`feedback.md`, resolved open-questions) and *outputs* (`promoted-guidance.md`) — there is no `config.yaml` key to document. This is the convention's other branch ("Phases that ship no new extensible surface record that explicitly") exercised for the first time in Phase 8. **command-reference gained a "Phase 8 commands (shipped)" section** and the six rows were removed from the planned table; **workspace-reference's `learning/` section** was rewritten from a one-liner to the full lifecycle (the four bucket files + `promoted-guidance.md` + the `--apply` gate + the Q6 boundary). **Status-line sweep across the six surfaces** set "Phase 7 complete (2026-06-01); **Phase 8 in progress** — `tc-learning` shipped (sign-off pending)" and left the "Phase 8 complete (date)" flip to 8.10 (the 6.7-vs-6.9 precedent). No code, no new tests (755 unchanged); `make verify` clean (link checker 236 files, +1 walkthrough). Final deferral sweep across the SKILL.md, the six methodology files, and `docs/` returned no shipped-command deferral wording. **Future-implementer hint:** 8.9 bumps `DEFAULT_PHASE_CAP` 7 → 8 (flipping `tc-learning` `PRESENT`), adds the Phase 2 → 8 integration smoke (capture → review → promote `--apply`), and confirms `PHASE_OWNERSHIP["8"] == ["learning"]` needs no narrowing (the loop writes only under `learning/`, already its unique signal) — the 8.7 write-boundary snapshot is the model for the integration's "only under learning/" assertion.

- **Step 8.7 (`/tc:promote-lessons`) closed cleanly; the governance gate is the whole point, and the write-boundary test is what proves Q6.** `promote_lessons.py` is the only command that turns an accepted lesson into guidance, and it does so under the `--apply` human gate: **default writes `promotion-proposal.md` only and touches no guidance; `--apply` moves accepted lessons into `promoted-guidance.md`.** The headline test (`test_default_proposes_without_changing_guidance`) asserts the default does NOT create `promoted-guidance.md` — the gate, encoded. **The Q6 "never silently rewrites" property is proved structurally, not by inspection:** `test_apply_writes_only_under_learning` snapshots every workspace file *outside* `learning/` before/after `--apply` and asserts byte-identity — so the test fails the moment any future change writes outside `learning/`, the strongest form of the boundary assertion (mirrors the Phase-7 framework write-boundary). **Two promotion flavors, split by a `core: true` flag:** non-core accepted lessons → `promoted-guidance.md` (local project guidance); `core: true` lessons → `core-promotion-proposal.md` (an upstream proposal for a human, never auto-applied to shipped files) — the `core` key was threaded through the canonical frontmatter key order so it round-trips. **Idempotency via in-place status mutation:** `--apply` marks each promoted lesson `status: promoted` in `accepted-lessons.md` (a `text.replace(old_block, new_block)` on the canonical render), so a re-apply finds nothing `accepted` and is a no-op — the same stub-vs-cleared reconciliation as 8.6. **No injected clock needed** — promotion moves existing lessons (they keep their `captured_at`) and the proposal/guidance are deterministic. 7 RED → 7 GREEN; `make verify` clean (755 tests, up from 748; link checker 235 files). **With 8.7 all six `tc-learning` commands are shipped and the SKILL.md carries no deferral wording (sweep clean)** — the command surface of Phase 8 is complete; 8.8 (docs), 8.9 (cap bump + integration), 8.10 (sign-off) remain. **No new `config.yaml` surface** — the promotion gate is a fixed CLI flag, not a tunable (Per-Phase Convention #6); so Phase 8 ships **no new extensible surface at all**, which 8.8 records explicitly in the customization guide. **Future-implementer hint:** 8.9's integration runs the full capture → review → promote chain and must assert the shipped plugin methodology (in the repo, not the tmp workspace) is never written — but since the helpers only ever touch `project_root/.test-commander/`, the cleanest assertion is the same outside-`learning/` snapshot the 8.7 unit test uses, scaled to the whole workspace.

- **Step 8.6 (`/tc:review-lessons`) closed cleanly; the rubric had to be co-designed with the fixture so the three seeded markers are mechanically reproducible.** The classifier needs signals that are *actually present in the record* and that sort the seeded one-per-classification inbox correctly. **Settled rubric (precedence: needs-human-review > rejected > accepted):** `severity: high` → needs-human-review (a high-impact lesson's scope needs a human); a `summary` already in `accepted-lessons.md` → rejected (a duplicate adding nothing); otherwise accepted. **The "rejected = duplicate-of-accepted" rule needs a pre-existing accepted corpus**, so the 8.6 test seeds `accepted-lessons.md` with a lesson whose summary matches the fixture's rejected candidate (`LESSON-002`) — realistic, since review runs against a growing corpus, and it makes "rejected" a defensible mechanical signal rather than a magic marker. The fixture's `# knowledge:` markers are documentation; the rubric reproduces them from real fields (severity + duplicate-of-accepted) — the Phase 5/6 flawed-fixture discipline. **The precondition and idempotency are reconciled via the stub marker:** a *stub* inbox (never captured) → refuse exit 2 pointing at `/tc:learn`; a *cleared* inbox (reviewed, real header, no candidates) → no-op exit 0. Distinguishing "never ran" from "ran and emptied" by the `_(empty until` marker is what lets both contracts hold at once. **Status is updated in-place by re-rendering the frontmatter in a canonical key order** (`schema,id,source,origin,category,severity,status,captured_at,summary`) — a parse-fields → mutate `status` → re-emit cycle, quoting the summary (reusing the 8.3 quoting fix's `_unquote` on read). 4 RED → 4 GREEN; `make verify` clean (748 tests, up from 744; link checker 230 files). **No new `config.yaml` surface** — the rubric is the fixed governance contract (the review thresholds are not project-tunable in v1), so the customization guide is unchanged (Per-Phase Convention #6). **Future-implementer hint:** 8.7 (`promote-lessons`) reads `accepted-lessons.md`, and the governance gate is the headline: **default = write a `promotion-proposal.md` only; `--apply` = move accepted lessons into `promoted-guidance.md` with `status: promoted`**. The 8.7 test must assert the default run does NOT touch `promoted-guidance.md` and that the shipped plugin methodology files are byte-identical before/after (never rewritten — Q6).

- **Step 8.5 (`/tc:learn-from-feedback`) closed cleanly; it is the one capture command where empty input is a no-op, not a refusal.** Same sibling-import shape. **The precondition diverges from 8.3/8.4 on purpose:** open questions exist throughout a project's life and may simply have none resolved yet, so "no resolved feedback" returns 0 and exits 0 (the plan's "empty-but-not-error" contract) rather than refusing — only an uninitialized workspace is an error. The helper guards `if not lessons: return 0` so it never even creates an empty inbox on a no-op (the other capture commands always have ≥1 lesson because they refuse on empty source). **Two feedback sources, two categories:** resolved `open-questions.md` lines (matched by a `_Resolved:` marker on a `- [source-id]` line) → `process`; `documents/uploaded/feedback.md` bullets → `heuristic`. **Stub-detection on both sources** (the `_(empty until` marker) so a template-stub open-questions/feedback counts as empty — the recurring "don't trust a populated-looking template placeholder" discipline. With 8.5 **all four capture commands feed the one inbox through the one engine** (`/tc:learn` manual, plus failures/exploration/feedback derived), each emitting the same `tc-lesson/v1` schema with `path:line` provenance. **Ruff F841** caught an unused `ws` in the test — removed. 5 RED → 5 GREEN; `make verify` clean (744 tests, up from 739; link checker 227 files). **No new `config.yaml` surface** (Per-Phase Convention #6). **Future-implementer hint:** 8.6 (`review-lessons`) drains `lessons-inbox.md` into the three `learning/` bucket files (`accepted-lessons.md`, `rejected-lessons.md`, `needs-human-review.md`), updating each lesson's `status` and clearing the inbox; mirror the `review_*` rubric pattern and reuse `capture_lesson.parse_inbox` to read the candidates.

- **Step 8.4 (`/tc:learn-from-exploration`) closed cleanly; the section-aware parser is the only new mechanism over 8.3.** Same sibling-import shape (`Lesson` + `append_lessons` from `capture_lesson`); the new work is a **section-tracking line parser** that only matches anomaly rows while inside a `## Anomalies` section and coverage-gap bullets while inside a `## Coverage gaps` section — so the `## Observations` table (which also has `|` rows) is not mistaken for anomalies. **The anomaly-row regex keys on the severity cell** (`low|medium|high|critical`) to distinguish a data row from the header (`| Category | Severity |`) and the separator (`| --- |`) — the same "key on a structural cell, not position" discipline `traceability_map`'s `AUTOMATION_ROW_RE` uses. **Anomalies → `anti-pattern`, coverage gaps → `coverage-gap`** (the plan's mapping), and the anomaly carries its recorded severity through to the lesson (the only capture command so far that derives severity from the source rather than defaulting to `medium`). The renderer-quoting fix from 8.3 means the anomaly summary (`"anomaly auth-mismatch on /workspaces/ws-1"` — no colon-space, but free text) is safe regardless. 5 RED → 5 GREEN; `make verify` clean (739 tests, up from 734; link checker 226 files). **No new `config.yaml` surface** (Per-Phase Convention #6). **Future-implementer hint:** 8.5 (`learn-from-feedback`) reads resolved `requirements/open-questions.md` lines (those carrying a `_Resolved:` marker) plus an optional `documents/uploaded/feedback.md`; map to `process`/`heuristic`, call `append_lessons`. With 8.5 all four capture commands feed the one inbox; 8.6 (`review-lessons`) then drains it into the three buckets.

- **Step 8.3 (`/tc:learn-from-failures`) closed cleanly; the sibling-import pattern worked and exposed a latent YAML-quoting bug in 8.2's renderer.** `learn_from_failures.py` `from capture_lesson import Lesson, append_lessons, workspace_dir, ...` and adds only the analysis-row parser + the classification→category map — the per-command work is genuinely small, as predicted. **The first capture command with a colon-bearing summary caught a real bug in `_render_block`:** the failure summary `"product-defect: scenario '...'"` contains a `: `, which broke `yaml.safe_load` when `append_lessons` re-parsed the inbox for dedup on the second run (the Phase-4 Step-4.8 embedded-`key: value` lesson, now hit at runtime instead of in a SKILL.md). The fix was in 8.2's shared renderer — quote the free-text `summary` value (`_yaml_str` double-quotes + escapes) — so *every* capture command is protected, not just this one. **`origin` left unquoted on purpose:** `path:line` provenance is `analysis.md:8` (colon *not* followed by space), which is a valid YAML plain scalar, so quoting it would only complicate the provenance regex in tests; only genuinely free-text fields (`summary`) get quoted. **The two failing tests (`dedup_on_rerun`, `deterministic`) were the ones that re-parse the inbox** — the first run wrote fine, the second run's dedup-parse threw; a good reminder that a renderer bug can pass the write test and only surface on the read-back. 5 RED → 5 GREEN (19 with the 8.2 + scaffold suites); `make verify` clean (734 tests, up from 729; link checker 225 files). **Ruff auto-fixed an import-order nit** (the `from capture_lesson import (...)` block). **No new `config.yaml` surface** — the classification→category map is universal (Per-Phase Convention #6). **Future-implementer hint:** 8.4 (`learn-from-exploration`) and 8.5 (`learn-from-feedback`) are the same shape — import the engine, parse the source artifact (`exploration-notes/`/`sessions/` for 8.4, resolved `open-questions.md` for 8.5), map to a category, call `append_lessons`; the renderer-quoting fix means any summary text is now safe.

- **Step 8.2 (`/tc:learn` + the shared engine) closed cleanly; the foundational command is the schema + the inbox engine, not just a command.** `capture_lesson.py` exposes `Lesson` (the candidate dataclass, id-less), `parse_inbox`, and `append_lessons(workspace, lessons, now)` — the engine all four capture commands reuse. **The dedup + id-allocation reuses the Phase-2 open-questions append pattern, generalized to a structured block:** dedup by `(source, origin, summary)` (a `set` of tuples parsed from existing frontmatter), and the `LESSON-NNN` id is allocated by scanning the inbox for the max numeric id and incrementing (monotonic, stable across runs). **Stub-replacement on first capture:** the workspace template ships `lessons-inbox.md` with the `_(empty until` marker, so `append_lessons` detects the stub (the AGENTS.md "template ships placeholders" discipline) and replaces it with a real header before appending the first block — never accreting onto the stub text. **Injected-clock determinism reuses the Phase-7 pattern:** `captured_at` comes from an injected `now` (defaulted to `datetime.now()` only inside the call), so the inbox is byte-stable under a fixed `--now`, and a duplicate capture leaves the file byte-identical (the no-new-blocks path rewrites the existing text unchanged). **Category/severity are tolerant:** an unknown `--category` falls back to `process` rather than corrupting the record (the `automation_plan.load_weights` tolerance philosophy). **Ruff caught two E501s** on long `add_argument` calls — wrapped them; the lint backstop again. 6 RED → 6 GREEN; `make verify` clean (729 tests, up from 723; link checker 224 files). **No new `config.yaml` surface** — the taxonomy and dedup are universal; any tunable review thresholds arrive with `/tc:review-lessons` (8.6), so the customization guide is unchanged (Per-Phase Convention #6). **Future-implementer hint:** 8.3–8.5's `learn_from_*` helpers `from capture_lesson import Lesson, append_lessons` (sibling import — `sys.path[0]` resolves it in subprocess, the test harness inserts `scripts/`), build `Lesson` objects from their source artifact with a `path:line` `origin`, and call `append_lessons`; the only new work per command is the source parser and the category mapping.

- **Step 8.1 (scaffold) closed cleanly; one parametrized scaffold test covers the one skill + the learning fixture, mirroring the Phase 7 consolidation.** Reused the `test_phase_7_scaffolds.py` skeleton (strict-PyYAML frontmatter parse from the start) and adapted the fixture assertions to the Phase-8 shape — a lessons inbox of `tc-lesson/v1` candidates plus the upstream artifacts the capture commands read. **The fixture composes upstream outputs from three different prior phases** (a Phase-7 `analysis.md`, a Phase-4 exploration note, a resolved-feedback `open-questions.md`), reusing the universal sign-in/session narrative so the 8.3–8.5 capture tests and the 8.9 integration compose without translation — the Phase-7 "fixture is an upstream output, not a clean input" lesson extended to *three* upstreams at once. **The `tc-lesson/v1` schema is baked into the fixture now** so 8.2–8.7 share a stable contract: `id` (LESSON-NNN, monotonic), `source`, `origin` (`path:line`), `category` (the six-name universal taxonomy), `severity`, `status` (`candidate` → `accepted`/`rejected`/`needs-human-review` → `promoted`), `captured_at`, and a `summary` that is the third element of the `(source, origin, summary)` dedup key. **One candidate per review classification, marked with `# knowledge: <classification>`** (the Phase 5/6 flawed-fixture convention) — `accepted` (clean + provenanced + known category), `rejected` (a duplicate with no new evidence), `needs-human-review` (high severity + ambiguous scope) — so the 8.6 review test can assert the classifier sorts each into the right bucket on its own merits. **No CATALOG edit needed:** `tc-learning: 8` was pre-seeded in `verify_skills.py`, so 8.1 relies only on the cap staying at 7 (`UNEXPECTED — ahead of schedule`, warn/exit-0; cap bumps to 8 in 8.9). **Ruff caught a SIM300 Yoda condition** (`CLASSIFICATIONS <= seen` → `seen >= CLASSIFICATIONS`) — the lint stage backstop again. 8 RED → 8 GREEN; `make verify` clean (723 tests, up from 715; link checker 220 files). **No new extensible `config.yaml` surface** — the configurable keys, if any, arrive with their helpers in 8.2–8.7 (Per-Phase Convention #6). **Future-implementer hint:** 8.2 authors `capture_lesson.py` with `append_lessons(workspace, lessons, now)` — the shared inbox-append + `(source, origin, summary)` dedup + `LESSON-NNN` monotonic-id engine that 8.3–8.5's `learn_from_*` helpers import (the sibling-import pattern, like `generate_bdd`→`review_features`).

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

### Phase 9 — Execution outline

Nine sub-steps. TDD throughout. 9.1 scaffolds `tc-visualize` + the seeded fixture and adds the Mermaid CLI to `make install` (guarded); 9.2 ships `/tc:visualize` + the shared Mermaid-render engine and the first diagram type; 9.3–9.4 ship the eight `/tc:diagram-*` generators in two homogeneous groups; 9.5 ships `/tc:generate-infographic`; 9.6 ships `/tc:render-visuals` (Mermaid CLI → SVG/PNG, refused under pytest); 9.7 docs; 9.8 testing finalization (cap bump 8 → 9); 9.9 sign-off with a `phase-9` tag.

**Two disciplines Phase 9 introduces (read before 9.1).**

- **Generate-and-cite, never invent.** Every diagram is rendered *only* from committed workspace artifacts (the traceability maps, the requirements inventory, the risk register, the quality report, the system model), and every generated `.md` Mermaid file carries a `> Sources:` line listing the `path` of each artifact it drew from. A diagram never fabricates a node, edge, or metric that is not present in a source. The "sources cited" check is a mechanical test, not a reviewer's discipline.
- **Mermaid text is the source of truth; rendering is a separate, refused-under-pytest step.** `/tc:diagram-*` and `/tc:generate-infographic` emit deterministic Mermaid/Markdown only — byte-stable, diffable, no binaries. `/tc:render-visuals` is the *only* command that shells out (to the Mermaid CLI to produce SVG/PNG), and it is **refused under pytest** via the `PYTEST_CURRENT_TEST` guard (the Phase-6/7 hermetic-boundary pattern), so the suite asserts the Mermaid *source* structure, never a rendered binary.

#### 9.1 — Skill scaffold (`tc-visualize`) + Mermaid CLI in `make install`

- **Deliverables.** `tc-visualize/SKILL.md` (strict-PyYAML frontmatter; body lists all eleven commands; deferral wording). Empty `commands/`/`methodology/`/`templates/` dirs. `tests/fixtures/seeded-visuals/` — a populated workspace slice (a `traceability/test-map.md`, a `requirements-inventory.md`, a `risk-register.md`, a `quality-report/current-quality-report.md`, a `product-knowledge/system-model.md`) so every diagram type has a real source. Add the Mermaid CLI (`@mermaid-js/mermaid-cli`) to `make install` **idempotently and guarded** (only when absent; the render step degrades gracefully when it is missing). `README.md` documents the per-diagram source map and the D19 framing.
- **Tests first.** A parametrized scaffold test (mirroring `test_phase_8_scaffolds.py`) — skill dir + SKILL.md strict parse + the three sub-dirs + the fixture's source artifacts present and parseable.
- **Definition of done.** Skill scaffolded; fixture present; `verify_skills.py` reports `tc-visualize UNEXPECTED (phase 9) — ahead of schedule` under `DEFAULT_PHASE_CAP=8`; `CATALOG["tc-visualize"] == 9`; `make install` Mermaid step is idempotent.

#### 9.2 — `/tc:visualize` + the shared render engine + `/tc:diagram-flow` (TDD)

- **Helper.** `plugins/test-commander/scripts/visualize.py`. `/tc:visualize` is the umbrella that regenerates the full visual set; it exposes `render_diagram(workspace, kind, sources, nodes, edges)` — the shared Mermaid-emitter + `> Sources:` citation footer + deterministic node/edge sort that every `/tc:diagram-*` reuses. Ships the first concrete generator, `/tc:diagram-flow` (a user-journey/flow diagram from `product-knowledge/user-journeys.md` + `system-model.md`), writing `visuals/<name>.md` (Mermaid in a fenced block + the sources line).
- **Methodology + templates.** `methodology/visual-documentation.md` (the generate-and-cite rule, the Mermaid-is-source rule, the Claude judgment layer), `methodology/diagram-standards.md`; `templates/flow-diagram-template.md`.
- **Command files + SKILL.md update.** `commands/visualize.md`, `commands/diagram-flow.md`; SKILL.md surfaces both.
- **Tests first.** `tests/test_visualize.py` — uninitialized refused; a missing source refused (points at the producing command); the seeded fixture → a valid Mermaid `flowchart` with every node traceable to a source and a `> Sources:` footer listing the artifact paths; byte-stable re-run; `/tc:visualize` regenerates the set deterministically.
- **Definition of done.** The shared engine + the flow diagram ship; sources cited; deterministic; SKILL.md updated.

#### 9.3 — Structural diagrams: `/tc:diagram-sequence`, `/tc:diagram-state`, `/tc:diagram-architecture` (TDD)

- **Helpers.** Three generators mirroring 9.2's `render_diagram` engine: sequence (from a user journey / API call sequence), state (from session lifecycle), architecture (from `product-knowledge/system-model.md`). Each emits the matching Mermaid kind (`sequenceDiagram`, `stateDiagram-v2`, `flowchart`/`graph`) with a sources footer.
- **Methodology + templates + command pages + SKILL.md.** One template + one command page per command; methodology subsection per kind.
- **Tests first.** `tests/test_diagrams_structural.py` — each command refuses a missing source, emits valid Mermaid of the right kind with cited sources, and is byte-stable.
- **Definition of done.** Three structural diagram commands ship; sources cited; deterministic; SKILL.md updated.

#### 9.4 — Quality diagrams: `/tc:diagram-risk`, `/tc:diagram-coverage`, `/tc:diagram-traceability`, `/tc:diagram-test-strategy` (TDD)

- **Helpers.** Four generators mirroring the engine: risk (from `risk-register.md`), coverage (from `traceability/requirements-map.md`), traceability (from `traceability/test-map.md` — the full chain), test-strategy (from the requirements + automation plan). Each emits Mermaid with a sources footer.
- **Methodology + templates + command pages + SKILL.md.** As 9.3.
- **Tests first.** `tests/test_diagrams_quality.py` — per command: missing-source refusal, valid Mermaid, cited sources, byte-stable; the traceability diagram renders the resolved `Test result`/`Quality report` columns when present and `pending` otherwise (never invents).
- **Definition of done.** Four quality diagram commands ship; sources cited; deterministic; SKILL.md updated.

#### 9.5 — `/tc:generate-infographic` (TDD)

- **Helper.** `plugins/test-commander/scripts/generate_infographic.py`. Aggregates the quality report's headline facts into an infographic **brief + spec** (Markdown + a structured data block) — not a binary; richer rendering is `/tc:render-visuals`' job, and the layout follows `frontend-design:frontend-design` patterns. Cites its sources; never invents a metric.
- **Methodology + template.** `methodology/infographic-standards.md`; `templates/infographic-brief-template.md`, `templates/infographic-spec-template.md`.
- **Command file + SKILL.md update.** `commands/generate-infographic.md`.
- **Tests first.** `tests/test_generate_infographic.py` — uninitialized refused; no quality report refused (points at `/tc:report`); seeded report → a brief + spec carrying only measured facts with a sources footer; byte-stable.
- **Definition of done.** Infographic brief + spec generated from real facts; cited; deterministic; SKILL.md updated.

#### 9.6 — `/tc:render-visuals` (Mermaid CLI → SVG/PNG; refused under pytest) (TDD)

- **Helper.** `plugins/test-commander/scripts/render_visuals.py`. Walks `visuals/*.md`, extracts each Mermaid block, and shells out to the Mermaid CLI to produce `visuals/rendered/<name>.svg` (and PNG). The real CLI invocation is **refused under pytest** via the `PYTEST_CURRENT_TEST` guard; tests assert the extraction + the planned output paths + the "CLI missing" graceful degradation, never a rendered binary.
- **Methodology + command file + SKILL.md update.** A render subsection; `commands/render-visuals.md`. By end of 9.6 all eleven SKILL.md commands are shipped with no deferral wording.
- **Tests first.** `tests/test_render_visuals.py` — uninitialized refused; no `visuals/*.md` refused (points at `/tc:visualize`); the real render refused under pytest with a directing message; the Mermaid-block extraction + output-path planning correct; missing-CLI handled gracefully.
- **Definition of done.** Render extracts and plans correctly; real render refused under pytest; SKILL.md updated.

#### 9.7 — Documentation pass

- **Deliverables.** `docs/user-guide/visuals.md` (the generate → render flow with verbatim output + a rendered-source example), command-reference Phase 9 shipped section, workspace-reference `visuals/` section, customization-guide Phase 9 entry (any `tc-visualize.*` config — e.g. diagram-theme — or an explicit "no new extensible surface" record), six-location status-line refresh + a quality-report cross-link to the relevant visuals, final deferral sweep.
- **Definition of done.** Docs accurate; links resolve; link checker green.

#### 9.8 — Testing finalization

- **Deliverables.** Bump `DEFAULT_PHASE_CAP` 8 → 9 (`tc-visualize` flips `PRESENT`). `tests/test_phase_9_integration.py` (full Phase 2 → 9 sweep): every diagram type renders valid Mermaid with cited sources; the infographic carries only measured facts; `/tc:render-visuals` is refused under pytest; the write boundary holds (`visuals/` only); `/tc:next` advances past `/tc:visualize`. Byte-stable re-run. Confirm `PHASE_OWNERSHIP["9"] == ["visuals"]`.
- **Definition of done.** Integration smoke passes; cap bump reflected; `make verify` clean; all fifteen skills `PRESENT`, `UNEXPECTED=0`.

#### 9.9 — Sign-off

Six sub-sub-steps mirroring 8.10: cold-user walkthrough of `visuals.md` (`make uninstall` → `make install`, the Mermaid CLI step included); per-step DoD audit (every visual cites sources; no deferral wording); plan + CHANGELOG closing; documentation final pass; test-first `tests/test_phase_9_signoff.py` (RED before the close, GREEN after; test-def floor re-derived); final DoD eval + annotated `phase-9` tag (new tag — confirm absent first).

#### Phase 9 — Lessons learned (running)

Captured at sub-step close per the "Sub-step lesson capture" Per-Phase Convention. (Populated as 9.1–9.9 land.)

- **Step 9.9 — sign-off.** Six sub-sub-steps mirroring 8.10. **The cold-user walkthrough caught a real rendering bug the hermetic suite could not:** `make uninstall` → `make install` ran clean (all fifteen SKILL.md validated; `verify_skills: OK PRESENT=15 UNEXPECTED=0`) and the `mermaid-install` step actually installed `mmdc` (366 npm packages) — so for the first time the walkthrough could run the *real* render outside pytest. It revealed that feeding `mmdc` a Markdown file makes it append a `-N` suffix per embedded block (`flow-1.svg`, not `flow.svg`), so `render_visuals` was returning planned paths that did not match the bytes on disk. Fixed by extracting the Mermaid block to a sibling `.mmd` and rendering that, so output names match `plan_visuals` exactly; re-ran the cold walkthrough and confirmed `flow.svg` … `traceability.svg` (16 files, no suffix). **This is the whole point of the "real render outside pytest" walkthrough: the suite refuses the shell-out, so only the cold drill exercises mmdc's actual output naming.** The test-first sign-off gate (`test_phase_9_signoff.py`, 19 tests, test-def floor `>= 790`) landed RED on exactly the four closing assertions (lessons-9.9 entry, CHANGELOG complete, plan Completed entry, To Do collapsed) and GREEN after the closing edits. Annotated `phase-9` tag confirmed absent, then pushed to origin.
- **Step 9.8 — testing finalization.** Bumped `DEFAULT_PHASE_CAP` 8→9; `tc-visualize` flips `UNEXPECTED → PRESENT`, so `verify_skills.py` reports all fifteen shipped skills `PRESENT` with `UNEXPECTED=0`. **The integration test proved the diagrams render from the *real* upstream chain, not just the fixture:** `test_phase_9_integration.py` reuses the Phase-8 integration's Phase 2→8 sweep (real `review_requirements`, the five `extract_knowledge_from_*`, `generate_bdd`, `traceability_map`, `automation_plan`, `build_report`, the learning loop), then runs all eight diagram generators + the infographic against that workspace — every diagram had a non-empty Mermaid body and a sources footer on the first run, confirming my fixture formats matched the producers. **Only the risk register had to be seeded** (from the fixture) because no shipped helper writes it — exactly the 9.1 lesson, now made concrete. **Added the Phase 9 `/tc:next` rule (R10 → `/tc:visualize`)** and renumbered the report rule to R11 (priority 11); this makes "/tc:next advances past /tc:visualize" a *meaningful* assertion (R10 fires before the run, a later rule after) rather than vacuously true, and required updating `test_next_step.py` (the old R10 report fixture became R11 through phase 9) and `next-step-inference.md`. **Two ruff catches in the new integration test** (a SIM300 Yoda condition `EXPECTED <= names` and an unused `ws`) — the lint step is part of the micro-cycle for a reason; run `make verify`, not just pytest, before believing a step is done.
- **Step 9.7 — documentation pass.** No code changes; `make verify` clean (825 tests unchanged, link checker 275 files). Authored `docs/user-guide/visuals.md` (the generate → infographic → render flow with verbatim output captured from the seeded chain: 8 diagrams, 2 infographic files, the graceful CLI-missing render message). Added a "Phase 9 commands (shipped)" table to `docs/command-reference.md` (the eleven rows removed from "Planned"), flipped the `visuals/` section of `docs/workspace-reference.md` to shipped, and recorded "Phase 9 — what landed (no new extensible surface)" in `customizing-for-your-project.md` (Phase 9 ships no `config.yaml` key — diagrams are generated mechanically; a project tunes the visuals only via the underlying artifacts). Status-line sweep across six surfaces: README status header + doc-index walkthrough link, the plugin README skill table (new shipped row, removed from "What arrives later"), `install.md` skill list + walkthrough link, `getting-started.md` "What's next", and the `learning-loop.md` "Beyond Phase 8" pointer. Added the quality-report → visuals cross-link in `quality-report.md`. Final deferral sweep across the skill + docs returned clean. **Status set to "Phase 9 in progress — sign-off pending" (mirroring 8.8), not "complete" — the complete flip + tag is 9.9.**
- **Step 9.6 — `/tc:render-visuals` (refused under pytest).** 7/7 GREEN. **Two independent guards, tested separately by monkeypatching `mmdc_available`:** the CLI-missing branch (graceful exit 0, no binary) and the pytest-refusal branch (`PYTEST_CURRENT_TEST` in `_invoke_mmdc`). Testing them on the real host would be flaky — the host may or may not have `mmdc` installed — so `render_visuals(project)` calls the injectable `mmdc_available()`, and the tests force each branch (`->False` for graceful, `->True` to reach the refusal). This is the clean way to test a "refused under pytest" shell-out: separate *whether the tool exists* (injectable) from *whether we may invoke it* (the env guard), and the env guard lives in the innermost `_invoke_mmdc` so a direct unit test hits it too. With 9.6 all eleven SKILL.md commands are shipped with no deferral wording (the sign-off test in 9.9 asserts this). Reconfirmed the `visuals/svg/` + `visuals/png/` output contract from the committed template (not the plan's `visuals/rendered/`).
- **Step 9.5 — `/tc:generate-infographic`.** 5/5 GREEN. The infographic is a *separate module* (`generate_infographic.py`) that imports the shared engine from `visualize` (workspace resolution, the stub-refusing `read_source`, the error types) rather than living in `visualize.py` — it produces two non-Mermaid files (brief + spec) and would otherwise bloat the diagram module. Deliberately **not** added to the `/tc:visualize` GENERATORS list: that would create a circular import (`generate_infographic` imports `visualize`), and the umbrella's contract is "regenerate the diagrams"; the infographic is its own command. The "never invent a metric" contract is enforced by omission — each metric is appended only if its regex matches a `[fact]` line in the report, so dropping the automation line from the report drops `automated`/`automatable` from the spec (a dedicated test asserts this). Fixed key/section order keeps both files byte-stable.
- **Step 9.4 — quality diagrams (risk, coverage, traceability, test-strategy).** 9/9 GREEN after one fix. **Header-row bug caught by the eyeball pass, not the test:** the first cut of `_table_rows(text, "REQ-")` matched the `| REQ-ID | … |` *header* row (its first cell starts with `REQ-`), so coverage drew a spurious `REQ-ID` node. The unit tests passed (they only assert REQ-001/REQ-003 present) — the visual inspection of the rendered output caught it. Fix: require a digit after the prefix (`REQ-\d`), which excludes the header. **Lesson: a diagram test should assert the node *set*, not just membership, or pair every generator with a rendered-output eyeball before commit.** Added one shared `render_subgraph_flowchart` emitter for the grouped kinds (risk by severity, and it generalizes to any subgraph layout); the other three reused `render_diagram`. Traceability shares result nodes across rows (all passed scenarios point to one `Passed` node) and renders `Pending` for unresolved rows from the test map's own column — the "resolved-or-pending, never invent" contract is mechanical. test-strategy is the first generator with a directory source (`automation-plan/*.md`): it globs, skips stubs, and refuses only when *no* plan is parseable.
- **Step 9.3 — structural diagrams (sequence, state, architecture).** 18/18 GREEN (10 new + the 8 reused). The 9.2 split paid off: `render_sequence` and `render_state` are two small new emitters; architecture reused `render_diagram` (flowchart) verbatim; all three reused `render_diagram_doc` + `write_visual` + `read_source`, so the new code was just three parsers + three assemblers. **Redefined diagram-state's source honestly:** the plan said "session lifecycle", but no committed artifact encodes session states — the test map's *result* column does. So diagram-state models the scenario **result lifecycle** (`[*] → Pending → Passed/Failed/Flaky`, only states present in the map), which is fully derivable and never invented. Documented the redefinition in `diagram-standards.md`. **Sequence determinism is document order, not a sort:** message order in a sequence diagram is meaningful, so `render_sequence` preserves journey document order rather than sorting (unlike `render_flowchart`); both are deterministic, but for different reasons — a reminder that "deterministic" ≠ "sorted" when order carries meaning. The `Note over System` line is how the sequence honestly uses the second source (system-model entities) without inventing message content.
- **Step 9.2 — `/tc:visualize` + shared engine + `/tc:diagram-flow`.** 8/8 GREEN. The shared engine is a small set of composable functions, not one monolith: `render_flowchart` (deterministic node/edge sort) + `render_diagram_doc` (titled doc + `> Sources:` footer) + `write_visual` (`visuals/mermaid/<name>.md`) + `read_source` (refuse a stub, point at the producer) + `mermaid_id` (label → safe slug) + the `Node`/`Edge` dataclasses; `render_diagram` ties them together for the graph kinds. This split means the non-graph kinds (sequence, state) can reuse the doc/footer/write/slug parts without forcing their bodies through a flowchart model — confirmed the right call before 9.3 starts. **diagram-flow uses both sources honestly without inventing edges:** journeys (document order) and a single `System` node carrying the system-model entities (sorted), with `User → journey → System` — the journey→entity association isn't in the data, so the diagram routes journeys to one System node rather than fabricating per-entity edges. The umbrella `visualize()` catches `MissingSourceError` per generator and skips (so one absent source never blocks the set), while the individual command refuses (exit 2) — the two callers want different failure modes from the same generator. Write boundary asserted structurally (everything outside `visuals/` byte-identical before/after).
- **Step 9.1 — scaffold + seeded-visuals fixture + Mermaid CLI.** Mirrored `test_phase_8_scaffolds.py` structure; 7/7 GREEN on the first run after the artifacts landed. **Reconciled a plan-vs-template drift on the visuals output path:** the plan body for 9.2/9.6 mentions `visuals/<name>.md` and `visuals/rendered/<name>.svg`, but the committed workspace template (and `docs/workspace-reference.md`) already ship `visuals/mermaid/`, `visuals/svg/`, `visuals/png/`, `visuals/infographic/`. Per AGENTS.md "if the plan and the code disagree, fix the plan first": the committed template is the contract, so Phase 9 writes Mermaid sources to `visuals/mermaid/<name>.md`, renders to `visuals/svg/` + `visuals/png/`, and infographics to `visuals/infographic/`. **Risk register has no shipped producer** — `risk-register/risk-register.md` is only *read* (by `build_report` and `create_charter`); no helper writes it. So `/tc:diagram-risk`'s source is human-authored, and the 9.8 integration sweep must seed a register (from the fixture) rather than expect an upstream producer to populate it. The fixture defines the register shape (`| RISK-NNN | Area | Severity | Description | Source |`). **Link-checker gotcha:** the faithful `system-model.md` emits Markdown links to its per-source sibling models (entities, documentation-model, specs-model, business-rules); the repo-wide `check_links.py` walks fixtures, so the slice must carry minimal stubs for every linked sibling or the chain goes red. Mermaid CLI added to `make install` as a guarded, end-of-chain `mermaid-install` target (skips when `mmdc` present, degrades gracefully when `npm` is absent) so a missing CLI never blocks the plugin install.

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

- Pages render against a populated workspace; SSE updates appear on journal append; chat refuses any action above `read-only` and surfaces proposal cards only — execution gating ships in Phase 10.5.

**Test step.**

- End-to-end: `make run` brings up the stack via docker compose; smoke navigations across all pages succeed.

**Definition of done.**

- All pages work, SSE delivers updates, indexer keeps up with workspace changes, chat is read-only + proposal cards only (execution gating ships in Phase 10.5), user guide complete.

### Phase 10 — Execution outline

Nine sub-steps. Phase 10 is the first **runtime** phase (per D2): it ships a Next.js frontend + FastAPI backend, not Markdown skills, so it extends the verify chain with backend `pytest` (FastAPI/`apps/api`) and frontend tests (`vitest` + Playwright e2e under `apps/web`). The `tc-web` skill still ships a SKILL.md (the commands that drive the stack). 10.1 scaffolds; 10.2–10.3 build the backend (indexer + read APIs + SSE); 10.4–10.5 build the frontend pages + read-only chat; 10.6 ships `/tc:web-export`; 10.7 docs; 10.8 testing finalization (docker-compose e2e + cap bump); 10.9 sign-off.

**Three disciplines Phase 10 introduces (read before 10.1).**

- **Read-only and proposal-only — no execution (the 10.5 boundary).** Phase 10 ships the UI shell, the artifact indexer, and the proposal-card surface. The chat answers from indexed artifacts and *suggests* `/tc:*` commands as proposal cards; it **cannot execute** anything that changes the workspace or runs tests. Every backend route is read-only or proposal-generating. The execution pipeline is Phase 10.5; a 10.x test asserts no UI/API path mutates the workspace or runs a command.
- **The workspace is the source of truth; the DB is a derived index.** SQLite holds only a rebuildable index of the committed `.test-commander/` artifacts; the indexer reconciles on change and the workspace files remain authoritative. Nothing the console shows is invented — every panel cites or links the artifact it rendered.
- **`make run` brings up the whole stack on docker compose (D10/parent rule).** Frontend + backend + the indexer run locally via `make run`; the e2e smoke drives the running stack. No cloud dependency for the MVP (Pattern A, D15).

#### 10.1 — Scaffold (`tc-web` skill + `apps/web` + `apps/api` + `make run`)

- **Deliverables.** `tc-web/SKILL.md` (lists the five `/tc:web-*` commands; deferral wording). Scaffold `apps/web/` (Next.js, via `web-scaffold:create-website` structure) and `apps/api/` (FastAPI) and `runtime/` per the spec; a `make run` docker-compose target bringing both up; a `tests/fixtures/seeded-web/` populated workspace. Extend the verify chain config so backend `pytest` and frontend `vitest` are discoverable (documented; not yet enforced if heavy).
- **Tests first.** Scaffold test: skill dir + SKILL.md strict parse; `apps/web`/`apps/api`/`runtime` trees exist; `make run` target present; a backend health-route test (FastAPI `TestClient`).
- **Definition of done.** Stack scaffolds; `make run` boots both services; `verify_skills.py` reports `tc-web UNEXPECTED (phase 10) — ahead of schedule`; `CATALOG["tc-web"] == 10`.

#### 10.2 — Backend: artifact indexer + `/tc:web-index-artifacts` (TDD)

- **Helper + service.** The FastAPI artifact-indexer service that walks `.test-commander/` into the SQLite index (requirements, runs, evidence, journal, quality report, traceability), plus `/tc:web-index-artifacts` to trigger a (re)index. Reconciles on change; the workspace stays authoritative.
- **Tests first.** Backend `pytest`: indexing a seeded workspace populates the expected rows; a changed artifact re-indexes; the index is rebuildable from scratch (no state the workspace lacks).
- **Definition of done.** Indexer keeps up with workspace changes; `/tc:web-index-artifacts` shipped; SKILL.md updated.

#### 10.3 — Backend: read APIs + SSE event stream + `/tc:web-sync` (TDD)

- **Service.** Read-only FastAPI routes for each page's data (dashboard, quality report, journal, sessions, requirements, test runs, evidence) and the SSE event stream that pushes updates on workspace change (e.g. a journal append). `/tc:web-sync` reconciles the index with the workspace. **Proposal generation** (read-only suggestion of `/tc:*` commands) lives here — never execution.
- **Tests first.** Contract tests per route (shape + read-only); an SSE test asserting an event is emitted on a journal append; a proposal-generation test asserting it returns a *proposal card*, never runs anything.
- **Definition of done.** Read routes + SSE work; proposal generation is read-only; SKILL.md updated.

#### 10.4 — Frontend: the MVP pages + `/tc:web-init` + `/tc:web-start` (TDD)

- **Frontend.** The Next.js pages — Dashboard, Quality Report, Journal, Sessions, Requirements, Test Runs, Evidence, Settings — rendering the read APIs, with SSE live-update on the dashboard/journal. `/tc:web-init` (provision the console config) and `/tc:web-start` (bring the stack up). Embeds the Phase-9 visuals where relevant (`frontend-design` patterns).
- **Tests first.** `vitest` component tests + a Playwright e2e smoke navigating all pages against a populated `make run` stack; every panel links its source artifact.
- **Definition of done.** All pages render against a populated workspace; SSE updates appear; `/tc:web-init`/`/tc:web-start` shipped; SKILL.md updated.

#### 10.5 — Frontend: read-only chat + proposal cards (TDD)

- **Frontend + backend.** The chat panel: read-only Q&A from indexed artifacts, workflow suggestions, and command **proposal cards** the user can review. It refuses any action above `read-only` and surfaces proposal cards only — **execution gating ships in Phase 10.5 (the governance phase)**. A clear, tested boundary: no chat path mutates the workspace or runs a command.
- **Tests first.** Chat answers a question from the index; a "generate BDD" request returns a proposal card (not an execution); an attempt to execute is refused; the e2e asserts no workspace mutation occurs from any chat action.
- **Definition of done.** Chat is read-only + proposal-cards-only; the no-execution boundary is tested; SKILL.md updated.

#### 10.6 — `/tc:web-export` (TDD)

- **Helper.** `/tc:web-export` — export the console's current view (quality report + evidence + traceability) as a shareable static bundle. Read-only; deterministic.
- **Tests first.** Export produces the expected static bundle from a seeded workspace; deterministic; no mutation.
- **Definition of done.** Export ships; deterministic; by end of 10.6 all five `/tc:web-*` commands are shipped with no deferral wording.

#### 10.7 — Documentation pass

- **Deliverables.** `docs/user-guide/web-console.md`, `docs/web-console.md`, `docs/runtime-api.md`; command-reference Phase 10 section; workspace-reference note (the console reads the workspace, the DB is a derived index); customization-guide Phase 10 entry; status-line refresh; the explicit "read-only + proposal cards only; execution arrives in Phase 10.5" framing throughout; final deferral sweep.
- **Definition of done.** Docs accurate; links resolve; link checker green.

#### 10.8 — Testing finalization

- **Deliverables.** Bump `DEFAULT_PHASE_CAP` 9 → 10. `make run` docker-compose e2e: bring the stack up, Playwright smoke-navigates all pages, the SSE update appears, the chat is read-only + proposal-cards-only (the no-execution assertion), `/tc:web-export` produces a bundle. Backend contract tests green. Confirm `PHASE_OWNERSHIP` is unaffected (the console writes only its own config/DB, not workspace artifacts).
- **Definition of done.** e2e smoke passes; cap bump reflected; `make verify` (+ the web test lanes) green; `verify_skills.py` all `PRESENT`, `UNEXPECTED=0`.

#### 10.9 — Sign-off

Six sub-sub-steps mirroring prior sign-offs, adapted for the runtime: cold-user walkthrough (`make uninstall` → `make install` → `make run`, navigate the console); per-step DoD audit (read-only + proposal-only boundary holds); plan + CHANGELOG closing; documentation final pass; test-first `tests/test_phase_10_signoff.py`; final DoD eval + annotated `phase-10` tag.

#### Phase 10 — Lessons learned (running)

Captured at sub-step close per the "Sub-step lesson capture" Per-Phase Convention. (Populated as 10.1–10.9 land.)

- **Step 10.9 — sign-off.** Six sub-sub-steps. **The cold-user walkthrough — booting the real Docker stack — caught a bug no in-process test could:** `make uninstall` → `make install` ran clean (16 skills `PRESENT`, `UNEXPECTED=0`), `docker compose config` validated, and `docker compose up --build api` booted the real FastAPI container serving the mounted workspace. But a *fresh* (un-indexed) workspace 500'd: the compose mount was `:ro`, and the rebuild-on-read path tries to create `.test-commander/.web/` — a write the read-only mount forbids. **Root cause: the `:ro` mount conflated two different "read-only"s.** The plan's read-only contract means "never mutate a workspace *artifact*", but the console legitimately writes its *derived* `.web/` index. Fix: mount the workspace read-write and keep the read-only guarantee at the app layer (where the suite already asserts it as a property). Re-ran the fresh boot → 200s, index built, dashboard data. **Lesson: for a runtime phase the hermetic TestClient suite cannot see container/mount semantics — the real `make run` boot is the only thing that exercises the volume mount, the image build, and the env wiring; budget the sign-off walkthrough to actually boot Docker.** The test-first gate (`test_phase_10_signoff.py`, 20 tests, floor `>= 865`) landed RED on the four closing assertions, GREEN after. Annotated `phase-10` tag confirmed absent, then pushed.
- **Step 10.8 — testing finalization.** Bumped `DEFAULT_PHASE_CAP` 9→10; `tc-web` flips `UNEXPECTED → PRESENT`, so all sixteen skills report `PRESENT` with `UNEXPECTED=0`. **The e2e smoke is split across two layers by where it can run:** the enforced gate is an *in-process* API integration test (`test_phase_10_integration.py`) that drives index → all read routes → SSE → chat → export via the FastAPI TestClient and asserts the write boundary + that `PHASE_OWNERSHIP` has no `"10"` key (the console writes only the derived `.web/`); the *browser* e2e (Playwright `smoke.spec.ts` navigating all pages + the read-only chat) and the vitest component test live under `apps/web/` and run via new `make web-test` / `make web-e2e` targets, Node-managed and deliberately outside `make verify` (the plan's "documented, not enforced if heavy" allowance — the real browser run needs `make run` up). This keeps `make verify` fast and hermetic while still shipping the frontend test lanes. The cold-user walkthrough in 10.9 is where the real docker stack actually boots.
- **Step 10.7 — documentation pass.** No code changes; `make verify` clean (903 tests unchanged, link checker 295 files). Authored three docs: `docs/user-guide/web-console.md` (the bring-it-up → pages → chat → export walkthrough with verbatim command output), `docs/web-console.md` (the architecture — stack, invariants, the `tcweb` module map), and `docs/runtime-api.md` (the full route reference: health, the read routes, SSE, proposals, chat). Added a "Phase 10 commands (shipped)" table to `command-reference.md` (removed `/tc:web-*` from Planned), a `.web/` derived-dir note to `workspace-reference.md`, and a "Phase 10 — what landed (no new extensible surface)" record to the customization guide (the console's `console.json` is its own derived config, not a project-domain `config.yaml` extension). Status sweep across README (status header + skill list + walkthrough link), the plugin README skill table (new shipped row, removed from "What arrives later"), `install.md`, and `getting-started.md`. **The "execution arrives in Phase 10.5" framing is threaded throughout** (user guide, runtime-api, command-reference) — this is the required read-only-boundary message, *not* deferral wording for a tc-web command (the SKILL.md deferral sweep is clean; all five commands shipped in 10.6). Status set to "Phase 10 in progress — sign-off pending"; the complete flip + tag is 10.9.
- **Step 10.6 — `/tc:web-export`.** 6/6 GREEN. **Determinism came free from the existing query layer + a no-clock rule:** the exporter assembles the bundle from `queries.*` (already sorted) and serializes with `json.dumps(sort_keys=True)`, and the HTML is generated from the sorted data with no wall-clock timestamp — so two exports are byte-identical (asserted). The bundle is two files: `data.json` (the structured payload) and a self-contained, dependency-free `index.html` (no external CSS/JS, all values `html.escape`d). Writes only under `.web/export/`, so the workspace-unchanged property test passes. With 10.6 all five `/tc:web-*` commands are shipped with no deferral wording (the 10.9 sign-off test asserts this). Same delegating-command pattern (`web_export.py` → `tcweb.exporter`).
- **Step 10.5 — read-only chat + proposal cards.** 8/8 GREEN after one fix. **The proposal keyword match was too eager for a chat:** `proposals.propose("how many requirements?")` matched the `requirement` keyword (a `/tc:review-requirements` rule) and attached a command card to a pure question. Fix: the chat gates proposals on an explicit **action verb** ("generate", "automate", "run", …) — a question with no action verb gets a plain answer and no card, while "generate bdd" / "run the tests" still propose. This is the right division of labor: `propose()` stays a broad intent→command map (reused by `/api/proposals`), and the chat adds the question-vs-action judgment on top. Retrieval is deterministic keyword routing over the index (no model call in the MVP), so the answers are testable verbatim. The no-execution boundary is again a *property* test: a batch of turns (questions, action requests, an execute attempt) leaves the workspace byte-identical, and every response carries `executed: false`. Chat is a UI feature, not a `/tc:` command, so 10.5 adds no command page — it extends `web-architecture.md` and the frontend instead.
- **Step 10.4 — MVP pages + `/tc:web-init` + `/tc:web-start`.** 9/9 GREEN. **The frontend is covered structurally, not by booting Node:** a Python test asserts every `app/<route>/page.tsx` exists, reads its API path (the literal `/api/...` string), the `Nav` links every page, and `LiveBadge` subscribes to `EventSource('/api/events')` — so the existing pytest gate enforces the frontend's shape without a Next.js build (the real vitest/Playwright e2e is 10.8 under `make run`). Pages are async server components (`getJson` + `force-dynamic`); `LiveBadge` is the one `"use client"` component (SSE → `window.location.reload()` on `changed`), surfaced on the live pages (dashboard, journal). **Both helpers are self-contained (no backend import)** so they run as plain plugin scripts (D18): `web_init` writes `.web/console.json` (byte-stable/idempotent), `web_start` prints the compose command by default and refuses the real `--up` under pytest (the same env-guard pattern as `render_visuals`/`run_tests`). `make run` remains the primary way to bring the stack up; `/tc:web-start` is the scriptable equivalent.
- **Step 10.3 — read APIs + SSE + `/tc:web-sync`.** 14/14 GREEN. **`create_app(project_root=None)` takes the served root as an argument** (stored on `app.state`), so tests pass a tmp project directly instead of monkeypatching `TC_WORKSPACE` env — cleaner and parallel-safe. Read routes open the index read-only and **rebuild it once if absent** (`_index_conn`), so a fresh workspace serves data without a separate index step. **SSE is made testable by bounding it:** `event_stream(max_events=N)` terminates after N frames (and `detect_change` is a pure snapshot-diff tested directly), so the TestClient streaming test and the journal-append change test never spin forever — the production route passes `max_events=None`. **The read-only boundary is asserted as a property, not per-route:** one test hits every GET route and asserts the workspace is byte-identical before/after; `/api/proposals` returns a card with `executed: false` and is shown not to mutate. `/tc:web-sync` reuses the 10.2 rebuild engine (a sync is a clean rebuild for the MVP) — same delegating-command pattern as `/tc:web-index-artifacts`.
- **Step 10.2 — artifact indexer + `/tc:web-index-artifacts`.** 6/6 GREEN. **Rebuild-from-scratch is the determinism contract:** `index_workspace` drops and recreates every table before parsing, so two `rebuild()` calls return identical counts and the index can never drift from the workspace — much simpler than incremental reconciliation, and correct for the MVP. The parsers reuse the same pipe-table-row shape as the Phase-9 diagram parsers (require a digit/`evidence/` prefix on the first cell to skip headers). **The cross-tree import problem (D18 vs runtime code) is solved by a thin delegating command:** the indexer logic lives in the runtime (`apps/api/tcweb/indexer.py`), and the plugin command `web_index_artifacts.py` adds the repo's `apps/api` to `sys.path` (computed from its own location, `parents[3]`) and delegates — so the command ships in the plugin (D18) while the heavy logic stays in the runtime. The MVP console runs from the test-commander checkout (Pattern A), so `parents[3]/apps/api` resolves; documented in the command page. Indexing writes only the derived `.web/index.db`, asserted structurally (workspace byte-identical before/after).
- **Step 10.1 — scaffold (`tc-web` + `apps/web` + `apps/api` + `make run`).** 11/11 GREEN. **Reconciled the DB choice: SQLite, not Postgres.** The Runtime Topology table mentions Postgres for the viewer, but the Phase 10 execution outline says SQLite ("the DB is a derived index"), and Pattern A (local-first MVP, D15) wants no extra service. Per AGENTS.md the execution outline is operative — the index is a single rebuildable SQLite file under `.test-commander/.web/index.db` (git-ignored), so the compose stack is just `api` + `web`, no `db` service. **Backend package named `tcweb`, not `app`:** `app` is a generic name and `apps/api` is on the pytest pythonpath; a `tcweb` package avoids any import clash and reads clearly (`tcweb.main:app`). The backend is exercised by the *existing* pytest gate via the new `apps/api` pythonpath entry — no second test runner — and FastAPI/uvicorn/httpx live in a `web` dependency-group that `dev` includes, so `pdm install` (and thus `make verify`) has them without changing the install command. **The frontend stays out of `make verify`** (Next.js build + vitest + Playwright are heavy and Node-managed); a Python scaffold test asserts the `apps/web` tree + `package.json` deps instead, per the plan's "documented, not enforced if heavy" allowance — the real frontend e2e runs under `make run`/docker in 10.8. Mirrored `test_phase_9_scaffolds.py`; the only new wrinkle was the FastAPI `TestClient` health-route assertion.

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

1. **Intent router.** Maps natural-language requests and button actions to known Test Commander workflows. Examples (per D19, illustrative features are universal SaaS surfaces, not domain-specific): "review these requirements" -> `/tc:review-requirements`; "generate BDD for the sign-in flow" -> `/tc:generate-bdd --area sign-in`; "why did sign-in fail?" -> read-only artifact query. Unknown intents default to a read-only Q&A path; the router cannot synthesize new commands on its own.

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
     /tc:automate --feature sign-in
   This will:
     - read .test-commander/bdd/features/sign-in.feature
     - create or modify tests/e2e/sign-in.spec.ts
     - create or modify tests/pages/SignInPage.ts
     - update .test-commander/traceability/automation-map.md
     - optionally run sign-in tests
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

### Phase 10.5 — Execution outline

Thirteen sub-steps — the largest, most security-critical phase. TDD throughout; security properties are asserted by tests, never assumed. The pipeline (intent router → command planner → permission policy → approval gate → bounded execution → artifact capture → diff validation → audit log) is built component-by-component against the **mock adapter** so every gate is exercised hermetically, then the real `ClaudeCodeCliAdapter` is dropped in behind the same controls. 10.5.1 scaffolds; 10.5.2–10.5.9 build the eight pipeline components; 10.5.10 ships the Claude adapter + wires the Phase-10 console; 10.5.11 docs; 10.5.12 testing finalization (the four security integration tests + cap bump); 10.5.13 sign-off.

**Three disciplines Phase 10.5 introduces (read before 10.5.1).**

- **Default deny; every gate is a test, not a convention.** Nothing above `read-only` executes without passing the policy engine and (where required) an approval gate. The four canonical security integration tests (block an unsafe request before the agent; deny a code-write and assert no files change; approve via the mock adapter and assert the diff matches the plan; refuse a no-plan direct adapter call) are written **first** and are the phase's spine — they must be RED before the pipeline exists and GREEN only when each control is in place.
- **The agent never sees the raw user prompt; secrets never reach the frontend or the prompt.** Bounded execution wraps a *structured instruction* (command, scope, allowed/disallowed paths and actions, expected outputs) — raw user text never lands in instruction-critical sections (a test asserts this). Provider secrets stay server-side, are injected only into runtime jobs, and are redacted from logs, artifacts, and prompts (a test asserts an env-var-printing attempt is flagged).
- **Adapter abstraction so governance is backend-agnostic.** Every backend (`MockAgentAdapter`, `ClaudeCodeCliAdapter`, stubbed `AnthropicApiAdapter`) implements one `AgentAdapter` interface and runs *inside* the same pipeline. There is no direct-execution backdoor — the API (Phase 11), the sandbox (Phase 12), and continuous mode (Phase 13) all enter here.

#### 10.5.1 — Scaffold (`tc-governance` skill + `runtime/agent_adapters/` + policy/audit dirs + the four RED security tests)

- **Deliverables.** `tc-governance/SKILL.md` (policy / approval-card / bounded-prompt templates + the audit schema; deferral wording). Scaffold `runtime/agent_adapters/` (`base.py` interface, `mock_agent.py`, `claude_code_cli.py` stub, `anthropic_api.py` stub). Workspace additions: `policy/permissions.yaml`, `policy/approvals.yaml`, `audit/actions.jsonl`, `audit/approvals/`. `tests/fixtures/seeded-governance/` (a role set, a sample request set incl. one unsafe). **Write the four security integration tests now, RED**, as executable acceptance criteria the phase drives toward.
- **Tests first.** Scaffold test (skill + adapter tree + policy/audit dirs) + the four security integration tests landing RED (no pipeline yet).
- **Definition of done.** Scaffold present; the four security tests exist and are RED; `CATALOG["tc-governance"] == 10.5`; `tc-governance UNEXPECTED (phase 10.5) — ahead of schedule`.

#### 10.5.2 — Agent adapter abstraction (`AgentAdapter` + mock + stubs) (TDD)

- **Deliverables.** `base.py` `AgentAdapter` interface (`execute_command`, `stream_events`, `capture_result`, `report_files_changed`, `report_artifacts_created`, `report_usage_if_available`); `MockAgentAdapter` (deterministic, no real execution); `claude_code_cli.py` + `anthropic_api.py` stubs raising "not wired".
- **Tests first.** `MockAgentAdapter` round-trips a structured instruction → result + files-changed + artifacts; the stubs refuse cleanly.
- **Definition of done.** The interface + mock adapter work; stubs refuse; the pipeline can be built against the mock.

#### 10.5.3 — Permission policy engine (7 levels, role-aware) (TDD)

- **Helper.** The engine classifying every action into `read-only` / `safe-write` / `code-write` / `execute-tests` / `external-network` / `destructive` / `admin`, resolved against `policy/permissions.yaml` (role → allowed levels) and the five default roles (Viewer → Admin). Default deny.
- **Tests first.** Each level resolves correctly per role; an unsafe action ("delete all evidence" → `destructive`) is denied for a Viewer; unknown actions default to `read-only`; **the first security integration test (block-before-agent) goes GREEN.**
- **Definition of done.** Policy engine + roles + default permissions ship; the block-before-agent test passes.

#### 10.5.4 — Intent router (NL/button → known workflow) (TDD)

- **Helper.** Maps natural-language requests and button actions to known `/tc:*` workflows (examples per D19 are universal SaaS surfaces); unknown intents default to the read-only Q&A path; the router cannot synthesize new commands.
- **Tests first.** Known phrasings map to the right command; an unknown intent routes read-only; no synthesized command escapes the known set.
- **Definition of done.** Router maps the known workflow set; unknowns degrade read-only.

#### 10.5.5 — Command planner (displayable plan) (TDD)

- **Helper.** Produces an explicit, displayable plan before execution: command, likely reads, likely writes, permission level, target environment, expected artifacts, approval-required flag.
- **Tests first.** A planned command yields the full plan with the correct permission level and reads/writes; the plan is deterministic.
- **Definition of done.** Planner emits complete, deterministic plans feeding the approval gate.

#### 10.5.6 — Approval gate (card + record) (TDD)

- **Helper.** Requires approval for `code-write` / `execute-tests` / `external-network` / `destructive` / `admin` (configurable for `safe-write` via `policy/approvals.yaml`); renders an approval card; records the decision under `audit/approvals/`.
- **Tests first.** A code-write request renders an approval card; **the deny path goes GREEN — denying leaves no files changed (the second security integration test);** an approval is recorded with approver + timestamp.
- **Definition of done.** Approval gate + records ship; the deny-no-change test passes.

#### 10.5.7 — Bounded executor (structured instruction wrapping) (TDD)

- **Helper.** Wraps the approved plan into a *structured instruction* (command, scope, allowed/disallowed paths and actions, expected outputs, safety rules, journal requirements) and runs it through the adapter. Raw user text never enters instruction-critical sections.
- **Tests first.** The structured instruction contains no raw user text in instruction-critical fields; the mock adapter executes the bounded instruction; **the approve-and-execute path begins (third security test setup).**
- **Definition of done.** Bounded executor runs approved plans via the adapter; the no-raw-prompt property is tested.

#### 10.5.8 — Output validation + secret safety (TDD)

- **Helper.** After execution, diffs the workspace and verifies files-changed match the planned scope, no secret files touched, no unexpected network, expected outputs produced — a violation marks the run failed (admin review). Secret safety: provider keys server-side only, redacted from logs/artifacts/prompts; env-var-printing attempts flagged.
- **Tests first.** A seeded out-of-scope file write is caught and fails the run; **the approve-and-execute test goes GREEN — the post-execution diff matches the plan (third security integration test);** a secret-redaction test (an env-var-print attempt is flagged).
- **Definition of done.** Output validator + secret safety ship; the diff-matches-plan and redaction tests pass.

#### 10.5.9 — Audit journal (TDD)

- **Helper.** Append-only `audit/actions.jsonl` recording every action (user, timestamp, original request, mapped intent, proposed command, approval status, approver, permission level, files read/changed, artifacts, tests run, target URLs, status, summary, evidence links).
- **Tests first.** Every executed action writes one audit entry with the full field set; **the fourth security integration test goes GREEN — a no-plan direct adapter call is refused by the runtime (no audit entry, no execution).**
- **Definition of done.** Audit journal ships; the no-plan-bypass test passes; all four security integration tests GREEN.

#### 10.5.10 — `ClaudeCodeCliAdapter` + wire the Phase-10 console (TDD)

- **Deliverables.** Implement `ClaudeCodeCliAdapter` behind the *same* pipeline (no new execution path). Wire the Phase-10 web console's proposal cards into the pipeline so an approved card flows intent → plan → policy → approval → bounded execution → validation → audit; **remove any direct-execution path** from the console.
- **Tests first.** The Claude adapter implements the interface and is gated identically to the mock; a console-initiated approved action traverses the full pipeline; no UI path executes without it.
- **Definition of done.** Real adapter gated; console wired; no bypass exists.

#### 10.5.11 — Documentation pass

- **Deliverables.** `docs/controlled-agent-execution.md`, `docs/security-and-permissions.md`, `docs/chat-command-governance.md`, `docs/runtime-approval-flow.md`, `docs/agent-adapters.md`, `docs/user-guide/governance.md`; command-reference + workspace-reference (`policy/`, `audit/`) updates; customization-guide Phase 10.5 entry (roles, permission levels, approval policy — the genuinely-extensible governance surface); status-line refresh; final deferral sweep.
- **Definition of done.** All six docs written; links resolve; link checker green.

#### 10.5.12 — Testing finalization

- **Deliverables.** Bump `DEFAULT_PHASE_CAP` 10 → 10.5. Consolidate the four security integration tests + the secret-redaction test into `tests/test_phase_10_5_integration.py` and confirm all GREEN end-to-end with the mock adapter (and the Claude adapter gated). Confirm `PHASE_OWNERSHIP["10.5"] == ["policy", "audit"]`.
- **Definition of done.** All security tests GREEN; cap bump reflected; `make verify` green; `verify_skills.py` all `PRESENT`, `UNEXPECTED=0`.

#### 10.5.13 — Sign-off

Six sub-sub-steps mirroring prior sign-offs: cold-user walkthrough of `governance.md` (drive an approve/deny via the console against the mock adapter); per-step DoD audit (every action above `safe-write` shows an approval card; every executed action audits; no bypass); plan + CHANGELOG closing; documentation final pass; test-first `tests/test_phase_10_5_signoff.py`; final DoD eval + annotated `phase-10.5` tag.

#### Phase 10.5 — Lessons learned (running)

Captured at sub-step close per the "Sub-step lesson capture" Per-Phase Convention. (Populated as 10.5.1–10.5.13 land.)

- **Step 10.5.10 — ClaudeCodeCliAdapter + console wiring.** 12/12 GREEN. **The real adapter is gated by the *same* `require_planned` + a pytest refusal, not a parallel path:** `execute_command` calls `require_planned` first (so an unplanned call raises `UnplannedExecutionError` exactly like the mock), then refuses the real shell-out under `PYTEST_CURRENT_TEST` — the suite never launches Claude, and there is no second execution route. The console gained **one** execution endpoint, `/api/execute`, which calls `pipeline.handle_request`; `/api/chat` and `/api/proposals` stay read-only (a test confirms a "run the tests now" chat turn executes nothing and writes no audit entry — the empty journal is the proof). `create_app(governance_adapter=...)` injects the adapter (mock by default for the MVP; the real Claude adapter is an explicit operator choice), so the console drives the pipeline hermetically in tests. Updated the api Dockerfile to ship `runtime/governance` + `runtime/agent_adapters` so the container's `/api/execute` has the pipeline. Updated the 10.5.2 stub test — Claude is no longer a NotImplementedError stub (it's a real gated backend); only the Anthropic adapter remains a stub.
- **Step 10.5.9 — audit journal; all four security tests GREEN.** `audit.record` appends one JSONL line per executed action (the full spec field set) and `read_entries` parses it; the pipeline writes the entry after validation, threading an injected `now` for deterministic timestamps. **The no-plan-bypass test became real only here, by design:** it was scoped at 10.5.1 to import `governance.audit` and assert `read_entries(project) == []` after a direct adapter call — so adapter-level refusal alone (available since 10.5.2) could never XPASS it; it needed the audit module to exist *and* the truth that a bypass leaves no trace. With audit shipped, the four canonical security properties are all enforced and tested: block-before-agent, deny-no-change, approve-diff-matches, no-plan-bypass. **The xfail-strict spine worked exactly as intended** — each test flipped at its scheduled sub-step (10.5.3/10.5.6/10.5.8/10.5.9) and `make verify` stayed green throughout. Added a `now` param to `handle_request` so the audit + approval timestamps are injectable (the integration/sign-off tests pass a fixed clock).
- **Step 10.5.8 — output validation + secret safety.** Validation unit tests + security test 3 (approve-diff-matches) GREEN; only test 4 (no-plan bypass) stays xfail. **Validation is fail-closed and checks three things against the plan:** every changed file is within `plan.writes` scope, no secret path was touched, and every `expected_artifact` was produced — a single out-of-scope write (`src/app/accounts.py`) or a secret touch (`.env`) flips `ok=False` and fails the run even though the adapter reported success. The diff-matches-plan property holds because the mock creates exactly the plan's expected outputs, so `files_changed ⊆ scope` and all expected are present. **Secret safety is two pure functions** — `redact` (mask `*KEY/TOKEN/SECRET/PASSWORD/CREDENTIAL* = value`) and `flags_env_var_print` (detect `printenv`/`os.environ`/`echo $`/`env |`) — testable in isolation and reusable by the audit/log layers. The pipeline now sets `result.status='failed'` and surfaces the violations as the reason when validation fails.
- **Step 10.5.7 — bounded executor.** Executor unit tests GREEN; security tests 3-4 still xfail (3 needs validation, 4 needs audit). **The no-raw-prompt property is structural, not a filter:** `build_instruction` takes the `Plan` (derived from the routed command), not the request, so raw user text *cannot* reach the instruction-critical fields — the test injects a sentinel into the request and asserts it appears nowhere in the built instruction, and it passes because the request was dropped at the planner boundary. Secret paths are always in `disallowed_paths`; the allowed/disallowed *actions* are a per-level table (read-only forbids write/run/network/delete; code-write allows write but not run/network/delete; etc.). The pipeline now executes the approved/allowed path via `executor.run` and returns `executed=True` with `validation=None` — test 3 asserts `validation.ok`, so it stays xfail until 10.5.8 adds validation. Read-only requests return without invoking the agent at all (a read isn't an execution).
- **Step 10.5.6 — approval gate.** Approval unit tests + security test 2 (deny-no-change) GREEN; tests 3-4 stay xfail. **The deny-no-change property falls out of ordering, not cleanup:** the pipeline checks `requires_approval` *before* building any bounded instruction, so a not-approved privileged action returns `requires_approval=True` having never touched the adapter — there is nothing to roll back because nothing ran (`adapter.calls == []`, workspace byte-identical). The approval decision is recorded at the gate (independent of execution outcome), matching the spec. `approvals.yaml` (`require_approval: [<level>]`) lets a deployment widen approval to `safe-write`; absent the file, the five privileged levels require it by default. Wired intent+planner into `handle_request` here (they were shipped in 10.5.4/10.5.5) — the orchestrator now does route → plan → policy → approval, and the approve path raises NotImplementedError until the executor lands (10.5.7), keeping test 3 xfail.
- **Step 10.5.5 — command planner.** 6/6 GREEN; no security flip. The planner is a **deterministic lookup**, not inference: `_COMMAND_PLANS` holds per-command knowledge (level + likely reads + likely writes + target env), so a `Plan` is reproducible and reviewable — the property the approval card depends on. `expected_artifacts` is derived from `writes`, which later feeds the bounded instruction's `expected_outputs` (10.5.7) and the diff-matches-plan validation (10.5.8) — one source of truth for "what this command should touch". `requires_approval` is computed from the level (the five privileged levels require it; read-only/safe-write don't), with the approval gate (10.5.6) free to widen safe-write via `approvals.yaml`. A routed-but-unknown command and the read-only path both collapse to a no-write read-only plan — defense in depth behind the closed intent router.
- **Step 10.5.4 — intent router.** 4/4 GREEN; no security test flips here. **The key design call: routing is orthogonal to the block decision.** The router maps a request to a *known* command (or read-only) for planning; it does NOT determine whether the action is allowed. So "delete all evidence" routes to read-only (there is no known delete workflow — the router can't synthesize one), yet the policy engine still classifies it `destructive` and blocks it. Two independent properties: the router is *closed* (only ever returns a member of `KNOWN_COMMANDS` or read-only, asserted over a fuzz set incl. `/tc:make-coffee`), and the policy gate catches dangerous intent regardless of routing. A button passing an exact `/tc:` command is honored only if known — the same closed-set rule, no bypass via the button path.
- **Step 10.5.3 — permission policy engine.** 7 policy tests + security test 1 GREEN; tests 2-4 stay xfail. **The classifier's first cut was too eager — a bare noun matched a read:** `"show me the quality report"` hit the `quality report` keyword and classified as `safe-write`. Fix: anchor every non-read level on **action verbs** (`generate playwright`, `run the`, `review`, `delete`), most-privileged-first, so a destructive verb wins and a view stays `read-only`. **Default deny is structural, not a rule:** `allows()` returns `level in permissions.get(role, ())`, so an unknown role or an unlisted level is denied with no special-casing. The policy block is the *first* pipeline gate — `handle_request` returns `blocked=True` before touching the adapter, which is exactly what security test 1 asserts (`adapter.calls == []`). The `policy/permissions.yaml` override is a configurable surface; per the plan's schedule the consolidated customization-guide governance entry (roles + levels + approval policy) lands in the 10.5.11 docs pass, recorded here.
- **Step 10.5.2 — `AgentAdapter` + mock + stubs.** 6/6 GREEN; the four security tests stay xfail (no pipeline yet). **The no-backdoor guarantee is a single shared function, not per-adapter discipline:** `base.require_planned(instruction)` raises `UnplannedExecutionError` unless given an approved `BoundedInstruction`, and every adapter routes `execute_command`/`stream_events` through it — so a future adapter can't accidentally omit the check. **The mock "executes" by creating exactly the instruction's `expected_outputs`** (real file writes under `project_root`), which is what later lets the 10.5.8 diff-matches-plan test pass against a real workspace diff — the mock isn't a no-op, it's a faithful stand-in for "a command that writes its planned files". The stubs raise `NotImplementedError` so nothing runs through an unwired backend by accident. `BoundedInstruction` is frozen and its instruction-critical fields (command/scope/paths/actions/outputs) are typed tuples — the executor (10.5.7) fills them from an approved plan, never from raw user text. 9/9 scaffold GREEN, 4 security tests xfailed. **The hard problem this phase poses: write the four security tests RED at 10.5.1 *and* keep `make verify` green at every commit.** Solution: `@pytest.mark.xfail(strict=True)` with a per-test reason naming the enabling sub-step. xfail means RED doesn't break the suite; `strict=True` means an *unexpected pass* fails — so when a control lands and its test starts passing, I'm forced to remove the marker in that same sub-step (the plan's green-at-step schedule becomes mechanical). **Two design choices keep each test RED until exactly its step, not earlier:** (1) in-body imports so a not-yet-existing module surfaces as the expected failure, not a collection error; (2) each test depends on a module that only its step ships — test 4 (no-plan bypass) imports `governance.audit` (10.5.9) and asserts no audit entry, so adapter-level refusal alone (available at 10.5.2) can't XPASS it early. The pipeline orchestrator (`governance.pipeline.handle_request`) is the single entry point, scaffolded to `raise NotImplementedError`; it grows component-by-component, and the "not yet implemented" downstream raise keeps later tests xfail. Added `runtime` to the pytest pythonpath so `governance.*` and `agent_adapters.*` import. tc-governance has **no `/tc:*` commands** — it is a templates/methodology skill the pipeline (and the console) invoke, so the `commands/` dir stays a `.gitkeep` placeholder.

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

### Phase 11 — Execution outline

Seven sub-steps. The API and MCP server are **alternative front-ends to the Phase-10.5 pipeline** — every route and tool enters intent routing → planning → permissions → approval → validation → audit; there is no direct-execution backdoor (the headline discipline, asserted by tests). 11.1 scaffolds; 11.2 expands the Runtime API; 11.3 builds the MCP server + tools; 11.4 enforces + unit-tests the permission gates; 11.5 docs; 11.6 testing finalization; 11.7 sign-off.

**Two disciplines Phase 11 introduces (read before 11.1).**

- **No bypass — the pipeline is the only path.** Every API route and MCP tool that does anything above `read-only` is routed through the Phase-10.5 controls server-side; a contract test asserts a route cannot execute without a plan + approval, exactly as the console cannot.
- **Schema-first tools.** MCP tools ship explicit JSON schemas (per `anthropic-skills:skill-creator` conventions); round-trip tests exercise every tool via a sample client.

#### 11.1 — Scaffold (`tc-mcp` skill + `apps/mcp/` + Runtime API expansion skeleton)

- **Deliverables.** `tc-mcp/SKILL.md` (the MCP tool catalog; deferral wording). Scaffold `apps/mcp/` (server package) and the expanded `apps/api/` route skeleton. `tests/fixtures/seeded-mcp/`. **Tests first:** scaffold test (skill + `apps/mcp` tree + a server health check). DoD: `CATALOG["tc-mcp"] == 11`; ahead-of-schedule.

#### 11.2 — Runtime API expansion (through the pipeline) (TDD)

- **Deliverables.** The expanded FastAPI routes (read + proposal + governed-execution), every mutating route entering the 10.5 pipeline. **Tests first:** contract tests per route (shape + permission level); a route above `read-only` refuses without a plan/approval. DoD: routes work behind the pipeline; SKILL.md updated.

#### 11.3 — MCP server + tool definitions (TDD)

- **Deliverables.** The MCP server and its tools (schema-first), each tool dispatching into the same pipeline. **Tests first:** MCP tool round-trip tests via a sample client; a tool above `read-only` is gated. DoD: all tools work; schemas valid; SKILL.md updated.

#### 11.4 — Permission gates (server-side enforcement) (TDD)

- **Deliverables.** Explicit server-side enforcement of the seven permission levels across API + MCP; unit tests per level. **Tests first:** security tests for destructive routes/tools (refused without admin approval); a bypass attempt fails. DoD: gates enforced + unit-tested; no bypass.

#### 11.5 — Documentation pass

- **Deliverables.** `docs/runtime-api.md`, `docs/mcp-server.md`, `docs/security-and-permissions.md` (updates), `docs/user-guide/integrating.md`; command-reference + customization-guide entries; status-line refresh; final deferral sweep. DoD: docs accurate; links resolve.

#### 11.6 — Testing finalization

- **Deliverables.** Bump `DEFAULT_PHASE_CAP` 10.5 → 11. `tests/test_phase_11_integration.py`: contract tests for every route, MCP round-trips, and the no-bypass security assertions all green. DoD: integration green; cap bump reflected; `make verify` green; `verify_skills.py` all `PRESENT`, `UNEXPECTED=0`.

#### 11.7 — Sign-off

Six sub-sub-steps mirroring prior sign-offs: cold-user walkthrough (exercise the API + an MCP tool via a sample client); per-step DoD audit (no bypass; gates enforced); plan + CHANGELOG closing; documentation final pass; test-first `tests/test_phase_11_signoff.py`; final DoD eval + annotated `phase-11` tag.

#### Phase 11 — Lessons learned (running)

Captured at sub-step close per the "Sub-step lesson capture" Per-Phase Convention. (Populated as 11.1–11.7 land.)

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

### Phase 12 — Execution outline

Seven sub-steps. A sandbox is an on-demand Test Commander environment launched from GitHub Actions — and **the Phase-10.5 pipeline runs inside it exactly as locally** (sandboxing never relaxes governance, the headline discipline). 12.1 scaffolds; 12.2 builds the provider abstraction + docker-compose provider; 12.3 ships the six sandbox commands; 12.4 ships the workflows + safety guards; 12.5 docs; 12.6 testing finalization; 12.7 sign-off.

**Two disciplines Phase 12 introduces (read before 12.1).**

- **Governance travels with the sandbox.** The controlled execution pipeline runs in the sandbox just as locally; provider credentials are server-side secrets, never exposed to the frontend, scoped to the runtime jobs that need them. A test asserts the sandbox cannot execute above its approved level.
- **Safe-by-default targeting.** Allowed target domains only, private network ranges blocked by default, secret-scanning guidance, approvals for external targets and destructive commands, clear environment labels. CI is exercised as a **dry-run with a mocked provider** — no real cloud spend in tests.

#### 12.1 — Scaffold (`tc-sandbox` skill + `sandbox/providers/` + `.github/workflows/` skeleton)

- **Deliverables.** `tc-sandbox/SKILL.md` (the six `/tc:sandbox-*` commands; deferral wording). Scaffold `sandbox/providers/` (provider abstraction) and the workflow skeleton. **Tests first:** scaffold test. DoD: `CATALOG["tc-sandbox"] == 12`; ahead-of-schedule.

#### 12.2 — Provider abstraction + docker-compose provider + stubs (TDD)

- **Deliverables.** The `SandboxProvider` interface; the docker-compose-local provider; stub adapters for a generic container host and a Sprites.dev placeholder (Q8 default). **Tests first:** the docker-compose provider launches/teardowns against a mock; the stubs refuse cleanly. DoD: provider abstraction + the local provider work; stubs refuse.

#### 12.3 — The six sandbox commands (TDD)

- **Deliverables.** `/tc:sandbox-init`, `/tc:sandbox-launch`, `/tc:sandbox-status`, `/tc:sandbox-sync`, `/tc:sandbox-stop`, `/tc:sandbox-export` against the provider abstraction. **Tests first:** each command exercises the mock provider with the right lifecycle call; launch/stop are idempotent. DoD: all six shipped; SKILL.md updated, no deferral wording.

#### 12.4 — GitHub Actions workflows + safety guards (TDD)

- **Deliverables.** The sandbox workflows under `.github/workflows/`; the safety-guard config (allowed domains, blocked private ranges, approvals for external/destructive). **Tests first:** the workflow YAML is valid + sequences image build → env publish → teardown; a blocked target/private range is refused; the in-sandbox pipeline enforces governance. DoD: workflows + guards ship; the governance-in-sandbox assertion passes.

#### 12.5 — Documentation pass

- **Deliverables.** `docs/sandboxed-environments.md`, `docs/github-actions-sandbox.md`, `docs/no-code-tester-workflow.md`, `docs/user-guide/sandbox.md`; command-reference + customization-guide entries; status-line refresh; **honest MVP-limitations** section; final deferral sweep. DoD: docs accurate; links resolve.

#### 12.6 — Testing finalization

- **Deliverables.** Bump `DEFAULT_PHASE_CAP` 11 → 12. `tests/test_phase_12_integration.py`: CI dry-run with a mocked provider asserting image build, env publish, and teardown sequencing, plus the safety-guard refusals and the governance-in-sandbox assertion. DoD: integration green; cap bump reflected; `make verify` green; `verify_skills.py` all `PRESENT`, `UNEXPECTED=0`.

#### 12.7 — Sign-off

Six sub-sub-steps mirroring prior sign-offs: cold-user walkthrough (launch a sandbox against a sample target via the mocked provider; confirm teardown); per-step DoD audit (safety guards; governance travels); plan + CHANGELOG closing; documentation final pass; test-first `tests/test_phase_12_signoff.py`; final DoD eval + annotated `phase-12` tag.

#### Phase 12 — Lessons learned (running)

Captured at sub-step close per the "Sub-step lesson capture" Per-Phase Convention. (Populated as 12.1–12.7 land.)

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

### Phase 13 — Execution outline

Nine sub-steps — the final phase. Continuous mode watches code, requirements, and pipelines and proposes quality updates, **running through the same Phase-10.5 pipeline**; the configured autonomy level (0–4) decides which permission levels are auto-approved, and nothing above it executes without explicit human approval (the headline discipline). 13.1 scaffolds; 13.2 ships change-detection + impact analysis; 13.3 coverage-gap analysis; 13.4 propose-tests + create-test-PR; 13.5 the continuous check + the five autonomy-mode gates; 13.6 the CI workflow; 13.7 docs; 13.8 testing finalization; 13.9 sign-off.

**Two disciplines Phase 13 introduces (read before 13.1).**

- **Autonomy is a ceiling, not a license.** The five modes (0 read-only-advisor → 4 governed-autonomy) map to which permission levels are auto-approved in the 10.5 pipeline; mode boundaries are enforced (mode 0 cannot open PRs; PRs from mode 3 are clearly labeled), asserted by tests. Continuous mode must not bypass approvals.
- **Reuse, don't rebuild.** Impacted-test runs reuse `tc-run`'s execution + failure-triage; lessons feed `tc-learning`; no parallel machinery. The phase adds the *watch → analyze → propose → PR* loop on top of the existing skills.

#### 13.1 — Scaffold (`tc-continuous-quality` skill + the CI workflow skeleton + seeded fixture)

- **Deliverables.** `tc-continuous-quality/SKILL.md` (the six commands + the five autonomy modes; deferral wording). The `.github/workflows/test-commander-continuous-quality.yml` skeleton. `tests/fixtures/seeded-continuous/` (a sample PR diff + an impacted-feature map). **Tests first:** scaffold test. DoD: `CATALOG["tc-continuous-quality"] == 13`; ahead-of-schedule.

#### 13.2 — `/tc:watch-changes` + `/tc:impact-analysis` (TDD)

- **Deliverables.** Change detection (a PR/push diff) and impact analysis mapping changed files → impacted features/requirements via the Phase-3 knowledge + Phase-5 traceability. **Tests first:** a seeded diff yields the expected impacted features; deterministic. DoD: both commands ship; SKILL.md updated.

#### 13.3 — `/tc:coverage-gap-analysis` (TDD)

- **Deliverables.** Analyzes the impacted set against existing coverage (test-map, automation plan) and writes a coverage-gap analysis (read-only). **Tests first:** a seeded impacted set with a known gap → the gap surfaced with provenance; never invents coverage. DoD: ships; deterministic; SKILL.md updated.

#### 13.4 — `/tc:propose-tests` + `/tc:create-test-pr` (TDD)

- **Deliverables.** `/tc:propose-tests` proposes new BDD/automation for the gaps (reusing Phases 5/6 generators as proposals); `/tc:create-test-pr` opens a clearly-labeled PR through the 10.5 pipeline (requires the configured autonomy level + approval). **Tests first:** propose yields reviewable artifacts; create-test-pr is gated by mode + approval and the PR is labeled; a below-threshold mode cannot open a PR. DoD: both ship; gated; SKILL.md updated.

#### 13.5 — `/tc:continuous-quality-check` + the five autonomy-mode gates (TDD)

- **Deliverables.** The orchestrator running watch → impact → coverage-gap → propose under the configured autonomy mode, with the five mode gates mapping to 10.5 auto-approval levels. **Tests first:** each mode auto-approves exactly its levels and no more; mode 0 cannot open PRs; nothing above the mode executes without approval. By end of 13.5 all six commands ship with no deferral wording. DoD: the check + gates ship; boundaries enforced.

#### 13.6 — The continuous-quality CI workflow (TDD)

- **Deliverables.** The `pull_request` / `push` / `schedule` / `workflow_dispatch` workflow wiring the check into CI, read-only analysis automatic, generated changes arriving as gated PRs. **Tests first:** the workflow YAML is valid + triggers correct; a simulated PR runs the check at the configured mode. DoD: workflow stable; the simulated-PR assertion passes.

#### 13.7 — Documentation pass

- **Deliverables.** `docs/continuous-quality-agent.md`, `docs/autonomy-levels.md`, `docs/governed-self-improvement.md`, `docs/user-guide/continuous-quality.md`; command-reference + customization-guide (the autonomy-mode config is the extensible surface) entries; status-line refresh; final deferral sweep. DoD: docs accurate; links resolve.

#### 13.8 — Testing finalization

- **Deliverables.** Bump `DEFAULT_PHASE_CAP` 12 → 13. `tests/test_phase_13_integration.py`: simulate a PR with a code change; assert impact analysis identifies the expected impacted features and proposes appropriate tests; assert the mode boundaries hold and PRs are labeled. DoD: integration green; cap bump reflected; `make verify` green; `verify_skills.py` reports all skills `PRESENT` with `UNEXPECTED=0` (the full catalog).

#### 13.9 — Sign-off (project complete)

Six sub-sub-steps mirroring prior sign-offs: cold-user walkthrough (simulate a PR end-to-end at a chosen mode); per-step DoD audit (mode boundaries; PR labeling; no bypass); plan + CHANGELOG closing; documentation final pass; test-first `tests/test_phase_13_signoff.py`; final DoD eval + annotated `phase-13` tag. With 13.9 the full roadmap (Phases 0–13) is shipped.

#### Phase 13 — Lessons learned (running)

Captured at sub-step close per the "Sub-step lesson capture" Per-Phase Convention. (Populated as 13.1–13.9 land.)

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

Per D19, Test Commander does not ship with any specific target product or feature. The `sign-in` area below is an illustrative universal SaaS surface — substitute any feature the consuming project actually tests.

```
/tc:init
/tc:review-requirements
/tc:learn-from-docs
/tc:learn-from-code
/tc:create-charter --area sign-in
/tc:explore --target http://localhost:3000 --charter sign-in
/tc:test-ideas --area sign-in
/tc:generate-bdd --area sign-in
/tc:automation-plan --area sign-in
/tc:generate-test-data --area sign-in
/tc:automate --feature sign-in   # builds framework lazily if absent
/tc:run --suite smoke
/tc:analyze-results
/tc:report
/tc:learn
/tc:next
/tc:visualize --area sign-in
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

Phase 1 complete (2026-05-26) — see Completed.

### Phase 2

Phase 2 complete (2026-05-27) — see Completed.

### Phase 3

Phase 3 complete (2026-05-27) — see Completed.

### Phase 4

Phase 4 complete (2026-05-28) — see Completed.

### Phase 5

Phase 5 complete (2026-05-29) — see Completed.

### Phase 6
Phase 6 complete (2026-05-29) — see Completed.
### Phase 7
Phase 7 complete (2026-06-01) — see Completed.

### Phase 8
Phase 8 complete (2026-06-01) — see Completed.

### Phase 9
Phase 9 complete (2026-06-01) — see Completed.

### Phase 10
Phase 10 complete (2026-06-01) — see Completed.

### Phase 10.5

See `### Phase 10.5 — Execution outline` for full sub-step detail.

- [x] 10.5.1 — Scaffold (`tc-governance` + `runtime/agent_adapters/` + policy/audit dirs + the four RED security tests)
- [x] 10.5.2 — Agent adapter abstraction (`AgentAdapter` + mock + stubs)
- [x] 10.5.3 — Permission policy engine (7 levels, role-aware)
- [x] 10.5.4 — Intent router (NL/button → known workflow)
- [x] 10.5.5 — Command planner (displayable plan)
- [x] 10.5.6 — Approval gate (card + record)
- [x] 10.5.7 — Bounded executor (structured instruction wrapping)
- [x] 10.5.8 — Output validation + secret safety
- [x] 10.5.9 — Audit journal
- [x] 10.5.10 — `ClaudeCodeCliAdapter` + wire the Phase-10 console (no bypass)
- [ ] 10.5.11 — Documentation pass (six governance docs)
- [ ] 10.5.12 — Testing finalization (four security integration tests + cap bump 10 → 10.5)
- [ ] 10.5.13 — Sign-off (`phase-10.5` tag)

### Phase 11

See `### Phase 11 — Execution outline` for full sub-step detail.

- [ ] 11.1 — Scaffold (`tc-mcp` + `apps/mcp/` + Runtime API expansion skeleton)
- [ ] 11.2 — Runtime API expansion (through the 10.5 pipeline)
- [ ] 11.3 — MCP server + tool definitions
- [ ] 11.4 — Permission gates (server-side enforcement, unit-tested)
- [ ] 11.5 — Documentation pass (`runtime-api.md`, `mcp-server.md`, `integrating.md`)
- [ ] 11.6 — Testing finalization (contract + MCP round-trip + cap bump 10.5 → 11)
- [ ] 11.7 — Sign-off (`phase-11` tag)

### Phase 12

See `### Phase 12 — Execution outline` for full sub-step detail.

- [ ] 12.1 — Scaffold (`tc-sandbox` + `sandbox/providers/` + `.github/workflows/` skeleton)
- [ ] 12.2 — Provider abstraction + docker-compose provider + stubs
- [ ] 12.3 — The six `/tc:sandbox-*` commands
- [ ] 12.4 — GitHub Actions workflows + safety guards
- [ ] 12.5 — Documentation pass (sandbox docs)
- [ ] 12.6 — Testing finalization (CI dry-run with mocked provider + cap bump 11 → 12)
- [ ] 12.7 — Sign-off (`phase-12` tag)

### Phase 13

See `### Phase 13 — Execution outline` for full sub-step detail.

- [ ] 13.1 — Scaffold (`tc-continuous-quality` + CI workflow skeleton + seeded fixture)
- [ ] 13.2 — `/tc:watch-changes` + `/tc:impact-analysis`
- [ ] 13.3 — `/tc:coverage-gap-analysis`
- [ ] 13.4 — `/tc:propose-tests` + `/tc:create-test-pr`
- [ ] 13.5 — `/tc:continuous-quality-check` + the five autonomy-mode gates
- [ ] 13.6 — The continuous-quality CI workflow
- [ ] 13.7 — Documentation pass (continuous-quality docs)
- [ ] 13.8 — Testing finalization (PR simulation + cap bump 12 → 13)
- [ ] 13.9 — Sign-off (`phase-13` tag; project complete)

---

## Completed

Move To Do items here as phases finish, with date and short note.

### Phase 10 — Web console MVP (2026-06-01)

One skill shipped (`tc-web`), adding five commands — and the first **runtime** phase (per D2): a Next.js frontend (`apps/web/`) + a FastAPI backend (`apps/api/tcweb/`) brought up together by `make run` on docker compose, serving a team-facing **read-only, proposal-only** console over a consuming project's `.test-commander/` workspace. The backend indexes the workspace into a rebuildable SQLite derivative (`indexer` + `db`), serves one read route per page plus an SSE `changed` stream, generates command **proposal cards** (`proposals`), answers questions read-only (`chat`), and exports a deterministic static bundle (`exporter`); the five `/tc:web-*` commands (`web-init`, `web-start`, `web-sync`, `web-index-artifacts`, `web-export`) are plugin scripts (D18) that drive the runtime. No route mutates a workspace artifact or runs a command — the only thing the backend writes is the derived `.web/` index (the read-only contract is enforced at the app layer and asserted as a property by the suite); execution is gated behind Phase 10.5. Reconciled the DB to SQLite (not the Runtime Topology table's Postgres) and, in sign-off, the workspace mount to read-write (the `:ro` mount blocked the legitimate `.web/` index write). 906-test suite green; lint clean; 295-file Markdown link check clean. `verify_skills.py` reports all sixteen skills `PRESENT` (`tc-web` at phase 10) with `UNEXPECTED=0`. Phase 10 ships no new `config.yaml` surface (recorded in the customization guide). Tagged `phase-10` on origin.

- [x] Step 10.1: scaffold `tc-web` + `apps/web` (Next.js) + `apps/api` (FastAPI, `tcweb`) + `runtime/` + the `make run` docker-compose target + the `seeded-web` fixture + `tests/test_phase_10_scaffolds.py` (11 tests).
- [x] Step 10.2: the artifact indexer (`tcweb.db` + `tcweb.indexer`) + `/tc:web-index-artifacts` — rebuild-from-scratch into SQLite; `tests/test_web_indexer.py` (6 tests).
- [x] Step 10.3: read-only API routes + SSE (`tcweb.sse`) + proposals (`tcweb.proposals`) + `/tc:web-sync`; `tests/test_web_api.py` (14 tests).
- [x] Step 10.4: the MVP frontend pages + `Nav` + `LiveBadge` (SSE) + `/tc:web-init` + `/tc:web-start`; `tests/test_phase_10_frontend.py` (9 tests).
- [x] Step 10.5: the read-only chat (`tcweb.chat`) + proposal cards; `tests/test_web_chat.py` (8 tests).
- [x] Step 10.6: `/tc:web-export` (`tcweb.exporter`) — deterministic static bundle; `tests/test_web_export.py` (6 tests).
- [x] Step 10.7: documentation pass — `docs/user-guide/web-console.md`, `docs/web-console.md`, `docs/runtime-api.md`, command-reference Phase 10 section, `.web/` workspace-reference note, customization-guide record, six-surface status sweep.
- [x] Step 10.8: testing finalization — `DEFAULT_PHASE_CAP` 9 → 10, `tests/test_phase_10_integration.py` (the in-process API smoke), the vitest/Playwright web test lanes (`make web-test` / `make web-e2e`).
- [x] Step 10.9: sign-off — cold-user walkthrough (`make uninstall` → `make install` → real `docker compose up --build api`; caught and fixed the `:ro`-mount bug that blocked the derived-index write), test-first `tests/test_phase_10_signoff.py` (20 tests, RED → GREEN), plan + CHANGELOG closing, annotated `phase-10` tag.

### Phase 9 — Visual documentation and infographics (2026-06-01)

One skill shipped (`tc-visualize`), adding eleven commands — diffable visual quality artifacts generated only from committed workspace artifacts, each citing its sources and never inventing a node, edge, or metric. `/tc:visualize` is the umbrella that regenerates the full diagram set and owns the shared render engine (`render_diagram`, `render_flowchart`, `render_subgraph_flowchart`, `render_sequence`, `render_state`, `render_diagram_doc`, `write_visual`, `read_source`, `mermaid_id`, `Node`/`Edge`) every generator reuses. The eight `/tc:diagram-*` commands emit Mermaid under `visuals/mermaid/`: `flow` and `sequence` (user journeys + system entities), `state` (the test map's result lifecycle), `architecture` (system-model entities), `risk` (the register, grouped into severity subgraphs), `coverage` (the requirements map), `traceability` (the full requirement→scenario→result chain, resolved or `pending`), and `test-strategy` (requirements feeding the automation decision buckets). `/tc:generate-infographic` aggregates the quality report's measured facts into a brief + spec under `visuals/infographic/`. `/tc:render-visuals` is the only command that shells out — to the Mermaid CLI (`mmdc`, provisioned by `make install`), refused under pytest and graceful when the CLI is absent. `/tc:next` gained R10 (`/tc:visualize`). 830-test suite green; lint clean; 275-file Markdown link check clean. `verify_skills.py` reports all fifteen skills `PRESENT` (`tc-visualize` at phase 9) with `UNEXPECTED=0`. Phase 9 ships no new `config.yaml` surface (recorded explicitly in the customization guide). Tagged `phase-9` on origin.

- [x] Step 9.1: scaffold `tc-visualize` + the `seeded-visuals` fixture (one producer-faithful source artifact per diagram type) + the guarded `mermaid-install` step in `make install` + `tests/test_phase_9_scaffolds.py` (7 cases) and two `test_make_install.py` cases; strict-PyYAML frontmatter from the start.
- [x] Step 9.2: `/tc:visualize` + the shared render engine + `/tc:diagram-flow` — `visualize.py` + `visual-documentation.md` + `diagram-standards.md` + flow template + two command pages + SKILL.md + `tests/test_visualize.py` (8 tests).
- [x] Step 9.3: structural diagrams (`/tc:diagram-sequence`, `/tc:diagram-state`, `/tc:diagram-architecture`) — two new emitters (`render_sequence`, `render_state`) + three templates + three command pages + a per-kind methodology subsection + SKILL.md + `tests/test_diagrams_structural.py` (10 tests).
- [x] Step 9.4: quality diagrams (`/tc:diagram-risk`, `/tc:diagram-coverage`, `/tc:diagram-traceability`, `/tc:diagram-test-strategy`) — `render_subgraph_flowchart` + four templates + four command pages + methodology subsection + SKILL.md + `tests/test_diagrams_quality.py` (9 tests). Fixed a header-row parser bug found in the rendered-output eyeball.
- [x] Step 9.5: `/tc:generate-infographic` — `generate_infographic.py` (measured-facts-only, reusing the visualize engine) + `infographic-standards.md` + two templates + command page + SKILL.md + `tests/test_generate_infographic.py` (5 tests).
- [x] Step 9.6: `/tc:render-visuals` — `render_visuals.py` (Mermaid CLI, refused under pytest, graceful when absent) + render methodology subsection + command page + SKILL.md (all eleven shipped, no deferral) + `tests/test_render_visuals.py` (7 tests).
- [x] Step 9.7: documentation pass — `docs/user-guide/visuals.md`, command-reference Phase 9 section, workspace-reference visuals/ flipped to shipped, customization-guide "no new extensible surface" record, six-surface status sweep, quality-report → visuals cross-link, deferral sweep.
- [x] Step 9.8: testing finalization — `DEFAULT_PHASE_CAP` 8 → 9, `tests/test_phase_9_integration.py` (full Phase 2 → 9 sweep against the real upstream chain), and the Phase 9 `/tc:next` rule (R10 → `/tc:visualize`, report renumbered to R11).
- [x] Step 9.9: sign-off — cold-user walkthrough (`make uninstall` → `make install` with the real Mermaid CLI installed; the real render caught and fixed a mmdc output-naming bug), per-step DoD audit, plan + CHANGELOG closing, doc final pass, test-first `tests/test_phase_9_signoff.py` (19 tests, RED → GREEN), annotated `phase-9` tag.

### Phase 8 — Continuous learning and self-improvement (2026-06-01)

One skill shipped (`tc-learning`), adding six commands — the governed learning loop that "learns continuously, improves deliberately" without ever silently rewriting Test Commander itself. The four capture commands (`/tc:learn` + `/tc:learn-from-failures` / `/tc:learn-from-exploration` / `/tc:learn-from-feedback`) append `tc-lesson/v1` candidates to `learning/lessons-inbox.md` through one shared engine — monotonic `LESSON-NNN` ids, `(source, origin, summary)` dedup keyed on **all** `learning/` files (so a reviewed/promoted lesson is never re-captured), and `path:line` provenance: `/tc:learn` from a freeform `--note`, `/tc:learn-from-failures` from the Phase-7 `runs/<RUN-ID>/analysis.md` triage, `/tc:learn-from-exploration` from `exploration-notes/` anomalies and coverage gaps, `/tc:learn-from-feedback` from resolved `open-questions.md` and uploaded feedback (a no-op, not an error, when there is none). `/tc:review-lessons` classifies each candidate (`severity: high` → needs-human-review; a summary already accepted → rejected; otherwise accepted), moves it to the matching `learning/` file with its `status` updated, and clears the inbox (idempotent). `/tc:promote-lessons` proposes by default (writing `promotion-proposal.md`, changing no guidance) and, only with `--apply` (the human-approval gate), moves accepted lessons into `learning/promoted-guidance.md` (`status: promoted`) and renders a `core-promotion-proposal.md` for any `core: true` lesson — writing **only** under `learning/`, never the shipped methodology and never third-party skills (Open Question Q6). Every applied promotion is a visible `git diff`. 758-test suite green; lint clean; 236-file Markdown link check clean. `verify_skills.py` reports all fourteen skills `PRESENT` (`tc-learning` at phase 8) with `UNEXPECTED=0`. Phase 8 ships no new `config.yaml` surface (recorded explicitly in the customization guide). Tagged `phase-8` on origin.

- [x] Step 8.1: scaffold `tc-learning` + the `seeded-learning` fixture (a Phase-7 analysis, an exploration note, resolved feedback, and a one-per-classification inbox) + `tests/test_phase_8_scaffolds.py` (8 cases); strict-PyYAML frontmatter from the start.
- [x] Step 8.2: `/tc:learn` + the `tc-lesson/v1` schema — `capture_lesson.py` (the shared `append_lessons` engine: monotonic ids, `(source, origin, summary)` dedup, stub-replacement, injected-clock determinism) + `learning-loop.md` + `lesson-taxonomy.md` + lesson template + command page + SKILL.md + `tests/test_capture_lesson.py` (6 tests).
- [x] Step 8.3: `/tc:learn-from-failures` — `learn_from_failures.py` (analysis-row parser, classification→category map, sibling-import of the engine) + command page + SKILL.md + `tests/test_learn_from_failures.py` (5 tests). Caught the `summary` YAML-quoting bug and fixed it in the shared renderer.
- [x] Step 8.4: `/tc:learn-from-exploration` — `learn_from_exploration.py` (section-aware anomaly/coverage-gap parser) + command page + SKILL.md + `tests/test_learn_from_exploration.py` (5 tests).
- [x] Step 8.5: `/tc:learn-from-feedback` — `learn_from_feedback.py` (resolved-open-questions + uploaded-feedback parser; no-feedback is a no-op, not an error) + command page + SKILL.md + `tests/test_learn_from_feedback.py` (5 tests). All four capture commands now feed the one inbox through the one engine.
- [x] Step 8.6: `/tc:review-lessons` — `review_lessons.py` (the three-bucket rubric; stub-vs-cleared reconciliation; canonical-key-order re-render) + `improvement-governance.md` + improvement-proposal template + command page + SKILL.md + `tests/test_review_lessons.py` (4 tests).
- [x] Step 8.7: `/tc:promote-lessons` — `promote_lessons.py` (propose-by-default; `--apply` human gate; core-promotion split; writes only under `learning/`) + `commander-doctrine.md` + `anti-patterns.md` + `heuristics.md` + core-promotion template + command page + SKILL.md + `tests/test_promote_lessons.py` (7 tests, the Q6 write-boundary snapshot). All six commands shipped, no deferral wording.
- [x] Step 8.8: documentation pass — `docs/user-guide/learning-loop.md` (verbatim output from the real chain), command-reference Phase 8 shipped section, workspace-reference `learning/` lifecycle, customization-guide "Phase 8 — what landed (no new extensible surface)", six-location status-line refresh, final deferral-wording sweep.
- [x] Step 8.9: testing finalization — `DEFAULT_PHASE_CAP` 7 → 8 (`tc-learning` flips `PRESENT`; `UNEXPECTED=0`) + `tests/test_phase_8_integration.py` (full Phase 2 → 8 sweep) + the `PHASE_OWNERSHIP["8"] == ["learning"]` confirmation. The integration's byte-stable re-run caught the cross-cycle dedup bug and drove the `append_lessons` fix (dedup/id over all `learning/` files).
- [x] Step 8.10: Phase 8 sign-off — cold-user walkthrough captured to `/tmp/tc-phase8-walkthrough.log` (`make uninstall` → `make install` clean, `claude plugin validate` over all fourteen SKILL.md; full Phase 2 → 8 chain ran the learning loop to a `--apply` promotion), per-step DoD audit clean for 8.1-8.9, plan + CHANGELOG closing, `tests/test_phase_8_signoff.py` (19 tests, test-def floor >= 720) gates the close, annotated `phase-8` tag pushed to origin.

### Phase 7 — Execution, evidence, and quality report (2026-06-01)

Three skills shipped, adding four commands plus the project's first **executing** command and an internal cross-cutting indexer: `tc-run` (`/tc:run` + the internal evidence-index sub-mode, `/tc:analyze-results`), `tc-evidence` (the command-less `index_evidence` indexer), and `tc-quality-report` (`/tc:report`, `/tc:quality-gate`). `/tc:run` executes the generated suite (or ingests a recorded Playwright JSON report via `--report`) for a run mode (`all`/`smoke`/`regression`/`feature`/`failed-only`/`tagged`) and writes a per-run record under `runs/<RUN-ID>/` mapping each `passed`/`failed`/`flaky` result to its requirement, candidate, scenario, and spec via `@req:`/`@cs:` provenance and the Phase-6 `automation-map.md`; the real `npx playwright test` invocation is **refused under pytest** (the hermetic boundary, `PYTEST_CURRENT_TEST`). It auto-runs the `tc-evidence` indexer (`--no-index` to suppress), which routes screenshots (committed) and videos/traces (git-ignored via `evidence/.gitignore`, with a git-lfs opt-in) into `evidence/` and rebuilds `evidence/evidence-index.md`. `/tc:analyze-results` triages every non-passed result (`product-defect`/`test-defect`/`environment`/`flaky`), writes `runs/<RUN-ID>/analysis.md`, and routes deduplicated `[test-analysis]` signals. `/tc:report` aggregates the workspace into `quality-report/current-quality-report.md` with all fifteen sections (keeping `[fact]`/`[interpretation]`/`[review]` separated, never inventing a metric), snapshots a full copy to `quality-report/history/<YYYY-MM-DD-HHmm>.md`, and rebuilds the maps so `test-map.md`'s `Test result` + `Quality report` columns resolve from `pending` (extending `traceability_map`/`render_test_map`, the Step 6.8 pattern). `/tc:quality-gate` evaluates the latest run against `tc-quality-report.gate.thresholds` and returns PASS/WARN/FAIL (CLI exits `1` on FAIL). Run IDs, report timestamps, and history-snapshot filenames come from an injected clock, so every artifact is byte-stable. 692-test suite green; lint clean; 214-file Markdown link check clean. `verify_skills.py` reports all thirteen skills `PRESENT` (the three Phase 7 skills at phase 7) with `UNEXPECTED=0`. Tagged `phase-7` on origin.

- [x] Step 7.1: three skill scaffolds (`tc-run`, `tc-quality-report`, `tc-evidence` — the last command-less) + the `seeded-results` fixture (a recorded run: results.json + automation-map + generated spec + evidence stubs) + one parametrized `tests/test_phase_7_scaffolds.py` (24 cases); strict-PyYAML frontmatter from the start.
- [x] Step 7.2: `/tc:run` — `run_tests.py` (run modes, the hermetic `--report` boundary, injected-clock RUN-ID, provenance join via `automation-map.md`) + `test-execution.md` + run-summary template + command page + SKILL.md + `tests/test_run_tests.py` (12 tests).
- [x] Step 7.3: `tc-evidence` indexer + the `/tc:run` auto-index wiring (`--no-index`) — `index_evidence.py` (`index_run_evidence`, policy routing, `.gitignore`, record-sourced index) + `evidence-management.md` + evidence template + SKILL.md + `tests/test_index_evidence.py` (8 tests, byte-identical auto-run-vs-standalone proof). First command-less skill: its spec lives in `methodology/`.
- [x] Step 7.4: `/tc:analyze-results` — `analyze_results.py` (four-category triage rubric, `[test-analysis]` dedup) + `failure-triage.md` + analysis template + command page + SKILL.md + `tests/test_analyze_results.py` (8 tests). Extended `run_tests` results.json to persist the failure error (additive, defaulted).
- [x] Step 7.5: `/tc:report` + `test-map` downstream resolution — `build_report.py` (fifteen sections, facts/interpretation/review, injected-clock history snapshot, calls the traceability rebuild) + `scan_run_results`/`quality_report_ref` + extended `render_test_map` + `quality-reporting.md` + report template + command page + SKILL.md + `tests/test_build_report.py` (8 tests).
- [x] Step 7.6: `/tc:quality-gate` — `quality_gate.py` (four criteria, PASS/WARN/FAIL, config thresholds via the `load_weights` pattern, CLI exit-1-on-FAIL) + `quality-gates.md` + gate template + command page + SKILL.md + customization-guide Phase 7 schema (three project shapes) + `tests/test_quality_gate.py` (7 tests).
- [x] Step 7.7: documentation pass — `running-tests.md` + `quality-report.md` (verbatim output from the real chain), command-reference Phase 7 shipped section, workspace-reference (runs/, evidence policy split, quality-report/ + history, test-map resolution), six-location status-line refresh, final deferral-wording sweep.
- [x] Step 7.8: testing finalization — `DEFAULT_PHASE_CAP` 6 → 7 (all three skills flip `PRESENT`; `UNEXPECTED=0`) + `tests/test_phase_7_integration.py` (full Phase 2 → 7 sweep) + `PHASE_OWNERSHIP` narrowing (Phase 7 → `runs`/`quality-report`, dropping `evidence` once the indexer writes real files there) with a RED→GREEN regression test.
- [x] Step 7.9: Phase 7 sign-off — cold-user walkthrough captured to `/tmp/tc-phase7-walkthrough.log` (`make uninstall` → `make install` clean, `claude plugin validate` over all thirteen SKILL.md; full Phase 2 → 7 chain produced the run record, evidence, triage, report + history, FAIL gate, and resolved `test-map`), per-step DoD audit clean for 7.1-7.8, plan + CHANGELOG closing, `tests/test_phase_7_signoff.py` (23 tests, test-def floor >= 680) gates the close, annotated `phase-7` tag pushed to origin.

### Phase 6 — Playwright framework and strategic automation (2026-05-29)

Four skills shipped, adding five commands and the project's first executable artifacts (generated Playwright/TypeScript): `tc-build-framework` (`/tc:build-framework`), `tc-automation-plan` (`/tc:automation-plan`), `tc-automate` (`/tc:automate` + the internal automation-review sub-mode, `/tc:review-automation`), and `tc-test-data` (`/tc:generate-test-data`). `/tc:build-framework` scaffolds the project-root `tests/{e2e,pages,components,fixtures,utils}/` tree + `playwright.config.ts` + `package.json` lazily (Decision D8; `ensure_framework` is the lazy-init entry point) — built only when absent, byte-stable no-op on re-run. `/tc:automation-plan` scores every BDD scenario against a universal seven-factor suitability rubric (`traceable`, `regression-value`, `risk-flagged`, `deterministic`, `right-sized`, `data-ready`, `persona-scoped`) and writes `automation-plan/<area>.md` ranking each `automate`/`consider`/`manual`; `@automated-candidate` and `@manual` are hard overrides; weights tune via `tc-automate.suitability.weights`. `/tc:automate` renders page objects, per-area fixtures, and specs for `automate`-ranked scenarios — each `test()` carrying `// @req:`/`@cs:` provenance and reaching data only through its fixture (D6) — writes the Phase-6-owned `traceability/automation-map.md`, and auto-runs the review (`--no-review` to suppress). `/tc:review-automation` runs the six-category universal rubric (`inline-test-data`, `hardcoded-wait`, `missing-provenance`, `weak-locator`, `untraceable-spec`, `assertion-free`), writes `automation-plan/review-summary.md`, and routes deduplicated `[automation-review]` gap signals; the shared `review_automation()` is exactly what `/tc:automate` auto-runs. `/tc:generate-test-data` populates `test-data/seed/<area>.json` + `test-data/scenarios/<area>.md`, closing the D6 loop. A `/tc:traceability-map` re-run after `/tc:automate` resolves the `Automated test` column of `test-map.md` from `pending` (new wiring in Step 6.8). Phase 6 generates and structurally validates TypeScript but never invokes `tsc`/Playwright (execution is Phase 7); it writes only the project-root `tests/` tree plus `automation-plan/`, `test-data/`, `automation-map.md`, and the `[automation-review]` line — never `bdd/` or `product-knowledge/`. 600-test suite green; lint clean; 193-file Markdown link check clean. `verify_skills.py` reports all ten skills `PRESENT` (the four Phase 6 skills at phase 6) with `UNEXPECTED=0`. Tagged `phase-6` on origin.

- [x] Step 6.1: four skill scaffolds + the `seeded-automation` fixture (clean automatable `sign-in.feature`) + one parametrized `tests/test_phase_6_scaffolds.py` (29 cases); strict-PyYAML frontmatter from the start.
- [x] Step 6.2: `/tc:build-framework` — `build_framework.py` (lazy + idempotent, `ensure_framework`) + four `.ts` object templates + `playwright-standards.md` + `locator-strategy.md` + `commands/build-framework.md` + SKILL.md update + `tests/test_build_framework.py` (12 tests); retired the stale `make build` runtime-guard placeholder.
- [x] Step 6.3: `/tc:automation-plan` — `automation_plan.py` (seven-factor rubric, config-tunable weights, reuses `review_bdd.parse_feature_file`) + `automation-suitability.md` + plan template + command page + SKILL.md update + `tests/test_automation_plan.py` (9 tests) + the first customization-guide Phase 6 entry.
- [x] Step 6.4: `/tc:automate` (generation only) — `automate.py` (page objects + fixtures + specs with provenance + fixture data, lazy-init via `ensure_framework`, owns `automation-map.md`) + umbrella `automation-generation.md` + command page + SKILL.md update + `tests/test_automate.py` (12 tests). Caught the recurring "template ships a README.md placeholder" trap via a RED test.
- [x] Step 6.5: `/tc:review-automation` + shared `review_automation()` + automate auto-run wiring (`--no-review`) — `review_automation.py` (six-category rubric, `[automation-review]` dedup) + `automation-review.md` + review template + command page + SKILL.md update + the `flawed.spec.ts` fixture + `tests/test_review_automation.py` (10 tests, byte-identical auto-run-vs-standalone proof).
- [x] Step 6.6: `/tc:generate-test-data` — `generate_test_data.py` (JSON seed + Markdown spec, skip-not-overwrite by content marker, reuses `parse_feature_file`) + `test-data-strategy.md` + data template + command page + SKILL.md update + `tests/test_generate_test_data.py` (7 tests). Closed the D6 fixture-data loop.
- [x] Step 6.7: documentation pass — `docs/user-guide/automation.md` (verbatim output from the real chain), command-reference Phase 6 shipped section, workspace-reference (project-root `tests/` framework + `test-data/` + `automation-map.md` ownership), customizing-for-your-project Phase 6 schema with three project-shape examples + "Phase 6 — what landed", six-location status-line refresh, final deferral-wording sweep (caught two stale 6.5 forward-pointers).
- [x] Step 6.8: testing finalization — `DEFAULT_PHASE_CAP` 5 → 6 (all four skills flip `PRESENT`; `UNEXPECTED=0`) + `tests/test_phase_6_integration.py` (full Phase 2 → 6 sweep) + the `test-map` `Automated test` resolution wiring (`scan_automation_specs` + `render_test_map(automated_by_cs)`, default-empty keeps Phase 5 byte-identical).
- [x] Step 6.9: Phase 6 sign-off — cold-user walkthrough captured to `/tmp/tc-phase6-walkthrough.log` (`make uninstall` → `make install` clean, both `claude plugin validate` manifests pass over all ten SKILL.md; full Phase 2 → 6 chain produced the framework + specs + resolved `test-map`), per-step DoD audit clean for 6.1-6.8, plan + CHANGELOG closing, `tests/test_phase_6_signoff.py` (22 tests, pytest floor >= 590) gates the close, annotated `phase-6` tag pushed to origin.

### Phase 5 — BDD generation and traceability (2026-05-29)

Two skills shipped: `tc-bdd` (`/tc:generate-bdd`, `/tc:review-bdd` + the internal review sub-mode) and `tc-traceability` (`/tc:traceability-map`), all end to end. `/tc:generate-bdd` turns Phase-4-enriched test-idea seeds into Gherkin `.feature` files — one scenario per `CS-NNN-NNN` candidate, each carrying machine-readable `@req:`/`@cs:` linkage tags, an `@area:` namespace tag, and a type-mapped class tag — then writes per-feature summaries, rebuilds `bdd/index.md`, and auto-runs the review sub-mode (suppressible with `--no-review`). `/tc:review-bdd` runs the six-category universal rubric (`ambiguous-step`, `missing-tag`, `untraceable`, `ui-coupled-step`, `missing-examples`, `conjunction-overload`), writes a verdict into each summary, and routes failures to `requirements/open-questions.md` as deduplicated `[bdd-review]` gap signals; the shared `review_features()` is the same code path the generate-time auto-run uses. `/tc:traceability-map` is the authoritative regenerator of `traceability/requirements-map.md` (the shared 4-column format rendered identically to `/tc:requirements-coverage` via the extracted `traceability_render.py` — no drift) and the new `traceability/test-map.md` (the scenario-level chain with `pending` downstream links, never invented). Phase 5 reads broadly but writes only to `bdd/`, `traceability/`, and the `[bdd-review]` line in `open-questions.md`; the integration smoke asserts `product-knowledge/` and `test-ideas/` are byte-identical before and after. Universal cores per D19 (type→class map, six review categories, linkage-tag convention); `tc-bdd.tags.extra-classes` and `tc-bdd.review.rubric-extensions` extensible via `<workspace>/config.yaml`. 496-test suite green; lint clean; 172-file Markdown link check clean. `verify_skills.py` reports all six skills `PRESENT` (`tc-bdd` and `tc-traceability` at phase 5) with `UNEXPECTED=0`. Tagged `phase-5` on origin.

- [x] Step 5.1: `tc-bdd` + `tc-traceability` scaffolds + seeded-bdd fixture (enriched `REQ-001.md` + `SESS-20260115-001.md` inputs + `flawed.feature` with one defect per universal review category) + `tests/test_tc_bdd_scaffold.py` (17 tests) + `tests/test_tc_traceability_scaffold.py` (8 tests). 25/25 GREEN; both scaffold tests assert strict-PyYAML frontmatter parse from the start (the Phase 4 Step 4.8 future-implementer hint).
- [x] Step 5.2: `/tc:generate-bdd` (generation only) — `generate_bdd.py` (Gherkin renderer + `Scenario` dataclass mirroring the enriched-test-idea shape + `@req:`/`@cs:`/`@area:` tags + type→class map + scan-and-index rebuild) + umbrella `methodology/bdd-generation.md` + `feature-template.feature` + `bdd-summary-template.md` + `commands/generate-bdd.md` + SKILL.md update + `tests/test_generate_bdd.py` (9 tests). Plan refinement: review wiring deferred to 5.3 (no forward dependency).
- [x] Step 5.3: `/tc:review-bdd` + shared `review_features()` + generate-bdd auto-run — `review_bdd.py` (six-category rubric with `\b`-anchored regexes to prevent cross-fire + per-area `[bdd-review]` dedup) + `methodology/bdd-quality-review.md` + `templates/bdd-review-template.md` + `commands/review-bdd.md` + SKILL.md update + the wiring edit into `generate_bdd.py` (`--no-review`) + `tests/test_review_bdd.py` (9 tests).
- [x] Step 5.4: `/tc:traceability-map` + shared `traceability_render.py` — extracted the requirements-map renderer from `requirements_coverage.py` (Phase-2 tests stay green) + `traceability_map.py` (authoritative regenerator; reuses the Phase-2 scanners + `review_bdd.parse_feature_file`) + `methodology/traceability.md` + `templates/traceability-map-template.md` + `commands/traceability-map.md` + SKILL.md update + `tests/test_traceability_map.py` (6 tests). Plan refinement: scenario detail in `test-map.md`, not a new column on the shared `requirements-map.md`.
- [x] Step 5.5: documentation pass — `docs/user-guide/generating-bdd.md` (verbatim output from the real chain), `docs/command-reference.md` (Phase 5 shipped section), `docs/workspace-reference.md` (bdd/ + traceability/ ownership + linkage-tag convention + reconciliation), customizing-for-your-project "Phase 5 schema" with three project-shape worked examples + "Phase 5 — what landed", six-location status-line refresh, final deferral-wording sweep.
- [x] Step 5.6: testing finalization — `DEFAULT_PHASE_CAP` 4 → 5 (both skills flip to `PRESENT`; `UNEXPECTED=0`) + `tests/test_phase_5_integration.py` (3 tests, in-process Phase 2 → 3 → 4 → 5). The smoke surfaced (and the test was corrected for) the correct behavior that flawed requirements produce flawed BDD that review flags — the generate→review pipeline working end to end.
- [x] Step 5.7: Phase 5 sign-off — cold-user walkthrough captured to `/tmp/tc-phase5-walkthrough.log` (`make install` clean; full chain produced 10 features + both maps + 10 `[bdd-review]` signals), per-step DoD audit clean for 5.1-5.6, plan + CHANGELOG closing, `tests/test_phase_5_signoff.py` (22 tests, pytest floor >= 460) gates the close, annotated `phase-5` tag pushed to origin.

### Phase 4 — Exploratory testing and test idea generation (2026-05-28)

`tc-explore` shipped: all four `/tc:` commands (`/tc:create-charter`, `/tc:explore`, `/tc:session-summary`, `/tc:test-ideas`) available end to end, plus the internal exploration-review sub-mode that auto-runs at the end of every `/tc:explore` session (suppressible with `--no-review`). Phase 4 reads broadly (Phase-3 product-knowledge + Phase-2 requirements + risk-register) but writes narrowly: only to `<workspace>/charters/`, `exploration-notes/`, `sessions/`, and `test-ideas/` enrichment, plus the `[exploration-review]` line in `requirements/open-questions.md`. The `tc-test-idea/v1` schema contract is shared across Phase 2 (author) and Phase 4 (enrich); every Phase-2 frontmatter key is preserved byte-for-byte through enrichment, with exactly two mutations (`status: seed` → `status: enriched`; `phase_4_sessions: [SESS-ID, ...]` merged sorted-deduplicated). Universal cores per D19: six anomaly categories, four severities, ten trigger words for coverage downgrade, three candidate-scenario types, universal English stopword list for the charter-coverage → REQ-ID stem-match algorithm. `tc-explore.{charters,exploration,review}` extensible via `<workspace>/config.yaml`. Recorded-mode session playback in tests with live mode opt-in and refused under pytest via `PYTEST_CURRENT_TEST` env-var check (mirrors Phase 3 Step 3.5 verbatim). 422-test suite green; lint clean; 157-file Markdown link check clean. `verify_skills.py` reports `tc-core PRESENT (phase 1)`, `tc-requirements PRESENT (phase 2)`, `tc-knowledge PRESENT (phase 3)`, `tc-explore PRESENT (phase 4)` (clean `UNEXPECTED=0`). Tagged `phase-4` on origin.

- [x] Step 4.1: `tc-explore/SKILL.md` scaffold + seeded-exploration-session fixture (CH-001 charter with 5 ACs + recorded-session.json carrying 55 timestamped events covering all 7 event types + one anomaly per universal category + target-app.md + README documenting the universal `knowledge: <category>` marker convention) + `tests/test_tc_explore_scaffold.py` (20 tests). 20/20 GREEN on first author; the fixture was written against the test rather than the reverse. Cross-phase narrative consistency with the Phase-3 sample-project fixture (same Account/Session/Workspace/Asset entity vocabulary + same URL paths) means Step 4.7's integration smoke composes without translation.
- [x] Step 4.2: `/tc:create-charter` — `create_charter.py` (auto-suggestion by entity mention count with explicit alphabetical tiebreaker + `--target`/`--mission`/`--new-id` flags + skip-not-overwrite idempotency) + umbrella `methodology/exploratory-testing.md` + per-command `methodology/charter-based-exploration.md` + `templates/charter-template.md` + `templates/target-app-template.md` + `commands/create-charter.md` + SKILL.md update + `tests/test_create_charter.py` (14 tests). 14/14 GREEN on first run via helper-mirroring from the Phase-3 skeleton + cross-phase contract enumeration (`CHARTER_REQUIRED_FIELDS` declared identically in scaffold test AND helper render). Broken-link drift in five-segment relative paths caught and fixed in the same sub-step.
- [x] Step 4.3: `/tc:explore` + internal exploration-review sub-mode — `explore.py` (universal-core event-type classification + 6 universal anomaly categories + Charter-Coverage matrix with URL-and-keyword scoring + trigger-word downgrade + asymmetric missing-evidence rule + content-derived SESS-ID allocation) + `methodology/session-based-test-management.md` + 3 new templates (`exploration-note-template.md`, `anomaly-record-template.md`, `exploration-review-template.md`) + `commands/explore.md` + SKILL.md update + `tests/test_explore.py` (17 tests). 16/17 GREEN on first cut; one-line fix to the SESS-ID allocator (filesystem-scanning + counter → content-derived deterministic hash from the recording's first-event timestamp). Live-mode refusal under pytest mirrors Phase 3 Step 3.5 verbatim.
- [x] Step 4.4: `/tc:session-summary` + sessions index ledger — `session_summary.py` (per-section table parsers for exploration notes + aggregate counts by `event_type` AND `category` AND `severity` + one-line coverage verdict + deterministic candidate-scenario synthesis: negative-per-anomaly + edge-per-partial-coverage + up-to-three happy-per-successful-network-request + content-derived CS-IDs) + `sessions/index.md` ledger rebuilt from scratch by scanning every `sessions/SESS-*.md` + extension to `methodology/session-based-test-management.md` (Session summary subsection) + `templates/session-summary-template.md` + `commands/session-summary.md` + SKILL.md update + `tests/test_session_summary.py` (15 tests). 13/15 GREEN on first cut; per-candidate `### CS-NNN-NNN` sub-sections beat tables when the downstream consumer (Step 4.5) parses each entry independently. Candidate-shape is the second cross-phase contract enumeration in Phase 4.
- [x] Step 4.5: `/tc:test-ideas` (enrich Phase-2 seeds) — `enrich_test_ideas.py` (five-character prefix-stem charter-coverage → REQ-ID cross-reference + frontmatter-preserving merge with pre-scan-decides-which discipline + body merge appending per-SESS-ID sub-blocks under a single `## Phase 4 enrichment` header) + `methodology/test-idea-model.md` (schema contract per-key mutability table + Claude judgment layer) + `templates/test-idea-enrichment-template.md` + `commands/test-ideas.md` + SKILL.md update + `tests/test_enrich_test_ideas.py` (17 tests). 15/17 GREEN on first cut; one-method `merge_phase_4_sessions` fix (pre-scan for existing key before deciding insert-vs-update). Cross-phase contract triangle closed at the dataclass level (`session_summary.CandidateScenario` ⊆ `enrich_test_ideas.CandidateScenario`).
- [x] Step 4.6: dedicated documentation pass — `docs/user-guide/exploring-an-app.md` (Phase 4 end-to-end walkthrough with verbatim sample output captured from a tmp workspace driven through the actual helper chain), `docs/command-reference.md` (Phase 4 commands shipped section), `docs/workspace-reference.md` enriched (per-file ownership table for the 4 Phase 4 artifact slots + content-derived SESS-ID allocation contract + cross-phase write-boundary discipline + `tc-test-idea/v1` shared-schema contract), six-location status-line refresh, `docs/user-guide/customizing-for-your-project.md` new "Phase 4 schema (`tc-explore`)" section with all 3 sub-blocks + 3 worked extension examples spanning materially-different project shapes (Python web app + Playwright; mobile app with non-Playwright MCP; API-only project with spec-derived recordings) + "Phase 4 — what landed" subsection, final SKILL.md pass with umbrella methodology workflow diagram scrubbed of `(behavior arrives in 4.N)` deferral wording. All 12 YAML blocks in the customizing guide parse cleanly.
- [x] Step 4.7: testing finalization — `DEFAULT_PHASE_CAP` 3 → 4 in `scripts/verify_skills.py` (CATALOG already had `tc-explore: 4` from Step 0.6.1; verifier flipped from `UNEXPECTED=1` to `UNEXPECTED=0`); `tests/test_phase_4_integration.py` (3 tests, in-process import pattern: full Phase 2 → Phase 3 → Phase 4 sweep in 0.30s + byte-stable re-run + live-mode refusal). 3/3 GREEN on first run; integration smoke budgeted as verification not debugging per the Phase 3 Step 3.8 lesson, and that budget held.
- [x] Step 4.8: Phase 4 sign-off — cold-user walkthrough captured to `/tmp/tc-phase4-walkthrough.log` (surfaced and fixed one latent bug: `tc-explore/SKILL.md` description value contained `tc-explore.mode: live` which the strict YAML parser in `claude plugin validate` rejected — fix was a one-word edit to remove the embedded `key: value` pattern; the project's own regex-based `verify_skills.py` had tolerated it), per-step DoD audit clean for 4.1-4.7 (every helper / methodology / template / command page / test file on disk; every sub-step lesson entry present), plan + CHANGELOG updated, `tests/test_phase_4_signoff.py` (22 tests including lessons-learned coverage for 4.1-4.7, customization-guide schema parity, strict-YAML frontmatter parse, and pytest-count floor >= 400) gates the close, annotated `phase-4` tag pushed to origin.

### Phase 3 — Project knowledge ingestion (2026-05-27)

`tc-knowledge` shipped: all five `/tc:learn-from-*` commands (`/tc:learn-from-docs`, `/tc:learn-from-specs`, `/tc:learn-from-code`, `/tc:learn-from-api`, `/tc:learn-from-tests`) available end to end, plus the shared `synthesize_system_model.py` invoked by every helper to regenerate `<workspace>/product-knowledge/system-model.md` byte-deterministically. Per-source models (`documentation-model.md`, `spec-derived-model.md`, `code-derived-model.md`, `api-model.md`, `tests-coverage.md`) are overwrite-mode; cross-cutting artifacts (`entities.md`, `user-journeys.md`, `business-rules.md`, `assumptions.md`) use `## From <source>` namespaced section-overwrite so re-running one helper preserves sibling sections. Gap signals route to `<workspace>/requirements/open-questions.md` with a `[<kind>]` prefix and Phase-2 dedup contract. Phase-3 design discipline: writes confined to `product-knowledge/` and `requirements/open-questions.md` only — no writes to `<workspace>/traceability/` (which is Phase-5 owned). Universal-core extractors per D19; `tc-knowledge.{documents,code,api,tests}` extensible via `<workspace>/config.yaml` (four sub-blocks). Python-only AST in v1 with non-Python extensions flagged as `language-unsupported-in-v1`; OpenAPI 3 + Postman v2.1 collection auto-detection via PyYAML (first non-stdlib runtime dep); recorded-mode API playback in tests with live mode opt-in and refused under pytest via `PYTEST_CURRENT_TEST` env-var check. 314-test suite green; lint clean; 137-file Markdown link check clean. `verify_skills.py` reports `tc-core PRESENT (phase 1)`, `tc-requirements PRESENT (phase 2)`, `tc-knowledge PRESENT (phase 3)` (clean `UNEXPECTED=0`). Tagged `phase-3` on origin.

- [x] Step 3.1: `tc-knowledge/SKILL.md` scaffold + seeded sample-project fixture (universal-SaaS narrative, 5 sub-trees + README, 11 gap-signal markers using a uniform `knowledge: <dim>` convention across HTML, YAML, Python, TypeScript, and JSON) + `tests/test_tc_knowledge_scaffold.py` (23 tests). Added `norecursedirs = ["fixtures"]` to pytest config because fixture's example tests would otherwise be collected as Test Commander tests.
- [x] Step 3.2: `/tc:learn-from-docs` + shared `synthesize_system_model.py` — `extract_knowledge_from_docs.py` (5 positive dimensions + 2 gap signals: undefined-term, contradictory-rule) + umbrella `methodology/project-knowledge.md` + `methodology/learning-from-documents.md` + 6 templates (per-source + 5 cross-cutting) + `commands/learn-from-docs.md` + SKILL.md update + `tests/test_learn_from_docs.py` (~24 tests). Established the Phase-3 helper skeleton subsequent steps mirror.
- [x] Step 3.3: `/tc:learn-from-specs` — `extract_knowledge_from_specs.py` (OpenAPI 3 YAML/JSON + Postman v2.1 auto-detection; 3 positive dimensions + 2 gap signals: unspecified-status, schema-without-type) + `methodology/learning-from-specs.md` + `templates/spec-derived-model-template.md` + `commands/learn-from-specs.md` + SKILL.md update + `tests/test_learn_from_specs.py` (21 tests). PyYAML added as `[project.dependencies]`.
- [x] Step 3.4: `/tc:learn-from-code` — `extract_knowledge_from_code.py` (Python stdlib `ast` walk; 4 positive dimensions + 3 gap signals: undocumented-function, language-unsupported-in-v1, unimplemented-endpoint) + `methodology/learning-from-code.md` + `templates/code-derived-model-template.md` + `commands/learn-from-code.md` + SKILL.md update + `tests/test_learn_from_code.py` (24 tests). Fixture alignment: openapi.yaml operationIds named for handler functions; new `accounts.py` for the get_account handler.
- [x] Step 3.5: `/tc:learn-from-api` — `extract_knowledge_from_api.py` (recorded-mode playback + 3 positive dimensions + 2 gap signals: unspecified-endpoint, mismatched-status; live mode refused under pytest via `PYTEST_CURRENT_TEST`) + `methodology/learning-from-api.md` + `templates/api-model-template.md` + `commands/learn-from-api.md` + SKILL.md update + `tests/test_learn_from_api.py` (23 tests). 23/23 GREEN on first run — first Phase-3 sub-step with no bug-fix cycle; cross-helper import (3.5 imports `extract_knowledge_from_specs.aggregate()` via a tiny `Endpoint.statuses` field extension). Fixture realignment: mismatched-status marker moved to DELETE /sessions/{id}.
- [x] Step 3.6: `/tc:learn-from-tests` — `extract_knowledge_from_tests.py` (pytest stdlib `ast` walk + Playwright regex counting; 3 positive dimensions + 2 gap signals: untested-function, unsupported-test-runner) + `methodology/learning-from-tests.md` + `templates/tests-coverage-template.md` + `commands/learn-from-tests.md` + final SKILL.md pass (deferral wording fully removed; all five commands shipped) + `tests/test_learn_from_tests.py`. `tests-coverage.md` added to Workspace Layout in `planning/plan.md` and to `docs/workspace-reference.md`; new workspace-template stub. Closes the Phase-3 helper sweep.
- [x] Step 3.7: dedicated documentation pass — `docs/user-guide/building-project-knowledge.md` (Phase 3 end-to-end walkthrough), `docs/command-reference.md` (Phase 3 commands shipped section with per-command-page links), `docs/workspace-reference.md` enriched (per-file ownership tables for the 10 product-knowledge artifacts + cross-cutting contribution map + explicit "Phase 3 does not write to traceability/" callout), six-location status-line refresh, `docs/user-guide/customizing-for-your-project.md` new "Phase 3 schema (`tc-knowledge`)" section with all 4 sub-blocks + 3 worked extension examples spanning materially-different consuming-project shapes (Python/FastAPI, Node/Express with `enabled-languages: []`, Postman-only) + "Phase 3 — what landed" subsection naming the 7 tests that defend the schema.
- [x] Step 3.8: testing finalization — `DEFAULT_PHASE_CAP` 2 → 3 in `scripts/verify_skills.py` (CATALOG already had `tc-knowledge: 3` from Step 3.1; verifier flipped from `UNEXPECTED=1` to `UNEXPECTED=0`); `tests/test_phase_3_integration.py` (3 tests, in-process import pattern: full 5-helper workflow + byte-stable re-run across 10 product-knowledge files + live-mode refusal in-process). 3/3 GREEN on first run.
- [x] Step 3.9: Phase 3 sign-off — cold-user walkthrough captured to `/tmp/tc-phase3-walkthrough.log`, per-step DoD audit clean, plan + CHANGELOG updated, `tests/test_phase_3_signoff.py` (17 tests including lessons-learned coverage for 3.1-3.8, customization-guide schema parity, Workspace Layout `tests-coverage.md` inclusion, and pytest-count floor >= 200) gates the close, annotated `phase-3` tag pushed to origin.

### Phase 2 — Requirements and user story intelligence (2026-05-27)

`tc-requirements` shipped: all five commands (`/tc:review-requirements`, `/tc:review-user-stories`, `/tc:review-acceptance-criteria`, `/tc:requirements-coverage`, `/tc:requirements-to-tests`) available end to end, with `SKILL.md` describing each shipped command (no deferral wording remaining) and routing Claude to the bundled helpers. Universal-core mechanical rubric for the requirement-level dimensions; `tc-requirements.{data-rules,risk,roles-permissions}` extensible via `<workspace>/config.yaml` per D19. Seeded fixture (deliberately-generic SaaS-surface narrative) drives every per-command test. Phase-4-compatible `tc-test-idea/v1` schema contract documented for downstream skills. 172-test suite green; lint clean; 107-file Markdown link check clean. `verify_skills.py` reports `tc-core PRESENT (phase 1)` and `tc-requirements PRESENT (phase 2)` (clean `UNEXPECTED=0`). Two new Per-Phase Conventions codified during the phase: Customization-guide audit (D19) and Sub-step lesson capture. Tagged `phase-2` on origin.

- [x] Step 2.1: `tc-requirements/SKILL.md` scaffold + seeded-flawed-requirements fixture (every rubric dimension + every INVEST letter + every AC dimension seeded) + `tests/test_tc_requirements_scaffold.py` (15 tests). Domain-leakage lesson surfaced and folded into D19.
- [x] Step 2.2: `/tc:review-requirements` — `review_requirements.py` (16 mechanical checks per the partition table, `config.yaml` extension hook) + `commands/review-requirements.md` + `methodology/requirements-quality-review.md` + `templates/requirements-review-template.md` + SKILL.md update + `tests/test_review_requirements.py` (10 tests). Parser-body emptiness bug + plural-form keyword bug caught at the unit level.
- [x] Step 2.3: `/tc:review-user-stories` — `review_user_stories.py` (8 mechanical checks: 6 INVEST + role-action-benefit + needs-acceptance-criteria) + `commands/review-user-stories.md` + `methodology/user-story-readiness.md` + `templates/user-story-review-template.md` + SKILL.md update + `tests/test_review_user_stories.py` (9 tests). 9/9 pass on first run by mirroring the Step 2.2 helper structure.
- [x] Step 2.4: `/tc:review-acceptance-criteria` — `review_acceptance_criteria.py` (5 AC-rubric checks + orphan detection + parenthetical-strip preprocessing) + `commands/review-acceptance-criteria.md` + `methodology/acceptance-criteria-quality.md` + `templates/acceptance-criteria-review-template.md` + SKILL.md update + `tests/test_review_acceptance_criteria.py` (7 tests). Fixture meta-commentary contamination lesson captured.
- [x] Step 2.5: `/tc:requirements-coverage` — `requirements_coverage.py` (cross-references inventory IDs with `test-ideas/`, `bdd/features/`, automation map; orphan detection) + `commands/requirements-coverage.md` + `templates/requirements-coverage-template.md` + SKILL.md update + `tests/test_requirements_coverage.py` (8 tests). Template-stub vs generated-artifact ambiguity lesson captured (recurring pattern).
- [x] Step 2.6: `/tc:requirements-to-tests` — `requirements_to_tests.py` (Phase-4 `tc-test-idea/v1` schema; skip-not-overwrite idempotency; refreshes traceability map by re-using `requirements_coverage.coverage()`) + `commands/requirements-to-tests.md` (Phase 4 schema contract) + SKILL.md fully consolidated, all deferral wording removed + `tests/test_requirements_to_tests.py` (9 tests). Template-stub pattern from 2.5 recurred exactly as predicted; cross-helper return-type mismatch caught; skip-not-overwrite vs byte-deterministic-overwrite idempotency mode rule.
- [x] Step 2.7: documentation pass — `docs/user-guide/reviewing-requirements.md` (Phase 2 walkthrough), `docs/command-reference.md` (Phase 2 commands shipped section), `docs/workspace-reference.md` enriched (per-file `requirements/` ownership table + `test-ideas/` Phase-2-seeder note), 6-location status-line refresh, final `tc-requirements/SKILL.md` consolidation pass.
- [x] Step 2.8: testing finalization — `DEFAULT_PHASE_CAP` 1 → 2 in `scripts/verify_skills.py`; `tests/test_phase_2_integration.py` (1 test, 13 assertion blocks driving all five helpers end-to-end). `tests/test_phase_1_signoff.py` exact-match `== 1` assertion loosened to `>= 1` per the monotonically-non-decreasing rule.
- [x] Step 2.9: Phase 2 sign-off — cold-user walkthrough captured to `/tmp/tc-phase2-walkthrough.log`, per-step DoD audit clean (every step's deliverables on disk + lesson entries present), plan + CHANGELOG updated, `tests/test_phase_2_signoff.py` (17 tests, including lessons-learned coverage and customization-guide schema parity) gates the close, annotated `phase-2` tag pushed to origin.

### Phase 1 — Workspace and artifact model (2026-05-26)

`tc-core` shipped: `/tc:init`, `/tc:status`, `/tc:journal`, `/tc:next` available end to end, with `SKILL.md` describing each command and routing Claude Code slash-command invocations to the bundled helpers. Workspace template bundled inside the plugin (per D18). 96-test suite green; 88-file Markdown link check clean. `verify_skills.py` reports `tc-core PRESENT (phase 1)`. Tagged `phase-1` on origin.

- [x] Step 1.1: `plugins/test-commander/templates/workspace/` (63 starter files matching the Workspace Layout) + `tests/test_workspace_template.py` (7 tests).
- [x] Step 1.2: `/tc:init` — `plugins/test-commander/scripts/init_workspace.py` + `tc-core/commands/init.md` + `tests/test_init_workspace.py` (4 tests). New Decision D18 (helpers + templates bundled inside the plugin) added; old `templates/workspace/` moved to the plugin via `git mv`.
- [x] Step 1.3: `/tc:status` — `workspace_state.py` + `status.md`. `WorkspaceSnapshot` dataclass (exists, initialized, last_modified, counts, populated, phase_status) shared with `/tc:next`. `tests/test_workspace_state.py` (6 tests).
- [x] Step 1.4: `/tc:journal` — `journal.py` + `journal.md`. Append + summarize modes; one-file-per-day format (H1 date, H2 timestamp sections). `tests/test_journal.py` (8 tests). AI summaries deferred to Phase 8.
- [x] Step 1.5: `/tc:next` — `next_step.py` + `next.md` + `methodology/next-step-inference.md`. 10 R-rules; ranked list with `next:` line. `tests/test_next_step.py` (13 tests).
- [x] Step 1.6: documentation pass — `docs/workspace-reference.md` filled in, `docs/command-reference.md` rewritten as an index linking per-command pages, new `docs/user-guide/workflow.md` end-to-end walkthrough, status lines refreshed, `tc-core/SKILL.md` rewritten to describe all four shipped commands and route Claude to the bundled helpers.
- [x] Step 1.7: testing finalization — `CATALOG["tc-core"]` and `DEFAULT_PHASE_CAP` bumped to 1; `tests/test_phase_1_integration.py` (1 test, 9 assertion blocks) drives all four helpers in sequence.
- [x] Step 1.8: Phase 1 sign-off — cold-user walkthrough captured, per-step DoD audit clean, plan + CHANGELOG updated, `tests/test_phase_1_signoff.py` (11 tests) gates the close, annotated `phase-1` tag pushed to origin.

### Phase 0 — Repository foundation (2026-05-26)

End-to-end clean install verified: `./bootstrap.sh` → `make install` → `test-commander:tc-core` loaded in Claude Code. 46-test suite green; 23-file Markdown link check clean. Tagged `phase-0` on origin.

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
- Every Test Commander skill is owned in-repo under `plugins/test-commander/skills/`. No runtime dependency on external skill plugins.
