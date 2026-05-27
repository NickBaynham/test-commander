# Learning from documents

The methodology for `/tc:learn-from-docs` (Phase 3 Step 3.2). Sits underneath the umbrella [`project-knowledge.md`](project-knowledge.md).

## What this command consumes

Every `*.md` file under `<workspace>/documents/uploaded/` whose body does **not** contain any `REQ-\d+` token. The inverse filter is intentional: requirement documents are handled by `/tc:review-requirements` (Phase 2); narrative product docs (overviews, READMEs, design notes, glossaries, journey walkthroughs) are this command's territory.

## Universal-core extraction rules

Seven dimensions, all matched against the universal-core English heading and keyword sets. Domain extensions (per D19) come from `<workspace>/config.yaml` under `tc-knowledge.documents:`.

### `entities`

Mechanical check: capitalized noun phrases under a Markdown heading whose text contains any of `entit`, `model`, `noun`, `glossary` (case-insensitive). Two shapes are recognized:

- Bullets with a bolded leading entity name: `- **Account** - registered user account.`
- Table rows whose first column is a single capitalized noun phrase.

Extension hook: `tc-knowledge.documents.entity-keywords` adds domain entity names (case-sensitive) that the helper will also flag wherever they appear in prose - even when they fall outside an entity-tokened heading.

**Worked example** (seeded fixture - `tests/fixtures/seeded-sample-project/documents/product-overview.md`):

```markdown
## Entities

- **Account** - a registered user.
- **Session** - an authenticated session token.
- **Workspace** - a named container an account owns.
```

The helper extracts five entities (`Account`, `Session`, `Workspace`, `Asset`, `Permission`) with `<path>:<line>` provenance pointing at each bullet's source line.

**Claude judgment layer:** decide whether an extracted name is a domain entity (a thing the system models) or an attribute of an existing entity. The helper cannot tell that "Session expires_at" is an attribute of Session, not a separate entity; Claude does.

### `terms`

Mechanical check: Markdown definition-list shape (`Term\n: definition`) anywhere in the document, or table rows under a heading containing `glossary` / `terminology` (case-insensitive).

**Worked example** (seeded fixture - `documents/glossary.md`):

```markdown
Account
: A registered user of the platform.

Session
: A short-lived authenticated context bound to a single account.
```

The helper captures each `(term, definition)` pair with `<path>:<line>` provenance pointing at the term line.

**Claude judgment layer:** identify when a term is a synonym of an entity already extracted (the Glossary's `Account` is the entity bullet's `Account`) and avoid double-counting. Also: surface terms that need disambiguation (the document defines `Permission` as a relation; the code may use `Permission` to mean an enum value).

### `user-journeys`

Mechanical check: any heading containing `journey`, `flow`, `walkthrough`, `scenario` (or any extension token). The helper scans the journey heading's section (including all deeper child headings up to the next same-or-shallower-level heading) for numbered or bulleted lists and captures every list item as a journey step.

Extension hook: `tc-knowledge.documents.journey-headings` adds additional heading tokens. A consuming project that uses `story` headings can extend with `journey-headings: [story]`.

**Worked example** (seeded fixture - `documents/user-journey-sign-in.md`):

```markdown
# User journey - sign in and open a workspace

## Steps

1. The user navigates to the sign-in page.
2. The user submits an account identifier and a one-time code.
...
```

The helper captures the journey title, the seven ordered steps, and the line range. The journey heading is at H1 but the steps live under the H2 `## Steps`; the same-or-shallower-level termination keeps the steps in scope.

**Claude judgment layer:** name the journey clearly (the heading may be terse), rank journeys by how much of the system surface they exercise, and flag missing journeys (a critical surface with no walkthrough is worth raising as an open question).

### `business-rules`

Mechanical check: any line containing an RFC-2119 modal (`must`, `shall`, `should`, `may`) that is **not** inside a journey section's range. Lines whose first non-whitespace character is `#`, `|`, `>`, or `:` are excluded (those are headings, table rows, blockquotes, and definition-list value markers).

**Worked example** (seeded fixture - `documents/product-overview.md`):

```markdown
- A session must be active before any workspace endpoint may be called.
- An asset must be smaller than 10 MB.
- A workspace must have at least one owner at all times.
```

The helper captures three rules with their modal (`must`), a subject anchor (the last substantive word before the modal - `session`, `asset`, `workspace`), and `<path>:<line>` provenance.

**Claude judgment layer:** translate the rule into a testable predicate where possible (the asset-size rule becomes `assert upload(>10MB) is rejected`), rank rules by user-visible impact, and surface rules that imply unstated constraints (the workspace-owner rule implies an "ownership transfer" path that may not be documented).

### `assumptions`

Mechanical check: lines containing any of the assumption markers `assume`, `expected`, `presumed`, `likely`, where the line is not a heading / table row / blockquote / definition value.

**Worked example** (seeded fixture - the closing paragraph of `documents/product-overview.md`):

```markdown
The narrative assumes that every account verifies its email before signing in
for the first time, but no document confirms how that verification flow works.
```

The helper captures the assumption with `no direct citation` flagging.

**Claude judgment layer:** distinguish a useful assumption (one that constrains design) from a throwaway one (a parenthetical caveat). Flag assumptions that the project teams should convert into either a requirement or a confirmed-fact citation.

## Gap signals

Two gap signals are detected and routed to `<workspace>/requirements/open-questions.md`.

### `undefined-term`

A capitalized noun phrase that:

- appears in two or more distinct documents, **and** is never the subject of a glossary or definition-list entry; OR
- is bolded (`**Term**`) in prose somewhere in the corpus, but is never the subject of a glossary or definition-list entry.

Either path emits one open question per term, deduplicated by `(source-id, question-text)`.

### `contradictory-rule`

Two business rules sharing a subject anchor where one carries a negation marker (`not`, `never`, `without`) and the other does not. Reuses the same "subject + opposing modal" shape Phase 2's `consistency` check uses on requirements.

## Idempotency contract

Re-running `/tc:learn-from-docs` against unchanged input produces:

- byte-identical `documentation-model.md` (pure generated report);
- byte-identical `## From documents` section bodies in every cross-cutting artifact (other sources' sections are untouched);
- no new lines in `open-questions.md` (the dedup key is `(source-id, question-text)`);
- a byte-identical `system-model.md` regenerated by `synthesize_system_model.py`.

## See also

- [Umbrella methodology](project-knowledge.md)
- [Per-command page](../commands/learn-from-docs.md)
- [Output template](../templates/documentation-model-template.md)
- [Customizing extensions](../../../../../docs/user-guide/customizing-for-your-project.md)
