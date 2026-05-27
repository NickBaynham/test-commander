# Requirements Review

The structure `/tc:review-requirements` generates. The helper writes a file matching this shape to `<workspace>/requirements/requirements-review.md` on every run (overwriting any prior content; the file is generated, not hand-edited).

## Executive summary

- Requirements parsed: **N**
- Findings: **N** across **M** dimensions
- Open questions: **N**

Findings per dimension:

- `clarity`: N
- `testability`: N
- ... (only dimensions with at least one finding appear)

## Findings

A flat table of every finding, sorted by `(req-id, dimension, trigger)`.

| Requirement | Dimension | Trigger |
| --- | --- | --- |
| REQ-001 | `clarity` | vague-marketing buzzword(s): leverage, robust, seamless |
| REQ-002 | `testability` | vague predicate(s) without numeric threshold: user-friendly |
| ... | ... | ... |

## Per-requirement detail

One section per parsed requirement, in document order. Each section shows the requirement's body verbatim and every dimension it triggered.

### REQ-NNN

_Source: `<filename.md>`_

> Verbatim requirement body, line-wrapped as blockquote.

**Findings:**

- `dimension` — trigger detail
- `dimension` — trigger detail

If a requirement has no mechanical findings, the section reads:

> _No mechanical findings. Review with judgment._

## Open questions

Auto-generated questions that need human resolution. Format: `[REQ-NNN] question text`.

The same questions also land in `<workspace>/requirements/open-questions.md` (appended, deduplicated). They are emitted by:

- **Dependencies (broken reference).** `"<source-REQ> references <target-REQ> which does not exist"`.
- **Consistency (mutual exclusion).** `"<REQ-A> and <REQ-B> assert mutually-exclusive constraints over [<shared subjects>] — which is authoritative?"`.

## Traceability

Parsed requirement IDs (document order):

`REQ-001, REQ-002, ..., REQ-NNN`

## Notes for human reviewers

This template is the contract for the **mechanical** output. Claude is expected to add a narrative judgment layer around the helper's findings when summarizing for a human reviewer (severity ranking, product-context explanations, gaps the keyword check could miss). The mechanical output is deterministic and idempotent; the narrative layer is rendered per session.
