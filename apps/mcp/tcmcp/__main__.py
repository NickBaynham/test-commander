"""Stdio entry point for the Test Commander MCP server (Phase 11).

A thin transport: read one JSON message per line from stdin, hand it to
`server.dispatch`, and write the JSON response (with the request id echoed back)
to stdout. The dispatch logic — and all governance — lives in `server`; this
module only wires stdin/stdout, so it stays trivially correct and the testable
core is exercised directly by the round-trip tests.
"""

from __future__ import annotations

import json
import sys

from tcmcp import server


def serve(stdin=sys.stdin, stdout=sys.stdout) -> None:
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            stdout.write(json.dumps({"isError": True, "error": f"invalid JSON: {exc}"}) + "\n")
            stdout.flush()
            continue
        response = server.dispatch(message)
        if "id" in message:
            response = {"id": message["id"], **response}
        stdout.write(json.dumps(response) + "\n")
        stdout.flush()


if __name__ == "__main__":
    serve()
