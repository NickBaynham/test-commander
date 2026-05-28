---
id: CH-001
mission: Discover whether the sign-in and workspace-asset journey behaves correctly for an authenticated member account, including edge cases around expired sessions and large asset uploads.
target: Sign-in flow plus workspace-detail asset upload (POST /workspaces/{id}/assets).
time-box: 60min
risk-areas:
  - auth-required endpoints accepting unauthenticated requests
  - asset uploads exceeding the 10 MB limit
  - session expiration mid-workspace
  - workspace access controls (member vs admin)
acceptance-criteria:
  - Sign-in completes with a valid session token returned in the response body
  - Workspace list endpoint returns only workspaces the authenticated account owns
  - Asset upload succeeds for files under 10 MB and produces a resolvable asset ID
  - Asset upload rejects files over 10 MB with a clear error
  - Session expiration during workspace navigation routes the user back to /sign-in
created_at: 2026-05-28T10:00:00Z
phase_3_sources:
  - product-knowledge/entities.md
  - product-knowledge/user-journeys.md
  - requirements/open-questions.md
---

# CH-001 — Sign-in and Workspace Asset Upload Charter

> Test asset, not a claim about scope. Per the D19 fixture-discipline lesson from Phase 2 Step 2.1, this charter ships with the seeded sample-project fixture and exercises only universal SaaS vocabulary (sign-in, account, workspace, asset). Consuming projects supply their own charters against their actual application via `/tc:create-charter`.

## Mission

Discover whether the sign-in and workspace-asset journey behaves correctly for an authenticated member account, including edge cases around expired sessions and large asset uploads.

## Target Area

Sign-in flow plus workspace-detail asset upload (`POST /workspaces/{id}/assets`). The target is the generic SaaS dashboard described in [`target-app.md`](target-app.md) — Account / Session / Workspace / Asset / Permission. Exploration enters at `/sign-in`, lands on `/dashboard`, navigates into a workspace, attempts an asset upload, and terminates the session.

## Time-Box

60 minutes. Within this time-box, the exploration should produce at least one observation per acceptance criterion and capture screenshots at every significant page transition (sign-in submit, dashboard load, workspace open, asset upload result).

## Risk Areas

- **auth-required endpoints accepting unauthenticated requests** — Phase 3's `/tc:learn-from-api` flagged GET /workspaces as auth-required (Authorization header present in every recorded session); the exploration should confirm the endpoint rejects requests without the header.
- **asset uploads exceeding the 10 MB limit** — Phase 3's `/tc:learn-from-docs` extracted the business rule "An asset must be smaller than 10 MB" from product-overview.md; the exploration should attempt a large upload and confirm the rejection path.
- **session expiration mid-workspace** — Phase 3's `documentation-model.md` captured an open thread ("does not describe what happens when a session times out mid-workspace"); the exploration should simulate session expiration and observe the recovery flow.
- **workspace access controls (member vs admin)** — Phase 3's `/tc:learn-from-docs` surfaced the contradictory-rule gap on admin workspace deletion; the exploration should exercise both roles to test the access boundary.

## Acceptance Criteria

1. Sign-in completes with a valid session token returned in the response body.
2. Workspace list endpoint returns only workspaces the authenticated account owns.
3. Asset upload succeeds for files under 10 MB and produces a resolvable asset ID.
4. Asset upload rejects files over 10 MB with a clear error message.
5. Session expiration during workspace navigation routes the user back to `/sign-in` rather than producing a broken state.

## Out of Scope

- Admin-level workspace creation or destruction (separate charter scope).
- Cross-workspace permission propagation (deferred to a later charter once `tc-knowledge.code.endpoint-decorator-patterns` extension lands).
- Visual styling / theming (`/tc:learn-from-tests` flagged the Playwright spec files as `unsupported-test-runner` in v1; UI assertion gates wait on Phase 6).

## Phase 3 Sources

- `<workspace>/product-knowledge/entities.md` — Account, Session, Workspace, Asset entity definitions and cross-source provenance.
- `<workspace>/product-knowledge/user-journeys.md` — "Sign in and open a workspace" journey from product-overview.md.
- `<workspace>/requirements/open-questions.md` — the `[undefined-term]` (Telemetry), `[contradictory-rule]` (admin workspace deletion), `[unspecified-endpoint]` (GET /accounts/me), and `[mismatched-status]` (DELETE /sessions/{id} returning 500) gaps that motivate several risk areas above.

## See also

- [`target-app.md`](target-app.md) — the seeded target application narrative.
- [`recorded-session.json`](recorded-session.json) — the playback of a hypothetical exploration session against this charter.
- [Phase 4 plan section](../../../planning/plan.md) — the full Phase 4 design decisions and per-sub-step deliverables.
