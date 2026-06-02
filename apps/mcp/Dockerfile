# Test Commander MCP server (Phase 11).
FROM python:3.12-slim

WORKDIR /srv

# Runtime deps only; the MCP server is a thin schema-first registry that
# dispatches into the governance pipeline.
RUN pip install --no-cache-dir "pyyaml>=6.0"

COPY apps/mcp/tcmcp ./tcmcp
# The governance pipeline + agent adapters (Phase 10.5) every tool above
# read-only dispatches into.
COPY runtime/governance ./governance
COPY runtime/agent_adapters ./agent_adapters

# The consuming project's workspace is mounted at /workspace.
ENV TC_WORKSPACE=/workspace

# The MCP server speaks over stdio (the stdio entry point lands in Step 11.3).
CMD ["python", "-m", "tcmcp"]
