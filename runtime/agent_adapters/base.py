"""The AgentAdapter interface and its data shapes (Phase 10.5 Step 10.5.2).

Every backend (mock, Claude Code CLI, Anthropic API) implements `AgentAdapter`
and runs inside the same governed pipeline. The adapter receives a
`BoundedInstruction` — a structured instruction built by the executor from an
approved plan — never a raw user prompt. Calling an adapter without an approved
bounded instruction is refused (`UnplannedExecutionError`): there is no
direct-execution backdoor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path


class UnplannedExecutionError(Exception):
    """Raised when an adapter is called without an approved bounded instruction."""


@dataclass(frozen=True)
class BoundedInstruction:
    """A structured instruction the executor builds from an approved plan.

    Raw user text never appears in the instruction-critical fields (command,
    scope, paths, actions, outputs). `approved` must be True for an adapter to
    run it.
    """

    command: str
    scope: str
    project_root: Path
    allowed_paths: tuple[str, ...] = ()
    disallowed_paths: tuple[str, ...] = ()
    allowed_actions: tuple[str, ...] = ()
    disallowed_actions: tuple[str, ...] = ()
    expected_outputs: tuple[str, ...] = ()
    safety_rules: tuple[str, ...] = ()
    journal_required: bool = True
    approved: bool = False


@dataclass
class ExecutionResult:
    status: str  # "succeeded" | "failed"
    files_changed: list[str] = field(default_factory=list)
    artifacts_created: list[str] = field(default_factory=list)
    usage: dict | None = None
    summary: str = ""
    events: list[str] = field(default_factory=list)


def require_planned(instruction: BoundedInstruction | None) -> BoundedInstruction:
    """Refuse any call that is not an approved bounded instruction."""
    if not isinstance(instruction, BoundedInstruction) or not instruction.approved:
        raise UnplannedExecutionError(
            "refused: the agent runs only an approved BoundedInstruction; "
            "there is no direct-execution path"
        )
    return instruction


class AgentAdapter(ABC):
    """Backend-agnostic execution seam. All backends are gated identically."""

    @abstractmethod
    def execute_command(self, instruction: BoundedInstruction | None) -> ExecutionResult: ...

    @abstractmethod
    def stream_events(self, instruction: BoundedInstruction | None) -> Iterator[str]: ...

    @abstractmethod
    def capture_result(self) -> ExecutionResult | None: ...

    @abstractmethod
    def report_files_changed(self) -> list[str]: ...

    @abstractmethod
    def report_artifacts_created(self) -> list[str]: ...

    @abstractmethod
    def report_usage_if_available(self) -> dict | None: ...
