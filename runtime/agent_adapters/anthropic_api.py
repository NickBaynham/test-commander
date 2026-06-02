"""AnthropicApiAdapter - stub (remains stubbed in Phase 10.5).

The Anthropic API backend (Pattern C, deferred past v1) is stubbed so the
interface is complete; every method refuses cleanly. When implemented it runs
behind the same governed pipeline as every other backend.
"""

from __future__ import annotations

from collections.abc import Iterator

from agent_adapters.base import AgentAdapter, BoundedInstruction, ExecutionResult

_NOT_WIRED = "AnthropicApiAdapter is not wired in v1 (Pattern C, deferred past v1)"


class AnthropicApiAdapter(AgentAdapter):
    def execute_command(self, instruction: BoundedInstruction | None) -> ExecutionResult:
        raise NotImplementedError(_NOT_WIRED)

    def stream_events(self, instruction: BoundedInstruction | None) -> Iterator[str]:
        raise NotImplementedError(_NOT_WIRED)

    def capture_result(self) -> ExecutionResult | None:
        raise NotImplementedError(_NOT_WIRED)

    def report_files_changed(self) -> list[str]:
        raise NotImplementedError(_NOT_WIRED)

    def report_artifacts_created(self) -> list[str]:
        raise NotImplementedError(_NOT_WIRED)

    def report_usage_if_available(self) -> dict | None:
        raise NotImplementedError(_NOT_WIRED)
