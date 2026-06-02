"""Shared support for the /tc:sandbox-* command helpers (Phase 12 Step 12.3).

Workspace + config + state I/O, and provider resolution. Self-contained (D18):
it computes the repo root from __file__ to import the sandbox provider
abstraction only when a real provider is needed, so a test can inject a provider
without any repo-root import.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

WORKSPACE_DIRNAME = ".test-commander"

# The default config written by /tc:sandbox-init (universal defaults, D19).
DEFAULT_CONFIG = {
    "schema": "tc-sandbox/v1",
    "provider": "docker-compose",
    "environment_label": "Test Commander Sandbox (ephemeral)",
    "target": {"base_url": "https://sandbox.example.com"},
    "allowed_domains": ["example.com", "*.example.com"],
    "block_private_ranges": True,
    "approvals_required": ["external-network", "destructive"],
}


def workspace(project_root: Path) -> Path:
    return Path(project_root) / WORKSPACE_DIRNAME


def require_workspace(project_root: Path) -> Path:
    ws = workspace(project_root)
    if not ws.is_dir():
        raise FileNotFoundError(
            f"not a Test Commander workspace: {project_root} (no {WORKSPACE_DIRNAME}/)"
        )
    return ws


def sandbox_dir(project_root: Path) -> Path:
    return require_workspace(project_root) / "sandbox"


def config_path(project_root: Path) -> Path:
    return workspace(project_root) / "sandbox" / "config.yaml"


def state_path(project_root: Path) -> Path:
    return workspace(project_root) / "sandbox" / "state.json"


def load_config(project_root: Path) -> dict:
    path = config_path(project_root)
    if not path.is_file():
        raise FileNotFoundError(
            f"sandbox not initialized: {path} missing (run /tc:sandbox-init first)"
        )
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_state(project_root: Path) -> dict | None:
    path = state_path(project_root)
    if not path.is_file():
        return None
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def save_state(project_root: Path, state: dict) -> Path:
    import json

    path = state_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def resolve_provider(name: str):
    """Resolve a real provider by name. Adds the repo root to sys.path so the
    sandbox abstraction (a repo-root runtime, not bundled in the plugin cache) is
    importable when a command runs from the repo."""
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from sandbox.providers import get_provider

    return get_provider(name)
