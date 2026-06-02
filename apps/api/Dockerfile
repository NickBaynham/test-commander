# Test Commander web console - FastAPI backend (Phase 10).
FROM python:3.12-slim

WORKDIR /srv

# Runtime deps only; the backend is a thin read-only service over the workspace.
RUN pip install --no-cache-dir "fastapi>=0.115" "uvicorn[standard]>=0.30" "pyyaml>=6.0"

COPY apps/api/tcweb ./tcweb
# The governance pipeline + agent adapters (Phase 10.5) the /api/execute route uses.
COPY runtime/governance ./governance
COPY runtime/agent_adapters ./agent_adapters

# The consuming project's workspace is mounted at /workspace.
ENV TC_WORKSPACE=/workspace
EXPOSE 8100

CMD ["uvicorn", "tcweb.main:app", "--host", "0.0.0.0", "--port", "8100"]
