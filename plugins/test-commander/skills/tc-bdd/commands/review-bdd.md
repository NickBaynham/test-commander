# /tc:review-bdd

Review Gherkin feature files against a deterministic six-category universal
rubric. Writes a verdict into each feature's summary and routes failures to
`requirements/open-questions.md` as `[bdd-review]` gap signals. The same
implementation backs the `/tc:generate-bdd` generate-time review sub-mode.

## Inputs

- `<workspace>/bdd/features/*.feature` - the features to review. Required: at
  least one file.
- `<workspace>/config.yaml` - optional `tc-bdd.review.rubric-extensions`
  (extra `vague-words` / `ui-words`).

## Outputs

- `<workspace>/bdd/summaries/<area>.md` - the `- Review verdict:` line is set to
  `pass` or `N finding(s) - categories: ...` (only when a summary exists).
- `<workspace>/requirements/open-questions.md` - one `[bdd-review]` gap signal
  per finding, deduplicated by `(source-id, question)`.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- At least one `.feature` file exists under `bdd/features/`. Otherwise exit 2
  with an error directing the user at `/tc:generate-bdd`.

## Behavior

1. **Resolve** the workspace and discover `bdd/features/*.feature`.
2. **Parse** each feature into scenarios (tags, steps, examples-presence).
3. **Apply** the six-category rubric per scenario (one finding per category at
   most): `ambiguous-step`, `missing-tag`, `untraceable`, `ui-coupled-step`,
   `missing-examples`, `conjunction-overload`. See
   [`methodology/bdd-quality-review.md`](../methodology/bdd-quality-review.md).
4. **Write** the verdict into each feature's summary.
5. **Route** findings to `requirements/open-questions.md` with the per-area
   source-id `tc-bdd/bdd-review-<area>` and the Phase-2 dedup contract.

A clean (generated) feature produces zero findings and a `pass` verdict.
Re-running is idempotent: verdicts are byte-stable and no gap signal is
duplicated.

## Safety

- Reads `bdd/features/`; writes only `bdd/summaries/` verdicts and appends to
  `requirements/open-questions.md` (append-only, deduplicated). No network, no
  browser, fully deterministic.

## Implementation

- Helper: `plugins/test-commander/scripts/review_bdd.py` (per D18). The shared
  `review_features()` entry point is imported and auto-run by
  `generate_bdd.py`.
- Run: `python3 <plugin-root>/scripts/review_bdd.py <project-root>`.
- Mirrors the `_review_session()` rubric pattern from Phase 4's `explore.py` and
  the open-questions append + dedup pattern from Phase 2/3.

## Definition of Done

- Every universal rubric category is detected; a clean feature passes.
- Verdicts written; gap signals routed and deduplicated.
- `review_features()` is the same code path `/tc:generate-bdd` auto-runs.
- `tc-bdd/SKILL.md` describes the shipped behavior with no deferral wording.

## See also

- [BDD quality review methodology](../methodology/bdd-quality-review.md) - the six categories, worked examples, Claude judgment layer.
- [BDD review template](../templates/bdd-review-template.md) - the verdict and gap-signal shapes.
- [generate-bdd command page](generate-bdd.md) - the generator whose output this reviews.
- [tc-bdd skill](../SKILL.md)
- [Seeded flawed feature](../../../../../tests/fixtures/seeded-bdd/flawed.feature) - one defect per category.
