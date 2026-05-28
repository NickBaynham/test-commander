# Exploration-review template

The exploration-review sub-mode auto-runs at the end of every `/tc:explore` session (unless `--no-review` is set). When the review fires gap signals, they route to `<workspace>/requirements/open-questions.md` with the `[exploration-review]` prefix.

## Gap-signal entry shape

Each gap appended to `open-questions.md`:

```text
- [tc-explore/explore-review] [exploration-review] <gap description>.
```

The two `[]`-bracketed segments:

- `[tc-explore/explore-review]` — the **source-id** for the Phase-2 dedup contract. Constant across all `/tc:explore` runs.
- `[exploration-review]` — the **kind** prefix established in Phase 3 (every gap signal carries a `[<kind>]` prefix so the open-questions ledger groups cleanly by phase).

## Gap kinds shipped in v1

| Kind | When it fires | Worked example |
| --- | --- | --- |
| `missing-evidence` | Anomaly carries `screenshot_id: null` AND no `screenshot` event exists within ±3s of the anomaly timestamp | The seeded fixture's anomaly at `2026-05-28T10:00:48.100Z` reports an undocumented `last_login_at` response field with no nearby screenshot. |
| `charter-coverage-shortfall` | One or more acceptance criteria from the charter are marked `unobserved` after the full session. (Criteria marked `partial` do NOT trigger this gap.) | A charter that declares an AC mentioning `/admin` endpoints when the session never touched any `/admin` URL. |

## Dedup contract

The append-only ledger in `open-questions.md` deduplicates by `(source-id, question-text)` per the Phase 2 contract. Re-running `/tc:explore` against the same recording produces zero new lines in `open-questions.md` because every gap signal's `(tc-explore/explore-review, [<kind>] <description>.)` key matches an existing entry.

## `--no-review` flag

When `/tc:explore` is invoked with `--no-review`, the review sub-mode is skipped entirely:

- No `[exploration-review]` open-question appends.
- The exploration note still renders the Charter Coverage matrix and the Anomalies summary, but the "Review findings" section at the bottom is omitted.

`--no-review` is the escape hatch for advanced users who chain commands manually (e.g., custom review pipelines, or replaying a session purely to regenerate the note).

## See also

- [Session-based-test-management methodology](../methodology/session-based-test-management.md) — the deterministic rubric the review sub-mode runs.
- [Per-command page: /tc:explore](../commands/explore.md) — full command reference including the `--no-review` flag.
