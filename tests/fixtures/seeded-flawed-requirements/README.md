# Seeded-flawed-requirements fixture

A small Markdown corpus that carries intentional defects, one per rubric dimension. The Test Commander Phase 2 commands (`/tc:review-requirements`, `/tc:review-user-stories`, `/tc:review-acceptance-criteria`, `/tc:requirements-coverage`, `/tc:requirements-to-tests`) are tested against this fixture: every command suite asserts that the corresponding finding is produced for each seeded defect.

The fixture is the rubric's contract. Adding a new rubric dimension means adding a seeded defect here first, then turning the corresponding command test green.

## Files

- `requirements.md` — REQ-NNN requirements, one defect per top-level rubric dimension.
- `user-stories.md` — user stories in role-action-benefit shape, one defect per INVEST letter.
- `acceptance-criteria.md` — Given/When/Then acceptance criteria, one defect per AC-rubric dimension.

## Defect-marking convention

Every seeded defect is marked with an inline HTML comment immediately preceding (or on the same line as) the offending content:

```
<!-- defect: <dimension> -->
```

Where `<dimension>` is a lowercase, kebab-case dimension key. The fixture loader parses these comments to drive coverage assertions.

### Top-level rubric dimensions (used in `requirements.md`)

`clarity`, `testability`, `completeness`, `consistency`, `atomicity`, `measurability`, `ac-quality`, `edge-cases`, `negative-cases`, `data-rules`, `roles-permissions`, `nfrs`, `dependencies`, `ambiguity`, `risk`, `automation-suitability`.

### INVEST letters (used in `user-stories.md`)

`invest-independent`, `invest-negotiable`, `invest-valuable`, `invest-estimable`, `invest-small`, `invest-testable`.

### AC-rubric dimensions (used in `acceptance-criteria.md`)

`ac-missing-edge-cases`, `ac-missing-negative-cases`, `ac-untestable-predicate`, `ac-ambiguous-data-rule`, `ac-missing-role-context`.

## Adding a new seeded defect

1. Pick a dimension key (kebab-case, lowercase).
2. Add the dimension to the appropriate list in this README and in `tests/test_tc_requirements_scaffold.py`.
3. Add a defect example in the corresponding fixture file, marked with the inline `<!-- defect: <dimension> -->` comment.
4. Add a test case in the relevant command test (`test_review_requirements.py`, etc.) that asserts the command surfaces a finding for the new dimension.

## Narrative

The fixture documents requirements for a fictional online bookstore. The narrative is intentionally light — the goal is to exercise the rubric, not to design a real product.
