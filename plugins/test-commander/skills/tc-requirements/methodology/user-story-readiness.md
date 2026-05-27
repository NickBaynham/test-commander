# User Story Readiness — Methodology

The rubric `/tc:review-user-stories` applies to every parsed `US-NNN` entry. Eight dimensions: the six INVEST letters plus role-action-benefit shape and acceptance-criteria-pointer presence. Each dimension has a deterministic mechanical check shipped in `review_user_stories.py` and a narrative judgment layer Claude is expected to add when summarizing for a human reviewer.

The seeded fixture at `tests/fixtures/seeded-flawed-requirements/user-stories.md` has one defect per INVEST letter, tagged with an inline `<!-- defect: invest-<letter> -->` comment. The fixture is the test contract; this doc explains the *why* alongside the *what*.

## Shape: role-action-benefit

Test Commander expects every user story to use the canonical shape:

> **As a** `<role>`, **I want** `<action>`, **So that** `<benefit>`.

This shape forces three things: a named actor, a concrete action, and a verifiable benefit. Stories that drop any of the three lose information that downstream tests cannot recover.

**Mechanical check.** Body must contain `As a` (or `As an`), `I want`, and `So that` (case-insensitive). Missing any one yields a `role-action-benefit` finding.

**Worked example.** `US-300` (synthetic, used in tests): *"Make the system faster and better."* — missing all three markers; flagged.

**Claude judgment layer.** Propose the role, action, and benefit that the author probably meant; ask the team to confirm. If no plausible role exists, the requirement may not be a user story (could be an NFR or a constraint).

A story flagged for `role-action-benefit` is considered *blocked* — the rest of the INVEST review has limited signal until the shape is fixed.

## INVEST — Independent

**Definition.** Stories should be schedulable in any order; one story's completion should not block another's.

**Mechanical check.** Body matches `\b(depends on|after|requires)\b\s+US-\d+` (case-insensitive). Explicit dependency clauses signal the story cannot ship alone.

**Worked example.** `US-001`: *"As a returning user, I want to view my dashboard, So that I can see my recent activity. (Depends on US-002 'Sign in' being completed and released first; cannot be developed or shipped independently.)"* — explicit dependency clause.

**Claude judgment layer.** Identify whether the dependency is essential (the linked story is a true prerequisite) or accidental (could be made independent by splitting the work or introducing a stub). Propose the smaller, shippable shape.

## INVEST — Negotiable

**Definition.** Stories should describe what users need, not how to implement it. Over-specification (pixel coordinates, exact fonts, hex colors, "no deviation" clauses) freezes the design before the team has explored options.

**Mechanical check.** Body contains any of: UI coordinates `(\d+,\s*\d+)`, pixel dimensions `\d+\s*px`, hex colors `#[0-9a-fA-F]{3,8}`, or the phrase `no deviation`.

**Worked example.** `US-002`: *"As a user, I want a red 'Submit' button at coordinates (240, 480) on the form page, measuring exactly 120px wide by 36px tall, with Helvetica 14pt bold text... No deviation from these specifications is acceptable."* — coordinates, pixel dimensions, and a "no deviation" clause.

**Claude judgment layer.** Separate the *intent* (the user can find and use the action) from the *implementation* (button placement). Recommend moving design-specific details to a design spec or visual review, leaving the user story focused on the user's need.

## INVEST — Valuable

**Definition.** Stories should articulate user or business value. Engineering work (refactoring, code cleanup, internal modules) is legitimate but should not masquerade as a user story.

**Mechanical check.** Body contains an engineering verb from `{refactor, refactoring}` or a developer-as-actor pattern (`As a backend developer`, `As a software engineer`, etc.).

**Worked example.** `US-003`: *"As a backend developer, I want to refactor the authentication module into smaller files, So that the code is cleaner. (No direct user-facing or business-facing value articulated; this is engineering work disguised as a user story.)"* — developer actor plus engineering verb.

