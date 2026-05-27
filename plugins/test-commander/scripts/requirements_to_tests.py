#!/usr/bin/env python3
"""/tc:requirements-to-tests helper.

For every reviewed requirement, generates a seed test-idea file under
`<workspace>/test-ideas/<REQ-ID>.md` containing a Phase-4-compatible
YAML frontmatter schema (`tc-test-idea/v1`), a verbatim copy of the
requirement body, candidate scenario titles (happy / edge / negative),
the Phase 2 review findings for that requirement, and optional pointers
to the acceptance-criteria review when present. Refreshes the
traceability map via `requirements_coverage.coverage()` so each
requirement row links to its new test-idea seed.

Idempotency contract: existing test-idea files are **never** overwritten.
Phase 4 will enrich these files (charters, sessions, refined ideas) and
those enrichments must survive re-runs. The helper records how many
files were created vs skipped; re-running produces zero `created`.

Per D18 the helper ships inside the plugin so consuming-project users
can invoke it after `claude plugin install`.

Exit codes:
    0 - seeds written (or all preserved)
    2 - uninitialized workspace, missing review
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

import requirements_coverage
import review_requirements

WORKSPACE_DIRNAME = ".test-commander"
SCHEMA_VERSION = "tc-test-idea/v1"


# ---------------------------------------------------------------------------
# Exceptions and dataclasses
# ---------------------------------------------------------------------------

class ToTestsError(Exception):
    """Base class for requirements_to_tests errors."""


class UninitializedWorkspaceError(ToTestsError):
    """Raised when `<project>/.test-commander/` does not exist."""


class ReviewMissingError(ToTestsError):
    """Raised when `requirements/requirements-review.md` is absent or stub.

    `/tc:requirements-to-tests` depends on the review artifact produced by
    `/tc:review-requirements`. Run `/tc:review-requirements` first.
    """


@dataclass
class SeedResult:
    workspace: Path
    requirements_count: int
    created_count: int
    skipped_count: int
    created_paths: list[Path] = field(default_factory=list)
    skipped_paths: list[Path] = field(default_factory=list)
    traceability_path: Path | None = None
    ac_review_present: bool = False


# ---------------------------------------------------------------------------
# Review-artifact gate
# ---------------------------------------------------------------------------

def _review_is_generated(review_path: Path) -> bool:
    """True iff `requirements-review.md` shows signs of being written by
    `/tc:review-requirements` (Step 2.2).

    The workspace template ships a review placeholder; before Step 2.2
    has run the placeholder still occupies the file. Detect the Step 2.2
    generator's structural markers.
    """
    if not review_path.is_file():
        return False
    text = review_path.read_text(encoding="utf-8")
    return "## Executive summary" in text and "## Findings" in text


def _ac_review_is_generated(ac_review_path: Path) -> bool:
    """True iff `acceptance-criteria-review.md` shows signs of being
    written by `/tc:review-acceptance-criteria` (Step 2.4).

    Same template-stub-vs-generated pattern as `_review_is_generated`
    and `requirements_coverage._inventory_is_generated`. The Step 2.4
    helper always writes either an executive-summary block or a
    "no acceptance criteria found" sentinel; the template placeholder
    contains neither.
    """
    if not ac_review_path.is_file():
        return False
    text = ac_review_path.read_text(encoding="utf-8")
    return (
        "## Executive summary" in text
        or "no acceptance criteria found" in text.lower()
    )


# ---------------------------------------------------------------------------
# Seed generation
# ---------------------------------------------------------------------------

def _derive_title(body: str, max_words: int = 12) -> str:
    """Return a short title derived from the requirement body."""
    words = body.split()
    if len(words) <= max_words:
        return body.strip().rstrip(".")
    return " ".join(words[:max_words]).rstrip(",.;:") + "..."


def _seed_content(
    requirement: review_requirements.Requirement,
    findings_for_req: list[str],
    ac_review_present: bool,
) -> str:
    title = _derive_title(requirement.body)
    findings_block = "[]"
    if findings_for_req:
        findings_block = "\n" + "\n".join(f"  - {d}" for d in findings_for_req)

    ac_block_lines: list[str] = []
    if ac_review_present:
        ac_block_lines.append("## Related acceptance-criteria findings")
        ac_block_lines.append("")
        ac_block_lines.append(
            "An acceptance-criteria review is present at "
            "`requirements/acceptance-criteria-review.md`. Review its findings "
            "for ACs that trace back to this requirement's parent story (if any) "
            "before authoring concrete test scenarios — the AC review surfaces "
            "missing edge cases, missing negative cases, untestable predicates, "
            "ambiguous data rules, and missing role context."
        )
        ac_block_lines.append("")

    ac_pointer_for_yaml = "true" if ac_review_present else "false"

    lines = [
        "---",
        f"schema: {SCHEMA_VERSION}",
        f"requirement_id: {requirement.id}",
        f"requirement_title: {title}",
        f"source: documents/uploaded/{requirement.source_file}",
        "status: seed",
        f"ac_review_present: {ac_pointer_for_yaml}",
        "phase_2_findings:" + findings_block,
        "candidates:",
        f"  - id: {requirement.id}-happy-01",
        "    title: Happy path",
        "    type: positive",
        "    source: helper-derived",
        f"  - id: {requirement.id}-edge-01",
        "    title: Edge case (define from product knowledge)",
        "    type: edge",
        (
            "    source: ac-review"
            if ac_review_present
            else "    source: helper-derived"
        ),
        f"  - id: {requirement.id}-negative-01",
        "    title: Negative case (define from product knowledge)",
        "    type: negative",
        (
            "    source: ac-review"
            if ac_review_present
            else "    source: helper-derived"
        ),
        "generated_by: /tc:requirements-to-tests",
        "---",
        "",
        f"# Test ideas for {requirement.id}",
        "",
        "## Requirement",
        "",
        f"_Source: `documents/uploaded/{requirement.source_file}`_",
        "",
        "> " + requirement.body.replace("\n", "\n> "),
        "",
        "## Candidate scenarios",
        "",
        f"- **Happy path** (`{requirement.id}-happy-01`) — the canonical success "
        "trajectory; refine from product knowledge.",
        f"- **Edge case** (`{requirement.id}-edge-01`) — boundary, unusual, or "
        "rarely-exercised conditions; refine from product knowledge.",
        f"- **Negative case** (`{requirement.id}-negative-01`) — failure modes "
        "(invalid input, denied permission, network error, etc.); refine from "
        "product knowledge.",
        "",
    ]

    if ac_block_lines:
        lines.extend(ac_block_lines)

    if findings_for_req:
        lines.append("## Phase 2 review findings")
        lines.append("")
        lines.append(
            f"The Step 2.2 review flagged this requirement on **{len(findings_for_req)}** "
            "rubric dimension(s). Use these to prioritize scenarios above:"
        )
        lines.append("")
        for dim in findings_for_req:
            lines.append(f"- `{dim}`")
        lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append(
        "Seeded by `/tc:requirements-to-tests`. Phase 4 (`tc-explore`) enriches "
        "this file with charters, exploration sessions, and refined test ideas. "
        "User edits to this file are preserved on re-run — the helper never "
        "overwrites an existing seed."
    )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Top-level entry
# ---------------------------------------------------------------------------

def to_tests(project_root: Path) -> SeedResult:
    project_root = Path(project_root)
    workspace = project_root / WORKSPACE_DIRNAME
    if not workspace.is_dir():
        raise UninitializedWorkspaceError(
            f"workspace not found: {workspace} (run /tc:init first)"
        )

    review_path = workspace / "requirements" / "requirements-review.md"
    if not _review_is_generated(review_path):
        raise ReviewMissingError(
            "requirements-review.md not found or not yet generated; "
            "run /tc:review-requirements first"
        )

    # Parse the source requirements (same logic the review used).
    reqs, _collisions = review_requirements.parse_workspace(workspace)

    # Build per-REQ Phase-2 finding list for the seed schema.
    findings, _open_questions = review_requirements.apply_checks(
        reqs, review_requirements.load_extensions(workspace),
    )
    findings_by_req: dict[str, list[str]] = {}
    for f in findings:
        findings_by_req.setdefault(f.req_id, []).append(f.dimension)
    for rid in findings_by_req:
        findings_by_req[rid] = sorted(set(findings_by_req[rid]))

    ac_review_path = workspace / "requirements" / "acceptance-criteria-review.md"
    ac_review_present = _ac_review_is_generated(ac_review_path)

    test_ideas_dir = workspace / "test-ideas"
    test_ideas_dir.mkdir(parents=True, exist_ok=True)

    created_paths: list[Path] = []
    skipped_paths: list[Path] = []
    for req in reqs:
        path = test_ideas_dir / f"{req.id}.md"
        if path.exists():
            skipped_paths.append(path)
            continue
        path.write_text(
            _seed_content(req, findings_by_req.get(req.id, []), ac_review_present),
            encoding="utf-8",
        )
        created_paths.append(path)

    # Refresh the traceability map (re-uses Step 2.5's scanner).
    coverage_result = requirements_coverage.coverage(project_root)

    return SeedResult(
        workspace=workspace,
        requirements_count=len(reqs),
        created_count=len(created_paths),
        skipped_count=len(skipped_paths),
        created_paths=created_paths,
        skipped_paths=skipped_paths,
        traceability_path=coverage_result.trace_path,
        ac_review_present=ac_review_present,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate seed test-idea files (one per reviewed requirement) "
            "under .test-commander/test-ideas/, with a Phase-4-compatible "
            "YAML frontmatter schema. Refreshes the traceability map."
        ),
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Path to the consuming project root (default: cwd).",
    )
    args = parser.parse_args(argv)

    try:
        result = to_tests(Path(args.project_root))
    except (UninitializedWorkspaceError, ReviewMissingError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"workspace:        {result.workspace}")
    print(f"requirements:     {result.requirements_count}")
    print(f"created:          {result.created_count}")
    print(f"skipped (exists): {result.skipped_count}")
    print(f"ac_review:        {'present' if result.ac_review_present else 'absent'}")
    print(f"traceability:     {result.traceability_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
