# Controlled Agent Execution

Test Commander runs every user request through a policy-governed pipeline before any agent (Claude Code, Anthropic API, future provider) can act. Users drive Test Commander workflows; they never drive raw Claude Code.

This document describes the pipeline. It is the contract that the web console, the API, the MCP server, the sandbox, and the continuous quality agent all conform to.

## Pipeline

```
Frontend chat / request
  -> Intent router
  -> Command planner
  -> Permission policy
  -> Approval gate
  -> Bounded agent execution
  -> Artifact capture
  -> Diff validation
  -> Journal / audit log
```

No execution path bypasses this pipeline. There is no "direct" mode, no admin shortcut, no developer override that skips the gate.

## Components

### Intent router

Maps a user request (chat or button) to a known Test Commander workflow. Unknown intents default to read-only Q&A; the router cannot synthesize a new command surface on its own.

Examples:

- "Review these requirements" -> `/tc:review-requirements`
- "Generate BDD for sign-in" -> `/tc:generate-bdd --area sign-in`
- "Run smoke tests" -> `/tc:run --suite smoke`
- "Why did sign-in fail?" -> read-only artifact query
- "Improve coverage" -> proposes `/tc:coverage-gap-analysis`, not raw Claude execution

### Command planner

Produces an explicit, displayable plan before execution. The plan includes:

- Command or workflow to run.
- Files likely to be read.
- Files likely to be created or changed.
- Permission level required.
- Target website or environment if applicable.
- Expected artifacts.
- Whether human approval is required.

### Permission policy engine

Classifies actions into seven levels: `read-only`, `safe-write`, `code-write`, `execute-tests`, `external-network`, `destructive`, `admin`. See [security-and-permissions.md](security-and-permissions.md) for the level rubric and role mappings.

### Approval gate

Required for `code-write`, `execute-tests`, `external-network`, `destructive`, and `admin`. Configurable for `safe-write`. The UI surfaces an approval card; the pipeline records the approval (or denial) in the audit log. See [runtime-approval-flow.md](runtime-approval-flow.md).

### Bounded agent execution

The agent receives a structured instruction, not the user's raw prompt. The instruction wraps the user's intent in a bounded scope: allowed and disallowed paths, allowed and disallowed actions, expected outputs, safety rules, and journal requirements.

See [agent-adapters.md](agent-adapters.md) for adapter interface and implementations.

### Artifact capture

The runtime records what the agent produced: files written, artifacts created, tests run, evidence collected.

### Diff validation

After execution the runtime diffs the workspace and verifies:

- Files changed match the plan's declared scope.
- No secret files touched.
- No unexpected network access (where measurable).
- Expected outputs were produced.

Violations mark the run failed and route it to admin review.

### Journal / audit log

Append-only `actions.jsonl` plus per-approval records. Every action is captured. See [security-and-permissions.md](security-and-permissions.md) for the entry schema and secret-redaction rules.

## Non-negotiables

- The frontend never sends a raw prompt to the agent.
- The frontend never receives raw secrets.
- Continuous agent mode does not bypass approvals; the configured autonomy level only changes which permission levels auto-approve.
- The same pipeline runs in local, sandbox, and CI deployments.

## See also

- [Security and permissions](security-and-permissions.md)
- [Chat command governance](chat-command-governance.md)
- [Runtime approval flow](runtime-approval-flow.md)
- [Agent adapters](agent-adapters.md)
- [Architecture](architecture.md)
