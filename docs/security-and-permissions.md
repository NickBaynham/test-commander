# Security and Permissions

This document defines the roles, permission levels, approval rules, output-validation policy, and secret-safety rules that the [controlled execution pipeline](controlled-agent-execution.md) enforces.

## Roles

| Role | Default permissions |
| --- | --- |
| Viewer | View reports, view evidence, ask read-only questions |
| Tester | Viewer + upload docs, review requirements, generate test ideas, generate BDD, approved exploration, approved test runs |
| Automation Engineer | Tester + generate Playwright tests (with approval), modify page objects, update fixtures, review automation plans |
| Maintainer | Automation Engineer + approve code-write actions, create PRs, manage project settings |
| Admin | All actions including manage secrets, manage provider credentials, manage sandbox policy, manage users and roles |

Single-user local install defaults the caller to `Admin`. Multi-user deployments require explicit identity-provider integration (deferred past v1; see Open Question Q14).

## Permission levels

Every action the runtime can take is classified into exactly one level. The policy engine enforces the level before the action reaches an agent.

| Level | Description | Examples |
| --- | --- | --- |
| `read-only` | View or query indexed artifacts | View quality report, ask questions, summarize results, show screenshots, explain failures |
| `safe-write` | Produce non-code artifacts in the workspace | Review requirements, generate open questions, create test ideas, update risk register, generate diagrams, update quality report |
| `code-write` | Create or modify executable code | Generate Playwright tests, modify page objects, update fixtures, change test data, refactor automation |
| `execute-tests` | Run automated tests | Smoke, regression, feature, browser exploration |
| `external-network` | Touch external systems | Explore target website, call target APIs, run tests against staging |
| `destructive` | Cannot be undone with `git checkout` | Reset test data, delete artifacts, install dependencies, modify environment config, change GitHub Actions, destroy sandbox |
| `admin` | Govern the governance | Manage secrets, change provider credentials, change sandbox policy, change permission rules |

## Approval rules

| Level | Default approval requirement |
| --- | --- |
| `read-only` | None |
| `safe-write` | Configurable; default "always prompt" (Q13 default) |
| `code-write` | Required |
| `execute-tests` | Required |
| `external-network` | Required |
| `destructive` | Required |
| `admin` | Required + Admin role |

Approval is per-action. Approving once does not pre-approve future actions of the same shape.

## Output validation

After execution, the runtime diffs the workspace and confirms:

- Files changed are inside the plan's declared scope.
- No secret files were modified.
- No unexpected network requests were issued (where measurable).
- Expected outputs were produced.

Allow-lists by level:

- `safe-write` may update `.test-commander/**`, `specs/bdd/**`.
- `code-write` may update `tests/**`, `playwright.config.ts`, and `package.json` only when approved.

Universal deny-list (no command, regardless of level, modifies these without explicit admin approval and a documented reason):

- `.env`, `.env.*`
- `secrets/*`
- Cloud provider credentials
- Production-environment configuration
- Deploy keys

Violations mark the run failed and route to admin review. The audit log records the violation.

## Secret safety

- Frontend users never see provider secrets.
- AI provider keys stay server-side, injected only into runtime jobs that need them.
- Logs and artifacts redact secrets before they are written.
- Environment variables are never dumped into prompts, reports, or chat responses.
- Commands that attempt to print environment variables are flagged by output validation.
- Tokens are scoped to the minimum permission set and kept short-lived where the provider supports it.

## Audit journal

Append-only at `.test-commander/audit/actions.jsonl`. One JSON object per action. Required fields:

```
{
  "id": "uuid",
  "user": "role:identity",
  "timestamp": "ISO-8601",
  "request": "original user request (redacted)",
  "intent": "mapped TC workflow",
  "command": "command as planned",
  "permission_level": "code-write",
  "approval_status": "approved | denied | bypassed | n/a",
  "approver": "identity or null",
  "files_read": ["..."],
  "files_changed": ["..."],
  "artifacts_created": ["..."],
  "tests_run": ["..."],
  "target_urls": ["..."],
  "status": "success | failed | violated_policy",
  "summary": "one-line outcome",
  "evidence": ["paths or links"]
}
```

Individual approval records live alongside at `.test-commander/audit/approvals/<id>.json` so they can be cited from PRs and reports.

## See also

- [Controlled agent execution](controlled-agent-execution.md)
- [Runtime approval flow](runtime-approval-flow.md)
- [Chat command governance](chat-command-governance.md)
