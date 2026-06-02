# No-code tester workflow

Test Commander is built so that **frontend users drive workflows, not raw Claude
Code** (Decision D16). A sandbox makes that real for a tester who never touches a
terminal: a team member launches an on-demand environment, explores or runs
tests against it, and tears it down — all through governed actions, never by
issuing raw commands to an agent.

## The flow

1. **A maintainer prepares the sandbox config** once: the target, the allow-list,
   and the approval policy in `.test-commander/sandbox/config.yaml` (written by
   `/tc:sandbox-init`, edited for the project — see
   [customizing-for-your-project.md](user-guide/customizing-for-your-project.md)).
2. **A tester launches the sandbox** — via the GitHub Actions workflow (a button
   in the Actions tab) or `/tc:sandbox-launch`. The endpoints are published for
   the team.
3. **The tester works against the sandbox** — exploration, BDD execution, test
   runs. Every action that does anything above read-only flows through the
   Phase-10.5 pipeline: it is permission-checked, approved where required, and
   audited. A tester cannot execute above their role's approved level, and the
   agent never sees a raw prompt.
4. **The sandbox is torn down** — `/tc:sandbox-stop`, or automatically by the
   workflow's always-run teardown.

## Why this is safe

- The tester drives *workflows* (launch, run, report), not raw agent commands.
- Governance travels with the sandbox: the same default-deny policy, approval
  gate, and audit journal that protect the local runtime protect the sandbox.
- Targeting is safe-by-default: only allow-listed hosts, no private ranges.
- Secrets stay server-side; the tester never sees a provider credential.

## See also

- [Sandboxed environments](sandboxed-environments.md)
- [Sandbox user guide](user-guide/sandbox.md)
- [Security and permissions](security-and-permissions.md)
- [Governance user guide](user-guide/governance.md)
