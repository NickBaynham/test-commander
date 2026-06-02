"""Test Commander web console backend (Phase 10).

A read-only, proposal-only FastAPI service over a `.test-commander/` workspace.
The workspace is the source of truth; the SQLite index is a rebuildable
derivative. No route mutates the workspace or runs a command — execution is
gated behind Phase 10.5.
"""
