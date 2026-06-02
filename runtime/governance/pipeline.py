"""The governance pipeline orchestrator (scaffold; built across 10.5.3-10.5.10).

`handle_request` is the single entry point every request flows through. The
components it composes land in later sub-steps; until then it refuses to run.
"""

from __future__ import annotations


def handle_request(*args, **kwargs):  # noqa: ANN002, ANN003
    raise NotImplementedError(
        "the governance pipeline is built across Steps 10.5.3-10.5.10"
    )
