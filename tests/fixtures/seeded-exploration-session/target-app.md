# Target — Sample SaaS Dashboard

> Test asset, not a claim about scope. The same deliberately-generic SaaS-dashboard narrative the Phase 3 sample-project fixture uses. Domain-specific exploration targets are exercised by consuming projects via their own recorded sessions and `tc-explore:` config extensions.

The seeded target is a generic SaaS dashboard. Users sign in, manage their account, list and create workspaces, upload assets into workspaces, and view their account profile. The application surface mirrors the Phase 3 sample-project's `src/app/` tree so Phase 4 exploration of this target reads cleanly against Phase 3's product-knowledge artifacts (entities, journeys, business rules).

## Entities

| Entity | Notes |
| --- | --- |
| Account | Registered user; has `id`, `display_name`, `role` ∈ {`member`, `admin`}. |
| Session | Short-lived authenticated context bound to a single Account. |
| Workspace | Named container owned by an Account; holds Assets. |
| Asset | Binary file uploaded into a Workspace. |
| Permission | Relation between Account and Workspace; one of `read` / `write` / `admin`. |

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/sessions` | Sign in. |
| DELETE | `/sessions/{id}` | Sign out. |
| GET | `/accounts/{id}` | Read account profile. |
| GET | `/accounts/me` | Read the currently-authenticated account (undocumented in the spec; see Phase 3 `[unspecified-endpoint]` gap). |
| GET | `/workspaces` | List workspaces the caller owns. |
| POST | `/workspaces/{id}/assets` | Upload an asset into a workspace. |
| GET | `/workspaces/{id}/assets` | List assets in a workspace. |

## Pages

| Path | Purpose |
| --- | --- |
| `/sign-in` | Sign-in form (account_id + one-time code). |
| `/dashboard` | Workspaces list + recent assets summary. |
| `/workspaces/{id}` | Workspace detail with asset list and upload control. |
| `/account/profile` | Read-only account profile. |

## Known seeded behavior

The recorded session in [`recorded-session.json`](recorded-session.json) drives an exploration of the sign-in → dashboard → workspace-detail → asset-upload journey with at least one seeded anomaly per universal category. The seeded session is the contract Step 4.3's `/tc:explore` helper consumes in tests; the per-anomaly entries describe what real Playwright MCP would have produced during a live exploration.

The target itself is not implemented in the fixture (Phase 4 does not stand up a runtime target app); the fixture's `recorded-session.json` is the playback of a hypothetical session against this target. Consuming projects supply their own recorded sessions against their actual application.

## Cross-phase consistency

This target's entity model is identical to the Phase 3 sample-project's `src/app/models/` tree (Account, Workspace). The Phase 3 product-knowledge artifacts (`<workspace>/product-knowledge/entities.md`, `user-journeys.md`, `system-model.md`) produced against the Phase 3 fixture are valid Phase 4 inputs — the 4.7 integration smoke seeds the workspace with the Phase 3 sample-project, runs the five Phase 3 helpers to populate product-knowledge, then runs the four Phase 4 helpers against the same workspace. The two fixtures share their narrative deliberately so cross-phase tests compose without translation.
