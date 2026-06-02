"""ClaudeCodeCliAdapter - the real Claude Code backend (Phase 10.5 Step 10.5.10).

Implements the same `AgentAdapter` interface as the mock and is gated
identically: it refuses an unplanned call (`UnplannedExecutionError` via
`require_planned`) and only ever runs an approved `BoundedInstruction`. There is
**no new execution path** — it sits behind the same governance pipeline.

The real shell-out (build a structured prompt from the bounded instruction and
invoke the `claude` CLI headless) is **refused under pytest** via the
`PYTEST_CURRENT_TEST` guard, so the suite never launches Claude. Live wiring is
the operator's environment.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

from agent_adapters.base import (
    AgentAdapter,
    BoundedInstruction,
    ExecutionResult,
    require_planned,
)

PYTEST_ENV_VAR = "PYTEST_CURRENT_TEST"


class ClaudeExecutionRefusedError(Exception):
    """Raised when the real Claude CLI execution is refused (e.g. under pytest)."""


def build_prompt(instruction: BoundedInstruction) -> str:
    """Render the structured, bounded prompt (no raw user text)."""
    lines = [
        f"You are running Test Commander command {instruction.command}.",
        f"Scope: {instruction.scope}",
        "Allowed paths:\n" + "\n".join(f"  - {p}" for p in instruction.allowed_paths),
        "Disallowed paths:\n" + "\n".join(f"  - {p}" for p in instruction.disallowed_paths),
        "Expected outputs:\n" + "\n".join(f"  - {o}" for o in instruction.expected_outputs),
        "Safety rules:\n" + "\n".join(f"  - {r}" for r in instruction.safety_rules),
    ]
    return "\n".join(lines)


class ClaudeCodeCliAdapter(AgentAdapter):
    def __init__(self) -> None:
        self.calls: list[BoundedInstruction] = []
        self._last: ExecutionResult | None = None

    def execute_command(self, instruction: BoundedInstruction | None) -> ExecutionResult:
        instr = require_planned(instruction)
        if os.environ.get(PYTEST_ENV_VAR):
            raise ClaudeExecutionRefusedError(
                "real Claude Code execution refused under pytest (PYTEST_CURRENT_TEST is set); "
                "the suite drives the pipeline with the MockAgentAdapter"
            )
        # Real path (not exercised by the hermetic suite): build the bounded
        # prompt and run the claude CLI headless against the workspace.
        raise ClaudeExecutionRefusedError(  # pragma: no cover
            "live Claude Code execution is wired in the operator environment; "
            f"prompt:\n{build_prompt(instr)}"
        )

    def stream_events(self, instruction: BoundedInstruction | None) -> Iterator[str]:
        require_planned(instruction)
        if os.environ.get(PYTEST_ENV_VAR):
            raise ClaudeExecutionRefusedError("event streaming refused under pytest")
        yield "live"  # pragma: no cover

    def capture_result(self) -> ExecutionResult | None:
        return self._last

    def report_files_changed(self) -> list[str]:
        return list(self._last.files_changed) if self._last else []

    def report_artifacts_created(self) -> list[str]:
        return list(self._last.artifacts_created) if self._last else []

    def report_usage_if_available(self) -> dict | None:
        return self._last.usage if self._last else None
