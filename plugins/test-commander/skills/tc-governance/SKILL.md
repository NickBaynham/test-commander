---
name: tc-governance
description: Controlled agent execution and policy-governed chat for Test Commander. Use when the web console runs a user request through the governance pipeline - intent routing, command planning, permission policy, approval gate, bounded execution, output validation, and the append-only audit log. Owns the policy templates, approval-card templates, bounded-prompt templates, and the audit-log schema. Default deny - nothing above read-only executes without passing the policy engine and, where required, an approval gate, and the agent never sees the raw user prompt.
---

# tc-governance

The governance skill for Test Commander. It makes the web console safe to expose: every user request — chat message, button click, automation — flows through a policy-governed pipeline before it can touch Claude or the workspace. Users drive Test Commander workflows; they never drive raw Claude Code.

The pipeline runtime lives under `runtime/governance/` (the components) and `runtime/agent_adapters/` (the backend abstraction); this skill owns the **templates** (policy, approval card, bounded prompt) and the **audit-log schema**. There are no `/tc:*` commands — the pipeline is invoked by the console (Phase 10) and, later, the API (Phase 11), the sandbox (Phase 12), and continuous mode (Phase 13). They all enter here; there is no direct-execution backdoor.

## The pipeline

```
Frontend request -> Intent router -> Command planner -> Permission policy
  -> Approval gate -> Bounded execution -> Artifact capture -> Output validation
  -> Audit log
```

## Three disciplines

- **Default deny; every gate is a test, not a convention.** Nothing above `read-only` executes without passing the permission policy and (where required) an approval gate. Four canonical security integration tests are the phase's spine: block an unsafe request before the agent; deny a code-write and assert no files change; approve via the mock adapter and assert the diff matches the plan; refuse a no-plan direct adapter call.
- **The agent never sees the raw user prompt; secrets never reach the frontend or the prompt.** Bounded execution wraps a *structured instruction* (command, scope, allowed/disallowed paths and actions, expected outputs) — raw user text never lands in instruction-critical sections. Provider secrets stay server-side and are redacted from logs, artifacts, and prompts.
- **Adapter abstraction so governance is backend-agnostic.** Every backend (`MockAgentAdapter`, `ClaudeCodeCliAdapter`, stubbed `AnthropicApiAdapter`) implements one `AgentAdapter` interface and runs inside the same pipeline.

## Permission levels and roles

Seven levels — `read-only`, `safe-write`, `code-write`, `execute-tests`, `external-network`, `destructive`, `admin` — resolved per role (Viewer → Tester → Automation Engineer → Maintainer → Admin) against `<workspace>/policy/permissions.yaml`. Approval requirements live in `<workspace>/policy/approvals.yaml`. Every action is recorded in the append-only `<workspace>/audit/actions.jsonl`.

## Status

Phase 10.5. All pipeline components are shipped and gated end to end (the four canonical security tests are GREEN):

- Agent adapter abstraction (`AgentAdapter` + mock + stubs) — **shipped (Step 10.5.2).** The `AgentAdapter` interface, the `MockAgentAdapter` (deterministic; refuses unplanned calls via `UnplannedExecutionError`), and the refusing `ClaudeCodeCliAdapter`/`AnthropicApiAdapter` stubs. See [methodology/agent-adapters.md](methodology/agent-adapters.md).
- Permission policy engine (7 levels, role-aware) — **shipped (Step 10.5.3).** Classifies every request into one of the seven levels and resolves it against the role's allowed levels (default deny); overridable via `policy/permissions.yaml`. The pipeline blocks before the agent when denied. See [methodology/permission-policy.md](methodology/permission-policy.md).
- Intent router (NL/button → known workflow) — **shipped (Step 10.5.4).** Maps requests to the closed set of known `/tc:*` workflows or the read-only path; cannot synthesize a command outside the set. See [methodology/intent-and-planning.md](methodology/intent-and-planning.md).
- Command planner (displayable plan) — **shipped (Step 10.5.5).** Produces a deterministic `Plan` (command, level, reads, writes, expected artifacts, target environment, approval-required) the approval gate renders. See [methodology/intent-and-planning.md](methodology/intent-and-planning.md).
- Approval gate (card + record) — **shipped (Step 10.5.6).** Requires approval for the privileged levels (configurable for safe-write via `policy/approvals.yaml`), renders the approval card, and records the decision under `audit/approvals/`. A not-approved privileged action is held — no execution, no change. See [methodology/approval-and-audit.md](methodology/approval-and-audit.md).
- Bounded executor (structured instruction wrapping) — **shipped (Step 10.5.7).** Wraps an approved plan into a `BoundedInstruction` (derived only from the plan, never the raw request) and runs it through the adapter — the only path to execution. See [methodology/agent-adapters.md](methodology/agent-adapters.md).
- Output validation + secret safety — **shipped (Step 10.5.8).** After execution, verifies the diff matches the plan (in-scope writes, no secret file, expected outputs produced) — a violation fails the run. Redacts secret values and flags env-var-print attempts. See [methodology/output-validation.md](methodology/output-validation.md).
- Audit journal — **shipped (Step 10.5.9).** Writes one append-only `audit/actions.jsonl` entry (full field set) per executed action; a no-plan bypass is refused and writes nothing. All four security tests are GREEN. See [methodology/approval-and-audit.md](methodology/approval-and-audit.md).
- `ClaudeCodeCliAdapter` + console wiring — **shipped (Step 10.5.10).** The real Claude adapter implements the same interface, gated identically (refuses unplanned calls; real shell-out refused under pytest). The web console's single `/api/execute` route runs an approved request through the pipeline; no other UI path executes. See [methodology/agent-adapters.md](methodology/agent-adapters.md).

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [tc-web skill](../tc-web/SKILL.md)
