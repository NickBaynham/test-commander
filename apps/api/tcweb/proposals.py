"""Command proposal generation (Phase 10 Step 10.3).

The console never executes a `/tc:*` command. When the user asks for an action,
it returns a **proposal card** — a suggested command plus a rationale — that the
user reviews and runs themselves (execution is gated behind Phase 10.5). This
module maps a freeform intent to a card; it has no side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# (keyword, command, rationale). Universal vocabulary (D19); first match wins.
_RULES: list[tuple[tuple[str, ...], str, str]] = [
    (("bdd", "scenario", "gherkin"), "/tc:generate-bdd",
     "Generate BDD scenarios from the requirements and exploration notes."),
    (("automate", "automation"), "/tc:automation-plan",
     "Score scenarios for automation suitability before writing any test."),
    (("review", "requirement"), "/tc:review-requirements",
     "Review the requirements for testability, clarity, and completeness."),
    (("explore", "exploratory", "charter"), "/tc:create-charter",
     "Start a session-based exploratory testing charter."),
    (("run", "execute test", "test run"), "/tc:run",
     "Run the automated suite and collect evidence."),
    (("report", "quality"), "/tc:report",
     "Refresh the living quality report from the latest artifacts."),
    (("diagram", "visual", "chart"), "/tc:visualize",
     "Generate the visual documentation set from the workspace."),
]
_FALLBACK = ("/tc:next", "Ask Test Commander what the best next command is for this workspace.")


@dataclass(frozen=True)
class ProposalCard:
    command: str
    rationale: str
    kind: str = "proposal"
    executed: bool = False  # always False - the console never executes
    matched_on: str = field(default="")

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "command": self.command,
            "rationale": self.rationale,
            "executed": self.executed,
        }


def propose(intent: str) -> ProposalCard:
    """Map a freeform intent to a command proposal card. Never executes."""
    lower = (intent or "").lower()
    for keywords, command, rationale in _RULES:
        for kw in keywords:
            if kw in lower:
                return ProposalCard(command=command, rationale=rationale, matched_on=kw)
    return ProposalCard(command=_FALLBACK[0], rationale=_FALLBACK[1])
