# Test Commander — Agent Orientation

This file is for an agent (Claude, or any future operator) picking up Test Commander work cold. It is the entry point that points at the authoritative documents and names the disciplines a new session needs before touching code. Read this top-to-bottom **once per session** before reading anything else.

If you are the parent project's global agent and have already loaded `~/projects/CLAUDE.md`, this file extends and specializes those rules for the Test Commander repo. The parent rules still apply (PDM as the Python package manager, no emojis anywhere, root-cause-before-fix discipline, make targets, prove-the-problem-first).

## Project identity (one paragraph)

Test Commander is an AI-assisted testing system and quality intelligence center, shipped as a Claude Code plugin plus a small Python runtime. It turns requirements, exploration, BDD, automation, evidence, reporting, and continuous learning into one visible workflow. It is **product-domain-agnostic** (Decision D19): the shipped rubric, tag taxonomy, methodology, fixtures, and examples use universal English and software-engineering vocabulary only — domain vocabulary enters only through `<workspace>/config.yaml` extensions, the consuming project's uploaded documents, Phase 3 knowledge ingestion, and project-defined tag namespaces. The project ships phase by phase; as of the most recent tag, Phases 0–2 are complete (annotated `phase-0`, `phase-1`, `phase-2` tags on origin).

## Source of truth

