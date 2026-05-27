# User Story Review

The structure `/tc:review-user-stories` generates. The helper writes a file matching this shape to `<workspace>/requirements/user-story-review.md` on every run (overwriting any prior content; the file is generated, not hand-edited).

## Executive summary

- Stories parsed: **N**
- Findings: **N** across **M** dimensions
- Readiness: ready=N, needs-refinement=N, blocked=N

Findings per dimension:

- `invest-independent`: N
- `invest-negotiable`: N
- `invest-valuable`: N
- `invest-estimable`: N
- `invest-small`: N
- `invest-testable`: N
- `role-action-benefit`: N
- `needs-acceptance-criteria`: N

(Only dimensions with at least one finding appear.)

## Findings

A flat table of every finding, sorted by `(story-id, dimension, trigger)`.

| Story | Dimension | Trigger |
| --- | --- | --- |
| US-001 | `invest-independent` | explicit dependency clause: 'Depends on US-002' |
| US-002 | `invest-negotiable` | over-specified signal(s): UI coordinates, pixel dimensions, 'no deviation' clause |
| ... | ... | ... |

## Per-story detail

One section per parsed story, in document order. Each section shows the story's body verbatim, every dimension it triggered, and the readiness verdict.

### US-NNN — verdict: `<ready | needs-refinement | blocked>`

_Source: `<filename.md>`_

> As a <role>, I want <action>, So that <benefit>.

**Findings:**

- `dimension` — trigger detail
- `dimension` — trigger detail

If a story has no findings the section reads:

> _No mechanical findings; story is ready for the next stage._

## Readiness verdicts

| Verdict | Trigger |
| --- | --- |
| `ready` | No mechanical findings at all |
| `needs-refinement` | One or two findings, or only `needs-acceptance-criteria` |
| `blocked` | Three+ INVEST findings, or any `role-action-benefit` shape violation |

See [`methodology/user-story-readiness.md`](../methodology/user-story-readiness.md) for the verdict logic and per-dimension definitions.

## Traceability

Parsed story IDs (document order):

`US-001, US-002, ..., US-NNN`

## Notes for human reviewers

This template is the contract for the **mechanical** output. Claude adds the narrative judgment layer around the helper's findings: translating "subjective-experience words" into measurable proxies, proposing splits for stories flagged `invest-small`, and so on. The mechanical output is deterministic and idempotent; the narrative layer is rendered per session.
