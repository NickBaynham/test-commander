"""Autonomy modes (Phase 13).

The five autonomy modes map to which permission levels the continuous agent may
auto-approve in the Phase-10.5 pipeline. Autonomy is a ceiling: nothing above the
configured mode executes without explicit human approval. The gate logic
(`auto_approves`, `can_open_pr`) lands in Step 13.5; the scaffold ships the mode
names.
"""

from __future__ import annotations

AUTONOMY_MODES: dict[int, str] = {
    0: "read-only-advisor",
    1: "assisted-testing",
    2: "approved-execution",
    3: "pull-request-automation",
    4: "governed-autonomy",
}

# The permission levels each mode auto-approves (cumulative). read-only is never
# gated; destructive and admin are never auto-approved at any mode. The
# progression is advisor -> safe-write -> execute-tests -> code-write ->
# external-network (the autonomy progression, not the policy level order).
_AUTO_APPROVE: dict[int, frozenset[str]] = {
    0: frozenset(),
    1: frozenset({"safe-write"}),
    2: frozenset({"safe-write", "execute-tests"}),
    3: frozenset({"safe-write", "execute-tests", "code-write"}),
    4: frozenset({"safe-write", "execute-tests", "code-write", "external-network"}),
}

# Opening a pull request requires pull-request-automation (mode 3) or higher.
_MIN_PR_MODE = 3


def mode_name(mode: int) -> str:
    """The human name for an autonomy mode (default deny: unknown -> read-only-advisor)."""
    return AUTONOMY_MODES.get(mode, AUTONOMY_MODES[0])


def auto_approves(mode: int, level: str) -> bool:
    """Whether the mode auto-approves an action at this permission level.

    read-only is always allowed; destructive/admin are never auto-approved.
    Default deny: an unknown mode auto-approves nothing.
    """
    if level == "read-only":
        return True
    return level in _AUTO_APPROVE.get(mode, frozenset())


def can_open_pr(mode: int) -> bool:
    """Whether the mode may open a pull request (mode 3+)."""
    return mode >= _MIN_PR_MODE
