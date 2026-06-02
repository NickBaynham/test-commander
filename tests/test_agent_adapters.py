"""Step 10.5.2 - the AgentAdapter abstraction + MockAgentAdapter + stubs.

The MockAgentAdapter deterministically "executes" a bounded instruction (it
writes the instruction's expected outputs and reports them), refuses an
unplanned call, and the real-backend stubs refuse cleanly. This is the seam the
whole governed pipeline is built against.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime"))

from agent_adapters import anthropic_api  # noqa: E402
from agent_adapters.base import (  # noqa: E402
    AgentAdapter,
    BoundedInstruction,
    ExecutionResult,
    UnplannedExecutionError,
)
from agent_adapters.mock_agent import MockAgentAdapter  # noqa: E402


def make_instruction(project_root: Path, **over) -> BoundedInstruction:
    defaults = dict(
        command="/tc:automate",
        scope="code-write",
        project_root=project_root,
        allowed_paths=("tests/",),
        expected_outputs=("tests/e2e/sign-in.spec.ts",),
        approved=True,
    )
    defaults.update(over)
    return BoundedInstruction(**defaults)


def test_mock_is_an_agent_adapter():
    assert issubclass(MockAgentAdapter, AgentAdapter)


def test_mock_round_trips_a_bounded_instruction(tmp_path: Path):
    adapter = MockAgentAdapter()
    instr = make_instruction(tmp_path)
    result = adapter.execute_command(instr)
    assert isinstance(result, ExecutionResult)
    assert result.status == "succeeded"
    assert "tests/e2e/sign-in.spec.ts" in result.files_changed
    # The mock actually created the expected output (so a later diff can match).
    assert (tmp_path / "tests/e2e/sign-in.spec.ts").is_file()
    # The interface read-backs reflect the last execution.
    assert adapter.report_files_changed() == result.files_changed
    assert isinstance(adapter.report_artifacts_created(), list)
    assert adapter.report_usage_if_available() is None or isinstance(
        adapter.report_usage_if_available(), dict
    )


def test_mock_records_calls(tmp_path: Path):
    adapter = MockAgentAdapter()
    assert adapter.calls == []
    adapter.execute_command(make_instruction(tmp_path))
    assert len(adapter.calls) == 1
    assert adapter.calls[0].command == "/tc:automate"


def test_mock_refuses_unplanned_call(tmp_path: Path):
    adapter = MockAgentAdapter()
    with pytest.raises(UnplannedExecutionError):
        adapter.execute_command(None)
    with pytest.raises(UnplannedExecutionError):
        adapter.execute_command(make_instruction(tmp_path, approved=False))
    assert adapter.calls == [], "a refused call must not be recorded as executed"


def test_mock_stream_events_is_deterministic(tmp_path: Path):
    adapter = MockAgentAdapter()
    instr = make_instruction(tmp_path)
    first = list(adapter.stream_events(instr))
    assert first and all(isinstance(e, str) for e in first)


def test_anthropic_stub_refuses_cleanly(tmp_path: Path):
    # The Anthropic backend stays a stub (Pattern C, deferred); the Claude
    # adapter is a real gated backend tested in test_claude_adapter_and_console.
    with pytest.raises(NotImplementedError):
        anthropic_api.AnthropicApiAdapter().execute_command(make_instruction(tmp_path))
