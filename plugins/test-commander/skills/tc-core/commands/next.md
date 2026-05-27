# `/tc:next`

Read the current workspace state and recommend the next Test Commander command. The top recommendation is surfaced as a `next:` line; additional gaps are listed as followups.

## Inputs

| Name | Required | Default | Description |
| --- | --- | --- | --- |
| `target` | no | current working directory | Project root. Workspace is read from `<target>/.test-commander/`. |

## Outputs

Stdout in this shape:

```
next: <command-or-action>  (Phase N)
  <one-paragraph explanation>

followups:
  <command>  (Phase N)
  <command>  (Phase N)
  ...
```

If only one rule matches, the `followups:` section is omitted. If no rule matches, the first line is `next: (no recommendations — workspace state could not be classified)`.

Exit 0 in every case (read-only command).

## Preconditions

- None. A missing workspace is a valid state that triggers `R1` (run `/tc:init`).

## Behavior

1. Call `workspace_state.snapshot(target)` to get the current `WorkspaceSnapshot`.
2. Evaluate every rule in `_RULES` (declared inside the engine and documented in [`next-step-inference.md`](../methodology/next-step-inference.md)).
3. Collect every matching `Recommendation(command, explanation, phase, priority)`.
4. Sort by `priority` ascending (lower number = more urgent).
5. Print the top match as `next:` plus the explanation; print the rest as `followups:` (command + phase only).

The engine never modifies the workspace or the template.

## Rules

The full rule set lives in [`../methodology/next-step-inference.md`](../methodology/next-step-inference.md). Summary:

| Priority | Trigger | Recommends |
| --- | --- | --- |
| 1 | Workspace missing | `/tc:init` |
| 2 | Workspace exists; Phase 1 not customized | edit `project.md` / `config.yaml` / `methodology.md` |
| 3 | Phase 2 not started | `/tc:review-requirements` |
| 4 | Phase 3 not started | `/tc:learn-from-docs` |
| 5 | Phase 4 not started | `/tc:create-charter` |
| 6 | Phase 5 not started | `/tc:generate-bdd` |
| 7 | Phase 6 not started | `/tc:automation-plan` |
| 8 | Phase 7 not started | `/tc:run` |
| 9 | Phase 8 not started | `/tc:learn` |
| 10 | All MVP phases (1–8) in progress | `/tc:report` |

Phase 9 (visuals) and Phase 10.5 (controlled execution) have no R-rule yet — see the methodology doc for the rationale.

## Safety

- Read-only. Never writes to the workspace or anywhere else.
- Never resolves symlinks outside the target.
- Each rule is a pure predicate over the snapshot — no I/O outside the snapshot.

## Implementation

Implemented by `plugins/test-commander/scripts/next_step.py`. Invoke as:

```sh
python3 plugins/test-commander/scripts/next_step.py [target]
```

`next_step.recommendations(snapshot)` and `next_step.next_step(snapshot)` are the importable API used internally; `recommendations_for(path)` / `next_step_for(path)` wrap the snapshot call.

## Definition of Done

- Every rule in `next-step-inference.md` has a passing test fixture in `tests/test_next_step.py`.
- Recommendations always include an explanation, not just a command name.
- Output is grep-friendly: the first line always begins with `next: `.
- When multiple rules fire, recommendations are sorted by priority ascending and rendered with the top under `next:` and the rest under `followups:`.
- Read-only — verified by no-mutation tests in the snapshot suite.

## See also

- [`/tc:init`](init.md)
- [`/tc:status`](status.md)
- [`/tc:journal`](journal.md)
- [Methodology — next-step inference](../methodology/next-step-inference.md)
- [Phased plan](../../../../../planning/plan.md)
