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


def mode_name(mode: int) -> str:
    """The human name for an autonomy mode (default deny: unknown -> read-only-advisor)."""
    return AUTONOMY_MODES.get(mode, AUTONOMY_MODES[0])
