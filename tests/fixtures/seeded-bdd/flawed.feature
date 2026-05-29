# This is a deliberately-flawed test asset, not a claim about scope (D19).
# Each scenario below seeds exactly one defect from the universal BDD-review
# rubric, marked with a `# knowledge: <category>` comment so the scaffold test
# and the Step 5.3 review helper can verify rubric coverage.

Feature: Sign-in and session lifecycle (seeded BDD review fixture)

  # knowledge: ambiguous-step
  @area:sign-in @req:REQ-001 @cs:CS-001-003 @smoke
  Scenario: Ambiguous sign-in
    Given the user is on the page
    When the user does something
    Then it works

  # knowledge: missing-tag
  @req:REQ-001 @cs:CS-001-003
  Scenario: Sign-in without an area tag
    Given a registered account
    When the account signs in with valid credentials
    Then the dashboard is shown

  # knowledge: untraceable
  @area:sign-in @smoke
  Scenario: Sign-in with no linkage tag
    Given a registered account
    When the account signs in with valid credentials
    Then the dashboard is shown

  # knowledge: ui-coupled-step
  @area:sign-in @req:REQ-001 @cs:CS-001-003
  Scenario: UI-coupled sign-in
    Given the user navigates to /sign-in
    When the user clicks the "#submit" button
    Then the URL changes to /dashboard

  # knowledge: missing-examples
  @area:sign-in @req:REQ-001 @cs:CS-001-002
  Scenario Outline: Sign-in with various emails
    Given an account with email "<email>"
    When the account signs in
    Then the result is "<result>"

  # knowledge: conjunction-overload
  @area:sign-in @req:REQ-001 @cs:CS-001-001
  Scenario: Overloaded session lifecycle
    Given a registered account
    When the account signs in and creates a workspace and uploads an asset and signs out and the session expires
    Then everything is fine
