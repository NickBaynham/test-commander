"""The Test Commander MCP server (Phase 11, scaffold at Step 11.1).

A lightweight, schema-first tool registry. The scaffold ships the server
identity, a health check, and an empty tool registry; the schema-first tools
that dispatch into the governance pipeline land in Step 11.3, and the per-level
permission gates in Step 11.4.
"""

from __future__ import annotations

SERVER_NAME = "test-commander"
SERVER_VERSION = "0.11.0"


def health() -> dict[str, str]:
    """Server liveness + identity. Used by the scaffold test and stdio handshake."""
    return {"status": "ok", "server": SERVER_NAME, "version": SERVER_VERSION}


def tools() -> list[dict]:
    """The registered schema-first tool definitions. Populated in Step 11.3."""
    return []