| Document | What it owns |
| --- | --- |
| [planning/plan.md](planning/plan.md) | **The authoritative spec.** 1,900+ lines. Contains the Decisions (D1–D19), Open Questions (Q1–Q15), Per-Phase Conventions, Workspace Layout, Skill Authoring Strategy, per-phase execution outlines with sub-steps, To Do, Completed, and Phase N Lessons learned subsections. **If the plan and the code disagree, fix the plan first, then the code.** |
| [CHANGELOG.md](CHANGELOG.md) | Phase-by-phase shipping log. Newest changes at the top within each phase section. Each completed step has its own long-bullet entry. |
| [README.md](README.md) | User-facing project overview. Status line names the most recent completed phase. |
| [docs/](docs/) | User guides, workspace reference, command reference, customization guide, install guide. |
| [plugins/test-commander/skills/](plugins/test-commander/skills/) | Each shipped skill has SKILL.md (Claude's runtime entry point), commands/ (per-command pages — single source of truth at runtime), methodology/, templates/. |

**Start here every session:** open `planning/plan.md` and read (1) Decisions D1–D19, (2) the Per-Phase Conventions block, (3) the most recent phase's section to find the current sub-step. Do not skip this — most of the project's discipline is encoded in the plan, not in the code.

## Decisions at a glance (D1–D19)

These are settled and constrain every phase. Read the plan for each one's full text and rationale.

| # | One-liner |
| --- | --- |
| **D1** | **Vendor and own all skills.** Every skill Test Commander ships is authored in-repo under `plugins/test-commander/skills/<name>/`. Community skills are design references only, never runtime dependencies. |
| **D2** | Test Commander is a skill pack first, runtime second. Phases 0–5 + 7–9 author Markdown skills; Phase 6 adds Playwright; Phase 10 adds web/API runtime. |
| **D3** | No `examples/` directory. Real projects bring their own artifacts. |
| **D4** | All BDD lives under `.test-commander/bdd/`. |
| **D5** | Workspace is committed to git, including quality-report history. |
| **D6** | Test data lives at `.test-commander/test-data/`, never inline in test code. |
| **D7** | Capstone is Phases 0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 10.5. |
| **D8** | Playwright framework is built lazily by `/tc:build-framework`. |
| **D9** | Every phase has Review, Test, and Documentation steps. |
| **D10** | `make install` provisions the full environment. |
| **D11** | Phase 3 precedes Phase 4 in every rollout. |
| **D12** | Plugin structure follows Claude Code's convention (marketplace at repo root, plugin under `plugins/<name>/`, sibling skills under `skills/<skill-name>/`). No umbrella SKILL.md — the plugin manifest provides identity. |
| **D13** | Platform support: macOS, Linux, WSL2, Git Bash. No PowerShell. |
| **D14** | `bootstrap.sh` precedes `make install`. Idempotent verification only. |
| **D15** | Runtime topology: Pattern A (local-first) is the MVP default. |
| **D16** | Frontend users drive Test Commander workflows, not raw Claude Code. |
| **D17** | **Plan steps use the `claude` CLI, not interactive slash commands.** `claude plugin marketplace add`, `claude plugin install`, `claude plugin validate`, etc. — never `/plugin marketplace add` (unavailable in some sessions). |
| **D18** | **User-facing helpers and templates ship inside the plugin** (`plugins/test-commander/scripts/`, `plugins/test-commander/templates/`); dev tooling stays at the repo root (`scripts/verify_skills.py`, `scripts/check_links.py`). Only `plugins/test-commander/` contents are copied into the installed plugin cache. |
| **D19** | **Test Commander is product-domain-agnostic.** Universal English / software-engineering vocabulary only in shipped defaults. Domain vocabulary enters via `<workspace>/config.yaml` extensions, project documents under `documents/uploaded/`, Phase 3 knowledge ingestion, or project-defined tag namespaces. Illustrative examples prefer universal SaaS surfaces (`sign-in`, `dashboard`, `search`, `file upload`) over domain-specific features (`checkout`, `refund`, `prescription`). |

## Per-Phase Conventions

Every phase obeys all five conventions. They are codified in `planning/plan.md` under "Per-Phase Conventions." Numbered for cross-reference; the plan has the full text.

1. **Six per-phase deliverables.** Implementation, skills authored (or extended) + design references, documentation, review step, test step, definition of done.
2. **`claude` CLI for plugin operations** (per D17). Validate manifests with `claude plugin validate` before any install or marketplace registration.
3. **Retire prior-phase guards in the commit that lands the replacement.** When a phase adds artifacts a previous phase's guard test forbade ("no executable runtime until Phase 6"), retire the guard in the same commit.
4. **SKILL.md surfaces shipped behavior.** Each command sub-step that ships a helper + per-command page must, in the same sub-step, update the owning SKILL.md to describe the now-shipped behavior and instruct Claude to invoke the bundled helper. Stale "behavior arrives in Phase N+1" wording for a shipped command is a per-step DoD failure. The phase sign-off test asserts no deferral wording remains.
5. **Per-command page is the single source of truth.** Every `/tc:*` command has a page at `plugins/test-commander/skills/<skill>/commands/<command>.md` with these sections in order: Inputs, Outputs, Preconditions, Behavior, Safety, Implementation, Definition of Done, See also. The same file is what Claude reads at runtime and what users read for reference. `docs/command-reference.md` indexes — it does not duplicate.
6. **Customization-guide audit (per D19).** Every phase that ships a configurable surface — a new `<workspace>/config.yaml` schema key, a new tag namespace, a new keyword set, a new policy override — MUST update `docs/user-guide/customizing-for-your-project.md` in the same sub-step that ships the surface, with at least one worked example showing how a consuming project extends it for their domain. Phases that ship no new extensible surface record that explicitly in sign-off ("no new extensible surface; customization guide unchanged").
7. **Sub-step lesson capture (preventative care).** At the close of every phase sub-step — after helpers / methodology / templates / command page / SKILL.md updates land and the verify chain is clean — append any lessons learned, bugs found, or workarounds adopted to the phase's `### Phase N — Lessons learned (running)` subsection. **If the sub-step closed cleanly with no surprises, record that explicitly** ("no lessons; mirrored Step X.Y structure"). Silence is not evidence of cleanliness. Phase sign-off audits that every sub-step has a corresponding entry.

## TDD micro-cycle

Every command sub-step follows this strictly. No exceptions.

```text
1. Write the tests that define the helper's behavior.
2. Run pytest — confirm they fail (RED).
3. Implement the helper. Minimal code to make tests pass.
4. Run pytest — confirm they pass (GREEN).
5. Author the per-command page (commands/<name>.md).
6. Author or update methodology / template artifacts as the sub-step prescribes.
7. Update the owning SKILL.md to surface the shipped behavior (per Per-Phase Convention #4).
8. Run `make verify` — confirm full chain clean (lint, all tests, link checker, skill verifier).
9. Append the sub-step's lesson entry to planning/plan.md (per Per-Phase Convention #7).
10. Update CHANGELOG.md with the sub-step's "Added" entry.
11. Commit.
```

Steps 1–4 are non-negotiable. Implementation without a failing test first is forbidden.

## Helper-mirroring pattern

When authoring a sibling helper that consumes the same workspace shape and parses the same family of ID-prefixed Markdown markers (REQ-NNN, US-NNN, AC-NNN, etc.), **copy the closest sibling's skeleton and adapt the per-dimension checks**. The skeleton is already debugged. Phase 2 has five helpers; four share roughly 70% of their structure. Step 2.3 (`review_user_stories.py`) was 9/9 GREEN on the first run because it mirrored Step 2.2's `review_requirements.py`. New bugs concentrate in the new mechanical checks, which the per-command unit tests target precisely.

## Verify chain

```sh
make verify
```

Runs in order:

1. **`ruff`** lint (max 100 chars per line; no emojis in code).
2. **`pytest`** — full test suite. Current count at Phase 2 close: 172. Each phase has its own sign-off test (`tests/test_phase_N_signoff.py`) that gates the close.
3. **`scripts/verify_skills.py`** — walks `plugins/test-commander/skills/<name>/SKILL.md`, parses frontmatter, classifies each skill as PRESENT / MISSING / MALFORMED / UNEXPECTED. Default phase cap bumps each phase close (Phase 0 → 0, Phase 1 → 1, Phase 2 → 2, etc.). A clean run reports `PRESENT=N MISSING=0 MALFORMED=0 UNEXPECTED=0`.
4. **`scripts/check_links.py`** — verifies every relative Markdown link resolves. Current scope: 107 files.

**Do not push red.** If `make verify` is red, fix the root cause (per parent CLAUDE.md root-cause discipline) before committing.

## Commit and sign-off conventions

**Per-sub-step commits.** Each phase sub-step lands as one commit. Subject is the sub-step name, e.g. `Phase 2, Step 2.4: /tc:review-acceptance-criteria helper, methodology, template, command page`. The body is multi-paragraph and descriptive — it documents the deliverables, the TDD trace (RED → GREEN with any bug-fixes that surfaced), the verify-chain output, and the lessons captured. **Always include the `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>` line** at the end of the commit body — this repo's convention is to attribute Claude's work.

**Plan-only commits.** When the plan changes without code (decision additions, convention codification, lesson backfill, sub-step expansion), use a `plan:` subject prefix: `plan: backfill Phase 2 lessons learned + new Per-Phase Convention for sub-step lesson capture`.

**Use HEREDOC for commit messages** so multi-line formatting survives:

```sh
git commit -m "$(cat <<'EOF'
Phase N, Step N.M: <subject>

<paragraph 1: what shipped>

<paragraph 2: TDD trace and any bugs caught>

<paragraph 3: verify-chain output and counts>

<paragraph 4: lessons captured>

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

**Phase sign-off in six sub-sub-steps** (mirrors `1.8` / `2.9`):

1. Cold-user walkthrough — `make uninstall` → `make install` → fresh tmp consuming project → run the phase's commands in workflow order. Capture to `/tmp/tc-phaseN-walkthrough.log`.
2. Per-step DoD audit — every sub-step's deliverables on disk, every lesson entry present, every test passing.
3. Plan + CHANGELOG closing — collapse `### Phase N` To Do to marker line; populate `## Completed` with the phase's section; flip CHANGELOG heading from `(in progress)` to `(complete YYYY-MM-DD)`.
4. Documentation final pass — status-line drift sweep (6+ locations, in-context editing).
5. **Pre-flight sign-off test (test-first):** `tests/test_phase_N_signoff.py` lands RED before the closing edits, GREEN after. Assert every closing condition: artifacts on disk, test files exist, helpers exist, command pages exist, methodology and templates exist, fixture intact, verifier cap and catalog at this phase, SKILL.md has no deferral wording, CHANGELOG marked complete with date, plan Completed has phase entry, plan To Do collapsed, customization guide carries the shipped schema with worked examples, lessons-learned subsection has an entry per sub-step, pytest count meets the floor.
6. Final DoD eval — `make verify` clean, replay the cold-user walkthrough, commit, push, annotated `phase-N` tag pushed to origin.

**Numeric assertions in sign-off tests must use `>=`, never `==`.** A Phase N sign-off test that asserts `DEFAULT_PHASE_CAP == N` will break when Phase N+1 bumps the cap. The invariant is "Phase N closed by bumping the value to at least N", not "the value is forever N." Phase 2 caught this when Phase 1's sign-off test broke; the lesson is in `planning/plan.md` Phase 2 Lessons learned (Step 2.8 entry).

## Definition of Done (per sub-step)

A sub-step is done when:

1. Code, helpers, methodology, templates, and command pages are written and committed.
2. The TDD micro-cycle was followed (tests red before implementation; tests green after).
3. The owning SKILL.md surfaces the shipped behavior (Per-Phase Convention #4).
4. `make verify` is green (lint, tests, link checker, skill verifier).
5. CHANGELOG.md has a per-sub-step "Added" entry under the current phase's `(in progress)` heading.
6. `planning/plan.md` Phase N Lessons learned subsection has an entry for the sub-step (Per-Phase Convention #7) — "no lessons" counts as a lesson.
7. If a configurable surface shipped: `docs/user-guide/customizing-for-your-project.md` is updated with at least one worked example (Per-Phase Convention #6). Otherwise: the lessons entry records "no new extensible surface".
8. The plan's To Do checkbox for the sub-step is checked.

## What NOT to do

- **Do not write code without a failing test first.** TDD is non-negotiable. If you find yourself implementing before testing, stop and write the test.
- **Do not bake domain-specific vocabulary into shipped defaults.** Per D19, every rubric keyword set, fixture, tag taxonomy, and illustrative example must be universal. If you catch yourself writing `checkout`, `refund`, `PAN`, `PHI`, or any product-specific feature into a shipped artifact, route it to `<workspace>/config.yaml` extensions instead.
- **Do not skip the sub-step lesson entry.** Even "no lessons" must be written explicitly. Silence is not compliance.
- **Do not leave deferral wording in a shipped command's SKILL.md.** Phase 1 shipped with this gap and required a re-tag to fix. The current Per-Phase Convention #4 + the sign-off test prevent recurrence; honor them.
- **Do not assert exact-equality on monotonically-non-decreasing values in sign-off tests.** Use `>=`. Phase N+1's cap bump must not break Phase N's sign-off test.
- **Do not use interactive slash commands** (`/plugin marketplace add`, etc.) for plan steps. Per D17, the canonical, scriptable, environment-independent path is the `claude plugin ...` CLI.
- **Do not overwrite artifacts that downstream phases enrich.** Use skip-not-overwrite for seed files (`test-ideas/<REQ-ID>.md`); byte-deterministic overwrite for pure generated reports (`requirements-review.md`, etc.). Document the chosen mode in the helper's docstring.
- **Do not check `path.is_file()` alone** when consuming an upstream-generated artifact. The workspace template ships placeholders for every artifact slot, so `is_file()` is true from `/tc:init` onward. Check for the *generator's* structural markers (e.g. `## Executive summary`, `_No requirements parsed yet._`) to distinguish "the upstream has run" from "the template stub is still in place." Phase 2 hit this in Steps 2.5 and 2.6.
- **Do not `git add -A` or `git add .`.** Stage specific files. Sensitive files and build artifacts can slip in otherwise.
- **Do not force-push or force-overwrite an annotated tag on origin without explicit user confirmation.** Phase 1 needed a re-tag once; the user explicitly approved that operation.
- **Do not add emojis anywhere.** Code, content, logs, UI, docs — none of it. Per the parent CLAUDE.md.

## When this orientation is wrong

If you follow this file and something is wrong — a convention has drifted, a referenced section moved in the plan, a decision was superseded — **update this file in the same PR that fixes the underlying drift**. Treat this orientation like every other piece of preventative documentation in the project: it is only useful while it matches reality. The discipline mirrors the project's own Sub-step Lesson Capture Convention: write the correction down where the next operator will find it.

## Quick links

- [planning/plan.md](planning/plan.md) — the spec
- [CHANGELOG.md](CHANGELOG.md) — shipping log
- [docs/user-guide/customizing-for-your-project.md](docs/user-guide/customizing-for-your-project.md) — D19's extension model
- [docs/command-reference.md](docs/command-reference.md) — every shipped command, by phase
- [docs/workspace-reference.md](docs/workspace-reference.md) — per-directory ownership inside `.test-commander/`
- [README.md](README.md) — user-facing overview
- Parent project rules: `~/projects/CLAUDE.md` — PDM, no emojis, root-cause, make targets, parent global rules
