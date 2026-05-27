# Seeded-flawed-requirements fixture

A deliberately-generic Markdown corpus that exercises every rubric dimension the Phase 2 commands check. Each entry carries at least one intentional defect, marked with an inline `<!-- defect: <dimension> -->` comment. The Test Commander Phase 2 commands (`/tc:review-requirements`, `/tc:review-user-stories`, `/tc:review-acceptance-criteria`, `/tc:requirements-coverage`, `/tc:requirements-to-tests`) are tested against this fixture: every command suite asserts that the corresponding finding is produced for each seeded defect.

The fixture is a **test asset, not part of the shipped plugin**. Its narrative is intentionally domain-neutral because Test Commander is a generic testing tool — at runtime it works against whatever requirements the consuming project supplies, not against any pre-known product. Defects here use only universal English and software-engineering vocabulary; nothing in this fixture should be read as a claim about a specific product domain (e-commerce, banking, healthcare, etc.). Domain-specific vocabulary enters at runtime through `<workspace>/config.yaml` extensions, not through this fixture.

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
3. Add a defect example in the corresponding fixture file, marked with the inline `<!-- defect: <dimension> -->` comment. Keep the wording domain-neutral: universal English and software-engineering vocabulary only.
4. Add a test case in the relevant command test (`test_review_requirements.py`, etc.) that asserts the command surfaces a finding for the new dimension using the helper's universal-core keyword set.

## Domain-specific defects

Domain vocabulary (PCI: PAN, primary account number; HIPAA: PHI; commerce: refund, gift card; research: investigator, principal) does **not** belong in this fixture. Domain-specific defects are exercised by consuming projects via their own requirements documents and their own `<workspace>/config.yaml` keyword extensions; they are not part of Test Commander's universal contract.
