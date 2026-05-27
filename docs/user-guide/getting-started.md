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

   The script checks `make`, Python 3.12, PDM, Docker, and Git. It auto-installs the safe ones. For anything questionable, it prints a suggested install list and exits — install those manually, then re-run. All output is prefixed with `[bootstrap]`. Run `./bootstrap.sh --help` for the auto-install policy.

3. **Install the project.**

   ```sh
   make install
   ```

   This installs Python dependencies, validates the manifests, registers this repo as a local Claude Code marketplace, installs the `test-commander` plugin, and verifies the installed skills. Re-running `make install` is safe — each step skips when there is nothing to change. To remove everything later, run `make uninstall`.

4. **Confirm the plugin loaded.**

   Open Claude Code. Look for `test-commander:tc-core` in your available skills. If it appears, Phase 0 is verified.

## What's next

- Phase 1 commands are available: `/tc:init`, `/tc:status`, `/tc:journal`, `/tc:next`. See [workflow.md](workflow.md) for the first end-to-end walkthrough against a consuming project.
- Phase 2 commands are available: `/tc:review-requirements`, `/tc:review-user-stories`, `/tc:review-acceptance-criteria`, `/tc:requirements-coverage`, `/tc:requirements-to-tests`. See [reviewing-requirements.md](reviewing-requirements.md) for the Phase 2 walkthrough — upload your requirements documents to `.test-commander/documents/uploaded/` and run the review chain.
- Test Commander is a generic, product-domain-agnostic tool. To extend it for your project's domain (PCI/HIPAA vocabulary, your role taxonomy, your risk classes, etc.), see [customizing-for-your-project.md](customizing-for-your-project.md). The universal core works out of the box; extensions are opt-in per project.
- Watch [../../CHANGELOG.md](../../CHANGELOG.md) for phase progress.

## If something goes wrong

See the troubleshooting section in [../install.md](../install.md). File issues with a clear repro on GitHub. Track in-flight items under [../../TODO.md](../../TODO.md).
