# Agent adapters

The `AgentAdapter` interface decouples the governed pipeline from any specific
backend, so governance is backend-agnostic and there is no direct-execution
backdoor.

## The interface

`runtime/agent_adapters/base.py` defines `AgentAdapter` (ABC) with six methods:
`execute_command`, `stream_events`, `capture_result`, `report_files_changed`,
`report_artifacts_created`, `report_usage_if_available`. An adapter receives a
**`BoundedInstruction`** — a structured instruction built by the executor from an
approved plan — never a raw user prompt. Its instruction-critical fields are
`command`, `scope`, `allowed_paths` / `disallowed_paths`, `allowed_actions` /
`disallowed_actions`, and `expected_outputs`; `approved` must be `True`.

## No backdoor

`require_planned(instruction)` refuses any call that is not an approved
`BoundedInstruction` with `UnplannedExecutionError`. Every adapter routes
`execute_command` and `stream_events` through it, so calling an adapter directly
(no plan, or an unapproved instruction) is refused — the only way to execute is
through the pipeline.

## Implementations

| Adapter | Status |
| --- | --- |
| `MockAgentAdapter` | shipped — deterministic; creates the instruction's `expected_outputs` (so a post-execution diff matches the plan), records every call, refuses unplanned calls. The pipeline is built and tested against it. |
| `ClaudeCodeCliAdapter` | stub until Step 10.5.10 — wired behind the same pipeline, no new execution path. |
| `AnthropicApiAdapter` | stub (Pattern C, deferred past v1). |

A backend swap changes nothing about the gates: intent → plan → policy →
approval → bounded execution → validation → audit runs identically whichever
adapter is in use.

## See also

- [tc-governance skill](../SKILL.md)
