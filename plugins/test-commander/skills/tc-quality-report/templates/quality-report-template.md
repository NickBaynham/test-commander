# Current Quality Report

- Generated: <ISO-8601 timestamp> (injected clock)

## How to read this report

- **[fact]** - measured directly from a workspace artifact.
- **[interpretation]** - synthesis a human or Claude adds; not a measured value.
- **[review]** - an item that needs human review before release.

## Executive summary [interpretation]

_[fact]_ <N> requirement(s); latest run <RUN-ID> (passed: <p>, failed: <f>, flaky: <k>); <Q> open question(s).

_[interpretation] Claude summarizes overall quality posture from the facts below._

## Coverage [fact]

## Requirements readiness [review]

## Exploratory findings [fact]

## Automated regression status [fact]

## Known risks [fact]

## Known defects [fact]

## Open questions [review]

## Automation health [fact]

## Flaky tests [fact]

## Evidence summary [fact]

## Traceability summary [fact]

## Recommendations [interpretation]

## Release readiness [review]

## Recent changes [fact]

<!--
This is the shape /tc:report writes to quality-report/current-quality-report.md
and snapshots byte-for-byte to quality-report/history/<YYYY-MM-DD-HHmm>.md. Every
[fact] is read from an artifact (never invented); a section with no source reads
"_None recorded._". The report is deterministic under a fixed injected clock.
-->
