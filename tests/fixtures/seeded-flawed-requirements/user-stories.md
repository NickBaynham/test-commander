# User Stories (intentionally flawed)

These user stories describe behavior for the deliberately-generic system. Each story carries at least one INVEST violation, marked with an inline `<!-- defect: invest-<letter> -->` comment. See `README.md` for the defect-marking convention.

## Stories

<!-- defect: invest-independent -->
US-001: As a returning user, I want to view my dashboard, So that I can see my recent activity. (Depends on US-002 "Sign in" being completed and released first; cannot be developed or shipped independently.)

<!-- defect: invest-negotiable -->
US-002: As a user, I want a red "Submit" button at coordinates (240, 480) on the form page, measuring exactly 120px wide by 36px tall, with Helvetica 14pt bold text, So that I can complete the action. No deviation from these specifications is acceptable.

<!-- defect: invest-valuable -->
US-003: As a backend developer, I want to refactor the authentication module into smaller files, So that the code is cleaner. (No direct user-facing or business-facing value articulated; this is engineering work disguised as a user story.)

<!-- defect: invest-estimable -->
US-004: As a user, I want better search, So that I find what I need.

<!-- defect: invest-small -->
US-005: As a user, I want to sign up, sign in, configure my profile, manage notifications, view reports, schedule jobs, export data, manage integrations, configure API keys, audit my history, and contact support, So that I can fully use the system. (Far too large for a single iteration; should be split.)

<!-- defect: invest-testable -->
US-006: As a user, I want the system to feel intuitive and delightful, So that I enjoy using it.
