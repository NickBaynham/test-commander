# Acceptance Criteria Quality — Methodology

The rubric `/tc:review-acceptance-criteria` applies to every parsed `AC-NNN[-NN]` entry. Six dimensions: five AC-specific quality checks plus an `orphan` check that flags any AC whose parent user story is not in scope.

The seeded fixture at `tests/fixtures/seeded-flawed-requirements/acceptance-criteria.md` has one defect per AC-specific dimension, tagged with an inline `<!-- defect: ac-<dimension> -->` comment. The fixture is the test contract; this doc explains the *why* alongside the *what*.

## What an acceptance criterion is

A Test Commander acceptance criterion uses the canonical Given/When/Then shape:

> **Given** `<precondition>`, **When** `<action>`, **Then** `<outcome>`.

The ID convention is `AC-NNN-NN` where the first `NNN` matches a parent user story `US-NNN`. AC IDs without a second segment (`AC-NNN`) are accepted as standalone but should remain rare; the two-segment form makes the parent explicit.

The mechanical checks operate on the **canonical AC body only**. Parenthetical asides (`"(Happy path only — no coverage of edge cases.)"`) are stripped before the checks run, because such asides typically explain *why* the AC is incomplete and would otherwise satisfy the keyword checks they describe. The display version in the review file preserves the original body.

## What disqualifies an AC from being automatable

An AC is *not automatable* if any of the following hold:

- The "Then" clause uses subjective experience words (`feel`, `intuitive`, `snappy`).
- The "Then" clause uses vague predicates (`responsive`, `fast`) without a numeric threshold.
- The "Given" or "Then" clause uses ambiguity adjectives (`appropriately`, `as needed`, `sufficiently`).
- The behavior depends on a role that is not named (you cannot construct the test subject).
- The AC is orphaned — no parent user story exists to provide context.

The mechanical checks below catch each.

## Dimensions

### `ac-missing-edge-cases`

**Definition.** The AC describes a behavior path without acknowledging any edge condition.

**Mechanical check.** Body contains Given/When/Then and lacks any edge keyword from `{except, unless, otherwise, edge}`.

**Worked example.** `AC-001-01`: *"Given a user with at least one record in their view, When they click 'Open' and confirm the prompt, Then the record is shown and a confirmation banner appears."* — happy path only; no edge handling described.

**Claude judgment layer.** Propose the realistic edge cases for the AC's domain — expired records, locked records, stale data, concurrent edits — and recommend new ACs (e.g. `AC-001-02`, `AC-001-03`) that cover them. A single AC rarely covers all relevant edges; the check exists to surface the gap.

### `ac-missing-negative-cases`

**Definition.** The AC describes a success path without specifying a failure path.

**Mechanical check.** Body contains Given/When/Then and lacks any failure keyword from `{invalid, error, fail, missing, declined, rejected, denied, expired, locked}`.

**Worked example.** `AC-001-02`: *"Given a logged-in user at the form page, When they submit the form, Then the request is processed successfully."* — no failure path.

**Claude judgment layer.** List the failure modes that matter (validation failure, server error, network drop, permission denied, rate limit) and propose ACs for each. As with edge cases, the check exists to surface the gap; coverage is a judgment call shaped by risk.

### `ac-untestable-predicate`

**Definition.** The AC uses experience or quality words that cannot be verified by a test.

**Mechanical check.** Body contains a subjective-experience word from `{feel, snappy, smooth, fluid, intuitive, delightful, enjoyable, satisfying, pleasing}`, **or** a vague predicate from `{responsive, fast, slow, quick}` without a numeric threshold (digit run + optional unit).

**Worked example.** `AC-002-01`: *"Given the user is on the home page, When they scroll the page, Then the page should feel responsive and snappy."* — `feel`, `responsive`, `snappy`.

**Claude judgment layer.** Translate experience into measurable proxies (p95 frame-render time < 16ms, perceived-input-delay < 100ms, no jank under N-event load) and rewrite the Then-clause. If measurable proxies are not yet known, route the AC to a UX-research charter or performance-spike work item before reviewing it for test.

### `ac-ambiguous-data-rule`

**Definition.** The AC describes data handling using words that hide the actual rule.

**Mechanical check.** Body contains any ambiguity word from `{appropriately, as needed, suitable, sufficient, sufficiently, properly, accordingly, reasonable, appropriate}`.

**Worked example.** `AC-003-01`: *"Given the user enters their email address during sign-up, When they submit the form, Then the system processes the email appropriately and stores it as needed."* — `appropriately`, `as needed`.

**Claude judgment layer.** Pin down each ambiguity word to a concrete rule (format requirements, storage layout, duplicate handling, retention period). If multiple rules might apply, write multiple ACs. Use the consuming project's domain vocabulary from `<workspace>/config.yaml` (e.g., HIPAA `PHI` handling, PCI `PAN` storage) when the AC touches sensitive data.

### `ac-missing-role-context`

**Definition.** The AC describes a permission-bearing action without naming the role authorized to take it.

**Mechanical check.** Body contains a permission verb from the universal core `{delete, remove, approve, reject, modify, grant, revoke, issue, publish}` and lacks any role qualifier from `{admin, owner, operator}` (the universal core from Decision D19; extend per project via `<workspace>/config.yaml`).

**Worked example.** `AC-004-01`: *"Given an active session, When the delete button is clicked on a completed record, Then the record is removed."* — `delete` verb, no role qualifier in the canonical body.

**Claude judgment layer.** Surface the role question to the product owner. If multiple roles can take the action (e.g. both `admin` and `operator`), write distinct ACs per role, or one AC that explicitly names all permitted roles. Reference the project's `roles-permissions` config extensions when the answer depends on domain roles.

### `orphan`

**Definition.** The AC's parent user story (derived from the AC ID prefix) is not among the parsed user stories.

**Mechanical check.** `AC-NNN-NN` implies parent `US-NNN`. If no Markdown file under `documents/uploaded/` declares `US-NNN`, the AC is orphaned.

**Worked example.** A synthetic `AC-999-01` with no `US-999` in scope.

**Claude judgment layer.** Either the user story exists but was not uploaded (point the team at it), or the story was renamed (update the AC ID), or the AC was authored speculatively (route to product backlog for confirmation). Orphaned ACs cannot be linked back into the traceability map until resolved.

## What the helper does NOT detect

- AC duplication (two ACs covering the same scenario).
- ACs that contradict the parent user story.
- ACs that depend on missing data not yet defined elsewhere.
- The semantic quality of the Given/When/Then prose beyond keyword presence.

These belong to Claude's narrative review layer or to later phases (`/tc:requirements-coverage` for traceability gaps, `/tc:requirements-to-tests` for downstream test generation).

Domain-specific vocabulary (PCI compliance, HIPAA terms, your role taxonomy) feeds the rubric through `<workspace>/config.yaml` extensions for the `roles-permissions` dimension. The AC checks themselves are universal; project extensions sharpen the role-qualifier set.

## See also

- [`commands/review-acceptance-criteria.md`](../commands/review-acceptance-criteria.md) — command surface.
- [`requirements-quality-review.md`](requirements-quality-review.md) — the parallel requirement-level rubric.
- [`user-story-readiness.md`](user-story-readiness.md) — INVEST rubric (parent stories).
- [Customizing for your project](../../../../../docs/user-guide/customizing-for-your-project.md) — config.yaml extension model.
