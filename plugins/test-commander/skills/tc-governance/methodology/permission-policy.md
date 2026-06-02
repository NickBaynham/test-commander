# Permission policy

Every request is classified into one of seven escalating levels and resolved
against the acting role's allowed levels. **Default deny**: a level absent from a
role's list — or an unknown role — is denied.

## The seven levels

`read-only` → `safe-write` → `code-write` → `execute-tests` → `external-network`
→ `destructive` → `admin`.

| Level | Examples |
| --- | --- |
| read-only | view the quality report, ask questions, summarize results |
| safe-write | review requirements, generate BDD, test ideas, diagrams, update the quality report |
| code-write | generate Playwright tests, modify page objects, fixtures, refactor automation |
| execute-tests | run smoke / regression / feature tests, run exploration |
| external-network | explore the target site, call target APIs, run against staging |
| destructive | reset test data, delete artifacts, install deps, change environment |
| admin | manage secrets, provider credentials, sandbox policy, permission rules |

## Classification

`classify(request)` keys on **action-anchored** phrases (verbs, not bare nouns),
most-privileged first, so a destructive verb wins over an incidental "review" and
a read ("show me the quality report") is never mistaken for a write. Unknown
requests default to `read-only`.

## Roles and overrides

The five default roles (Viewer → Tester → Automation Engineer → Maintainer →
Admin) map to allowed levels in `policy.DEFAULT_ROLE_PERMISSIONS`. A deployment
overrides them in `<workspace>/policy/permissions.yaml` (role → list of levels);
`allows(role, level, project_root)` reads the override when present, else the
defaults. `decide(request, role, project_root)` returns a `PolicyDecision`
(level, allowed, reason) — the pipeline blocks before the agent when `allowed`
is false.

## See also

- [Agent adapters](agent-adapters.md)
- [tc-governance skill](../SKILL.md)
