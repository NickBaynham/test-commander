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
- **`/tc:next` recommends `/tc:automation-plan` not `/tc:learn-from-docs` after Phase 2 close.** This is a known interaction between Phase 2's traceability-map write and the R-rules in `next-step-inference.md`: writing to `traceability/requirements-map.md` (Phase 5 ownership) and `test-ideas/` (Phase 4 ownership) bumps both phases to in_progress, so R4/R5/R6 skip and R7 (Phase 6) fires. The integration test in 2.8 asserts `command != /tc:review-requirements` (advanced past Phase 2) rather than the specific next command, which is the robust invariant. **Future-implementer hint:** when an upstream skill (Phase 2) writes to a downstream-owned directory (Phase 4 / 5 traceability), the phase-status heuristic in `/tc:next` may skip phases that ostensibly still need their own commands. The R-rules will need refinement in Phase 8 (`tc-learning`) or earlier; for now, downstream phases need to be explicit about whether "directory has content" means "phase is in progress" or "phase has been worked on". Flag for the Phase 3 author.

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

- `tc-explore`'s internal review sub-mode (designed after `mcp-exploratory-testing:review-exploration`) runs against new session reports as part of the review gate.
- Findings link back to charter ID and product knowledge.

**Test step.**

- Replay a recorded exploration on a known sample app; confirm artifact counts and shape.

**Definition of done.**

- Exploration produces charters, notes, ideas, risks, and evidence in the right folders; `tc-explore`'s review sub-mode passes the artifacts; user guide is complete.

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

**Tags.** Shipped universal classes: `@smoke`, `@regression`, `@manual`, `@exploratory`, `@automated-candidate`. Per D19, Test Commander ships no hard-coded domain, risk, or persona taxonomy — projects add values under shared namespaces:

- `@area:<feature>` — project-defined feature areas (e.g. `@area:sign-in`, `@area:reports`).
- `@risk:<class>` — project-defined risk classes (e.g. severity `@risk:high`/`@risk:medium`/`@risk:low`, or category `@risk:data-loss`/`@risk:availability`/`@risk:integrity`).
- `@persona:<role>` — project-defined personas (e.g. `@persona:admin`, `@persona:operator`).

Test Commander ships the namespaces; the consuming project picks values, documents them in its own BDD methodology notes, and configures any tag-driven gates.

**Traceability chain.** Requirement → Test Idea → BDD Scenario → Automation Candidate → Automated Test → Test Result → Quality Report.

**Documentation.** `docs/user-guide/generating-bdd.md`.

**Review step.**

- `tc-bdd`'s internal review sub-mode (designed after `exploratory-to-bdd:review-bdd`) runs against new specs; traceability map updated and verified.

**Test step.**

- Round-trip a small requirement → BDD → traceability flow and assert the trace map contains the expected links.

**Definition of done.**

- Feature files live under `.test-commander/bdd/features/`, summaries written, traceability complete, `tc-bdd`'s review sub-mode passes, user guide complete.

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

- `tc-automate`'s internal review sub-mode (designed after `agentic-playwright-automation:review-playwright-test`) runs on generated tests.
- Test data files are referenced from at least one fixture; nothing inline.

**Test step.**

- A smoke spec runs against a local example app (brought up by the tester; not vendored) and passes.

**Definition of done.**

- Framework builds on demand, tests reference data via fixtures, suitability rubric is applied in the automation plan, `tc-automate`'s review sub-mode passes, user guide complete.

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

- Pages render against a populated workspace; SSE updates appear on journal append; chat refuses any action above `read-only` and surfaces proposal cards only — execution gating ships in Phase 10.5.

**Test step.**

- End-to-end: `make run` brings up the stack via docker compose; smoke navigations across all pages succeed.

**Definition of done.**

- All pages work, SSE delivers updates, indexer keeps up with workspace changes, chat is read-only + proposal cards only (execution gating ships in Phase 10.5), user guide complete.

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
- [ ] **3.1** — Scaffold `tc-knowledge` skill and seeded sample-project fixture (universal-SaaS narrative; defects tagged with `<!-- knowledge: ... -->`)
- [ ] **3.2** — `/tc:learn-from-docs` (TDD) + shared `synthesize_system_model.py` + umbrella `project-knowledge.md` methodology + cross-cutting and per-source templates
- [ ] **3.3** — `/tc:learn-from-specs` (TDD) — OpenAPI/Postman auto-detection
- [ ] **3.4** — `/tc:learn-from-code` (TDD) — Python AST walk; non-Python languages counted as `language-unsupported-in-v1`
- [ ] **3.5** — `/tc:learn-from-api` (TDD) — recorded playback in tests; live mode opt-in via config
- [ ] **3.6** — `/tc:learn-from-tests` (TDD) — pytest + Playwright detection; add `tests-coverage.md` to Workspace Layout and `workspace-reference.md`
- [ ] **3.7** — Documentation pass: author `docs/user-guide/building-project-knowledge.md`; update command-reference, workspace-reference, customizing-for-your-project (Phase 3 `tc-knowledge` schema + three worked extension examples), status lines
- [ ] **3.8** — Testing finalization: bump `DEFAULT_PHASE_CAP` to 3 and `CATALOG["tc-knowledge"] = 3`; author `test_phase_3_integration.py`; assert live-mode refusal under test harness
- [ ] **3.9** — Sign-off (six sub-sub-steps): cold-user walkthrough, per-step DoD audit, plan + CHANGELOG closing, doc final pass, test-first sign-off test, final DoD eval + `phase-3` annotated tag

### Phase 4
- [ ] Author `/tc:create-charter`, `/tc:explore`, `/tc:test-ideas`, `/tc:session-summary`
- [ ] Author methodology and templates
- [ ] Author `docs/user-guide/exploring-an-app.md`
- [ ] Author `tc-explore`'s internal review sub-mode (designed after `mcp-exploratory-testing:review-exploration`) and wire it into the review gate
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
