# /tc:watch-changes

Detect changes from a pull-request or push diff.

## Inputs

- A unified diff (CLI: `--diff <path>`; in CI, the PR/push diff).
- The initialized Test Commander workspace (`.test-commander/`).

## Outputs

- `<workspace>/.test-commander/continuous/changes.json` — the changed files and
  a count, for the downstream analysis.

## Preconditions

- The workspace exists. Otherwise exit 2.

## Behavior

1. Resolve the workspace.
2. Parse the diff into a deduplicated, ordered list of changed files.
3. Persist the changes record.

Read-only with respect to the application; writes only the changes record.

## Safety

- Reads a diff and writes one workspace record. No network, no execution.

## Implementation

- Command: `plugins/test-commander/scripts/watch_changes.py` (per D18; self-contained).
- Run: `python3 <plugin-root>/scripts/watch_changes.py <project-root> --diff <path>`.

## Definition of Done

- Parses the diff into changed files, persists `changes.json`; uninitialized
  refused (exit 2).
- `tc-continuous-quality/SKILL.md` describes the shipped command.

## See also

- [/tc:impact-analysis](impact-analysis.md)
- [Impact analysis](../methodology/impact-analysis.md)
- [tc-continuous-quality skill](../SKILL.md)
