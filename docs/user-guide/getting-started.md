# Getting Started

This guide takes you from a fresh clone to a working Test Commander plugin loaded in Claude Code.

## Prerequisites

See [../install.md](../install.md) for the full prerequisite list and per-platform notes.

## Steps

1. **Clone the repository.**

   ```sh
   git clone https://github.com/NickBaynham/test-commander.git
   cd test-commander
   ```

2. **Bootstrap your environment.**

   ```sh
   ./bootstrap.sh
   ```

   The script checks `make`, Python 3.12, PDM, Docker, and Git. It auto-installs the safe ones. For anything questionable, it prints a suggested install list and exits — install those manually, then re-run.

3. **Install the project.**

   ```sh
   make install
   ```

   This installs Python dependencies, registers this repo as a local Claude Code marketplace, installs the `test-commander` plugin, and verifies the installed skills.

4. **Confirm the plugin loaded.**

   Open Claude Code. Look for `test-commander:tc-core` in your available skills. If it appears, Phase 0 is verified.

## What's next

- Phase 1 ships `/tc:init`, which creates a `.test-commander/` workspace inside your consuming project. Until then, the plugin is loaded but its commands are not yet implemented.
- Watch [../../CHANGELOG.md](../../CHANGELOG.md) for phase progress.

## If something goes wrong

See the troubleshooting section in [../install.md](../install.md). File issues with a clear repro on GitHub. Track in-flight items under [../../TODO.md](../../TODO.md).
