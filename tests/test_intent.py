"""Step 10.5.4 - the intent router (NL/button -> known workflow).

Maps natural-language requests and button actions to known /tc:* workflows;
unknown intents route to the read-only Q&A path. The router cannot synthesize a
command outside the known set.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "runtime"))

from governance import intent  # noqa: E402

READ_ONLY = "read-only"


def test_known_phrasings_map_to_commands():
    assert intent.route("review these requirements") == "/tc:review-requirements"
    assert intent.route("generate BDD for the sign-in flow") == "/tc:generate-bdd"
    assert intent.route("generate playwright tests for sign-in") == "/tc:automate"
    assert intent.route("run the sign-in regression tests") == "/tc:run"
    assert intent.route("explore the staging site") == "/tc:explore"
    assert intent.route("draw a diagram of coverage") == "/tc:visualize"


def test_button_actions_map_directly():
    # A button can pass an exact command; the router passes it through if known.
    assert intent.route("/tc:report") == "/tc:report"


def test_unknown_intent_routes_read_only():
    assert intent.route("what is the weather today") == READ_ONLY
    assert intent.route("delete all evidence") == READ_ONLY  # no known workflow to do this


def test_router_never_synthesizes_outside_the_known_set():
    for phrase in ("review requirements", "frobnicate the doohickey", "/tc:make-coffee",
                   "generate playwright tests", "run tests"):
        result = intent.route(phrase)
        assert result == READ_ONLY or result in intent.KNOWN_COMMANDS, (
            f"router produced an unknown command: {result}"
        )
