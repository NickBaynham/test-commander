"""Shared support for the /tc:* continuous-quality command helpers (Phase 13).

Workspace + config + state I/O, diff parsing, the impact map, and provider/
pipeline resolution. Self-contained (D18): it computes the repo root from
__file__ to import the continuous/ autonomy package and the governance pipeline
only when needed (a real PR), so tests drive the pure logic directly.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

WORKSPACE_DIRNAME = ".test-commander"
_DIFF_GIT_RE = re.compile(r"^diff --git a/(\S+) b/(\S+)", re.MULTILINE)

# The default continuous-quality config (universal defaults, D19).
DEFAULT_CONFIG = {
    "schema": "tc-continuous/v1",
    "autonomy_mode": 0,
    "pr_label": "test-commander/auto",
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


def cq_dir(project_root: Path) -> Path:
    return require_workspace(project_root) / "continuous"


def config_path(project_root: Path) -> Path:
    return workspace(project_root) / "continuous" / "config.yaml"


def load_config(project_root: Path) -> dict:
    path = config_path(project_root)
    if path.is_file():
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data:
            return {**DEFAULT_CONFIG, **data}
    return dict(DEFAULT_CONFIG)


def parse_diff(text: str) -> list[str]:
    """Changed file paths from a unified `git diff` (the b/ side, dedup, ordered)."""
    seen: list[str] = []
    for _, b in _DIFF_GIT_RE.findall(text or ""):
        if b not in seen:
            seen.append(b)
    return seen


def load_changed_files(project_root: Path, *, diff_path: Path | None = None) -> list[str]:
    """Changed files from an explicit diff, else from the persisted changes.json."""
    if diff_path is not None:
        return parse_diff(Path(diff_path).read_text(encoding="utf-8"))
    persisted = cq_dir(project_root) / "changes.json"
    if persisted.is_file():
        return list(json.loads(persisted.read_text(encoding="utf-8")).get("changed_files", []))
    return []


def load_impact_map(project_root: Path) -> list[dict]:
    path = workspace(project_root) / "product-knowledge" / "impact-map.yaml"
    if not path.is_file():
        raise FileNotFoundError(
            f"impact map missing: {path} (run Phase-3 knowledge ingestion, or seed it)"
        )
    return yaml.safe_load(path.read_text(encoding="utf-8")) or []


def load_coverage(project_root: Path) -> dict[str, dict]:
    """Existing coverage keyed by feature (from traceability/coverage.yaml)."""
    path = workspace(project_root) / "traceability" / "coverage.yaml"
    if not path.is_file():
        raise FileNotFoundError(
            f"coverage map missing: {path} (run Phase-5 traceability, or seed it)"
        )
    rows = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return {row["feature"]: row for row in rows}


def load_impacted_features(project_root: Path) -> list[str]:
    """Impacted features from the persisted impact.json (from /tc:impact-analysis)."""
    path = cq_dir(project_root) / "impact.json"
    if not path.is_file():
        return []
    return list(json.loads(path.read_text(encoding="utf-8")).get("features", []))


def impacted(changed_files: list[str], impact_map: list[dict]) -> dict:
    """Map changed files -> impacted features + requirements, with provenance.

    Deterministic: a file maps to every impact-map entry whose pattern it starts
    with. A file matching no pattern contributes nothing (never invents impact).
    """
    features: list[str] = []
    requirements: list[str] = []
    provenance: list[dict] = []
    for f in changed_files:
        for entry in impact_map:
            pattern = entry.get("pattern", "")
            if pattern and f.startswith(pattern):
                for feat in entry.get("features", []):
                    if feat not in features:
                        features.append(feat)
                for req in entry.get("requirements", []):
                    if req not in requirements:
                        requirements.append(req)
                provenance.append({"file": f, "pattern": pattern})
    return {
        "features": sorted(features),
        "requirements": sorted(requirements),
        "provenance": provenance,
    }


def write_json(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def resolve_repo_root() -> Path:
    """Add the repo root + runtime/ to sys.path so the continuous/ autonomy
    package and the governance pipeline (under runtime/) are importable when a
    command runs from the repo."""
    repo_root = Path(__file__).resolve().parents[3]
    for path in (repo_root, repo_root / "runtime"):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
    return repo_root
