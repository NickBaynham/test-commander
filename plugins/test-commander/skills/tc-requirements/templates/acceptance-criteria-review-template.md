# Acceptance Criteria Review

The structure `/tc:review-acceptance-criteria` generates. The helper writes a file matching this shape to `<workspace>/requirements/acceptance-criteria-review.md` on every run (overwriting any prior content; the file is generated, not hand-edited).

## Executive summary

- Acceptance criteria parsed: **N**
- Parent stories in scope: **M**
- Findings: **N** across **K** dimensions

Findings per dimension:

- `ac-missing-edge-cases`: N
- `ac-missing-negative-cases`: N
- `ac-untestable-predicate`: N
- `ac-ambiguous-data-rule`: N
- `ac-missing-role-context`: N
- `orphan`: N

(Only dimensions with at least one finding appear.)

## Findings grouped by story

One section per parent user story, sorted alphabetically by story ID. ACs whose parent is not in scope appear under `(no parent)` or an orphan-marked story heading.

### US-NNN

#### AC-NNN-NN

_Source: `<filename.md>`_

> Given <precondition>, When <action>, Then <outcome>.

**Findings:**

- `dimension` — trigger detail
- `dimension` — trigger detail

ACs with no findings read:

> _No mechanical findings; AC is ready for review._

Orphan sections carry an inline marker:

> ### US-999  _(orphan — no matching user story)_

## All findings (flat)

A sortable table of every finding, ordered by `(ac-id, dimension, detail)`.

| AC | Dimension | Trigger |
| --- | --- | --- |
| AC-001-01 | `ac-missing-edge-cases` | Given/When/Then body has no edge keyword |
| AC-001-02 | `ac-missing-negative-cases` | Given/When/Then body has no failure keyword |
| ... | ... | ... |

## Traceability

Parsed AC IDs (document order):

`AC-001-01, AC-001-02, ..., AC-NNN-NN`

## Notes for human reviewers

This template is the contract for the **mechanical** output. Claude adds the narrative judgment layer around the helper's findings — proposing concrete edge cases, translating subjective predicates into measurable proxies, pinning down ambiguity words to project-specific rules, and naming roles per the consuming project's `<workspace>/config.yaml` extensions. The mechanical output is deterministic and idempotent; the narrative layer is rendered per session.