**Claude judgment layer.** If genuine user value exists (faster response, fewer bugs), rewrite from the user's perspective. If only engineering value exists, route the work to the engineering backlog rather than the product backlog. Engineering work has a place — just not as a user story.

## INVEST — Estimable

**Definition.** Stories should be concrete enough for the team to estimate scope.

**Mechanical check.** Body contains a vague-action keyword from `{better, improved, enhanced, more, faster, smarter, nicer}` without a numeric predicate. "Better" is unestimable; "30% faster" is estimable.

**Worked example.** `US-004`: *"As a user, I want better search, So that I find what I need."* — `better` without a measurable threshold.

**Claude judgment layer.** Propose a measurable predicate (specific filters added, p95 latency target, success-rate target). If the team cannot agree on a number, the story needs a spike or further user research before it can be sized.

## INVEST — Small

**Definition.** Stories should fit in a single iteration. Large stories carry compounding risk and harder estimates.

**Mechanical check.** The `I want to ...` clause contains a comma-list of ≥ 4 items, **or** the story body exceeds 40 words.

**Worked example.** `US-005`: *"As a user, I want to sign up, sign in, configure my profile, manage notifications, view reports, schedule jobs, export data, manage integrations, configure API keys, audit my history, and contact support, So that I can fully use the system."* — 11-item comma-list.

**Claude judgment layer.** Propose how to split: by actor, by workflow step, by data subset, or by happy-path-vs-edge-case. Each split should yield independently-valuable, independently-shippable sub-stories.

## INVEST — Testable

**Definition.** Stories should describe behavior that can be verified.

**Mechanical check.** Body contains a subjective-experience word from `{feel, delight, delightful, enjoyable, intuitive, satisfying, pleasing, fun, love}`. These words describe perception, not behavior, so no test can confirm them objectively.

**Worked example.** `US-006`: *"As a user, I want the system to feel intuitive and delightful, So that I enjoy using it."* — `feel`, `intuitive`, `delightful`.

**Claude judgment layer.** Translate subjective experience into measurable proxies: task-completion rate, time-on-task, support-ticket volume, SUS score, NPS, A/B test win rate. Replace the experiential goal with the proxy in the story, or move the goal to a UX research charter.

## Acceptance-criteria pointer (`needs-acceptance-criteria`)

**Definition.** A user story should point at acceptance criteria (AC-NNN). Without ACs, the team cannot agree on done.

**Mechanical check.** Body contains no `AC-\d+` reference.

**Worked example.** Every seeded fixture story (US-001 through US-006) lacks an AC pointer; all flag.

**Claude judgment layer.** Either the ACs exist elsewhere (link them in) or they need to be authored. Surface this to the product owner; if the team chooses to defer (e.g., for a spike story), record that explicitly.

A story flagged for `needs-acceptance-criteria` is **not** automatically *blocked* — many teams write ACs after the story is groomed. The check ensures the gap is visible.

## Readiness verdicts

`/tc:review-user-stories` assigns one verdict per story:

| Verdict | Trigger |
| --- | --- |
| `ready` | No findings at all |
| `needs-refinement` | One or two mechanical findings, or only `needs-acceptance-criteria` |
| `blocked` | Three+ INVEST findings, or any `role-action-benefit` shape violation |

The verdict is a starting point. Claude's narrative review may move a story from `needs-refinement` to `blocked` (or vice versa) based on judgment-level concerns.

## What the helper does NOT detect

- Cross-story duplication (two stories asking for the same thing).
- Stories that contradict requirements (`/tc:review-requirements` covers the requirement side).
- Stories that depend on missing ACs (`/tc:review-acceptance-criteria` covers the AC side).
- Subtle role/value mismatches that are domain-aware (Claude's narrative layer handles these).

Domain-specific vocabulary (PCI, HIPAA, your role taxonomy) does not influence the INVEST check directly — INVEST is universal — but Claude's narrative layer can lean on the project's `config.yaml` extensions when explaining why a finding matters.
