"""ClaudeCodeCliAdapter - stub until Step 10.5.10.

Implemented in 10.5.10 behind the *same* governed pipeline (no new execution
path). Until then every method refuses cleanly so nothing can run through it by
accident.
"""

from __future__ import annotations

from collections.abc import Iterator

from agent_adapters.base import AgentAdapter, BoundedInstruction, ExecutionResult

_NOT_WIRED = "ClaudeCodeCliAdapter is not wired until Phase 10.5 Step 10.5.10"


class ClaudeCodeCliAdapter(AgentAdapter):
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
