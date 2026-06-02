# Sandbox safety methodology

Sandboxing never relaxes governance. Two layers protect a sandbox: the Phase-10.5
controlled execution pipeline (which runs *inside* the sandbox), and the
safe-by-default targeting guards (which decide what the sandbox may point at).

## Governance travels with the sandbox

The controlled execution pipeline runs in the sandbox exactly as it does locally:
every request is routed, planned, permission-checked, approved where required,
validated, and audited. A sandbox cannot execute above its approved permission
level. Provider credentials (Anthropic API tokens, cloud creds) are server-side
secrets, never exposed to the frontend, and scoped only to the runtime jobs that
need them.

## Safe-by-default targeting

- **Allow-listed domains only.** A target whose host is not on the configured
  allow-list is refused.
- **Private network ranges blocked.** RFC 1918 (10/8, 172.16/12, 192.168/16),
  loopback (127/8), and link-local (169.254/16) are refused by default, so a
  sandbox cannot be aimed at an internal network.
- **Approvals.** External-network and destructive actions require approval (the
  same approval gate the local runtime uses).
- **Clear labels.** Every sandbox carries an explicit, visible environment label
  so an ephemeral environment is never mistaken for production.

CI exercises all of this as a dry run with a mocked provider — no real spend.

(Behavior shipped in Step 12.4; this methodology page is the scaffold spec.)
