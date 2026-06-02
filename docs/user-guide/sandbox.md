# Sandboxed environments

A sandbox is an on-demand, team-accessible Test Commander environment, launched
from GitHub Actions and governed exactly as the local runtime is — the
Phase-10.5 controlled execution pipeline runs inside it, so a sandbox cannot
execute above its approved permission level. Targeting is safe-by-default:
allow-listed hosts only, private network ranges blocked.

## The six commands

| Command | What it does |
| --- | --- |
| `/tc:sandbox-init` | Write `.test-commander/sandbox/config.yaml` (provider, target, allow-list, approvals). Idempotent. |
| `/tc:sandbox-launch` | Launch via the configured provider; persist state. Dry run by default (`--real` to launch for real). |
| `/tc:sandbox-status` | Report the sandbox state (`none`/`running`/`stopped`). |
| `/tc:sandbox-sync` | Push the committed workspace into the sandbox. |
| `/tc:sandbox-stop` | Tear the sandbox down. Idempotent. |
| `/tc:sandbox-export` | Write a shareable bundle (endpoints, labels, status) for a team or a PR comment. |

## Providers

The MVP default is **docker-compose-local** (Decision D15). A generic container
host and a Sprites.dev placeholder ship as refusing stubs that a consuming
project configures for its own backend.

## Safety

- **Allow-list.** Only hosts on `allowed_domains` may be targeted.
- **Private ranges blocked.** RFC 1918, loopback, and link-local addresses are
  refused while `block_private_ranges` is true.
- **Governance travels.** The Phase-10.5 pipeline runs inside the sandbox;
  approvals and the audit journal apply just as locally.
- **No real spend in tests.** CI runs as a dry run with a mocked provider; a real
  launch is refused under pytest.

Configure the target and the allow-list in `.test-commander/sandbox/config.yaml`
— see [customizing-for-your-project.md](customizing-for-your-project.md).

## See also

- [tc-sandbox skill](../../plugins/test-commander/skills/tc-sandbox/SKILL.md)
- [Security and permissions](../security-and-permissions.md)
