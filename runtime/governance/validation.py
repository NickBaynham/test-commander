"""Output validation + secret safety (Phase 10.5 Step 10.5.8).

After execution the runtime verifies the diff matches the plan: every changed
file is within the planned write scope, no secret file was touched, and the
expected outputs were produced. Any violation marks the run failed (admin
review). Secret safety: redact secret values from text and flag attempts to
print environment variables.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from governance.planner import Plan

# Path fragments that are never a legitimate target (secret safety).
SECRET_PATH_FRAGMENTS = (".env", "secret", "credential", ".pem", "id_rsa", "deploy")

# Secret-bearing assignments to redact in any text (logs, artifacts, prompts).
_SECRET_ASSIGN_RE = re.compile(
    r"([A-Za-z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)[A-Za-z0-9_]*\s*[=:]\s*)(\S+)",
    re.IGNORECASE,
)
_ENV_PRINT_RE = re.compile(r"printenv|os\.environ|echo\s+\$|env\s*\||\$\{?[A-Z_]+", re.IGNORECASE)


@dataclass
class ValidationResult:
    ok: bool
    violations: list[str] = field(default_factory=list)


def _in_scope(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path == p or path.startswith(p) for p in prefixes)


def _is_secret_path(path: str) -> bool:
    low = path.lower()
    return any(frag in low for frag in SECRET_PATH_FRAGMENTS)


def validate(plan: Plan, result, project_root=None) -> ValidationResult:
    """Verify the execution's changes match the planned scope. Default fail-closed."""
    violations: list[str] = []
    scope = tuple(plan.writes)
    for changed in result.files_changed:
        if _is_secret_path(changed):
            violations.append(f"secret file touched: {changed}")
        elif not _in_scope(changed, scope):
            violations.append(f"out-of-scope write: {changed}")
    for expected in plan.expected_artifacts:
        if not any(c == expected or c.startswith(expected) for c in result.files_changed):
            violations.append(f"expected output not produced: {expected}")
    return ValidationResult(ok=not violations, violations=violations)


def redact(text: str) -> str:
    """Mask secret-bearing values in arbitrary text."""
    return _SECRET_ASSIGN_RE.sub(lambda m: f"{m.group(1)}REDACTED", text or "")


def flags_env_var_print(text: str) -> bool:
    """Whether the text attempts to print environment variables / secrets."""
    return bool(_ENV_PRINT_RE.search(text or ""))
