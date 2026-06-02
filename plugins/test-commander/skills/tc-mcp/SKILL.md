---
name: tc-mcp
description: Runtime API and MCP server for Test Commander. Use when another tool or agent drives Test Commander over HTTP (the expanded Runtime API under apps/api) or over the Model Context Protocol (the schema-first MCP server under apps/mcp). Both are alternative front-ends to the Phase-10.5 governance pipeline - every route and tool above read-only enters intent routing, planning, permission policy, the approval gate, output validation, and the audit log. There is no direct-execution backdoor; the seven permission levels are enforced server-side.
---

# tc-mcp

The integration skill for Test Commander. It exposes the workspace to other tools and agents two ways:

- The **Runtime API** (`apps/api/`) — the Phase-10 read-only console API expanded with governed-execution routes.
- The **MCP server** (`apps/mcp/`) — a lightweight, schema-first Model Context Protocol server whose tools an MCP client (Claude, an IDE, another agent) can call.

Both are **alternative front-ends to the same governance layer** introduced in Phase 10.5. They cannot bypass intent routing, command planning, permission policy, approvals, output validation, or audit. Every route and every tool that does anything above `read-only` is routed through `governance.pipeline.handle_request` server-side; there is no "direct execution" backdoor. This is the headline discipline of the phase, asserted by tests.

## Two disciplines

- **No bypass — the pipeline is the only path.** Every API route and MCP tool above `read-only` enters the Phase-10.5 controls server-side. A route or tool cannot execute without a plan and (where required) an approval, exactly as the console cannot. A contract test asserts this for every mutating surface.
- **Schema-first tools.** Every MCP tool ships an explicit JSON schema for its arguments (per the `anthropic-skills:skill-creator` conventions). Round-trip tests exercise each tool through a sample in-process client, and a tool above `read-only` is gated by the same seven-level policy.

## Permission levels

The seven escalating levels — `read-only`, `safe-write`, `code-write`, `execute-tests`, `external-network`, `destructive`, `admin` — are enforced server-side on both front-ends, resolved per role against `<workspace>/policy/permissions.yaml`. A destructive route or tool is refused without an admin-level approval; a bypass attempt fails. See the `tc-governance` skill for the pipeline itself.

## Status

Phase 11 (Step 11.1 — scaffold). The skill, the `apps/mcp/` server package, the expanded `apps/api/` route skeleton, and the seeded-mcp fixture are in place; the governed behavior lands across 11.2–11.4:

- Runtime API expansion (read + proposal + governed-execution routes, every mutating route through the pipeline) — behavior arrives in Step 11.2.
- MCP server + schema-first tool definitions (each tool dispatching into the pipeline) — behavior arrives in Step 11.3.
- Server-side enforcement of the seven permission levels across API + MCP, with per-level unit tests and destructive-route security tests — behavior arrives in Step 11.4.

See [methodology/runtime-api.md](methodology/runtime-api.md) and [methodology/mcp-tools.md](methodology/mcp-tools.md).

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [tc-governance skill](../tc-governance/SKILL.md)
- [tc-web skill](../tc-web/SKILL.md)
