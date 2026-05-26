# Chat and Command Governance

The chat interface in the web console (and any future Test Commander UI) routes user requests through the [controlled execution pipeline](controlled-agent-execution.md). This document describes the two front-of-pipeline components: the intent router and the command planner.

## Intent router

Maps a free-form chat message or a button click to a known Test Commander workflow.

### Behavior

- Recognizes known commands and parameter shapes (e.g. "review requirements" -> `/tc:review-requirements`).
- Recognizes feature-area phrases (e.g. "for checkout" -> `--area checkout`).
- Recognizes target hints (e.g. "on staging" -> `--target staging` if configured).
- Defaults unknown intents to read-only Q&A against indexed artifacts.
- Never synthesizes a command that is not in the registered Test Commander surface.
- Never escalates permission level on its own — only the user (via approval) does.

### Examples

| User says | Mapped intent |
| --- | --- |
| "Review these requirements" | `/tc:review-requirements` |
| "Generate BDD for checkout" | `/tc:generate-bdd --area checkout` |
| "Run smoke tests" | `/tc:run --suite smoke` |
| "Why did checkout fail?" | Read-only artifact query |
| "Improve coverage" | Proposes `/tc:coverage-gap-analysis` (not executed) |
| "Delete the evidence folder" | Maps to `destructive`; policy blocks unless explicitly approved |
| "Print my AWS keys" | Read-only Q&A; secret-redaction strips the response |

### Failure modes the router must handle

- Ambiguous intent (multiple plausible commands): present the user with options.
- Intent below the user's role (e.g. Viewer asks for `code-write`): refuse and explain.
- Intent matches but parameters are missing: ask for the missing parameter; do not guess destructively.

## Command planner

Once the router has picked an intent, the planner produces an explicit, displayable plan that the user (or a downstream approver) can read before anything executes.

### Plan fields

- Command to be run.
- Files likely to be read.
- Files likely to be created or changed.
- Permission level required (one of the seven; see [security-and-permissions.md](security-and-permissions.md)).
- Target environment if applicable (URL, sandbox name, "local").
- Expected artifacts (paths under `.test-commander/`).
- Whether approval is required.
- Estimated runtime (where possible).

### Plan rules

- The plan is the source of truth for output validation later. If the plan says only `.test-commander/**` may change, that is what the validator enforces.
- The planner never invents files outside the known workspace + project layout.
- The planner declares **read** intent as well as write intent. Read scope informs the bounded prompt and the diff-checker.

## Proposal cards in the UI

The plan is rendered as a proposal card in the chat UI:

```
Command:
  /tc:automate --feature checkout
This will:
  - read .test-commander/bdd/features/checkout.feature
  - create or modify tests/e2e/checkout.spec.ts
  - create or modify tests/pages/CheckoutPage.ts
  - update .test-commander/traceability/automation-map.md
  - optionally run checkout tests
Permission level:
  code-write + execute-tests
Approve?
```

The user (or approver) clicks Approve, Deny, or Edit. Approve hands off to the [approval flow](runtime-approval-flow.md). Deny records a denial in the audit log. Edit lets the user adjust scope (e.g. uncheck the optional test run) before re-submitting.

## What the chat must not do

- Send the raw user message to the agent.
- Construct commands the registry does not know about.
- Show secret values in suggestions or completions.
- Auto-run anything above `safe-write` without an approval record.

## See also

- [Controlled agent execution](controlled-agent-execution.md)
- [Runtime approval flow](runtime-approval-flow.md)
- [Security and permissions](security-and-permissions.md)
