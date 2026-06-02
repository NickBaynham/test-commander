# /tc:web-start

Bring the web console stack (api + web) up via docker compose, pointed at a
project's `.test-commander/` workspace.

## Inputs

- A project root holding `.test-commander/` (sets `TC_WORKSPACE`).
- CLI: `<project-root>` (defaults to the current directory); `--up` to actually
  run docker compose.

## Outputs

- By default, the exact `docker compose up` command and the workspace it would
  use (a dry run — nothing is executed).
- With `--up`, the running stack (api on 8100, web on 3100).

## Preconditions

- Docker + docker compose available (for `--up`).

## Behavior

1. Resolve the workspace.
2. Without `--up`: print `TC_WORKSPACE=<path> docker compose up --build` and exit
   0 — the user reviews and runs it (or runs `make run`).
3. With `--up`: shell out to docker compose. This real invocation is **refused
   under pytest**, so the suite never starts Docker.

## Safety

- The only command that can start the stack; the stack itself is read-only and
  proposal-only. No workspace mutation.

## Implementation

- Command: `plugins/test-commander/scripts/web_start.py` (per D18; self-contained).
- Run: `python3 <plugin-root>/scripts/web_start.py <project-root> [--up]`, or `make run`.

## Definition of Done

- Prints the compose command without executing by default; `--up` refused under
  pytest; brings the stack up outside the suite.
- `tc-web/SKILL.md` describes the shipped command.

## See also

- [/tc:web-init](web-init.md)
- [Web console architecture](../methodology/web-architecture.md)
- [tc-web skill](../SKILL.md)
