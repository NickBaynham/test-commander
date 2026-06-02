# /tc:impact-analysis

Map changed files to impacted features and requirements.

## Inputs

- The changed files (from `/tc:watch-changes`'s `changes.json`, or `--diff <path>`).
- `<workspace>/product-knowledge/impact-map.yaml` — the impact map (file-path
  pattern → features + requirements), produced from Phase-3 knowledge and Phase-5
  traceability.

## Outputs

- `<workspace>/.test-commander/continuous/impact.json` and `impact-analysis.md` —
  the impacted features, requirements, and provenance.

## Preconditions

- The workspace exists and the impact map is present. Otherwise exit 2.

## Behavior

1. Resolve the changed files (from `changes.json` or the supplied diff).
2. For each changed file, match it against every impact-map pattern it starts
   with, accumulating the impacted features and requirements with provenance.
3. Write the analysis.

Deterministic — the same diff always yields the same impacted set. Never invents
impact: a file matching no pattern contributes nothing.

## Safety

- Read-only analysis. Reports only what the impact map records; no execution.

## Implementation

- Command: `plugins/test-commander/scripts/impact_analysis.py` (per D18).
- Run: `python3 <plugin-root>/scripts/impact_analysis.py <project-root> [--diff <path>]`.

## Definition of Done

- Maps changed files to impacted features/requirements with provenance,
  deterministically; writes the report; uninitialized/missing-map refused (exit 2).
- `tc-continuous-quality/SKILL.md` describes the shipped command.

## See also

- [/tc:watch-changes](watch-changes.md)
- [/tc:coverage-gap-analysis](coverage-gap-analysis.md)
- [Impact analysis](../methodology/impact-analysis.md)
- [tc-continuous-quality skill](../SKILL.md)
