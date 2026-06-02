# Continuous quality agent

Continuous quality mode is Test Commander's final capability: it watches
application changes, maps them to impacted features, finds where coverage is
missing, proposes new tests, and — when the autonomy mode allows — opens a
clearly-labeled pull request. It runs the **watch → analyze → propose → PR** loop
on top of the existing skills, through the same Phase-10.5 pipeline.

## The loop

```
watch-changes  ->  impact-analysis  ->  coverage-gap-analysis  ->  propose-tests  ->  create-test-pr
   (a diff)        (impacted set)       (gaps, read-only)         (proposals)        (gated, labeled)
```

`/tc:continuous-quality-check` runs the whole loop under the configured autonomy
mode: the read-only analysis always runs; the PR step is gated.

## The six commands

| Command | What it does | Class |
| --- | --- | --- |
| `/tc:watch-changes` | Parse a PR/push diff into changed files | read-only |
| `/tc:impact-analysis` | Map changed files → impacted features/requirements | read-only |
| `/tc:coverage-gap-analysis` | Find impacted features without coverage | read-only |
| `/tc:propose-tests` | Propose BDD/automation for the gaps | safe-write (proposals) |
| `/tc:create-test-pr` | Open a clearly-labeled PR for a gap | gated (mode 3+) |
| `/tc:continuous-quality-check` | Run the whole loop under the autonomy mode | orchestrator |

## Reuse, don't rebuild

Continuous mode adds the loop, not parallel machinery: impacted-test runs reuse
`tc-run`'s execution and failure triage; proposed tests reuse the Phase-5 (BDD)
and Phase-6 (automation) generators as proposals; lessons feed `tc-learning`. The
PR's underlying work routes through the same `governance.pipeline.handle_request`
the console uses.

## Determinism and honesty

The analysis is deterministic and read-only — the same diff always yields the
same impacted set and gaps, with provenance. It **never invents** impact or
coverage: a changed file matching no impact-map pattern contributes nothing, and
an impacted feature with no coverage record is reported as a gap, never assumed
covered.

## See also

- [Autonomy levels](autonomy-levels.md)
- [Governed self-improvement](governed-self-improvement.md)
- [Continuous quality user guide](user-guide/continuous-quality.md)
- [Security and permissions](security-and-permissions.md)
