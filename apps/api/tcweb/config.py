"""Workspace resolution and console configuration (Phase 10).

The console reads a single consuming-project `.test-commander/` workspace. The
path comes from the ``TC_WORKSPACE`` environment variable (the project root that
contains ``.test-commander/``), defaulting to the current working directory.
"""

from __future__ import annotations

import os
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"
WORKSPACE_ENV_VAR = "TC_WORKSPACE"


def project_root() -> Path:
    """The consuming-project root the console serves (TC_WORKSPACE or cwd)."""
    return Path(os.environ.get(WORKSPACE_ENV_VAR, ".")).expanduser().resolve()


def workspace_dir(root: Path | None = None) -> Path:
    """The `.test-commander/` directory under the project root."""
    return (root or project_root()) / WORKSPACE_DIRNAME


def index_db_path(root: Path | None = None) -> Path:
    """Where the derived SQLite index lives (inside the workspace, git-ignorable)."""
    return workspace_dir(root) / ".web" / "index.db"
