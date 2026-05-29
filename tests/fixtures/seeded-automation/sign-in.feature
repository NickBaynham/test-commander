# Clean, automatable BDD fixture for Phase 6 (tc-automate and siblings).
# This is the shape /tc:generate-bdd emits when its input is clean: every
# scenario carries @automated-candidate plus resolvable @req:/@cs: linkage
# tags, behavior-level steps, and an @area: namespace. It is a generic,
# universal SaaS narrative (sign-in / accounts / workspaces / assets) and
# is not a claim about any real product's scope (Decision D19).

@area:sign-in
Feature: Sign-in and session lifecycle (seeded automation fixture)

  @area:sign-in @req:REQ-001 @cs:CS-001-001 @smoke @automated-candidate
  Scenario: Sign in with valid credentials
    Given a registered account with valid credentials
    When the account signs in
    Then the dashboard is shown

  @area:sign-in @req:REQ-001 @cs:CS-001-002 @regression @automated-candidate
  Scenario: Sign in is rejected with an invalid password
    Given a registered account
    When the account signs in with an incorrect password
    Then sign-in is rejected with an authentication error

  @area:sign-in @req:REQ-001 @cs:CS-001-003 @regression @automated-candidate
  Scenario: Session expires after the idle timeout
    Given an account with an active session
    When the session is idle past the configured timeout
    Then the account is signed out and prompted to sign in again
