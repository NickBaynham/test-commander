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

`bootstrap.sh` is idempotent — re-running is a no-op when everything is already present. It never modifies `PATH` and never writes a `make` shim.

`make install` is also idempotent. It:

1. Runs `pdm install` for project Python dependencies.
2. Registers this repo as a local Claude Code marketplace.
3. Installs the `test-commander` plugin.
4. Runs `scripts/verify_skills.py` to confirm all expected skills are present and well-formed.

## Verifying the install

After `make install`, open Claude Code. The `test-commander:tc-core` skill should appear in available skills. Once Phase 1 ships, run `/tc:init` to confirm the workspace bootstraps in your consuming project.

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

> Filled out as install issues surface. Track them under [../TODO.md](../TODO.md) and reference fixes in [../CHANGELOG.md](../CHANGELOG.md).
