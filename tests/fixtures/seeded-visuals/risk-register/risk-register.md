# Risk Register

Known and suspected risks, with the area they touch, a severity, and the artifact that surfaced them. Populated across Phase 2 (requirements) and Phase 4 (exploration).

| ID | Area | Severity | Description | Source |
| --- | --- | --- | --- | --- |
| RISK-001 | Authentication | high | Invalid-password handling may reveal whether an account exists. | `requirements/requirements-inventory.md` |
| RISK-002 | Session | medium | Idle-timeout behavior is under-specified and was flaky in exploration. | `exploration-notes/SESS-001.md` |
| RISK-003 | File upload | high | Upload size and type limits are not stated, risking resource exhaustion. | `requirements/open-questions.md` |
| RISK-004 | Dashboard | low | Workspace ordering is unspecified and may confuse returning users. | `requirements/requirements-inventory.md` |
