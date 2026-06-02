# GitHub Actions sandbox workflow

The sandbox workflow (`.github/workflows/test-commander-sandbox.yml`) launches a
Test Commander sandbox against a target application from CI, then tears it down.

## Trigger

**Manual dispatch only** (`workflow_dispatch`). There is no `push` or
`pull_request` trigger, so the workflow never runs — or spends — unless an
operator explicitly starts it. `dry_run` defaults to `true`.

Inputs:

| Input | Default | Meaning |
| --- | --- | --- |
| `target_url` | (required) | The application under test (must be on the allow-list). |
| `allowed_domains` | `example.com,*.example.com` | Comma-separated allow-list of hostnames. |
| `provider` | `docker-compose` | The sandbox provider. |
| `dry_run` | `true` | Plan only; do not spend real cloud. |

## Sequence

The `sandbox` job runs, in order:

1. **Safety check** — `sandbox/safety.check_target` refuses the run if the target
   is not on the allow-list or is a private/loopback/link-local address.
2. **Build sandbox image** — provision the environment via the provider.
3. **Publish endpoints** — surface the sandbox endpoints (for a PR comment).
4. **Teardown sandbox** — `if: always()`, so the environment is cleaned up even
   if an earlier step fails.

## Injection safety

Workflow inputs are passed through a job-level `env:` block and referenced as
shell variables (`$TARGET_URL`), never interpolated into `run:` directly. This
is the injection-safe pattern — untrusted input never lands in a shell command
unescaped.

## Secrets

Provider credentials (Anthropic API tokens, cloud creds) are GitHub Actions
**secrets**, injected as environment variables only into the jobs that need them.
They are never written to the workspace, never echoed, and never exposed to the
frontend.

## MVP note

The build/publish/teardown steps are demonstrative placeholders in the MVP (see
[sandboxed-environments.md](sandboxed-environments.md#mvp-limitations-honest));
the provider lifecycle, the safety guards, and in-sandbox governance are fully
tested in Python with a mocked provider.

## See also

- [Sandboxed environments](sandboxed-environments.md)
- [Sandbox user guide](user-guide/sandbox.md)
