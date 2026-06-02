"""Test Commander MCP server (Phase 11).

A lightweight, schema-first Model Context Protocol server. Every tool above
read-only dispatches into the Phase-10.5 governance pipeline
(`governance.pipeline.handle_request`); there is no direct-execution backdoor.
The seven permission levels are enforced server-side.
"""
