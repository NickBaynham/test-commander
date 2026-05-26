# Public-skill evaluation pass

Phase 0 — Step 0.8. Informs the [TC-Owned Skill Catalog](../planning/plan.md) and Open Questions Q1 (non-Playwright testing scope) and Q12 (Mermaid skill).

## Source

The evaluation scans the two locally-installed Claude Code marketplaces:

- `claude-plugins-official` (Anthropic).
- `marketplace` (the user's personal marketplace).

Combined, 209 plugin entries with descriptions and categories. The scan greps for keywords per category. When no clear match is found, the entry says so explicitly. Web-search fallback is deliberately out of scope at this stage — for Phase 0 the local marketplaces are authoritative.

## Methodology

For each category we ask three questions:

1. Is there a public skill that already does this well?
2. If yes, do we adopt its prompts and patterns as a *design reference* (per Decision D1, never as a runtime dependency)?
3. If no, the plan stands: Test Commander owns the implementation.

## 1. Mermaid / diagram skill

**What it does.** A hypothetical skill that authors Mermaid Markdown given a textual description, validates Mermaid syntax, and optionally renders to SVG/PNG.

**Why interesting.** Phase 9 introduces `tc-visualize`, which produces Mermaid diagrams across flow, sequence, state, risk, coverage, traceability, test-strategy, and architecture types. A high-quality reference would shorten authoring time.

**Decision.** Pass. The catalog scan finds no dedicated Mermaid plugin. The `miro` plugin operates on an external whiteboard SaaS, not on local Mermaid Markdown. Q12 default (build `tc-visualize` ourselves) stands.

**Link.** N/A.

## 2. Devbox / sandbox skill (Coder, Daytona, Sprites.dev)

**What it does.** A hypothetical skill that provisions an ephemeral remote dev environment for browser-based development and testing.

**Why interesting.** Phase 12 introduces `tc-sandbox`, which wraps a provider abstraction so teams can launch a Test Commander environment from GitHub Actions.

**Decision.** Pass. The catalog scan finds no dedicated Coder/Daytona/Sprites.dev plugin. Q8 default (docker-compose first; stub generic and Sprites.dev adapters) stands.

**Link.** Provider docs: [coder.com](https://coder.com), [daytona.io](https://daytona.io), [sprites.dev](https://sprites.dev).

## 3. Traceability matrix

**What it does.** A hypothetical skill that maintains a requirements-to-test-results traceability matrix.

**Why interesting.** Phase 5 introduces `tc-traceability`, which produces and maintains traceability maps as a first-class artifact (requirement -> test idea -> BDD -> automation -> run -> report).

**Decision.** Pass. The catalog scan finds no dedicated traceability skill. `exploratory-to-bdd` does adjacent work (exploration -> BDD) but does not own traceability as an artifact. `tc-traceability` is novel work.

**Link.** N/A.

## 4. Accessibility testing

**What it does.** A hypothetical skill that runs axe-core, Lighthouse, or similar against a page and produces a WCAG report.

**Why interesting.** Q1 currently excludes a11y from v1. A strong reference might justify revisiting the scope.

**Decision.** Pass. The catalog scan finds no dedicated a11y skill. `liquid-skills` mentions WCAG patterns as part of a broader Shopify theme skill, not as a testing tool. Q1 default (a11y out of scope for v1) stands.

**Link.** N/A.

## 5. Performance testing

**What it does.** A hypothetical skill that drives k6, JMeter, Locust, or similar against a target and produces a load-test report.

**Why interesting.** Q1 currently excludes perf from v1. A strong reference might justify revisiting the scope.

**Decision.** Pass with a note. The catalog scan finds no dedicated load-testing skill. `chrome-devtools-mcp` records browser-side performance traces — that is observation, not load testing — and may be worth a closer look in Phase 7 or 9 if browser perf observation enters the quality report.

**Link.** `chrome-devtools-mcp` in `claude-plugins-official`.

## Summary

| Category | Decision | Plan delta |
| --- | --- | --- |
| Mermaid | Pass | None — Q12 default holds |
| Devbox / sandbox | Pass | None — Q8 default holds |
| Traceability matrix | Pass | None |
| Accessibility | Pass | None — Q1 default holds |
| Performance | Pass (note) | None — Q1 default holds; revisit chrome-devtools-mcp later |

No plan deltas. No new open questions surfaced. All five corresponding TC skills remain owned by Test Commander per Decision D1.

## Refresh trigger

Re-run this evaluation when (a) the marketplace adds a credible candidate in any of the five categories, (b) Q1 scope is revisited, or (c) Q12 default is challenged.
