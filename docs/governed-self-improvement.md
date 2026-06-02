# Governed self-improvement

Continuous quality mode lets Test Commander improve a project's test coverage
over time — proposing and (when allowed) opening test PRs as the application
changes. The principle is **autonomous where safe, human-governed where it
matters**.

## Why it is safe

- **One execution path.** Every action above read-only flows through the
  Phase-10.5 pipeline: intent → plan → permission policy → approval gate →
  bounded execution → output validation → audit. Continuous mode has no backdoor.
- **Autonomy is a ceiling, not a license.** The configured mode decides what
  auto-approves; nothing above it executes without explicit human approval, and
  `destructive`/`admin` never auto-approve. See [autonomy-levels.md](autonomy-levels.md).
- **Generated changes are gated and labeled.** A change the agent generates
  arrives only as a clearly-labeled pull request a human reviews and merges —
  never a direct push (the CI workflow's token is read-only).
- **Read-only by default.** Mode 0 is a pure advisor: it analyzes and proposes,
  but executes nothing. A team raises the mode deliberately.
- **Everything is audited.** Every executed action writes an append-only audit
  entry, so the agent's contributions are fully traceable.

## The mode progression

A team typically starts at mode 0 (advice only), moves to mode 1–2 once it trusts
the analysis and proposals, and adopts mode 3 (labeled PRs) only when it is
comfortable reviewing agent-opened PRs. Mode 4 widens auto-approval to external
targets but still stops at `destructive`/`admin`.

## What it does not do

- It never bypasses approvals or the audit log.
- It never auto-merges — a human reviews and merges every PR.
- It never touches secrets, destructive operations, or admin settings
  automatically.

## See also

- [Continuous quality agent](continuous-quality-agent.md)
- [Autonomy levels](autonomy-levels.md)
- [Controlled agent execution](controlled-agent-execution.md)
- [Security and permissions](security-and-permissions.md)
