# `/tc:journal`

Append a timestamped narrative entry to the project journal, or print a chronological summary.

## Inputs

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| Mode | yes | — | `append` or `summarize`. |
| `body` | yes (append) | — | Markdown body for the new entry. Must be non-empty and must not contain a line matching `## YYYY-MM-DDTHH:MM:SSZ`. |
| `--from` | no (summarize) | open-ended | Inclusive start date (`YYYY-MM-DD`). |
| `--to` | no (summarize) | open-ended | Inclusive end date (`YYYY-MM-DD`). |
| `--target` | no | current working directory | Project root. Journal lives at `<target>/.test-commander/journal/`. |

## Outputs

### Append mode

- A new H2 timestamp section appended to `<target>/.test-commander/journal/YYYY-MM-DD.md`.
- Day-file H1 header (`# YYYY-MM-DD`) created if the file is new.
- Stdout: `entry: <ISO timestamp>` and `file: <path>`.
- Exit 0 on success; 2 on invalid input or missing workspace.

### Summarize mode

- Stdout: chronological list of entries within `[--from, --to]` (inclusive), each rendered as its original H2 + body.
- `(no journal entries)` if the journal is empty or the date filter excludes everything.
- Exit 0 in every case.

## Preconditions

- Workspace must exist (`/tc:init` has run) for `append`.
- For `summarize`, a missing workspace or journal directory is reported as "no entries" rather than an error.

## Behavior

### Day-file layout

One file per day at `journal/YYYY-MM-DD.md`. Each file looks like:

```markdown
# 2026-05-26

## 2026-05-26T14:00:00Z

First entry body.

## 2026-05-26T15:30:00Z

Second entry body.
```

### Append flow

1. Validate body: non-empty after strip, no H2 timestamp heading inside.
2. Use timestamp = caller-provided or `datetime.now(UTC)`. Must be timezone-aware.
3. Open `journal/<date>.md` for append.
4. If new, write the day H1 header.
5. Write `## <timestamp>\n\n<body>\n\n`.
6. Print `entry:` and `file:` lines.

### Summarize flow

1. Walk `journal/*.md` (skipping `README.md`).
2. Parse each day file into `Entry(timestamp, body, source_path)` records by splitting on H2 timestamp headings.
3. Filter by `--from` / `--to` (each inclusive; either may be omitted).
4. Sort chronologically.
5. Print each entry's H2 + body, separated by blank lines.

## Safety

- Append writes only inside `<target>/.test-commander/journal/`.
- Summarize is read-only — never modifies any file.
- Rejects empty bodies and bodies that would break day-file parsing.
- Requires timezone-aware timestamps so day-file routing is deterministic.

## Out of scope (Step 1.4)

- AI-generated summarization. The `summarize` mode prints chronological entries verbatim. Synthesized summaries arrive with the learning loop in Phase 8.

## Implementation

Implemented by `plugins/test-commander/scripts/journal.py`. Invoke as:

```sh
python3 plugins/test-commander/scripts/journal.py append "body text"
python3 plugins/test-commander/scripts/journal.py summarize --from 2026-05-01 --to 2026-05-31
```

Both modes accept `--target <path>` to point at a project root other than the current directory.

## Definition of Done

- Append to an empty journal creates the day file with H1 + H2 + body.
- Append to an existing day appends a second H2 + body block; the day H1 appears exactly once.
- Summarize without filters returns every entry in chronological order.
- Summarize with `--from`/`--to` filters to the inclusive date range.
- Summarize on an empty (or missing) journal returns an empty result without error.
- Empty bodies and bodies containing H2 timestamp headings are rejected with `ValueError`.
- Append requires an existing workspace; raises `FileNotFoundError` otherwise.
- Journal files are valid Markdown (renders cleanly in any Markdown viewer).

## See also

- [`/tc:init`](init.md)
- [`/tc:status`](status.md)
- [Phased plan](../../../../../planning/plan.md)
