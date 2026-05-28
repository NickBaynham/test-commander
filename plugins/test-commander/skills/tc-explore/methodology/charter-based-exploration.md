# Charter-based exploration

The per-command methodology for `/tc:create-charter` (Phase 4 Step 4.2). Sits underneath the umbrella [`exploratory-testing.md`](exploratory-testing.md).

## What this command consumes

Phase 3 product-knowledge plus Phase 2 open-questions plus the project's risk-register:

- `<workspace>/product-knowledge/entities.md` — the cross-source entity index. Auto-suggestion picks the entity with the highest mention count.
- `<workspace>/product-knowledge/user-journeys.md` — bolded journey titles contribute to the mention-count tally.
- `<workspace>/product-knowledge/system-model.md` — synthesized cross-source overview. The "Sources ingested" list is the precondition check (at least one source must be ingested).
- `<workspace>/requirements/open-questions.md` — entity mentions in the gap-signal backlog increase the entity's mention-count score, biasing the suggestion toward entities the prior phases have already flagged as risky.
- `<workspace>/risk-register/risk-register.md` — lines matching universal-core OR project-extended risk keywords (via `tc-explore.charters.risk-keywords`) surface as risk-areas in the generated charter.

If `product-knowledge/` has not been populated by Phase 3, the helper refuses with a precondition error pointing the user at `/tc:learn-from-docs`. This is the Phase 4 design-decision discipline: Phase 4 reads Phase 3 outputs and refuses to operate without them.

## Charter rubric (six dimensions)

Every charter must satisfy six rubric dimensions. The seeded [`CH-001`](../../../../../tests/fixtures/seeded-exploration-session/charter.md) is the worked example for each.

### 1. Mission specificity

A specific, testable mission is the difference between an exploration that produces actionable findings and one that produces vague notes. The mission must name (a) what the exploration intends to discover and (b) the conditions under which the discovery applies.

**Worked example (CH-001):** "Discover whether the sign-in and workspace-asset journey behaves correctly for an authenticated member account, including edge cases around expired sessions and large asset uploads."

The mission names the target journey (sign-in + workspace-asset) and three edge conditions (expired sessions, large uploads, authenticated member account). A vague mission ("explore the sign-in flow") would not.

**Claude judgment layer:** when auto-suggesting a mission from a high-mention-count entity, layer the entity's Phase-3-extracted relationships into the mission — if the entity appears in user-journeys.md, name the journey; if it appears in business-rules.md, name the rule the mission tests. The helper supplies the entity + a generic mission shell; the judgment layer fills in the specificity.

### 2. Target scope

The target identifies which surfaces of the application the charter covers. Too narrow = the exploration misses related surfaces; too broad = the time-box overflows.

**Worked example (CH-001):** "Sign-in flow plus workspace-detail asset upload (POST /workspaces/{id}/assets)."

The target names two pages and one endpoint. The naming is concrete (page paths, HTTP method + path) rather than abstract ("authentication").

**Claude judgment layer:** the helper's auto-suggestion produces `<top-entity>-related endpoints and pages` as a starting target. The judgment layer narrows this to specific paths the entity actually appears on, drawing from the spec model and the journey index.

### 3. Time-box discipline

The time-box is a commitment. v1 defaults to `60min`. Charters that need more time should be split into multiple charters; charters that finish faster surface the saved time as a check on whether the mission was specific enough.

**Worked example (CH-001):** `60min`. The CH-001 mission produces at least one observation per acceptance criterion and one screenshot per page transition within the time-box.

**Claude judgment layer:** the time-box is a budget for the human exploration phase. When the auto-suggestion produces a target that's too broad for 60 minutes, the judgment layer recommends splitting into sub-charters rather than expanding the time-box.

### 4. Risk-area enumeration

Risk areas focus the exploration on what's most likely to fail. The universal-core risk keywords are generic English (`security`, `auth`, `performance`, `data-integrity`, `accessibility`, `compliance`, `session`, `permission`, `token`, `leak`). Project-specific risk keywords (e.g., `PCI`, `HIPAA`) extend the core via `tc-explore.charters.risk-keywords:` in `<workspace>/config.yaml`.

