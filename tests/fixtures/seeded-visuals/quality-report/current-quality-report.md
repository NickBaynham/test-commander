# Current Quality Report

- Generated: 2026-01-15T09:30:00 (injected clock)

## How to read this report

- **[fact]** - measured directly from a workspace artifact.
- **[interpretation]** - synthesis a human or Claude adds; not a measured value.
- **[review]** - an item that needs human review before release.

## Executive summary [interpretation]

_[fact]_ 3 requirement(s); latest run RUN-20260115-093000 (passed: 1, failed: 1, flaky: 1); 1 open question(s).

_[interpretation] Claude summarizes overall quality posture from the facts below._

## Coverage [fact]

Requirements inventoried: 3. See `traceability/requirements-map.md`.

## Requirements readiness [review]

3 requirement(s) parsed; 1 open question(s) outstanding.

## Exploratory findings [fact]

1 session(s) recorded.

## Automated regression status [fact]

Latest run: RUN-20260115-093000 - passed: 1, failed: 1, flaky: 1.

| requirement | candidate | scenario |
| --- | --- | --- |
| REQ-001 | CS-001-001 | Sign in with valid credentials | (passed)
| REQ-001 | CS-001-002 | Sign in is rejected with an invalid password | (failed)
| REQ-001 | CS-001-003 | Expired session routes the holder back to sign-in | (flaky)

## Known risks [fact]

4 risk(s) in the register.

## Known defects [fact]

| requirement | candidate | scenario |
| --- | --- | --- |
| REQ-001 | CS-001-002 | Sign in is rejected with an invalid password |

## Open questions [review]

1 open question(s) outstanding.

## Automation health [fact]

1 of 4 scenario(s) automated.

## Flaky tests [fact]

1 flaky result in the latest run.

## Evidence summary [fact]

3 evidence artifact(s) indexed.

## Traceability summary [fact]

See `traceability/test-map.md`.

## Recommendations [interpretation]

_[interpretation] Claude proposes next actions from the facts above._

## Release readiness [review]

_[review] Not release-ready: 1 failed scenario in the latest run._

## Recent changes [fact]

Latest run RUN-20260115-093000.
