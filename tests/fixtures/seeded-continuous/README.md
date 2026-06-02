# seeded-continuous fixture

Sample inputs the Phase-13 continuous-quality commands are exercised against.

- `pr-diff.txt` — a unified diff of a sample pull request, touching a couple of
  source files (a sign-in change and a search change).
- `impact-map.yaml` — the project's impact map (produced from Phase-3 knowledge
  and Phase-5 traceability): file-path pattern → impacted features + requirements.
- `coverage.yaml` — existing coverage (feature → automated?), so the gap analysis
  has a known gap (an impacted feature with no automated coverage).

Universal vocabulary only (Decision D19). Used by the watch/impact tests (13.2),
the coverage-gap tests (13.3), the propose/PR tests (13.4), and the integration
test (13.8).
