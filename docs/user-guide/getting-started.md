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
- Phase 7 commands are available: `/tc:run` (with the internal evidence-index sub-mode), `/tc:analyze-results`, `/tc:report`, `/tc:quality-gate`. See [running-tests.md](running-tests.md) and [quality-report.md](quality-report.md) for the Phase 7 walkthroughs — run the generated suite (or ingest a recorded report), index evidence under the commit-versus-ignore policy, triage failures and flaky tests, aggregate the living quality report with a committed history, and gate release readiness against project thresholds.
- Phase 8 commands are available: `/tc:learn`, `/tc:learn-from-failures`, `/tc:learn-from-exploration`, `/tc:learn-from-feedback`, `/tc:review-lessons`, `/tc:promote-lessons`. See [learning-loop.md](learning-loop.md) for the Phase 8 walkthrough — capture candidate lessons from runs, exploration, and feedback; review them into accepted / rejected / needs-human-review; and promote accepted lessons into project guidance under a human-approval gate, without ever silently rewriting Test Commander itself.
- Phase 9 commands are available: `/tc:visualize`, the eight `/tc:diagram-*` commands, `/tc:generate-infographic`, and `/tc:render-visuals`. See [visuals.md](visuals.md) for the Phase 9 walkthrough — generate diffable Mermaid diagrams (flow, sequence, state, architecture, risk, coverage, traceability, test-strategy) and a quality infographic from your committed artifacts, each citing its sources, then render them to SVG/PNG via the Mermaid CLI.
- Phase 10 commands are available: `/tc:web-init`, `/tc:web-start`, `/tc:web-sync`, `/tc:web-index-artifacts`, `/tc:web-export`. See [web-console.md](web-console.md) for the Phase 10 walkthrough — bring up a read-only web console (Next.js + FastAPI on `make run`) that renders the workspace, live-updates over SSE, and answers questions in a read-only chat with command proposal cards. The console never changes the workspace or runs a command; execution is gated behind Phase 10.5.
- Phase 10.5 ships governance (`tc-governance`): the controlled-execution pipeline behind the console's `/api/execute` — intent → command planner → permission policy → approval gate → bounded execution → output validation → audit log. Default deny; the agent never sees the raw prompt; every executed action is audited. Configure roles and approval policy in `<workspace>/policy/permissions.yaml` and `approvals.yaml`. See [governance.md](governance.md).
- Phase 11 ships runtime integrations (`tc-mcp`): the Runtime API (`apps/api`, the `/api/runtime/` namespace) and a schema-first MCP server (`apps/mcp`: `tc_status`, `tc_plan`, `tc_run_command`) — two alternative front-ends to the same governance pipeline, with the seven permission levels enforced server-side. See [integrating.md](integrating.md).
- Test Commander is a generic, product-domain-agnostic tool. To extend it for your project's domain (PCI/HIPAA vocabulary, your role taxonomy, your risk classes, etc.), see [customizing-for-your-project.md](customizing-for-your-project.md). The universal core works out of the box; extensions are opt-in per project.
- Watch [../../CHANGELOG.md](../../CHANGELOG.md) for phase progress.

## If something goes wrong

See the troubleshooting section in [../install.md](../install.md). File issues with a clear repro on GitHub. Track in-flight items under [../../TODO.md](../../TODO.md).
