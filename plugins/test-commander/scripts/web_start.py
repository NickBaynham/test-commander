#!/usr/bin/env python3
"""/tc:web-start - Phase 10 Step 10.4.

Brings the web console stack (api + web) up via docker compose, pointed at the
given project root (`TC_WORKSPACE`). By default it prints the exact command and
the workspace it would use, without executing — so the user can review it. Only
`--up` actually shells out, and that real invocation is refused under pytest
(the project's hermetic-boundary pattern), so the suite never starts Docker.

Self-contained (no backend import) so it runs as a plain plugin script (D18).

Exit codes:
    0 - command printed (default) or stack brought up.
    2 - precondition failure.
"""

from __future__ import annotations

import argparse
import os
import subprocess  # noqa: S404 - guarded; never reached under pytest
from pathlib import Path

PYTEST_ENV_VAR = "PYTEST_CURRENT_TEST"


class ComposeRefusedError(Exception):
    pass


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def compose_command() -> list[str]:
    return ["docker", "compose", "up", "--build"]


def _invoke_compose(workspace: Path) -> None:
    if os.environ.get(PYTEST_ENV_VAR):
        raise ComposeRefusedError(
            "docker compose up refused under pytest (PYTEST_CURRENT_TEST is set); "
            "run `make run` or `/tc:web-start --up` outside the test suite"
        )
    env = {**os.environ, "TC_WORKSPACE": str(workspace)}  # pragma: no cover
    subprocess.run(compose_command(), cwd=_repo_root(), env=env, check=True)  # pragma: no cover


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start the web console stack (docker compose).")
    parser.add_argument("project_root", nargs="?", default=".", help="Project root (workspace).")
    parser.add_argument("--up", action="store_true", help="Actually run docker compose up.")
    args = parser.parse_args(argv if argv is not None else None)
    workspace = Path(args.project_root).resolve()

    cmd = " ".join(compose_command())
    if not args.up:
        print(f"TC_WORKSPACE={workspace} {cmd}")
        print("(dry run — pass --up to bring the stack up; or run `make run`.)")
        return 0
    _invoke_compose(workspace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
