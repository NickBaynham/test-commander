# Requirements Quality Review — Methodology

The rubric `/tc:review-requirements` applies to every parsed `REQ-NNN` entry. Sixteen dimensions, each with a deterministic mechanical check shipped in `review_requirements.py` and a narrative judgment layer Claude is expected to add when summarizing the helper's findings for a human reviewer.

This doc is the contract: every dimension has at least one seeded defect in `tests/fixtures/seeded-flawed-requirements/requirements.md` and at least one mechanical check the helper performs. The seeded fixture is the test contract; this doc explains the *why* alongside the *what*.

The dimensions below cover **requirement-level** concerns. The AC-specific rubric (`ac-missing-edge-cases`, `ac-missing-negative-cases`, `ac-untestable-predicate`, `ac-ambiguous-data-rule`, `ac-missing-role-context`) belongs to `/tc:review-acceptance-criteria` and is documented in [`acceptance-criteria-quality.md`](acceptance-criteria-quality.md).

## Universal cores and project extensions

Test Commander ships only universal English and software-engineering vocabulary (per Decision D19 in `planning/plan.md`). Three dimensions accept domain-vocabulary extensions through `<workspace>/config.yaml`:

| Dimension | Extension key |
| --- | --- |
| `data-rules` | `tc-requirements.data-rules.sensitive-keywords` |
| `risk` | `tc-requirements.risk.compliance-keywords` |
| `roles-permissions` | `tc-requirements.roles-permissions.permission-verbs` and `role-qualifiers` |

The helper unions defaults with project extensions at runtime; extensions never replace defaults. Consumers extend the configuration for their domain (PCI, HIPAA, internal roles, etc.). See [`docs/user-guide/customizing-for-your-project.md`](../../../../../docs/user-guide/customizing-for-your-project.md).

---

## The 16 dimensions

### clarity

**Definition.** The requirement uses vague-marketing language that conveys no concrete behavior.

**Mechanical check.** Body contains any buzzword from `{robust, seamless, modern, best-of-breed, world-class, leverage}` (case-insensitive, word-boundary match).

**Worked example.** `REQ-001`: *"The system shall provide a robust and seamless user experience leveraging modern best-of-breed paradigms."* — three hits (`robust`, `seamless`, `leverage`).

**Claude judgment layer.** Translate the flagged buzzwords into the specific behavior or quality attribute the author probably intended; if no such intent can be reconstructed, recommend the requirement be rewritten or split.

### testability

**Definition.** The requirement cannot be objectively verified as met or not.

**Mechanical check.** Body contains a vague predicate from `{user-friendly, easy, intuitive, fast, slow}` without a numeric threshold nearby, **or** the body lacks any RFC-2119 modal (`shall`, `must`, `should`).

**Worked example.** `REQ-002`: *"The system shall be user-friendly."* — has `shall` (modal present) but `user-friendly` without a numeric threshold.

**Claude judgment layer.** Propose a measurable predicate (task-completion time, success rate, SUS score) that the author likely meant; flag for product-owner clarification if no measurable interpretation exists.

### completeness

**Definition.** The requirement is too short or too generic to act on.

**Mechanical check.** Body length ≤ 10 tokens (whitespace-separated), or the body specifies an action verb without naming an outcome or acceptance condition.

**Worked example.** `REQ-003`: *"The user shall be able to log in."* — 8 tokens, no outcome (with what credentials, what failure modes).

**Claude judgment layer.** Identify what the missing pieces are (preconditions, postconditions, error states, data shape) and propose a fuller rewrite; the mechanical check only flags brevity, not which dimensions of completeness are missing.

### consistency

**Definition.** Two or more requirements assert mutually-exclusive constraints over the same subject.

**Mechanical check.** Cross-requirement: any pair sharing at least one substantive noun (3+ chars, non-stopword) where one uses a permission modal (`may`, `can`) and the other uses an obligation modal (`shall`, `must`, `require`, `requires`).

