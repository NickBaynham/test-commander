# /tc:coverage-gap-analysis

Find where impacted features lack test coverage.

## Inputs

- The impacted set (from `/tc:impact-analysis`'s `impact.json`, or passed in).
- `<workspace>/traceability/coverage.yaml` — existing coverage (feature →
  automated?), from Phase-5 traceability.

## Outputs

- `<workspace>/.test-commander/continuous/coverage-gaps.json` and
  `coverage-gap-analysis.md` — the gaps (impacted but not covered) with
  provenance, and the covered impacted features.

## Preconditions

- The workspace exists and the coverage map is present. Otherwise exit 2.

## Behavior

1. Load the coverage map and the impacted features.
2. For each impacted feature: a feature that is not automated, or has no coverage
   record at all, is a **gap** (with its provenance); an automated feature is
   covered.
3. Write the analysis.

Read-only and deterministic. **Never invents coverage** — a feature with no
record is a gap, not assumed covered.

## Safety

- Read-only analysis. Reports only what the coverage map records; no execution.

## Implementation

- Command: `plugins/test-commander/scripts/coverage_gap_analysis.py` (per D18).
- Run: `python3 <plugin-root>/scripts/coverage_gap_analysis.py <project-root>`.

## Definition of Done

- Surfaces impacted-but-uncovered features with provenance, deterministically;
  never invents coverage; uninitialized/missing-map refused (exit 2).
- `tc-continuous-quality/SKILL.md` describes the shipped command.

## See also

- [/tc:impact-analysis](impact-analysis.md)
- [tc-continuous-quality skill](../SKILL.md)
