# Seeded learning fixture

This directory is the shared fixture for Phase 8 (`tc-learning`). It carries the
upstream artifacts the capture commands read plus a pre-seeded lessons inbox for
the review and promote commands. It is a **deliberately generic, universal SaaS
narrative** (sign-in / sessions / workspaces), reusing the entity vocabulary of
the earlier seeded fixtures so the Phase 8 integration smoke composes without
translation. Nothing here is a claim about any real product's scope (per
Decision D19).

## Files

| File | Role |
| --- | --- |
| `analysis.md` | A Phase-7 `/tc:analyze-results` triage (one `product-defect`, one `flaky` row). The input to `/tc:learn-from-failures`. |
| `SESS-20260115-001.md` | An exploration note with seeded anomalies and a coverage gap. The input to `/tc:learn-from-exploration`. |
| `open-questions.md` | A resolved-feedback excerpt. The input to `/tc:learn-from-feedback`. |
| `lessons-inbox.md` | A pre-seeded inbox with one candidate per review classification. The input to `/tc:review-lessons`. |
| `README.md` | This file. |

## The `tc-lesson/v1` schema

Every captured lesson is a Markdown block opened by `tc-lesson/v1` YAML
frontmatter:

- `id` — a stable `LESSON-NNN` identifier (monotonic, allocated by scanning the inbox).
- `source` — the command that captured it (`/tc:learn`, `/tc:learn-from-failures`, ...).
- `origin` — `path:line` provenance pointing at the committed artifact it came from.
- `category` — one of the universal taxonomy: `product-defect-pattern`, `flaky-pattern`, `coverage-gap`, `process`, `heuristic`, `anti-pattern`.
- `severity` — `low` / `medium` / `high`.
- `status` — `candidate` (in the inbox), then `accepted` / `rejected` / `needs-human-review` (after review), then `promoted` (after `/tc:promote-lessons --apply`).
- `captured_at` — an ISO timestamp from the injected clock.
- `summary` — a one-line summary used for the `(source, origin, summary)` dedup key.

## The governance flow

```
capture  ->  /tc:review-lessons  ->  /tc:promote-lessons --apply
(inbox)      accepted / rejected /     promoted-guidance.md
             needs-human-review        (only under the human gate)
```

Test Commander never silently rewrites its own methodology or any third-party
skill (Open Question Q6). `/tc:promote-lessons` proposes by default and writes
into the workspace `learning/` tree only with explicit `--apply` — every applied
promotion is a visible `git diff`.

## Classification markers

Each seeded inbox candidate carries a `# knowledge: <classification>` comment
naming its expected review bucket (`accepted` / `rejected` / `needs-human-review`).
The marker is fixture documentation; the real `/tc:review-lessons` classifier
decides the bucket on its own mechanical merits (the Phase 5/6 flawed-fixture
discipline).
