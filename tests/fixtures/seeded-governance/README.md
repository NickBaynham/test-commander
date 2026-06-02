# seeded-governance fixture

Inputs for the Phase 10.5 governance pipeline tests: a role-to-permission set
(`permissions.yaml`) and a sample request set (`requests.yaml`) that maps
universal SaaS phrasings to intents and permission levels, including at least
one **unsafe** request the policy engine must block.

Universal vocabulary only (Decision D19): sign-in, dashboard, workspaces, file
upload, evidence. A consuming project's real roles and policy replace these at
runtime via `<workspace>/policy/permissions.yaml` and `approvals.yaml`.
