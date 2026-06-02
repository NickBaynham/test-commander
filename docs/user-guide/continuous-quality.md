# Continuous quality

Continuous quality mode watches your application's changes and keeps test
coverage current — analyzing impact, finding gaps, proposing tests, and (when you
allow it) opening labeled pull requests. It runs through the same governed
pipeline as everything else in Test Commander.

## Quick start

1. **Initialize** the continuous config (autonomy mode + PR label) in
   `.test-commander/continuous/config.yaml`. Start at mode 0 (advisor).
2. **Run the check** on a change:
   ```bash
   python plugins/test-commander/scripts/continuous_quality_check.py . --diff <pr.diff>
   ```
   At mode 0 it produces advice only (impact, gaps, proposals) — no PR.
3. **Review the analysis** under `.test-commander/continuous/`
   (`impact-analysis.md`, `coverage-gap-analysis.md`, `proposals/`).
4. **Raise the mode** when you are ready for the agent to open labeled PRs
   (mode 3+).

## In CI

The workflow `.github/workflows/test-commander-continuous-quality.yml` runs the
check on `pull_request` / `push` / `schedule` / `workflow_dispatch`. Its token is
read-only: the analysis runs automatically, and any generated change arrives as a
gated, labeled PR you review — never a direct push.

## The commands

| Command | What it does |
| --- | --- |
| `/tc:watch-changes` | Detect changed files from a diff |
| `/tc:impact-analysis` | Map changes → impacted features/requirements |
| `/tc:coverage-gap-analysis` | Find impacted features without coverage |
| `/tc:propose-tests` | Propose tests for the gaps |
| `/tc:create-test-pr` | Open a labeled PR (gated by the autonomy mode) |
| `/tc:continuous-quality-check` | Run the whole loop under the mode |

## What you need

- An **impact map** at `product-knowledge/impact-map.yaml` (from Phase-3
  knowledge / Phase-5 traceability): file-path pattern → impacted features.
- A **coverage map** at `traceability/coverage.yaml`: feature → automated?

Both are workspace artifacts your earlier Test Commander phases produce.

## Autonomy

The autonomy mode is a ceiling on what auto-approves — see
[autonomy-levels.md](../autonomy-levels.md) and
[customizing-for-your-project.md](customizing-for-your-project.md). `destructive`
and `admin` never auto-approve; the agent never auto-merges.

## See also

- [Continuous quality agent (architecture)](../continuous-quality-agent.md)
- [Autonomy levels](../autonomy-levels.md)
- [Governed self-improvement](../governed-self-improvement.md)
- [tc-continuous-quality skill](../../plugins/test-commander/skills/tc-continuous-quality/SKILL.md)
