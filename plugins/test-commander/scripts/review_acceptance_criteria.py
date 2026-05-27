#!/usr/bin/env python3
"""/tc:review-acceptance-criteria helper.

Reads `*.md` files in `<workspace>/documents/uploaded/` that declare
`AC-NNN[-NN]` markers (Given/When/Then acceptance criteria), applies
the Phase 2 AC rubric, and writes `<workspace>/requirements/acceptance-
criteria-review.md`. ACs whose parent story (derived from the AC ID
prefix, e.g. `AC-001-01` -> `US-001`) is not found among parsed user
stories are flagged as orphans.

Per D18 the helper ships inside the plugin so consuming-project users
can invoke it after `claude plugin install`. Per D19 all checks use
universal English vocabulary; no domain-specific keywords ship with the
tool.

Exit codes:
    0 - review written
    2 - uninitialized workspace
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"
AC_PATTERN = re.compile(r"\bAC-(\d{1,4})(?:-(\d{1,3}))?\b")
AC_HEADER = re.compile(
    r"^(?:[-*]\s*)?AC-(\d{1,4})(?:-(\d{1,3}))?\s*:\s*(.*)$", re.MULTILINE
)
US_PATTERN = re.compile(r"\bUS-(\d{1,4})\b")

GIVEN_WHEN_THEN = re.compile(r"\b(given|when|then)\b", re.IGNORECASE)

CORE_EDGE_KEYWORDS = {"except", "unless", "otherwise", "edge"}
CORE_FAILURE_KEYWORDS = {
    "invalid", "error", "fail", "missing", "declined", "rejected", "denied",
    "expired", "locked",
}
CORE_SUBJECTIVE = {
    "feel", "snappy", "smooth", "fluid", "intuitive", "delightful",
    "enjoyable", "satisfying", "pleasing",
}
CORE_VAGUE_PREDICATES = {"responsive", "fast", "slow", "quick"}
CORE_AMBIGUITY = {
    "appropriately", "as needed", "suitable", "sufficient", "sufficiently",
    "properly", "accordingly", "reasonable", "appropriate",
}
CORE_PERMISSION_VERBS = {
    "delete", "remove", "approve", "reject", "modify", "grant", "revoke",
    "issue", "publish",
}
CORE_ROLE_QUALIFIERS = {"admin", "owner", "operator"}
NUMERIC_THRESHOLD = re.compile(
    r"\b\d+(\.\d+)?\s*(%|ms|s|min|hr|hours?|days?|GB|MB|KB|requests?|users?)?\b"
)


# ---------------------------------------------------------------------------
# Exceptions and dataclasses
# ---------------------------------------------------------------------------

class AcReviewError(Exception):
    """Base class for review_acceptance_criteria errors."""


class UninitializedWorkspaceError(AcReviewError):
    """Raised when `<project>/.test-commander/` does not exist."""


@dataclass
class AcceptanceCriterion:
    id: str
    story_id: str | None
    body: str
    source_file: str


@dataclass
class AcFinding:
    ac_id: str
    dimension: str
    detail: str


@dataclass
class ReviewResult:
    workspace: Path
    ac_count: int
    findings: list[AcFinding]
    review_path: Path | None = None
    story_ids: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def is_ac_or_story_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    return bool(AC_PATTERN.search(text) or US_PATTERN.search(text))


def parse_acs_from_file(path: Path) -> list[AcceptanceCriterion]:
    text = path.read_text(encoding="utf-8")
    matches = list(AC_HEADER.finditer(text))
    acs: list[AcceptanceCriterion] = []
    for i, m in enumerate(matches):
        story_num = int(m.group(1))
        sub_num = m.group(2)
        ac_id = f"AC-{story_num:03d}-{int(sub_num):02d}" if sub_num else f"AC-{story_num:03d}"
        story_id = f"US-{story_num:03d}"
        first_line = m.group(3).strip()
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        continuation = text[m.end():next_start]
        continuation = re.sub(r"<!--.*?-->", "", continuation, flags=re.DOTALL)
        cont_lines: list[str] = []
        for ln in continuation.split("\n"):
            stripped = ln.strip()
            if stripped.startswith("## ") or stripped.startswith("# "):
                break
            if stripped:
                cont_lines.append(stripped)
        body = first_line
        if cont_lines:
            body = (first_line + " " + " ".join(cont_lines)).strip()
        acs.append(AcceptanceCriterion(
            id=ac_id, story_id=story_id, body=body, source_file=path.name,
        ))
    return acs


def parse_story_ids_from_file(path: Path) -> set[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return set()
    return {f"US-{int(m.group(1)):03d}" for m in US_PATTERN.finditer(text)}


def parse_workspace(workspace: Path) -> tuple[list[AcceptanceCriterion], set[str]]:
    uploaded = workspace / "documents" / "uploaded"
    if not uploaded.is_dir():
        return [], set()
    all_acs: list[AcceptanceCriterion] = []
    all_story_ids: set[str] = set()
    for md in sorted(uploaded.glob("*.md")):
        if not is_ac_or_story_file(md):
            continue
        all_acs.extend(parse_acs_from_file(md))
        all_story_ids |= parse_story_ids_from_file(md)
    return all_acs, all_story_ids


# ---------------------------------------------------------------------------
# Check helpers
# ---------------------------------------------------------------------------

_PARENTHETICAL = re.compile(r"\([^()]*\)")


def _check_body(ac: AcceptanceCriterion) -> str:
    """Return the AC body with parenthetical asides stripped.

    Parentheticals carry meta-commentary (`(Happy path only — no coverage of
    edge cases.)`) rather than canonical AC behavior. If those notes contain
    keywords the AC is meant to be missing (`edge`, `fails`, `admin`), they
    would falsely satisfy the mechanical checks. Strip them so the checks
    operate on the canonical Given/When/Then prose only.
    """
    return _PARENTHETICAL.sub("", ac.body).strip()


def _contains_phrase(body: str, phrase: str) -> bool:
    p = phrase.lower()
    b = body.lower()
    if " " in p or "-" in p:
        return p in b
    return bool(re.search(rf"\b{re.escape(p)}s?\b", b))


def _hits(body: str, keywords) -> list[str]:
    return [k for k in keywords if _contains_phrase(body, k)]


# ---------------------------------------------------------------------------
# Per-dimension checks
# ---------------------------------------------------------------------------

def _check_missing_edge_cases(ac: AcceptanceCriterion) -> AcFinding | None:
    body = _check_body(ac)
    if not GIVEN_WHEN_THEN.search(body):
        return None
    if not _hits(body, CORE_EDGE_KEYWORDS):
        return AcFinding(
            ac.id, "ac-missing-edge-cases",
            "Given/When/Then body has no edge keyword (except/unless/otherwise/edge)",
        )
    return None


def _check_missing_negative_cases(ac: AcceptanceCriterion) -> AcFinding | None:
    body = _check_body(ac)
    if not GIVEN_WHEN_THEN.search(body):
        return None
    if not _hits(body, CORE_FAILURE_KEYWORDS):
        return AcFinding(
            ac.id, "ac-missing-negative-cases",
            "Given/When/Then body has no failure keyword (invalid/error/fail/...)",
        )
    return None


def _check_untestable_predicate(ac: AcceptanceCriterion) -> AcFinding | None:
    body = _check_body(ac)
    subjective = _hits(body, CORE_SUBJECTIVE)
    if subjective:
        joined = ", ".join(sorted(subjective))
        return AcFinding(
            ac.id, "ac-untestable-predicate",
            f"subjective-experience word(s): {joined}",
        )
    vague = _hits(body, CORE_VAGUE_PREDICATES)
    if vague and not NUMERIC_THRESHOLD.search(body):
        joined = ", ".join(sorted(vague))
        return AcFinding(
            ac.id, "ac-untestable-predicate",
            f"vague predicate(s) without numeric threshold: {joined}",
        )
    return None


def _check_ambiguous_data_rule(ac: AcceptanceCriterion) -> AcFinding | None:
    body = _check_body(ac)
    ambiguity = _hits(body, CORE_AMBIGUITY)
    if ambiguity:
        joined = ", ".join(sorted(ambiguity))
        return AcFinding(
            ac.id, "ac-ambiguous-data-rule",
            f"ambiguity word(s): {joined}",
        )
    return None


def _check_missing_role_context(ac: AcceptanceCriterion) -> AcFinding | None:
    body = _check_body(ac)
    verb_hits = _hits(body, CORE_PERMISSION_VERBS)
    if verb_hits and not _hits(body, CORE_ROLE_QUALIFIERS):
        joined = ", ".join(sorted(verb_hits))
        return AcFinding(
            ac.id, "ac-missing-role-context",
            f"permission verb(s) without role qualifier: {joined}",
        )
    return None


def _check_orphan(ac: AcceptanceCriterion, story_ids: set[str]) -> AcFinding | None:
    if ac.story_id and ac.story_id not in story_ids:
        return AcFinding(
            ac.id, "orphan",
            f"parent {ac.story_id} not found among parsed user stories",
        )
    return None


PER_AC_CHECKS = (
    _check_missing_edge_cases,
    _check_missing_negative_cases,
    _check_untestable_predicate,
    _check_ambiguous_data_rule,
    _check_missing_role_context,
)


def apply_checks(
    acs: list[AcceptanceCriterion], story_ids: set[str],
) -> list[AcFinding]:
    findings: list[AcFinding] = []
    for ac in acs:
        for check in PER_AC_CHECKS:
            f = check(ac)
            if f is not None:
                findings.append(f)
        orphan = _check_orphan(ac, story_ids)
        if orphan is not None:
            findings.append(orphan)
    findings.sort(key=lambda f: (f.ac_id, f.dimension, f.detail))
    return findings


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

def _render_review(
    acs: list[AcceptanceCriterion],
    findings: list[AcFinding],
    story_ids: set[str],
) -> str:
    lines = ["# Acceptance Criteria Review", ""]
    if not acs:
        lines.append("_No acceptance criteria found in `documents/uploaded/`._")
        lines.append("")
        lines.append(
            "Drop one or more Markdown files containing `AC-NNN-NN: Given ... When ... Then ...`"
        )
        lines.append("entries into `.test-commander/documents/uploaded/` and re-run.")
        lines.append("")
        return "\n".join(lines)

    counts: dict[str, int] = {}
    for f in findings:
        counts[f.dimension] = counts.get(f.dimension, 0) + 1

    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"- Acceptance criteria parsed: **{len(acs)}**")
    lines.append(f"- Parent stories in scope: **{len(story_ids)}**")
    lines.append(f"- Findings: **{len(findings)}** across **{len(counts)}** dimensions")
    lines.append("")
    if counts:
        lines.append("Findings per dimension:")
        lines.append("")
        for dim in sorted(counts.keys()):
            lines.append(f"- `{dim}`: {counts[dim]}")
        lines.append("")

    by_story: dict[str, list[AcceptanceCriterion]] = {}
    for ac in acs:
        key = ac.story_id or "(no parent)"
        by_story.setdefault(key, []).append(ac)

    lines.append("## Findings grouped by story")
    lines.append("")
    findings_by_ac: dict[str, list[AcFinding]] = {}
    for f in findings:
        findings_by_ac.setdefault(f.ac_id, []).append(f)
    for story_id in sorted(by_story.keys()):
        orphan = story_id != "(no parent)" and story_id not in story_ids
        suffix = "  _(orphan — no matching user story)_" if orphan else ""
        lines.append(f"### {story_id}{suffix}")
        lines.append("")
        for ac in by_story[story_id]:
            lines.append(f"#### {ac.id}")
            lines.append("")
            lines.append(f"_Source: `{ac.source_file}`_")
            lines.append("")
            lines.append("> " + ac.body.replace("\n", "\n> "))
            lines.append("")
            ac_findings = findings_by_ac.get(ac.id, [])
            if ac_findings:
                lines.append("**Findings:**")
                lines.append("")
                for f in ac_findings:
                    lines.append(f"- `{f.dimension}` — {f.detail}")
                lines.append("")
            else:
                lines.append("_No mechanical findings; AC is ready for review._")
                lines.append("")

    lines.append("## All findings (flat)")
    lines.append("")
    lines.append("| AC | Dimension | Trigger |")
    lines.append("| --- | --- | --- |")
    for f in findings:
        detail = f.detail.replace("|", "\\|")
        lines.append(f"| {f.ac_id} | `{f.dimension}` | {detail} |")
    lines.append("")

    lines.append("## Traceability")
    lines.append("")
    lines.append("Parsed AC IDs (document order):")
    lines.append("")
    lines.append(", ".join(ac.id for ac in acs))
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Top-level entry
# ---------------------------------------------------------------------------

def review(project_root: Path) -> ReviewResult:
    project_root = Path(project_root)
    workspace = project_root / WORKSPACE_DIRNAME
    if not workspace.is_dir():
        raise UninitializedWorkspaceError(
            f"workspace not found: {workspace} (run /tc:init first)"
        )

    acs, story_ids = parse_workspace(workspace)
    findings = apply_checks(acs, story_ids)

    requirements_dir = workspace / "requirements"
    requirements_dir.mkdir(parents=True, exist_ok=True)
    review_path = requirements_dir / "acceptance-criteria-review.md"
    review_path.write_text(
        _render_review(acs, findings, story_ids), encoding="utf-8",
    )

    return ReviewResult(
        workspace=workspace,
        ac_count=len(acs),
        findings=findings,
        review_path=review_path,
        story_ids=story_ids,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review acceptance criteria under .test-commander/documents/uploaded/ "
                    "and write the Phase 2 AC-rubric review artifact.",
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Path to the consuming project root (default: cwd).",
    )
    args = parser.parse_args(argv)

    try:
        result = review(Path(args.project_root))
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"workspace:        {result.workspace}")
    print(f"ACs:              {result.ac_count}")
    print(f"parent stories:   {len(result.story_ids)}")
    print(f"findings:         {len(result.findings)}")
    print(f"review:           {result.review_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