**Worked example (CH-001):**

```yaml
risk-areas:
  - auth-required endpoints accepting unauthenticated requests
  - asset uploads exceeding the 10 MB limit
  - session expiration mid-workspace
  - workspace access controls (member vs admin)
```

Each risk area names a specific failure mode. The helper's auto-suggestion extracts these from `risk-register/risk-register.md` lines matching the universal-core OR extended risk keywords.

**Claude judgment layer:** the judgment layer ranks risk areas by likelihood × impact. A risk area that the Phase 3 `/tc:learn-from-api` flagged as `[auth-mismatch]` already has runtime evidence; that ranks higher than a hypothetical risk drawn from the spec only.

### 5. Acceptance-criteria testability

Acceptance criteria are testable predicates. "Sign-in works" is not testable; "Sign-in completes with a valid session token returned in the response body" is.

**Worked example (CH-001):**

```yaml
acceptance-criteria:
  - Sign-in completes with a valid session token returned in the response body
  - Workspace list endpoint returns only workspaces the authenticated account owns
  - Asset upload succeeds for files under 10 MB and produces a resolvable asset ID
  - Asset upload rejects files over 10 MB with a clear error
  - Session expiration during workspace navigation routes the user back to /sign-in
```

Five criteria. Each names (a) an observable behavior, (b) the observable condition that confirms it, and (c) the failure mode if it does not.

**Claude judgment layer:** the helper's auto-suggestion produces three generic criteria from the entity. The judgment layer expands these into specific, testable predicates drawing from the entity's Phase 3 spec / API / code findings.

### 6. Out-of-scope discipline

Documenting what the charter does NOT cover prevents scope creep. v1 ships two universal defaults; project-specific out-of-scope items the judgment layer adds.

**Worked example (CH-001):**

```markdown
- Admin-level workspace creation or destruction (separate charter scope).
- Cross-workspace permission propagation (deferred to a later charter once `tc-knowledge.code.endpoint-decorator-patterns` extension lands).
- Visual styling / theming (`/tc:learn-from-tests` flagged the Playwright spec files as `unsupported-test-runner` in v1; UI assertion gates wait on Phase 6).
```

Three out-of-scope items, each citing the reason (separate scope, deferred until a Phase-3 extension lands, Phase 6 will handle).

**Claude judgment layer:** the helper's auto-suggestion produces two generic out-of-scope defaults. The judgment layer adds project-specific items by cross-referencing Phase 3 gap signals — anything flagged as `[language-unsupported-in-v1]` or `[unsupported-test-runner]` is a candidate for the out-of-scope list.

## Idempotency contract

Re-running `/tc:create-charter --target X`:

1. With an existing charter whose `target:` field matches X (case-insensitive exact match) → **skip**. CLI reports `created: 0 skipped: 1 -> <CH-ID> already exists`. The existing charter's bytes are preserved (user edits intact).
2. With `--new-id` → **allocate a fresh CH-NNN**, even if the target matches.
3. With no `--target`/`--mission` and an existing charter whose target matches the auto-suggestion → **skip**.

Allocation: scans `<workspace>/charters/CH-*.md`, finds the maximum NNN, allocates NNN+1 zero-padded to 3 digits. The seeded fixture's `CH-001` is the first allocation; consuming projects' subsequent charters become `CH-002`, `CH-003`, etc.

## Configurable extensions

```yaml
tc-explore:
  charters:
    # Additive. The helper unions these with the universal core.
    risk-keywords: [PCI, HIPAA, GDPR, SOC2]
    # Reserved for /tc:explore (Step 4.3) auto-detection of journey areas.
    area-keywords: [checkout, refund, prescribe]
```

The seeded fixture exercises only the universal cores; the customization guide (updated in Step 4.6) carries worked examples for three different consuming-project shapes.

## See also

- [Umbrella methodology](exploratory-testing.md)
- [Per-command page](../commands/create-charter.md)
- [Charter template](../templates/charter-template.md)
- [Target-app template](../templates/target-app-template.md)
