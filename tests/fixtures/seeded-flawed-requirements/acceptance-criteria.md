# Acceptance Criteria (intentionally flawed)

These acceptance criteria describe expected behavior for selected stories of the deliberately-generic system. Each AC carries at least one defect, marked with an inline `<!-- defect: ac-<dimension> -->` comment. See `README.md` for the defect-marking convention.

## US-001: Dashboard

<!-- defect: ac-missing-edge-cases -->
AC-001-01: Given a user with at least one record in their view, When they click "Open" and confirm the prompt, Then the record is shown and a confirmation banner appears. (Happy path only — no coverage of expired records, locked records, or stale-data edge cases.)

<!-- defect: ac-missing-negative-cases -->
AC-001-02: Given a logged-in user at the form page, When they submit the form, Then the request is processed successfully. (No negative case: what happens when validation fails, the request is rejected by the server, or the network drops mid-submit?)

## US-002: Submit button

<!-- defect: ac-untestable-predicate -->
AC-002-01: Given the user is on the home page, When they scroll the page, Then the page should feel responsive and snappy.

## US-003: Refactor authentication (engineering story)

<!-- defect: ac-ambiguous-data-rule -->
AC-003-01: Given the user enters their email address during sign-up, When they submit the form, Then the system processes the email appropriately and stores it as needed. (What format is required, what storage rule applies, what happens for duplicate addresses?)

## US-004: Delete records (role unspecified)

<!-- defect: ac-missing-role-context -->
AC-004-01: Given an active session, When the delete button is clicked on a completed record, Then the record is removed. (Which role is permitted to click the delete button — end user, operator, admin? Not specified.)
