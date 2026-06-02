# Intent routing and command planning

The first two pipeline stages turn a free-text request (or a button action) into
an explicit, reviewable plan — without ever letting the user synthesize a command.

## Intent router

`governance.intent.route(request)` maps a request to one of the known `/tc:*`
workflows (`KNOWN_COMMANDS`) or to the read-only Q&A path. It is closed: a button
may pass an exact command, but it is honored only if it is in the known set;
everything else falls back to `read-only`. The router cannot invent a new command.

Routing is **orthogonal to the permission gate**: the policy engine classifies a
request's inherent risk and blocks dangerous intent even when the router maps it
to read-only (e.g. "delete all evidence" routes read-only — there is no known
delete workflow — but the policy engine still classifies it `destructive` and
blocks it for low roles). The router supplies the *command* for the plan; the
policy supplies the *block decision*.

## Command planner

`governance.planner.plan(command)` produces an explicit, deterministic `Plan`
the approval gate renders and the bounded executor wraps: `command`, `level`,
`reads`, `writes`, `expected_artifacts`, `target_environment`, and
`requires_approval`. Per-command knowledge (what each `/tc:*` reads and writes,
and at what level) lives in `_COMMAND_PLANS`; a routed-but-unknown command and
the read-only path both yield a no-write read-only plan. `requires_approval` is
true for `code-write` / `execute-tests` / `external-network` / `destructive` /
`admin` by default (the approval gate may widen it for `safe-write`).

## See also

- [Permission policy](permission-policy.md)
- [tc-governance skill](../SKILL.md)
