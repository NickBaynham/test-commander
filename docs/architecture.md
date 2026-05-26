# Architecture

Test Commander has three layers.

1. **The plugin.** A Claude Code plugin at `plugins/test-commander/` containing the skills that orchestrate every phase of work. Each skill is independently loadable and owned in-repo.
2. **The workspace.** A `.test-commander/` directory inside each consuming project. Every quality artifact — requirements reviews, exploration notes, BDD specs, automation plans, evidence, learning, reports — lives here and is committed to git.
3. **The runtime.** A small Python and TypeScript runtime that arrives lazily: Playwright in Phase 6, web and API in Phase 10, MCP server in Phase 11.

The plugin is authored first. The runtime arrives when commands need it.

The repo is also a self-contained Claude Code marketplace, declared by `.claude-plugin/marketplace.json` at the root. `make install` registers it locally and installs the plugin.

> This document grows as each phase lands. Phase 0 establishes the plugin scaffold. Later phases fill in the runtime layer.
