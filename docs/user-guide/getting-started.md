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
- Phase 3 commands are available: `/tc:learn-from-docs`, `/tc:learn-from-specs`, `/tc:learn-from-code`, `/tc:learn-from-api`, `/tc:learn-from-tests`. See [building-project-knowledge.md](building-project-knowledge.md) for the Phase 3 walkthrough — upload narrative docs, OpenAPI/Postman specs, Python source, recorded API responses, and existing tests to `.test-commander/documents/uploaded/` and run the five learn helpers in any order.
- Phase 4 commands are available: `/tc:create-charter`, `/tc:explore` (with the internal exploration-review sub-mode), `/tc:session-summary`, `/tc:test-ideas`. See [exploring-an-app.md](exploring-an-app.md) for the Phase 4 walkthrough — scope an exploration session against your Phase-3 product-knowledge, replay a recorded Playwright MCP session, synthesize the session summary, and enrich the Phase-2 test-idea seeds with session-derived candidate scenarios.
- Phase 5 commands are available: `/tc:generate-bdd` (with the internal review sub-mode), `/tc:review-bdd`, `/tc:traceability-map`. See [generating-bdd.md](generating-bdd.md) for the Phase 5 walkthrough — turn the enriched test-ideas into traceable Gherkin `.feature` files, review them against the universal quality rubric, and rebuild the requirements and test traceability maps.
- Phase 6 commands are available: `/tc:build-framework`, `/tc:automation-plan`, `/tc:automate` (with the internal automation-review sub-mode), `/tc:review-automation`, `/tc:generate-test-data`. See [automation.md](automation.md) for the Phase 6 walkthrough — build the Playwright framework lazily, score scenarios for automation suitability, generate traceable TypeScript specs with fixture-mediated data, review them against the universal rubric, and populate the test-data tree.
- Test Commander is a generic, product-domain-agnostic tool. To extend it for your project's domain (PCI/HIPAA vocabulary, your role taxonomy, your risk classes, etc.), see [customizing-for-your-project.md](customizing-for-your-project.md). The universal core works out of the box; extensions are opt-in per project.
- Watch [../../CHANGELOG.md](../../CHANGELOG.md) for phase progress.

## If something goes wrong

See the troubleshooting section in [../install.md](../install.md). File issues with a clear repro on GitHub. Track in-flight items under [../../TODO.md](../../TODO.md).
