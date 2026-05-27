# `/tc:learn-from-docs`

The Phase 3 narrative-document ingestion command. Reads non-requirements Markdown under `<workspace>/documents/uploaded/`, extracts entities / terms / journeys / business rules / assumptions with file:line provenance, routes gap signals (`undefined-term`, `contradictory-rule`) to `<workspace>/requirements/open-questions.md`, populates the per-source model and cross-cutting artifacts under `<workspace>/product-knowledge/`, and regenerates `system-model.md` via the shared `synthesize_system_model.py` helper.

## Inputs

- `<workspace>/documents/uploaded/*.md` - every Markdown file that does **not** contain a `REQ-\d+` token. Requirements-source files are handled by `/tc:review-requirements` (Phase 2); this command's inverse filter keeps the two surfaces from overlapping. Workspace-template `README.md` placeholders at the root of `uploaded/` are ignored by name.
- `<workspace>/config.yaml` (optional) - the `tc-knowledge.documents:` block extends the universal-core extractors. Recognized keys:
  - `entity-keywords: [Patient, Provider, Claim]` - additive case-sensitive entity names; the helper surfaces each one wherever it appears in prose.
  - `journey-headings: [story, flow]` - additive heading tokens; the helper treats any heading containing any of these substrings (case-insensitive) as a journey heading.
- The current state of `<workspace>/product-knowledge/` (read-only for siblings): the helper reads the existing `## From <other-source>` sections to preserve them. No upstream artifact is required - on first run the cross-cutting files are still in their workspace-template state and the helper rewrites them from scratch.

## Outputs

| Path | Mode | Owner |
| --- | --- | --- |
| `<workspace>/product-knowledge/documentation-model.md` | overwrite | this command |
| `<workspace>/product-knowledge/entities.md` (`## From documents` section) | section-overwrite | this command |
| `<workspace>/product-knowledge/user-journeys.md` (`## From documents`) | section-overwrite | this command |
| `<workspace>/product-knowledge/business-rules.md` (`## From documents`) | section-overwrite | this command |
| `<workspace>/product-knowledge/assumptions.md` (`## From documents`) | section-overwrite | this command |
| `<workspace>/product-knowledge/system-model.md` | overwrite (synthesizer) | shared |
| `<workspace>/requirements/open-questions.md` | append, dedup by `(source-id, question)` | this command |

The helper does **not** write to `<workspace>/traceability/`. Per the Phase-2 Step-2.9 lesson, cross-source traceability is Phase 5's job; Phase 3 supplies the inputs.

## Preconditions

- `<workspace>/.test-commander/` exists (run `/tc:init` first). The helper exits non-zero with a clear error if the workspace is uninitialized.

No upstream Phase 3 helper is required - `/tc:learn-from-docs` is independent of `/tc:learn-from-specs`, `/tc:learn-from-code`, `/tc:learn-from-api`, and `/tc:learn-from-tests`. Running any subset in any order produces a valid partial synthesis.

## Behavior

1. Resolve the workspace under `<project-root>/.test-commander/`.
2. Load `tc-knowledge.documents:` extensions from `<workspace>/config.yaml`. Missing keys -> empty extension; the helper falls back to the universal core only.
3. Walk `documents/uploaded/*.md`, skipping every file containing a `REQ-\d+` token and every root-level `README.md`.
4. For each remaining file, parse headings and apply the seven universal-core extractors per the partition table in [`methodology/learning-from-documents.md`](../methodology/learning-from-documents.md). Track line numbers for provenance.
5. Run cross-document gap detection: `undefined-term` (capitalized phrase in >=2 docs not defined anywhere, plus the bolded-in-prose variant) and `contradictory-rule` (same subject anchor, opposing negation).
6. Render `documentation-model.md` (overwrite) with executive summary tables for sources / entities / terms / journeys / rules / assumptions / gap signals.
7. Render the `## From documents` section body for each cross-cutting artifact; call `update_cross_cutting()` which preserves every other source's `## From <other-source>` section and writes the file deterministically.
8. Append open questions for each gap signal, deduplicated by `(source-id, question-text)`.
9. Call `synthesize_system_model.synthesize(project_root)` to regenerate `system-model.md` from the current state of every per-source file plus every cross-cutting artifact.
10. Exit 0.

## Safety

- The helper never reads outside `<workspace>/documents/uploaded/`. No network, no shell-out, no file uploads.
- Re-running against unchanged input is byte-deterministic across every output. The `open-questions.md` dedup prevents append drift across re-runs.
- The cross-cutting section-overwrite is scoped: only the `## From documents` block is rewritten. A user-authored prelude above the first `## From <source>` heading is dropped (the file is restructured to the canonical header), but every other source's section body is preserved verbatim across re-runs.
- Per D19, no domain-specific vocabulary is baked into the shipped defaults. Consuming projects extend via `<workspace>/config.yaml`.

## Implementation

- Helper: `plugins/test-commander/scripts/extract_knowledge_from_docs.py` (~750 lines).
- Shared synthesizer: `plugins/test-commander/scripts/synthesize_system_model.py`. Lands in Step 3.2 because this is the first Phase 3 command to need it; reused unchanged by Steps 3.3-3.6.
- Tests: `tests/test_learn_from_docs.py` (26 cases - uninitialized refused, no-narrative-documents stub, requirements-source files skipped, seeded-fixture five positive dimensions + two gap signals with provenance, cross-cutting section-overwrite preserves siblings, idempotency across all outputs, `entity-keywords` and `journey-headings` extensions union with universal cores).

## Definition of Done

- Helper passes all 26 test cases against the seeded sample-project fixture.
- Synthesizer passes its standalone CLI test.
- Methodology covers all five positive dimensions plus the two gap signals with worked examples and Claude-judgment-layer paragraphs.
- Umbrella `project-knowledge.md` describes the cross-source synthesis model.
- Six templates authored.
- Per-command page complete (this file).
- `tc-knowledge/SKILL.md` describes `/tc:learn-from-docs`'s shipped behavior and the shared synthesizer; no deferral wording for this command.
- `make verify` chain green.

## See also

- [Methodology](../methodology/learning-from-documents.md)
- [Umbrella methodology](../methodology/project-knowledge.md)
- [Documentation-model template](../templates/documentation-model-template.md)
- [System-model template](../templates/system-model-template.md)
- [Customizing for your project](../../../../../docs/user-guide/customizing-for-your-project.md)
