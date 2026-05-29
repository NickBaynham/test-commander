# /tc:review-automation

Review the generated Playwright specs against a six-category universal rubric,
write a per-spec verdict, and route failures to the open-questions log. The same
engine auto-runs at the end of `/tc:automate`.

## Inputs

- `tests/e2e/*.spec.ts` - the generated specs (the review reads their text; it
  never runs them).
- `<workspace>/traceability/automation-map.md` - to determine whether each spec
  is linked (the `untraceable-spec` check).

## Outputs

- `<workspace>/automation-plan/review-summary.md` - one row per spec with its
  verdict (`pass` or `N finding(s) - categories: ...`).
- `<workspace>/requirements/open-questions.md` - one deduplicated
  `[automation-review]` line per finding.

## Preconditions

- The workspace exists (`/tc:init` has run). Otherwise exit 2.
- At least one spec exists under `tests/e2e/`. Otherwise exit 2 with an error
  directing the user at `/tc:automate`.

## Behavior

1. **Resolve** the workspace and read the automation map (for traceability).
2. **Review** each `tests/e2e/*.spec.ts` against the six categories:
   `inline-test-data`, `hardcoded-wait`, `missing-provenance`, `weak-locator`,
   `untraceable-spec`, `assertion-free` - one finding per category per spec.
3. **Write** the per-spec verdict to `automation-plan/review-summary.md`.
4. **Route** each finding to `requirements/open-questions.md` as a deduplicated
   `[automation-review]` gap signal (per-spec source-id
   `tc-automate/automation-review-<area>`).

Deterministic and idempotent: specs sort by name; re-running routes no
duplicate open-questions lines.

`review_automation()` is the shared implementation `/tc:automate` auto-runs
after generation. Running this command standalone judges the same specs by the
same rules.

## Safety

- Reads `tests/e2e/` and `automation-map.md`; writes only
  `automation-plan/review-summary.md` and `requirements/open-questions.md`.
  Never writes `bdd/` or `product-knowledge/`.
- No network, no browser. Reads spec text only - never invokes `tsc` or
  `npx playwright test`.

## Implementation

- Helper: `plugins/test-commander/scripts/review_automation.py` (per D18).
- Run: `python3 <plugin-root>/scripts/review_automation.py <project-root>`.
- Mirrors `review_bdd.py`: rubric + summary verdict + open-questions
  append/dedup. Exposes `review_automation()`, the same function `/tc:automate`
  calls (suppressible there with `--no-review`).

## Definition of Done

- The rubric detects every category; a clean generated spec passes.
- Findings route to open-questions, deduplicated across re-runs.
- `review_automation()` is shared between the standalone command and the
  `/tc:automate` auto-run; `--no-review` suppresses the auto-run.
- `tc-automate/SKILL.md` describes the shipped behavior.

## See also

- [Automation review methodology](../methodology/automation-review.md) - the six categories, verdict, routing, and judgment layer.
- [Automation review template](../templates/automation-review-template.md) - the summary shape.
- [/tc:automate](automate.md) - generation; auto-runs this review.
- [tc-automate skill](../SKILL.md)
