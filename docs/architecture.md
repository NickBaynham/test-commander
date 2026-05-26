# Architecture

Test Commander has three runtime roles, three deployment patterns, and one non-negotiable governance pipeline. Everything else is detail.

## Three runtime roles

| Role | What it does | Where it can run |
| --- | --- | --- |
| Orchestrator | Reads the workspace, generates BDD, decides what to automate, drafts the quality report | Claude — desktop Claude Code or Anthropic API |
| Test runtime | Executes Playwright tests, runs Postman collections, collects evidence | Node.js + browsers, locally or containerized |
| Viewer | Renders workspace artifacts as a team-accessible dashboard | FastAPI + Next.js + Postgres |

The orchestrator is always Claude. The viewer and test runtime are owned in this repo. Docker hosts the viewer and test runtime; Docker never hosts the orchestrator.

## Three deployment patterns

- **Pattern A — Local-first (MVP default).** Orchestrator is the user's local Claude Code. Docker hosts auxiliary services on the same machine. Workspace files travel with the consuming project's git.
- **Pattern B — Headless Claude in CI (Phase 13 opt-in).** GitHub Actions runs Claude Code with an Anthropic API token as a secret. Single-tenant.
- **Pattern C — Anthropic API via Agent SDK (deferred past v1).** Backend invokes the API directly via the Agent SDK. Multi-tenant SaaS. Major rearchitecture.

See `planning/plan.md` (Decision D15) for the canonical statement.

## Three layers

1. **The plugin.** A Claude Code plugin at `plugins/test-commander/` containing the skills that orchestrate every phase of work. Each skill is independently loadable and owned in-repo.
2. **The workspace.** A `.test-commander/` directory inside each consuming project. Every quality artifact lives here and is committed to git.
3. **The runtime.** A Python and TypeScript runtime that arrives lazily: Playwright in Phase 6, web/API in Phase 10, controlled-execution pipeline in Phase 10.5, MCP server in Phase 11.

The repo is also a Claude Code marketplace, declared by `.claude-plugin/marketplace.json` at the root. `make install` registers it and installs the plugin.

## Controlled execution pipeline (Phase 10.5)

Every user request — chat, button, API call, MCP tool invocation, CI trigger — flows through the same pipeline before any agent acts:

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

There is no bypass. The web console (Phase 10), the API and MCP server (Phase 11), the sandbox (Phase 12), and the continuous quality agent (Phase 13) all conform.

See [controlled-agent-execution.md](controlled-agent-execution.md) for the full description.

## Agent adapter abstraction

The orchestrator is reached through `AgentAdapter` implementations in `runtime/agent_adapters/`. The MVP ships:

- `MockAgentAdapter` — drives the integration tests.
- `ClaudeCodeCliAdapter` — local Claude Code, Pattern A.
- `AnthropicApiAdapter` — stub in Phase 10.5; full implementation defers with Pattern C.

See [agent-adapters.md](agent-adapters.md).

## Cross-references

- [Controlled agent execution](controlled-agent-execution.md)
- [Security and permissions](security-and-permissions.md)
- [Chat command governance](chat-command-governance.md)
- [Runtime approval flow](runtime-approval-flow.md)
- [Agent adapters](agent-adapters.md)
- [Roadmap](roadmap.md)
- [Phased plan](../planning/plan.md)
