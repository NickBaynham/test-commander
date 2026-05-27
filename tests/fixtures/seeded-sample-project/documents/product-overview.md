# Sample Project — Product Overview

A generic SaaS dashboard. Users sign in, manage their account, create workspaces, and upload assets into those workspaces. This document is the system narrative the consuming project would upload to `<workspace>/documents/uploaded/` for Test Commander to learn from.

## What the system does

The platform exposes a small HTTP API. Authenticated users may list the workspaces they own, create new ones, upload assets into a workspace, list the assets in a workspace, and end their session. A separate read-only `Account` resource exposes a user's profile. Administrators retain elevated rights over every workspace.

## Entities

The system models the following core entities. Each is the subject of at least one endpoint and at least one row in the data model.

- **Account** — a registered user. Has an identifier, a display name, and a role (`member` or `admin`).
- **Session** — an authenticated session token. Created by sign-in, destroyed by sign-out.
- **Workspace** — a named container an account owns. Owns a collection of assets.
- **Asset** — a file uploaded into a workspace. Has a name, a size, and a content type.
- **Permission** — the relation between an account and a workspace that grants read, write, or admin access.

The entity name **Telemetry** appears as a property of the dashboard but is never defined here, in the glossary, or in the user journey. <!-- knowledge: undefined-term -->

## Business rules

- A session must be active before any workspace endpoint may be called.
- An asset must be smaller than 10 MB.
- A workspace must have at least one owner at all times.
- An admin may delete any workspace. <!-- knowledge: contradictory-rule -->
- An admin must not delete a workspace they did not create. <!-- knowledge: contradictory-rule -->

The last two rules contradict each other; resolving the contradiction is one of the gap signals the documentation extractor should surface.

## Assumptions

The narrative assumes that every account verifies its email before signing in for the first time, but no document confirms how that verification flow works.
