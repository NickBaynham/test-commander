# /tc:generate-infographic

Aggregate the quality report's headline facts into a shareable infographic brief
and spec — measured facts only, never a binary.

## Inputs

- The initialized Test Commander workspace (`.test-commander/`).
- Source: `quality-report/current-quality-report.md`.
- CLI: `<project-root>` (defaults to the current directory).

## Outputs

- `<workspace>/visuals/infographic/quality-brief.md` — a narrative + suggested
  panels (following `frontend-design:frontend-design` patterns).
- `<workspace>/visuals/infographic/quality-spec.md` — a structured `yaml` data
  block of the measured facts.

Both carry a `> Sources:` footer naming the report.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- The quality report is populated. A missing or stub report is refused (exit 2)
  pointing at `/tc:report`.

## Behavior

1. Resolve the workspace and read the quality report (refusing a stub).
2. Extract the measured headline facts (requirements, pass/fail/flaky, automation
   coverage, risks, open questions, evidence) — only those the report states.
3. Render the brief and the spec, each citing the report, and write both under
   `visuals/infographic/`.

Deterministic: a fixed key/section order makes both files byte-stable. A metric
the report does not state is omitted, never invented.

## Safety

- Writes only under `visuals/infographic/`. Reads the report; never modifies it.
- No network, no browser. No binary is produced; rendering is `/tc:render-visuals`' job.

## Implementation

- Helper: `plugins/test-commander/scripts/generate_infographic.py` (per D18). Reuses
  the shared engine in `visualize.py` (workspace resolution, the stub-refusing
  source reader, the error types).
- Run: `python3 <plugin-root>/scripts/generate_infographic.py <project-root>`.

## Definition of Done

- Brief + spec generated from real facts; cited; byte-stable; an absent metric is
  not invented; uninitialized and no-report refused (exit 2).
- `tc-visualize/SKILL.md` describes the shipped command.

## See also

- [Infographic standards](../methodology/infographic-standards.md)
- [Infographic brief template](../templates/infographic-brief-template.md)
- [Infographic spec template](../templates/infographic-spec-template.md)
- [tc-visualize skill](../SKILL.md)