**Worked example.** `REQ-004` (*"Anonymous users may access the API without authentication."*) vs `REQ-005` (*"All API access requires an authenticated user account."*) — shared subjects `api`, `access`; opposing modals `may` vs `requires`. Generates an open question naming both REQ-IDs.

**Claude judgment layer.** Determine which requirement is authoritative (often the obligation), surface the conflict to the product owner, and propose a resolution. The mechanical pair-detection has false positives — Claude filters to genuine semantic conflicts.

### atomicity

**Definition.** A single requirement bundles multiple distinct requirements.

**Mechanical check.** Body joins ≥ 3 items in a comma-list ending in `and`/`or`, or two or more `and`-joined verb phrases.

**Worked example.** `REQ-006`: *"The system shall allow users to register an account, configure preferences, view reports, schedule jobs, and export data."* — 5 items in a comma-list ending in `and`.

**Claude judgment layer.** Split the bundle into independent REQs, preserving the original ID as the umbrella and assigning sub-IDs (e.g. `REQ-006.1`, `REQ-006.2`). The mechanical check catches comma-lists; Claude catches semantic atomicity violations where the grammar disguises the bundling.

### measurability

**Definition.** The requirement uses qualitative quantifiers without numeric thresholds.

**Mechanical check.** Body contains a qualitative quantifier from `{quickly, fast, many, few, often, soon, slow, rapidly}` without a numeric token (digit run, optional unit/percent) within ±1 sentence.

**Worked example.** `REQ-007`: *"The search shall return results quickly."* — `quickly` without a number.

**Claude judgment layer.** Propose a numeric SLO (p95 latency, throughput, count thresholds) appropriate to the product surface; flag for refinement when the right number depends on data not yet available.

### ac-quality

**Definition.** The requirement references acceptance criteria but no AC pointer exists in scope.

**Mechanical check.** Body matches `\bacceptance criteria\b` but contains no `AC-\d+` pointer.

**Worked example.** `REQ-008`: *"The notification engine shall surface relevant updates for each user. See acceptance criteria below..."* — references AC but no `AC-NNN` link.

**Claude judgment layer.** Identify whether ACs exist elsewhere (linked via a separate doc, owned by another team) and either link them in or flag as missing for the AC review step (`/tc:review-acceptance-criteria`).

### edge-cases

**Definition.** A behavior-defining requirement does not specify edge-case handling.

**Mechanical check.** Body contains an action modal (`shall`/`must`/`should`/`may`/`can`) but no edge keyword from `{except, unless, otherwise, edge}`.

**Worked example.** `REQ-009`: *"When a user submits a form, the system shall process the input and confirm acceptance."* — has `shall`, no edge keyword.

**Claude judgment layer.** Identify the realistic edge cases for the requirement's domain (expired sessions, locked records, partial input) and propose them explicitly. The mechanical check over-flags by design; Claude narrows to material gaps.

### negative-cases

**Definition.** A behavior-defining requirement does not specify failure paths.

**Mechanical check.** Body contains an action modal but no failure keyword from `{invalid, error, fail, missing, declined, rejected, denied}`.

**Worked example.** `REQ-010`: *"Users can apply filters to the report view to narrow the results."* — no failure-path coverage.

**Claude judgment layer.** Identify what can go wrong (invalid input, missing resource, permission denied, server failure, network drop) and propose the expected behavior for each. Again, over-flags by design; Claude narrows.

### data-rules

**Definition.** The requirement references sensitive data without naming a constraint on its handling.

**Mechanical check.** Body references a sensitive-data keyword from the universal core `{password, secret, token, credential, key}` (plus project extensions) without a constraint keyword from `{length, format, encoding, retention, hashed, encrypted, tokenized}`.

**Worked example.** `REQ-011`: *"User passwords are stored by the system."* — has `password`, no constraint.

**Claude judgment layer.** Propose the right constraint (algorithm for hashing, key-length policy, retention period, encryption at rest); call out compliance regimes (PCI, HIPAA, GDPR) if the project's `config.yaml` extension lists their keywords. The mechanical check only fires on the universal core in the shipped tool — extend `config.yaml` for domain coverage.

### roles-permissions

