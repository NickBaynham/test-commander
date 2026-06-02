"""Read-only chat over the index (Phase 10 Step 10.5).

Answers questions from the SQLite index and surfaces command **proposal cards**.
It never executes a command or mutates the workspace — an action request is
answered with a proposal and a note that the user must run it (execution is
gated behind Phase 10.5). Retrieval is deterministic keyword routing over the
index; there is no model call in the MVP.
"""

from __future__ import annotations

import sqlite3

from tcweb import proposals, queries

# Action verbs that turn a question into a request worth proposing a command for.
# A pure question ("how many requirements?") contains none of these, so it gets a
# plain answer with no proposal card.
_ACTION_VERBS = (
    "generate", "create", "write", "automate", "run", "execute", "explore",
    "visualize", "diagram", "draw", "build", "make", "review",
)
# Phrases that signal an attempt to *execute* (as opposed to ask about) something.
_EXECUTE_MARKERS = ("run ", "execute", "do it", "now", "trigger", "launch")


def _answer_from_index(question: str, conn: sqlite3.Connection) -> str:
    q = question.lower()
    facts = queries.quality_facts(conn)
    if "fail" in q:
        failed = [r for r in queries.run_results(conn) if r["status"] == "failed"]
        if failed:
            items = "; ".join(f"{r['candidate']} ({r['scenario']})" for r in failed)
            return f"{len(failed)} scenario(s) failed in the latest run: {items}."
        return "No failed scenarios in the latest run."
    if "flaky" in q:
        flaky = [r for r in queries.run_results(conn) if r["status"] == "flaky"]
        return f"{len(flaky)} flaky scenario(s) in the latest run."
    if "requirement" in q:
        return f"{facts.get('requirements', '0')} requirement(s) are inventoried."
    if "risk" in q:
        return f"{facts.get('risks', '0')} risk(s) are in the register."
    if "open question" in q:
        return f"{facts.get('open_questions', '0')} open question(s) outstanding."
    if "run" in q or "latest" in q or "result" in q:
        runs = queries.runs(conn)
        if runs:
            r = runs[0]
            return (
                f"Latest run {r['run_id']}: {r['passed']} passed, "
                f"{r['failed']} failed, {r['flaky']} flaky."
            )
        return "No runs recorded yet."
    return (
        "I can answer from the indexed workspace — try asking about requirements, "
        "the latest run, failures, flaky tests, risks, or open questions."
    )


def answer(question: str, conn: sqlite3.Connection) -> dict:
    """Answer a question read-only; attach a proposal card for action intents."""
    text = _answer_from_index(question, conn)
    lower = (question or "").lower()
    is_action = any(verb in lower for verb in _ACTION_VERBS)
    card = proposals.propose(question)
    proposal = card.to_dict() if (is_action and card.matched_on) else None
    if proposal and any(marker in lower for marker in _EXECUTE_MARKERS):
        text = (
            f"{text} I cannot run commands — the console is read-only. "
            f"Review and run `{card.command}` yourself."
        )
    return {"kind": "answer", "answer": text, "proposal": proposal, "executed": False}
