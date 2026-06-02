# Lessons Inbox

Newly captured candidate lessons awaiting review. Each block is a `tc-lesson/v1`
record. The `# knowledge: <classification>` comment is the seeded fixture's
expected review bucket (the Phase 5/6 flawed-fixture convention); the real
`/tc:review-lessons` classifier decides the bucket on its own mechanical merits.

---
schema: tc-lesson/v1
id: LESSON-001
source: /tc:learn-from-failures
origin: runs/RUN-20260115-093000/analysis.md:8
category: product-defect-pattern
severity: medium
status: candidate
captured_at: 2026-01-15T09:30:00
summary: Sign-in rejects valid credentials with a generic error
---
# knowledge: accepted

Sign-in returned a generic "Something went wrong" instead of the documented
authentication message when valid credentials were rejected. A recurring
product-defect pattern: add an explicit assertion on the rejection error copy to
the sign-in regression set.

---
schema: tc-lesson/v1
id: LESSON-002
source: /tc:learn
origin: requirements/open-questions.md:5
category: process
severity: low
status: candidate
captured_at: 2026-01-15T09:30:00
summary: Duplicate of an already-accepted process note
---
# knowledge: rejected

Restating an already-accepted note with no new evidence — a duplicate the review
should reject so the guidance corpus does not accrete near-identical entries.

---
schema: tc-lesson/v1
id: LESSON-003
source: /tc:learn-from-exploration
origin: exploration-notes/SESS-20260115-001.md:14
category: anti-pattern
severity: high
status: candidate
captured_at: 2026-01-15T09:30:00
summary: High-severity auth-mismatch may indicate a broader access-control gap
---
# knowledge: needs-human-review

A high-severity auth-mismatch anomaly on a workspace-detail page may indicate a
broader access-control design gap rather than a single defect. High severity
plus an ambiguous scope: route to a human before promoting any guidance.
