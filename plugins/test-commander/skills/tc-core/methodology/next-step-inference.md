---
name: next-step-inference
description: Rules `/tc:next` uses to recommend the next Test Commander command given a workspace snapshot.
---

# Next-Step Inference

The `/tc:next` engine (`plugins/test-commander/scripts/next_step.py`) reads the `WorkspaceSnapshot` produced by `/tc:status`, evaluates each heuristic below, and returns all matching recommendations sorted by priority (lower number = more urgent). The top match is surfaced as a `next:` line; the rest follow as `followups`.

Each `Recommendation` carries `command`, `explanation`, `phase` (owning phase), and `priority`. Drift between this document and `_heuristics()` in the engine is caught by code review; every rule listed here must have at least one passing test fixture in `tests/test_next_step.py`.

## Rules

### R1 — Initialize the workspace
- **Trigger.** `.test-commander/` does not exist on disk.
- **Recommends.** `/tc:init` (Phase 1).
- **Why.** Nothing else can happen until the workspace exists.
- **Priority.** 1.

### R2 — Customize project metadata
- **Trigger.** Workspace exists; `phase_status["1"]` is `not_started` (project.md, config.yaml, methodology.md still match the bundled template).
- **Recommends.** Manual edit of `.test-commander/project.md`, `config.yaml`, and `methodology.md`.
- **Why.** `/tc:init` copies the template verbatim; the user supplies project context by editing the three metadata files.
- **Priority.** 2.

### R3 — Review requirements
- **Trigger.** `phase_status["2"]` is `not_started`.
- **Recommends.** `/tc:review-requirements` (Phase 2).
- **Why.** Requirements review surfaces gaps, ambiguity, and testability issues before any downstream work.
- **Priority.** 3.

### R4 — Build project knowledge
- **Trigger.** `phase_status["3"]` is `not_started`.
- **Recommends.** `/tc:learn-from-docs` (Phase 3).
- **Why.** Knowledge artifacts (system model, business rules, APIs) feed every later phase. Without them, exploration and BDD generation lack grounding.
- **Priority.** 4.

### R5 — Start a charter
- **Trigger.** `phase_status["4"]` is `not_started`.
- **Recommends.** `/tc:create-charter` (Phase 4).
- **Why.** Session-based exploratory testing produces observations, test ideas, and risks that BDD generation depends on.
- **Priority.** 5.

### R6 — Generate BDD
- **Trigger.** `phase_status["5"]` is `not_started`.
- **Recommends.** `/tc:generate-bdd` (Phase 5).
- **Why.** BDD scenarios become the unit of automation and the unit of stakeholder review.
- **Priority.** 6.

### R7 — Plan automation
- **Trigger.** `phase_status["6"]` is `not_started`.
- **Recommends.** `/tc:automation-plan` (Phase 6).
- **Why.** Decide what to automate before writing code. Apply the suitability rubric: business criticality, repeatability, determinism, maintenance cost, bug detection value.
- **Priority.** 7.

### R8 — Run tests
- **Trigger.** `phase_status["7"]` is `not_started`.
- **Recommends.** `/tc:run` (Phase 7).
- **Why.** Run the automated suite and collect evidence (screenshots, traces, logs). Failures feed the next quality report.
- **Priority.** 8.

### R9 — Capture lessons
- **Trigger.** `phase_status["8"]` is `not_started`.
- **Recommends.** `/tc:learn` (Phase 8).
- **Why.** Capture candidate lessons from the round of work. Lessons land in `lessons-inbox.md` for human review before promotion.
- **Priority.** 9.

### R10 — Update the quality report
- **Trigger.** `phase_status["1"]` through `phase_status["8"]` are all `in_progress`.
- **Recommends.** `/tc:report` (Phase 7).
- **Why.** All MVP phases have content. Keep the live quality report fresh and assess release readiness with `/tc:quality-gate`.
- **Priority.** 10.

## Out of scope (Step 1.5)

- Phase 9 (visuals) and Phase 10.5 (controlled execution / governance) do not have R-rules yet. Visuals are optional; governance is invoked through the web console rather than a `/tc:*` command. They can be added once those phases land.
- "Already-done" detection. A recommendation can in principle become stale if the user did the work without recording it (e.g., manually edited files that match the template by coincidence). The engine trusts the snapshot.
