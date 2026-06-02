---
name: tc-continuous-quality
description: Continuous quality agent mode for Test Commander. Use when the user runs /tc:watch-changes, /tc:impact-analysis, /tc:coverage-gap-analysis, /tc:propose-tests, /tc:create-test-pr, or /tc:continuous-quality-check, or wants Test Commander to monitor application changes (a PR or push diff), map them to impacted features and requirements, surface coverage gaps, and propose new tests - opening a clearly-labeled pull request only when the configured autonomy level allows it. Continuous mode runs through the same Phase-10.5 pipeline as the console; the autonomy level (0-4) is a ceiling on what auto-approves, and nothing above it executes without explicit human approval. Autonomy is a ceiling, not a license.
---

# tc-continuous-quality

The continuous-quality skill for Test Commander — the final capability. It watches code, requirements, and pipelines, maps changes to impacted features, finds coverage gaps, and proposes new tests, running the *watch → analyze → propose → PR* loop on top of the existing skills. It owns the six `/tc:*` commands and the five autonomy-mode gates.

Each command is a self-contained Python helper bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec.

## Two disciplines

- **Autonomy is a ceiling, not a license.** The five modes (0 read-only-advisor → 4 governed-autonomy) map to which permission levels are *auto-approved* in the Phase-10.5 pipeline. Mode boundaries are enforced: mode 0 cannot open a pull request; a PR opened by mode 3 is clearly labeled; nothing above the configured mode executes without explicit human approval. Continuous mode must not bypass approvals.
- **Reuse, don't rebuild.** Impacted-test runs reuse `tc-run`'s execution and failure triage; proposed tests reuse the Phase-5 (BDD) and Phase-6 (automation) generators *as proposals*; lessons feed `tc-learning`. The phase adds the watch → analyze → propose → PR loop, not parallel machinery.

## Autonomy modes

| Mode | Name | Auto-approves up to | Can open PRs |
| --- | --- | --- | --- |
| 0 | read-only-advisor | nothing (read-only only) | no |
| 1 | assisted-testing | safe-write | no |
| 2 | approved-execution | execute-tests | no |
| 3 | pull-request-automation | code-write | yes (labeled) |
| 4 | governed-autonomy | external-network | yes (labeled) |

No mode ever auto-approves `destructive` or `admin`; those always require explicit human approval. The mode is configured in `<workspace>/continuous/config.yaml`.

## Status

Phase 13 (Step 13.4). Change detection, impact analysis, coverage-gap analysis, the proposals, and the gated PR are shipped; the orchestrator + CI land in 13.5–13.6:

- `/tc:watch-changes` + `/tc:impact-analysis` — **shipped (Step 13.2).** `/tc:watch-changes` parses a PR/push diff into changed files (`continuous/changes.json`); `/tc:impact-analysis` maps them to impacted features and requirements via `product-knowledge/impact-map.yaml` (Phase-3/5 derived), deterministically and with provenance, never inventing impact. Both are self-contained helpers sharing `cq_support.py`. See [commands/watch-changes.md](commands/watch-changes.md) and [commands/impact-analysis.md](commands/impact-analysis.md).
- `/tc:coverage-gap-analysis` — **shipped (Step 13.3).** Checks the impacted set against `traceability/coverage.yaml`: an impacted feature that is not automated, or has no coverage record, is a gap surfaced with provenance. Read-only, deterministic, never invents coverage. See [commands/coverage-gap-analysis.md](commands/coverage-gap-analysis.md).
- `/tc:propose-tests` + `/tc:create-test-pr` — **shipped (Step 13.4).** `/tc:propose-tests` writes one proposal per gap (a BDD scenario + an automation proposal; safe-write, never opens a PR). `/tc:create-test-pr` opens a clearly-labeled PR through the Phase-10.5 pipeline, gated by the autonomy mode: a below-threshold mode (0–2) cannot open a PR; mode 3+ runs the code-write generation through the pipeline (auto-approved by the autonomy gate, recorded in the audit log). The gate primitives `auto_approves`/`can_open_pr` live in `continuous/autonomy.py`. See [commands/propose-tests.md](commands/propose-tests.md) and [commands/create-test-pr.md](commands/create-test-pr.md).
- `/tc:continuous-quality-check` + the five autonomy-mode gates (the orchestrator) — behavior arrives in Step 13.5.
- The continuous-quality CI workflow — behavior arrives in Step 13.6.

See [methodology/autonomy-modes.md](methodology/autonomy-modes.md) and [methodology/impact-analysis.md](methodology/impact-analysis.md).

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [tc-governance skill](../tc-governance/SKILL.md)
- [tc-run skill](../tc-run/SKILL.md)
- [tc-learning skill](../tc-learning/SKILL.md)
