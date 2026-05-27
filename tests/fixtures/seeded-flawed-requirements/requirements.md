# Requirements (intentionally flawed)

These requirements describe a fictional, deliberately-generic software system. Each entry below carries at least one intentional defect, marked with an inline `<!-- defect: <dimension> -->` comment. The narrative is domain-neutral on purpose — Test Commander is a generic testing tool. See `README.md` for the defect-marking convention.

## Functional requirements

<!-- defect: clarity -->
REQ-001: The system shall provide a robust and seamless user experience leveraging modern best-of-breed paradigms.

<!-- defect: testability -->
REQ-002: The system shall be user-friendly.

<!-- defect: completeness -->
REQ-003: The user shall be able to log in.

<!-- defect: consistency -->
REQ-004: Anonymous users may access the API without authentication.

<!-- defect: consistency -->
REQ-005: All API access requires an authenticated user account.

<!-- defect: atomicity -->
REQ-006: The system shall allow users to register an account, configure preferences, view reports, schedule jobs, and export data.

<!-- defect: measurability -->
REQ-007: The search shall return results quickly.

<!-- defect: ac-quality -->
REQ-008: The notification engine shall surface relevant updates for each user. See acceptance criteria below (acceptance criteria deliberately omitted to exercise the rubric).

<!-- defect: edge-cases -->
REQ-009: When a user submits a form, the system shall process the input and confirm acceptance.

<!-- defect: negative-cases -->
REQ-010: Users can apply filters to the report view to narrow the results.

<!-- defect: data-rules -->
REQ-011: User passwords are stored by the system.

<!-- defect: roles-permissions -->
REQ-012: Users can delete completed records.

<!-- defect: nfrs -->
REQ-013: The system shall be available for use.

<!-- defect: dependencies -->
REQ-014: The confirmation email is sent only after REQ-099 (record finalization) completes successfully. REQ-099 is referenced but does not exist in this document.

<!-- defect: ambiguity -->
REQ-015: The user session shall persist for a reasonable time.

<!-- defect: risk -->
REQ-016: The system shall store authentication credentials in plain text in the database to simplify password recovery.

<!-- defect: automation-suitability -->
REQ-017: The visual theme of every page shall match the design style guide and feel inviting to users. Marked as a candidate for automated regression checks.
