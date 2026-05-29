---
name: tc-bdd
description: BDD generation and review commands for Test Commander. Use when the user runs /tc:generate-bdd or /tc:review-bdd, or asks about turning reviewed requirements and Phase-4-enriched test ideas into Gherkin feature files, writing scenarios with behavior-not-UI steps, tagging scenarios with universal classes and project namespaces, or reviewing BDD specs for ambiguity and traceability. Owns the two commands that generate .feature files carrying machine-readable @req and @cs linkage tags and review them against a deterministic quality rubric, plus the internal review sub-mode that auto-runs at the end of generation.
---

# tc-bdd

The BDD-generation skill for Test Commander. Owns the two commands that turn Phase-2 reviewed requirements and Phase-4-enriched test-idea seeds into Gherkin `.feature` files with full traceability, then review those specs against a deterministic quality rubric.

Each command is implemented as a Python helper script bundled inside the plugin (per Decision D18). The per-command pages under `commands/` are the authoritative behavior spec — link the user there for full detail.

## Status

Phase 5 in progress. Both `tc-bdd` commands are end-to-end runnable:

- `/tc:generate-bdd` — **shipped (Step 5.2).** Auto-runs the internal BDD review sub-mode at the end of generation (suppressible with `--no-review`).
- `/tc:review-bdd` — **shipped (Step 5.3).** Standalone, re-runnable review of already-written `.feature` files; shares one implementation (`review_features()`) with the generate-time review sub-mode.

Each sub-step ships the helper, methodology, template(s), and per-command page in a single commit, then updates this SKILL.md to describe the now-shipped behavior and remove the deferral wording for that command.

## Commands

### `/tc:generate-bdd`

Reads the Phase-4-enriched test-idea seeds under `<workspace>/test-ideas/` (the `## Phase 4 enrichment` candidate bullets are the scenario source) and writes Gherkin `.feature` files under `<workspace>/bdd/features/`. One `Scenario` per Phase-4 candidate (`CS-NNN-NNN`), each carrying machine-readable linkage tags (`@req:REQ-NNN`, `@cs:CS-NNN-NNN`, plus `@anomaly:<category>` when anomaly-derived), a universal class tag mapped from the candidate type (`happy`/`positive` → `@smoke`; `edge`/`negative` → `@regression`), and an `@area:` namespace tag derived from the requirement title — so `/tc:traceability-map` can rebuild the trace map mechanically. Also writes a per-feature summary under `<workspace>/bdd/summaries/` and rebuilds `<workspace>/bdd/index.md`. Deterministic and byte-stable (overwrite mode). The helper emits a refinable scaffold; Claude rewrites the Given/When/Then into domain-grounded steps, promotes data-driven scenarios to `Scenario Outline`, and adds `@risk:`/`@persona:` values, per the methodology. Projects union extra class tags via `tc-bdd.tags.extra-classes` in `<workspace>/config.yaml`.

**Run:**

```sh
python3 <plugin-root>/scripts/generate_bdd.py <project-root> [--req REQ-NNN]
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2) and the absence of any enriched test-idea seed (exit 2; the precondition error directs the user at `/tc:test-ideas`). After generation it auto-runs the BDD review sub-mode (the same implementation `/tc:review-bdd` uses), updating each feature's summary verdict and routing any findings to `requirements/open-questions.md`; pass `--no-review` to suppress it.

Full spec: [commands/generate-bdd.md](commands/generate-bdd.md). Methodology: [methodology/bdd-generation.md](methodology/bdd-generation.md).

### `/tc:review-bdd`

Reads `<workspace>/bdd/features/*.feature` and runs the six-category universal review rubric (`ambiguous-step`, `missing-tag`, `untraceable`, `ui-coupled-step`, `missing-examples`, `conjunction-overload`), one finding per category per scenario. Writes a verdict into each feature's `<workspace>/bdd/summaries/<area>.md` (`pass` or `N finding(s) - categories: ...`) and routes failures to `<workspace>/requirements/open-questions.md` as `[bdd-review]` gap signals (per-area source-id `tc-bdd/bdd-review-<area>`, Phase-2 dedup contract). A clean generated feature passes with zero findings; re-running is idempotent. The shared `review_features()` implementation is the same code path `/tc:generate-bdd` auto-runs. Project-specific vague/UI tokens union via `tc-bdd.review.rubric-extensions` in `<workspace>/config.yaml`.

**Run:**

```sh
python3 <plugin-root>/scripts/review_bdd.py <project-root>
```

`<project-root>` defaults to the current working directory. Refuses uninitialized workspaces (exit 2) and the absence of any `.feature` file (exit 2; the precondition error directs the user at `/tc:generate-bdd`).

Full spec: [commands/review-bdd.md](commands/review-bdd.md). Methodology: [methodology/bdd-quality-review.md](methodology/bdd-quality-review.md).

## Finding the helpers

The helpers live at `scripts/<name>.py` relative to this plugin's root (the directory containing this SKILL.md is `<plugin-root>/skills/tc-bdd/`). In a development checkout that is `<repo>/plugins/test-commander/scripts/`. In the installed plugin cache it is `~/.claude/plugins/cache/test-commander-marketplace/test-commander/<version>/scripts/`. Either way, resolve the helper path relative to this SKILL.md's own location.

## See also

- [Plugin README](../../README.md)
- [Phased plan](../../../../planning/plan.md)
- [Workspace reference](../../../../docs/workspace-reference.md)
- [Command reference](../../../../docs/command-reference.md)
- [tc-traceability skill](../tc-traceability/SKILL.md)
- [tc-explore skill](../tc-explore/SKILL.md)
