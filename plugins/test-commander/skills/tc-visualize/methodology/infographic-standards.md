# Infographic standards

How `/tc:generate-infographic` turns the quality report into a shareable
one-screen summary without inventing a single number.

## Two artifacts, no binary

`/tc:generate-infographic` emits two Markdown files under
`<workspace>/visuals/infographic/`:

- **`quality-brief.md`** — a human/Claude-facing narrative: headline stats and
  suggested panels (following `frontend-design:frontend-design` layout
  patterns). This is what a designer or `/tc:render-visuals` reads to lay out the
  visual.
- **`quality-spec.md`** — a structured data block (a fenced `yaml` block) of the
  measured facts, in a fixed key order, so the infographic's data is diffable.

Neither is an image. Richer rendering is `/tc:render-visuals`' job.

## Measured facts only

Every value comes from a `[fact]` line in
`quality-report/current-quality-report.md`:

| Key | Source line in the report |
| --- | --- |
| `requirements` | "Requirements inventoried: N" |
| `latest_run` | the `RUN-…` id |
| `passed` / `failed` / `flaky` | "passed: N, failed: N, flaky: N" |
| `automated` / `automatable` | "N of M scenario(s) automated" |
| `risks` | "N risk(s) in the register" |
| `open_questions` | "N open question(s)" |
| `evidence` | "N evidence artifact(s)" |

A metric the report does not state is **omitted** — never defaulted, estimated,
or invented. Both files end with a `> Sources:` footer naming the report.

## Determinism

The spec lists keys in a fixed order and the brief renders sections in a fixed
order, so the same report yields byte-identical output on every run.

## See also

- [Visual documentation methodology](visual-documentation.md)
- [tc-visualize skill](../SKILL.md)
