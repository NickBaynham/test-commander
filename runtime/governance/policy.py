"""Permission policy engine (Phase 10.5 Step 10.5.3).

Classifies every request into one of seven escalating permission levels and
resolves it against the role's allowed levels. Default deny: a level absent from
a role's list (or an unknown role) is denied. Per-deployment overrides live in
`<workspace>/policy/permissions.yaml`; the built-in defaults below are the
universal baseline (Decision D19).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

LEVELS = (
    "read-only",
    "safe-write",
    "code-write",
    "execute-tests",
    "external-network",
    "destructive",
    "admin",
)

# Keyword -> level, checked most-privileged first so a destructive verb wins over
# an incidental "review". Keys are action-anchored (verbs, not bare nouns) so a
# read like "show me the quality report" is not mistaken for a write. Universal
# vocabulary only.
_CLASSIFIERS: list[tuple[str, tuple[str, ...]]] = [
    ("admin", ("secret", "credential", "provider", "permission rule", "manage user", "api key")),
    ("destructive", ("delete", "reset", "destroy", "remove all", "install", "wipe", "drop")),
    ("external-network", ("explore", "staging", "target site", "target api", "external",
                          "call the api", "production")),
    ("execute-tests", ("run the", "run tests", "run a test", "regression", "smoke",
                       "execute the suite")),
    ("code-write", ("generate playwright", "generate test", "page object", "fixture",
                    "automate", "refactor", "spec.ts", "modify the test")),
    ("safe-write", ("review", "generate bdd", "create test idea", "update risk register",
                    "generate diagram", "update the quality report", "generate infographic",
                    "raise open question")),
]

DEFAULT_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "Viewer": ("read-only",),
    "Tester": ("read-only", "safe-write", "execute-tests"),
    "Automation Engineer": ("read-only", "safe-write", "code-write", "execute-tests"),
    "Maintainer": ("read-only", "safe-write", "code-write", "execute-tests",
                   "external-network", "destructive"),
    "Admin": LEVELS,
}

WORKSPACE_DIRNAME = ".test-commander"


@dataclass(frozen=True)
class PolicyDecision:
    level: str
    allowed: bool
    role: str
    reason: str


def classify(request: str) -> str:
    """Map a request (or command) to a permission level. Unknown -> read-only."""
    text = (request or "").lower()
    for level, keywords in _CLASSIFIERS:
        if any(kw in text for kw in keywords):
            return level
    return "read-only"


def load_permissions(project_root: Path | None = None) -> dict[str, tuple[str, ...]]:
    """Role -> allowed levels. Reads policy/permissions.yaml when populated."""
    if project_root is not None:
        path = Path(project_root) / WORKSPACE_DIRNAME / "policy" / "permissions.yaml"
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            data = yaml.safe_load(text)
            if isinstance(data, dict) and data:
                return {role: tuple(levels or ()) for role, levels in data.items()}
    return DEFAULT_ROLE_PERMISSIONS


def allows(role: str, level: str, project_root: Path | None = None) -> bool:
    """Whether a role may act at a level. Default deny (unknown role -> False)."""
    return level in load_permissions(project_root).get(role, ())


def decide(request: str, role: str, project_root: Path | None = None) -> PolicyDecision:
    level = classify(request)
    permitted = allows(role, level, project_root)
    reason = (
        f"{level} permitted for {role}"
        if permitted
        else f"permission denied: {level} not allowed for {role} (default deny)"
    )
    return PolicyDecision(level=level, allowed=permitted, role=role, reason=reason)
