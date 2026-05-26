# Agent Adapters

Test Commander does not bind itself to any single agent backend. The runtime invokes agents through an adapter interface so we can swap backends, mock them in tests, or add future providers without touching the controlled-execution pipeline.

## Adapter interface

The base interface lives at `runtime/agent_adapters/base.py`. Concrete adapters live alongside.

```python
class AgentAdapter:
    def execute_command(self, instruction: BoundedInstruction) -> ExecutionHandle: ...
    def stream_events(self, handle: ExecutionHandle) -> Iterator[AgentEvent]: ...
    def capture_result(self, handle: ExecutionHandle) -> AgentResult: ...
    def report_files_changed(self, handle: ExecutionHandle) -> list[Path]: ...
    def report_artifacts_created(self, handle: ExecutionHandle) -> list[Path]: ...
    def report_usage_if_available(self, handle: ExecutionHandle) -> UsageReport | None: ...
```

Key types (sketched; finalized in Phase 10.5):

- `BoundedInstruction` — the structured input the runtime built: scope, allowed paths, disallowed paths, expected outputs, journal requirements.
- `ExecutionHandle` — an opaque token the runtime uses to poll, stream, and reconcile.
- `AgentEvent` — one frame of streamed progress (status, partial output, tool call summary).
- `AgentResult` — terminal state plus a manifest of what the agent did.
- `UsageReport` — optional token/cost counters where the backend reports them.

## Concrete adapters

| Adapter | File | Phase | Notes |
| --- | --- | --- | --- |
| `MockAgentAdapter` | `runtime/agent_adapters/mock_agent.py` | 10.5 | Scripted responses; drives the test suite. Required for CI. |
| `ClaudeCodeCliAdapter` | `runtime/agent_adapters/claude_code_cli.py` | 10.5 | Shells out to local Claude Code. Single-user, Pattern A. |
| `AnthropicApiAdapter` | `runtime/agent_adapters/anthropic_api.py` | 10.5 stub, 14+ full | Uses the Anthropic API via the Agent SDK. Stub in 10.5; full implementation defers to Pattern C (Decision D15). |
| Future provider adapters | `runtime/agent_adapters/<provider>.py` | TBD | Same interface; gated by the same pipeline. |

## What an adapter is responsible for

- Receiving a `BoundedInstruction` and starting execution.
- Streaming progress events back to the runtime so the UI can show live logs.
- Returning a terminal `AgentResult` with a manifest of files read, files changed, and artifacts produced.
- Surfacing usage information where the backend exposes it.

## What an adapter is not responsible for

- Building the bounded instruction. That is the runtime's job (planner + bounded executor).
- Approval decisions. That is the gate's job.
- Diff validation. That is the validator's job.
- Audit logging. That is the journal's job.

An adapter is a thin shim. The governance lives outside.

## Testing

`MockAgentAdapter` is required to land before either of the live adapters. The integration tests for Phase 10.5 (see plan.md) drive the entire pipeline against the mock so the pipeline itself can be verified without making API calls or shelling out.

## Credentials

Adapters never read provider secrets directly from disk. The runtime injects credentials into the adapter at construction time, scoped to the job. See [security-and-permissions.md](security-and-permissions.md) for the secret-safety rules.

## See also

- [Controlled agent execution](controlled-agent-execution.md)
- [Security and permissions](security-and-permissions.md)
- [Architecture](architecture.md)
