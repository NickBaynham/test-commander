---
schema: tc-lesson/v1
id: LESSON-NNN
source: /tc:learn
origin: <path:line provenance, or "manual">
category: <product-defect-pattern | flaky-pattern | coverage-gap | process | heuristic | anti-pattern>
severity: <low | medium | high>
status: candidate
captured_at: <ISO-8601 timestamp>
summary: <one-line summary; the dedup key with source + origin>
---

<The lesson: the observation and the recommended guidance change. Be specific
and actionable — this is what a human reads when reviewing and, if accepted,
what gets promoted into project guidance.>

<!--
This is the shape every capture command appends to learning/lessons-inbox.md.
The id is allocated monotonically by scanning the inbox; the inbox dedups by
(source, origin, summary); captured_at comes from the injected clock so the
inbox is byte-stable. status moves candidate -> accepted/rejected/
needs-human-review (review) -> promoted (promote --apply).
-->
