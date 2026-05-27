# User journey — sign in and open a workspace

A new account signs in, lands on the dashboard, opens a workspace, and views the assets inside.

## Steps

1. The user navigates to the sign-in page.
2. The user submits an account identifier and a one-time code.
3. The platform validates the code and issues a session.
4. The dashboard loads. The user sees a list of workspaces they own.
5. The user selects a workspace.
6. The platform loads the workspace and lists its assets.
7. The user views the asset list.

## Edge branches

- If the one-time code is expired, the platform returns the user to the sign-in page with an error.
- If the account has no workspaces, the dashboard shows an empty-state prompt to create one.

## Open thread

The journey above describes the happy path and two edge branches. It does not describe what happens when a session times out mid-workspace. That branch is implemented in the code but not in this document.
