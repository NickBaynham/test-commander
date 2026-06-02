"""Intent router (Phase 10.5 Step 10.5.4).

Maps natural-language requests and button actions to known `/tc:*` workflows.
Unknown intents route to the read-only Q&A path. The router **cannot synthesize**
a command outside `KNOWN_COMMANDS` — a button that passes an exact command is
honored only if it is known; everything else falls back to read-only.

This is orthogonal to the permission gate: the policy engine (10.5.3) classifies
the request's inherent risk and blocks dangerous intent even when the router maps
it to read-only. The router supplies the *command* for planning, not the block
decision.
"""

from __future__ import annotations

READ_ONLY = "read-only"

# Known workflow set. The router may only ever return one of these or READ_ONLY.
KNOWN_COMMANDS = (
    "/tc:review-requirements",
    "/tc:generate-bdd",
    "/tc:automate",
    "/tc:run",
    "/tc:explore",
    "/tc:visualize",
    "/tc:report",
    "/tc:create-charter",
)

# (keywords, command), most-specific first. Action-anchored, universal vocabulary.
_ROUTES: list[tuple[tuple[str, ...], str]] = [
    (("review", "requirement"), "/tc:review-requirements"),
    (("generate bdd", "bdd for"), "/tc:generate-bdd"),
    (("generate playwright", "automate", "page object"), "/tc:automate"),
    (("run the", "run tests", "regression", "smoke"), "/tc:run"),
    (("explore",), "/tc:explore"),
    (("diagram", "visualize", "chart"), "/tc:visualize"),
    (("quality report", "report"), "/tc:report"),
    (("charter",), "/tc:create-charter"),
]


def route(request: str) -> str:
    """Return a known /tc:* command for the request, or READ_ONLY."""
    text = (request or "").strip()
    lower = text.lower()
    # A button may pass an exact command; honor it only if known (no synthesis).
    if text.startswith("/tc:"):
        return text if text in KNOWN_COMMANDS else READ_ONLY
    for keywords, command in _ROUTES:
        if any(kw in lower for kw in keywords):
            return command  # command is always a member of KNOWN_COMMANDS
    return READ_ONLY
