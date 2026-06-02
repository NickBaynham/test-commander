# Impact analysis methodology

Continuous mode watches a change (a PR or push diff), maps it to impacted
features and requirements, and finds where coverage is missing — all
deterministically and read-only.

## Watch → impact

`/tc:watch-changes` parses a diff into a list of changed files.
`/tc:impact-analysis` maps those files to impacted features and requirements via
the project's **impact map** — produced from the Phase-3 knowledge and Phase-5
traceability and stored at `<workspace>/product-knowledge/impact-map.yaml`. Each
entry maps a file-path pattern to the features and requirements it affects. The
mapping is deterministic: the same diff always yields the same impacted set, with
provenance (which pattern matched).

## Impact → coverage gap

`/tc:coverage-gap-analysis` takes the impacted set and checks it against existing
coverage (the test map / automation plan). A feature that is impacted but not
covered is a **gap**, surfaced with provenance. The analysis never invents
coverage — it only reports what the workspace records.

## Gap → proposal → PR

`/tc:propose-tests` proposes new BDD/automation for the gaps (reusing the
Phase-5/6 generators as proposals). `/tc:create-test-pr` opens a clearly-labeled
pull request — but only through the Phase-10.5 pipeline and only when the
configured autonomy mode allows it.

(Behavior shipped across Steps 13.2–13.4; this methodology page is the scaffold spec.)
