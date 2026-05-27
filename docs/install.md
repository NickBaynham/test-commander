# Install Guide

Test Commander ships as a Claude Code plugin plus a small Python and TypeScript runtime. Installing is a two-stage process.

## Platforms

| Platform | Shell | Status |
| --- | --- | --- |
| macOS | bash, zsh | Supported |
| Linux | bash | Supported |
| Windows (WSL2) | bash | Supported |
| Windows (Git Bash) | bash | Limited; install supported, full runtime requires WSL |
| Windows (PowerShell) | n/a | Not supported. Use WSL or Git Bash. |

## Prerequisites

`bootstrap.sh` verifies these before `make install` runs. It auto-installs the safe ones; for the rest it prints a suggested-install list and exits so you can choose.

| Tool | Auto-installed by bootstrap |
| --- | --- |
| `git` | Linux and WSL only (via apt) |
| `make` | Linux and WSL only (via apt) |
| Python 3.12 | No — choose pyenv, asdf, system, or Homebrew |
| PDM | Yes — installed via the official PDM installer once Python 3.12 is present |
| Docker | No — choose Docker Desktop, Colima, Rancher Desktop, or Podman with docker compatibility |

## Two-stage install

```sh
./bootstrap.sh
make install
```

`bootstrap.sh` is idempotent — re-running is a no-op when everything is already present. It never modifies `PATH` and never writes a `make` shim. Run `./bootstrap.sh --help` for the auto-install policy and usage.

All bootstrap output is prefixed with `[bootstrap]` so it is easy to recognize and grep.

`make install` is idempotent. It runs the following targets in order:

1. `pdm-install` — installs Python dependencies via PDM.
2. `validate-manifests` — schema-validates `marketplace.json` and `plugin.json` via `claude plugin validate`. Schema errors here abort before any state change.
3. `marketplace-add` — registers this repo as a Claude Code marketplace if not already registered.
4. `plugin-install` — installs `test-commander@test-commander-marketplace` if not already installed.
5. `verify-skills` — runs `scripts/verify_skills.py` to confirm all expected skills are present and well-formed.

Re-running `make install` is safe: each step detects existing state and skips if there is nothing to do.

### Uninstall

To remove the plugin and unregister the marketplace:

```sh
make uninstall
```

`make uninstall` tolerates an already-clean state — running it on a system where the plugin was never installed will not error.

## Verifying the install

After `make install`, open Claude Code. Both the `test-commander:tc-core` and `test-commander:tc-requirements` skills should appear in available skills. Run `/tc:init` (Phase 1) to bootstrap the workspace in your consuming project, then follow [user-guide/workflow.md](user-guide/workflow.md) for the Phase 1 walkthrough and [user-guide/reviewing-requirements.md](user-guide/reviewing-requirements.md) for the Phase 2 walkthrough.

## Platform notes

### macOS

You need Xcode Command Line Tools for `git` and `make`. Install with `xcode-select --install` if the bootstrap prompts you.

### Linux

`bootstrap.sh` uses `apt` for `git` and `make` on Debian and Ubuntu derivatives. For other distributions, install both manually before running.

### Windows via WSL2

Install Ubuntu under WSL2, then clone and run the install from your WSL shell. All scripts assume a POSIX shell.

### Windows via Git Bash

Git Bash does not ship with `make`. Install it separately (for example via Chocolatey) before `make install`. Runtime phases 6, 10, and 11 are not validated under Git Bash — use WSL for those.

## Troubleshooting

### `pdm: command not found` after bootstrap

The PDM installer drops the `pdm` binary in `~/.local/bin`. If that directory is not on your `PATH`, the command will not resolve.

Fix:

```sh
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc   # or ~/.bashrc
exec "$SHELL" -l
./bootstrap.sh                                            # confirms pdm is now visible
```

The bootstrap warns when this happens; if you saw `pdm installed but not on PATH`, this is the fix.

### `sudo` password prompt during bootstrap (Linux / WSL)

When `git` or `make` are missing on Linux or WSL, the script auto-installs them via `apt-get`, which requires `sudo`. The prompt is expected and not an error. If you cannot use `sudo` on the machine, install `git` and `make` manually before re-running.

### Bootstrap exited non-zero with a suggestion list

The script blocks on tools it will not auto-install (Python 3.12, Docker). Install them per the printed suggestion list, then re-run `./bootstrap.sh`. The script re-checks everything from scratch each run.

### `make install` says "already registered" or "already installed"

These are normal idempotency messages, not errors. `make install` re-runs are safe and turn into a no-op when there is nothing to change. To force a fresh install (e.g. after fixing the manifest):

```sh
make uninstall
make install
```

### `make install` aborts at `validate-manifests`

Schema validation failed before any state was changed. The CLI prints the specific field that failed. Fix the manifest, then re-run `make install`. No cleanup is needed because nothing was registered yet.

### More

> Filled out as install issues surface. Track them under [../TODO.md](../TODO.md) and reference fixes in [../CHANGELOG.md](../CHANGELOG.md).