**Definition.** A permission-bearing requirement does not name the role authorized to perform it.

**Mechanical check.** Body uses a permission verb from the universal core `{delete, approve, reject, modify, grant, revoke}` (plus project extensions) without a role qualifier from `{admin, owner, operator}` (plus project extensions).

**Worked example.** `REQ-012`: *"Users can delete completed records."* — has `delete`, role is `Users` (not in the core set).

**Claude judgment layer.** Propose the explicit role (often a tighter authority than "users") and surface the question to the product owner if uncertain.

### nfrs

**Definition.** An NFR adjective lacks a quantitative threshold.

**Mechanical check.** Body uses an NFR adjective from `{available, secure, performant, scalable, reliable}` without a numeric threshold.

**Worked example.** `REQ-013`: *"The system shall be available for use."* — `available`, no SLO.

**Claude judgment layer.** Propose a measurable SLO (uptime %, error budget, latency p95, RPS) appropriate to the product.

### dependencies

**Definition.** A cross-reference is broken (target REQ does not exist) or a cycle exists in the dependency graph.

**Mechanical check.** Parse `REQ-\d+` references in every requirement body. For each reference whose target is not in the parsed set, emit a finding **and** an open question. For each cycle in the reference graph, emit a finding.

**Worked example.** `REQ-014`: *"The confirmation email is sent only after REQ-099 (record finalization) completes successfully. REQ-099 is referenced but does not exist in this document."* — broken reference. Generates open question.

**Claude judgment layer.** Determine whether the target REQ was renamed, removed, or never authored; restore the link or rewrite. Cycles often indicate a missing intermediate REQ.

### ambiguity

**Definition.** The requirement uses words whose interpretation varies across readers.

**Mechanical check.** Body contains an ambiguity adjective from `{reasonable, appropriate, sufficient, robust, seamless}`.

**Worked example.** `REQ-015`: *"The user session shall persist for a reasonable time."* — `reasonable`.

**Claude judgment layer.** Replace the ambiguity word with a concrete predicate (e.g. *"persist for 30 minutes of inactivity"*); cite the project's authoritative policy when one exists.

### risk

**Definition.** The requirement describes a known security or compliance anti-pattern.

**Mechanical check.** Body contains a universal security anti-pattern from `{plain text, plaintext, unencrypted, raw password, hardcoded credential, default password}` (plus project compliance extensions, e.g. PCI: `PAN`; HIPAA: `PHI`).

**Worked example.** `REQ-016`: *"The system shall store authentication credentials in plain text in the database to simplify password recovery."* — `plain text` matches the universal core.

**Claude judgment layer.** Identify the compensating control the requirement should specify (tokenization, encryption-at-rest, vault storage); escalate as a defect or compliance blocker depending on severity.

### automation-suitability

**Definition.** A subjective requirement is marked as an automation candidate.

**Mechanical check.** Body contains a subjective verb from `{feel, look, match the brand, delight, inviting}` **and** an automation marker from `{automation candidate, regression check, automated}`.

**Worked example.** `REQ-017`: *"The visual theme of every page shall match the design style guide and feel inviting to users. Marked as a candidate for automated regression checks."* — `feel`, `inviting`, `automated regression checks`.

**Claude judgment layer.** Decide whether the requirement is genuinely automatable (visual regression with golden images can cover *some* subjective concerns) or whether the test should be manual / exploratory. The mechanical check exists to surface the question, not to answer it.

---

## What the helper does NOT detect

By design, the helper does not attempt:

- Semantic understanding of what a requirement *means* — it does keyword and pattern matching only.
- Cross-document reasoning beyond REQ-ID reference graphs (story-to-AC links, code-to-requirement links — those live in `/tc:requirements-coverage` and Phase 3 knowledge ingestion).
- Severity ranking — every mechanical finding carries the same weight; Claude prioritizes.
- Resolution proposals — Claude writes the narrative review around the findings.

If a check should expand to cover a new pattern, add a defect to the seeded fixture first; the scaffold test enforces "every dimension has at least one seeded example", so the check stays grounded in reality rather than drifting into theory.
