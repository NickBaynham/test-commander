"""The Test Commander MCP server (Phase 11).

A lightweight, schema-first tool registry. Every tool ships an explicit JSON
schema for its arguments; a tool above read-only dispatches into the Phase-10.5
governance pipeline (`governance.pipeline.handle_request`). There is no
direct-execution backdoor.

The server is transport-agnostic: `dispatch(message, ...)` handles one
MCP-style protocol message (`initialize`, `tools/list`, `tools/call`) and is what
the stdio entry point (`__main__`) wraps. Tests drive `dispatch` directly through
a sample in-process client.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from governance import pipeline
from governance.policy import LEVELS

SERVER_NAME = "test-commander"
SERVER_VERSION = "0.11.0"
PROTOCOL_VERSION = "2024-11-05"

WORKSPACE_ENV_VAR = "TC_WORKSPACE"


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    max_level: str
    input_schema: dict
    handler: Callable[..., dict]


class ToolError(Exception):
    """A tool call that is malformed (unknown tool, bad arguments)."""


# ---------------------------------------------------------------------------
# Tool handlers - read-only tools answer directly; tc_run_command goes through
# the governance pipeline. None of them bypass the pipeline for execution.
# ---------------------------------------------------------------------------


def _handle_status(arguments: dict, *, project_root: Path, adapter: Any) -> dict:
    return {
        "server": SERVER_NAME,
        "version": SERVER_VERSION,
        "permission_levels": list(LEVELS),
        "workspace_present": (Path(project_root) / ".test-commander").is_dir(),
    }


def _handle_plan(arguments: dict, *, project_root: Path, adapter: Any) -> dict:
    pv = pipeline.preview(
        arguments.get("request", ""),
        role=arguments.get("role", "Viewer"),
        project_root=Path(project_root),
    )
    return {
        "intent": pv.intent,
        "command": pv.plan.command,
        "level": pv.level,
        "allowed": pv.allowed,
        "requires_approval": pv.plan.requires_approval,
    }


def _handle_run_command(arguments: dict, *, project_root: Path, adapter: Any) -> dict:
    res = pipeline.handle_request(
        arguments.get("request", ""),
        role=arguments.get("role", "Viewer"),
        project_root=Path(project_root),
        adapter=adapter,
        approve=bool(arguments.get("approve", False)),
        approver=arguments.get("approver"),
        user=arguments.get("user", "anon"),
    )
    return {
        "blocked": res.blocked,
        "executed": res.executed,
        "requires_approval": res.requires_approval,
        "approved": res.approved,
        "level": res.level,
        "command": res.intent,
        "reason": res.reason,
    }


_REQUEST_PROP = {
    "type": "string",
    "description": "The natural-language request, routed and planned server-side.",
}
_ROLE_PROP = {
    "type": "string",
    "description": "The caller's role; resolved against policy/permissions.yaml.",
    "default": "Viewer",
}

REGISTRY: tuple[Tool, ...] = (
    Tool(
        name="tc_status",
        description="Server identity and the seven permission levels (read-only).",
        max_level="read-only",
        input_schema={"type": "object", "properties": {}, "additionalProperties": False},
        handler=_handle_status,
    ),
    Tool(
        name="tc_plan",
        description="Dry run: route, plan, and classify a request without executing it.",
        max_level="read-only",
        input_schema={
            "type": "object",
            "properties": {"request": _REQUEST_PROP, "role": _ROLE_PROP},
            "required": ["request"],
            "additionalProperties": False,
        },
        handler=_handle_plan,
    ),
    Tool(
        name="tc_run_command",
        description=(
            "Run a request through the governance pipeline (intent -> plan -> policy"
            " -> approval -> bounded execution -> validation -> audit)."
        ),
        max_level="admin",
        input_schema={
            "type": "object",
            "properties": {
                "request": _REQUEST_PROP,
                "role": _ROLE_PROP,
                "approve": {
                    "type": "boolean",
                    "description": "Approve a privileged action that requires approval.",
                    "default": False,
                },
                "approver": {"type": "string", "description": "Who approved (for the audit log)."},
                "user": {"type": "string", "description": "The acting user (for the audit log)."},
            },
            "required": ["request"],
            "additionalProperties": False,
        },
        handler=_handle_run_command,
    ),
)

_BY_NAME = {tool.name: tool for tool in REGISTRY}


# ---------------------------------------------------------------------------
# Registry surface
# ---------------------------------------------------------------------------


def health() -> dict[str, str]:
    """Server liveness + identity."""
    return {"status": "ok", "server": SERVER_NAME, "version": SERVER_VERSION}


def tools() -> list[dict]:
    """The schema-first tool catalog an MCP client lists."""
    return [
        {"name": t.name, "description": t.description, "inputSchema": t.input_schema}
        for t in REGISTRY
    ]


def _validate(schema: dict, arguments: dict) -> None:
    """Minimal JSON-Schema check: required keys present, no unknown keys."""
    for key in schema.get("required", []):
        if key not in arguments:
            raise ToolError(f"missing required argument: {key}")
    if schema.get("additionalProperties") is False:
        allowed = set(schema.get("properties", {}))
        for key in arguments:
            if key not in allowed:
                raise ToolError(f"unknown argument: {key}")


def call_tool(
    name: str, arguments: dict | None = None, *, project_root: Path, adapter: Any
) -> dict:
    """Validate arguments against the tool's schema and dispatch to its handler."""
    tool = _BY_NAME.get(name)
    if tool is None:
        raise ToolError(f"unknown tool: {name}")
    arguments = arguments or {}
    _validate(tool.input_schema, arguments)
    return tool.handler(arguments, project_root=Path(project_root), adapter=adapter)


# ---------------------------------------------------------------------------
# Protocol dispatch (what the stdio transport wraps)
# ---------------------------------------------------------------------------


def _default_project_root() -> Path:
    return Path(os.environ.get(WORKSPACE_ENV_VAR, ".")).expanduser().resolve()


def _default_adapter() -> Any:
    from agent_adapters.mock_agent import MockAgentAdapter

    return MockAgentAdapter()


def dispatch(message: dict, *, project_root: Path | None = None, adapter: Any = None) -> dict:
    """Handle one MCP protocol message and return the response body.

    Supported methods: `initialize`, `tools/list`, `tools/call`. A `tools/call`
    that fails validation or names an unknown tool returns `{"isError": True}`
    rather than raising, mirroring MCP error reporting.
    """
    root = Path(project_root) if project_root is not None else _default_project_root()
    method = message.get("method", "")
    params = message.get("params") or {}

    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "capabilities": {"tools": {}},
        }
    if method == "tools/list":
        return {"tools": tools()}
    if method == "tools/call":
        the_adapter = adapter if adapter is not None else _default_adapter()
        try:
            result = call_tool(
                params.get("name", ""),
                params.get("arguments") or {},
                project_root=root,
                adapter=the_adapter,
            )
        except ToolError as exc:
            return {"isError": True, "error": str(exc)}
        return {"result": result}
    return {"isError": True, "error": f"unknown method: {method}"}
