# Customizing Test Commander for Your Project

Test Commander is a **generic, product-domain-agnostic testing tool**. It ships with universal English and software-engineering defaults only — no e-commerce, healthcare, finance, research, or other product-domain vocabulary is baked into the shipped rubric, tags, methodology, fixtures, or examples. This is a deliberate design choice; see [Decision D19](../../planning/plan.md) in the phased plan.

This guide shows how a consuming project extends Test Commander for its own domain — what to add, where to add it, and what to leave alone.

## Why genericness, by default

Test Commander does not know in advance whether you are testing a banking app, a hospital information system, a research data platform, an online retailer, or an internal tool. The shipped rubric, tag taxonomy, and examples make no assumptions. Product-specific knowledge enters at runtime through hooks you control.

A direct consequence: out of the box, Test Commander will not flag PCI-, HIPAA-, or commerce-specific defects in your requirements. It catches universal quality problems (clarity, testability, dependencies, ambiguity, generic-security anti-patterns like `plain text`). To get domain-aware checks, extend the configuration as described below.

## Where domain knowledge enters

Four explicit hooks. None are required — Test Commander works without any of them on the universal defaults. Use as few or as many as your project needs.

| Hook | What you supply | When it ships |
| --- | --- | --- |
| 1 | `<workspace>/config.yaml` extensions to rubric keyword sets | Phase 2 (first surface), extended by later phases |
| 2 | Your project's documents under `.test-commander/documents/uploaded/` | Phase 2 |
| 3 | Phase 3 project knowledge ingestion (`/tc:learn-from-*`) | Phase 3 |
| 4 | Project-defined values inside shipped tag namespaces (`@area:`, `@risk:`, `@persona:`) | Phase 5 |

This guide is updated by every phase that adds an extensible surface. If a phase introduced a new hook or schema key, you will find a worked example here.

## Hook 1: `<workspace>/config.yaml` extensions

The workspace's `config.yaml` is the primary configuration surface. Test Commander reads it on every helper invocation and **unions** project-supplied lists with the shipped universal core. Extensions never replace defaults — only add to them.

### Phase 2 schema (`tc-requirements`)

Phase 2 ships three extensible rubric dimensions under `tc-requirements:` (read by `/tc:review-requirements` for `data-rules` and `risk`, and by `/tc:review-acceptance-criteria` for `roles-permissions`):

```yaml
tc-requirements:
  data-rules:
    sensitive-keywords:
      - PAN
      - primary account number
      - PHI
      - SSN
  risk:
    compliance-keywords:
      - PAN
      - primary account number
      - PHI
      - social security
  roles-permissions:
    permission-verbs:
      - issue
      - refund
      - dispense
      - prescribe
    role-qualifiers:
      - customer
      - store-manager
      - investigator
      - reviewer
```

Missing keys = no extension. The helper falls back to the universal core only. The shipped seeded fixture in `tests/fixtures/seeded-flawed-requirements/` does not rely on any extension; every seeded defect triggers via the universal core alone.

### Worked example — an e-commerce project

You are testing an online retail platform. Your requirements regularly mention `credit card`, `PAN`, `refund`, `customer`, `store manager`. Extend the configuration:

```yaml
tc-requirements:
  data-rules:
    sensitive-keywords: [PAN, primary account number, credit card, credit-card]
  risk:
    compliance-keywords: [PAN, primary account number, credit card, social security]
  roles-permissions:
    permission-verbs: [issue, refund, charge, dispute]
    role-qualifiers: [customer, store-manager, fulfillment-agent]
```

Effect: `/tc:review-requirements` now flags requirements that mention `refund` without naming the role authorized to issue it, and flags requirements that mention `credit card` storage without a constraint keyword (`encrypted`, `tokenized`).

### Worked example — a healthcare project

```yaml
tc-requirements:
  data-rules:
    sensitive-keywords: [PHI, medical record number, MRN, prescription history, diagnosis code]
  risk:
    compliance-keywords: [PHI, HIPAA, patient identifier, MRN]
  roles-permissions:
    permission-verbs: [dispense, prescribe, refer, transfer]
    role-qualifiers: [physician, nurse, pharmacist, technician, patient]
```

Effect: requirements mentioning `prescribe` without a clinician role qualifier are flagged; storage references to `PHI` without an encryption constraint are flagged for HIPAA risk.

