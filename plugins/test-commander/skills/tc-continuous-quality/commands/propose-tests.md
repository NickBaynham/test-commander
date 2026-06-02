# /tc:propose-tests

Propose new tests for the coverage gaps.

## Inputs

- The coverage gaps (from `/tc:coverage-gap-analysis`'s `coverage-gaps.json`, or
  passed in).

## Outputs

- `<workspace>/.test-commander/continuous/proposals/<feature>.md` — one proposal
  per gap (a BDD scenario + an automation proposal), reusing the Phase-5/6
  generators as proposals.

## Preconditions

- The workspace exists. Otherwise exit 2.

## Behavior

1. Resolve the gaps (from `coverage-gaps.json` or the supplied list).
2. Write one proposal per gap feature.

Read-only/safe-write: it *proposes*; it never opens a PR or runs anything.

## Safety

- Proposals only — no execution, no PR. Opening a PR is the gated, separate
  `/tc:create-test-pr` step.

## Implementation

- Command: `plugins/test-commander/scripts/propose_tests.py` (per D18).
- Run: `python3 <plugin-root>/scripts/propose_tests.py <project-root>`.

## Definition of Done

- Writes one proposal per gap; uninitialized refused (exit 2).
- `tc-continuous-quality/SKILL.md` describes the shipped command.

## See also

- [/tc:coverage-gap-analysis](coverage-gap-analysis.md)
- [/tc:create-test-pr](create-test-pr.md)
- [tc-continuous-quality skill](../SKILL.md)