### Worked example — a research data platform

```yaml
tc-requirements:
  data-rules:
    sensitive-keywords: [participant identifier, IRB protocol, consent record]
  risk:
    compliance-keywords: [IRB, deidentification, re-identification risk]
  roles-permissions:
    permission-verbs: [enroll, terminate, deidentify, archive]
    role-qualifiers: [investigator, study-coordinator, IRB-reviewer, participant]
```

Effect: requirements that move participant data without naming the IRB-authorized role are flagged; storage references that lack `deidentification` constraints are flagged for compliance.

### Extension rules

- Extensions are **additive**. The helper unions defaults with your list. You cannot remove a universal-core keyword via configuration.
- Keyword matching is case-insensitive. Single-token keywords match at word boundaries; multi-token phrases (e.g. `credit card`) match literally.
- Add the same vocabulary in multiple sections if the same term carries meaning under multiple dimensions (e.g. `PAN` is both `sensitive-keywords` for data-rules and `compliance-keywords` for risk — that is correct and intentional).
- Document your additions in your project's `.test-commander/methodology.md` so the team uses a shared taxonomy.

## Hook 2: project documents under `documents/uploaded/`

The Phase 2 helpers read every Markdown file in `.test-commander/documents/uploaded/` that matches their convention — `REQ-\d+` markers for requirements, `US-\d+` for stories, `AC-\d+` for acceptance criteria. Drop your real product requirements there as Markdown files. No tool configuration is needed; the helpers find and parse them.

This is the single most important customization: the requirements Test Commander reviews are *your* requirements. The shipped fixture exists only so Test Commander can be tested against itself.

## Hook 3: project knowledge ingestion (Phase 3)

When Phase 3 ships, the `tc-knowledge` skill (`/tc:learn-from-docs`, `/tc:learn-from-specs`, `/tc:learn-from-code`, `/tc:learn-from-api`, `/tc:learn-from-tests`) scans your codebase, OpenAPI specs, existing tests, and design documents to build a structured knowledge model under `.test-commander/product-knowledge/`. Downstream Phase 2, 4, 5, and 6 commands read this knowledge to make their findings product-aware without you hand-curating keyword lists.

This is the **preferred long-term path** for domain awareness. `config.yaml` extensions are a useful Phase 2 bootstrap; Phase 3 ingestion is how Test Commander learns your product without manual taxonomy work.

## Hook 4: project-defined tag namespaces

Test Commander (Phase 5+) ships three project-defined namespaces:

| Namespace | Purpose | Example values your project picks |
| --- | --- | --- |
| `@area:<feature>` | Feature area your project tests | `@area:sign-in`, `@area:reports`, `@area:billing` |
| `@risk:<class>` | Risk classification | severity: `@risk:high`/`medium`/`low`; category: `@risk:data-loss`/`availability`/`integrity`; domain: `@risk:compliance`/`fraud`/`safety` |
| `@persona:<role>` | User persona | `@persona:admin`, `@persona:customer`, `@persona:investigator` |

Test Commander ships the namespaces; you pick the values. Document your values in your project's `.test-commander/methodology.md`. Tag-driven gates (e.g. "block release if any `@risk:high` test is failing") are configured per-project.

## What NOT to do

- **Do not fork Test Commander.** The universal core is a contract — extending via `config.yaml` is the supported path. Forking divorces you from upstream improvements.
- **Do not put product-specific vocabulary in the shipped fixtures** (`tests/fixtures/`). Those test Test Commander itself; your domain belongs in your project's `documents/uploaded/` and `config.yaml`.
- **Do not expect overrides to remove defaults.** Extensions add to defaults, never replace them. If a universal keyword (e.g. `plain text` for risk) is not relevant to your product, your finding still includes it — you simply ignore the suggestion in your team's review.
- **Do not encode product knowledge inline in helpers or methodology docs.** Phase 3's knowledge ingestion is the canonical place for that information; `config.yaml` is the canonical place for vocabulary extensions.

## See also

- [Workspace reference](../workspace-reference.md) — where each artifact lives, including `config.yaml`.
- [Phased plan, Decision D19](../../planning/plan.md) — the genericness principle.
- [Workflow walkthrough](workflow.md) — first end-to-end run.
- [Command reference](../command-reference.md) — every command, by phase.
- [Getting started](getting-started.md) — install and verify.
