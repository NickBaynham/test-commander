#!/usr/bin/env python3
"""/tc:review-user-stories helper.

Reads `*.md` files in `<workspace>/documents/uploaded/` that declare
`US-NNN` markers, applies the Phase 2 INVEST rubric plus role-action-
benefit shape and acceptance-criteria-pointer checks, and writes
`<workspace>/requirements/user-story-review.md`.

Per D18 the helper ships inside the plugin so consuming-project users
can invoke it after `claude plugin install`. Per D19 all checks use
universal English / agile vocabulary; no domain-specific keywords ship
with the tool.

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
US_PATTERN = re.compile(r"\bUS-(\d{1,4})\b")
US_HEADER = re.compile(r"^(?:[-*]\s*)?US-(\d{1,4})\s*:\s*(.*)$", re.MULTILINE)
AC_POINTER = re.compile(r"\bAC-\d+\b")

DEPENDENCY_CLAUSE = re.compile(r"\b(?:depends on|after|requires)\b\s+US-\d+", re.IGNORECASE)
UI_COORDINATE = re.compile(r"\(\s*\d+\s*,\s*\d+\s*\)")
PIXEL_DIMENSION = re.compile(r"\b\d+\s*px\b", re.IGNORECASE)
NO_DEVIATION = re.compile(r"\bno deviation\b", re.IGNORECASE)
HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")

ENGINEERING_VERBS = {"refactor", "refactoring"}
DEVELOPER_ROLES = {
    "backend developer", "frontend developer", "fullstack developer",
    "full-stack developer", "software developer", "software engineer",
    "junior developer", "senior developer", "engineering manager",
}
VAGUE_ACTIONS = {"better", "improved", "enhanced", "more", "faster", "smarter", "nicer"}
SUBJECTIVE_EXPERIENCE = {
    "feel", "delight", "delightful", "enjoyable", "intuitive",
    "satisfying", "pleasing", "fun", "love",
}
NUMERIC_THRESHOLD = re.compile(
    r"\b\d+(\.\d+)?\s*(%|ms|s|min|hr|hours?|days?|GB|MB|KB|requests?|users?)?\b"
)


# ---------------------------------------------------------------------------
# Exceptions and dataclasses
# ---------------------------------------------------------------------------

class UserStoryError(Exception):
    """Base class for review_user_stories errors."""


class UninitializedWorkspaceError(UserStoryError):
    """Raised when `<project>/.test-commander/` does not exist."""


@dataclass
class UserStory:
    id: str
    body: str
    source_file: str


@dataclass
class UserStoryFinding:
    story_id: str
    dimension: str
    detail: str


@dataclass
class ReviewResult:
    workspace: Path
    story_count: int
    findings: list[UserStoryFinding]
    review_path: Path | None = None
    verdicts: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def is_user_stories_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    return bool(US_PATTERN.search(text))


def parse_file(path: Path) -> list[UserStory]:
    text = path.read_text(encoding="utf-8")
    matches = list(US_HEADER.finditer(text))
    stories: list[UserStory] = []
    for i, m in enumerate(matches):
        sid = f"US-{int(m.group(1)):03d}"
        first_line = m.group(2).strip()
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
        stories.append(UserStory(id=sid, body=body, source_file=path.name))
    return stories


def parse_workspace(workspace: Path) -> list[UserStory]:
    uploaded = workspace / "documents" / "uploaded"
    if not uploaded.is_dir():
        return []
    all_stories: list[UserStory] = []
    for md in sorted(uploaded.glob("*.md")):
        if not is_user_stories_file(md):
            continue
        all_stories.extend(parse_file(md))
    return all_stories


# ---------------------------------------------------------------------------
# Check helpers
# ---------------------------------------------------------------------------

def _contains_phrase(body: str, phrase: str) -> bool:
    p = phrase.lower()
    b = body.lower()
    if " " in p or "-" in p:
        return p in b
    return bool(re.search(rf"\b{re.escape(p)}s?\b", b))


def _hits(body: str, keywords) -> list[str]:
    return [k for k in keywords if _contains_phrase(body, k)]


def _word_count(text: str) -> int:
    return len(text.split())


def _comma_item_count(body: str) -> int:
    match = re.search(r"\bI\s+want\s+to\b(.+?)(?:\bSo that\b|$)", body, re.IGNORECASE | re.DOTALL)
    if not match:
        return 0
    return len(re.findall(r",", match.group(1)))


# ---------------------------------------------------------------------------
# Per-INVEST-letter checks
# ---------------------------------------------------------------------------

def _check_independent(story: UserStory) -> UserStoryFinding | None:
    match = DEPENDENCY_CLAUSE.search(story.body)
    if match:
        return UserStoryFinding(
            story.id, "invest-independent",
            f"explicit dependency clause: '{match.group(0)}'",
        )
    return None


def _check_negotiable(story: UserStory) -> UserStoryFinding | None:
    signals: list[str] = []
    if UI_COORDINATE.search(story.body):
        signals.append("UI coordinates")
    if PIXEL_DIMENSION.search(story.body):
        signals.append("pixel dimensions")
    if HEX_COLOR.search(story.body):
        signals.append("hex color")
    if NO_DEVIATION.search(story.body):
        signals.append("'no deviation' clause")
    if signals:
        return UserStoryFinding(
            story.id, "invest-negotiable",
            f"over-specified signal(s): {', '.join(signals)}",
        )
    return None


def _check_valuable(story: UserStory) -> UserStoryFinding | None:
    body_lower = story.body.lower()
    eng_hits = [v for v in ENGINEERING_VERBS if v in body_lower]
    dev_roles = [r for r in DEVELOPER_ROLES if r in body_lower]
    if eng_hits or dev_roles:
        signals = []
        if dev_roles:
            signals.append(f"developer-as-actor: {', '.join(sorted(dev_roles))}")
        if eng_hits:
            signals.append(f"engineering verb(s): {', '.join(sorted(eng_hits))}")
        return UserStoryFinding(
            story.id, "invest-valuable",
            "; ".join(signals),
        )
    return None


def _check_estimable(story: UserStory) -> UserStoryFinding | None:
    vague = _hits(story.body, VAGUE_ACTIONS)
    if vague and not NUMERIC_THRESHOLD.search(story.body):
        joined = ", ".join(sorted(vague))
        return UserStoryFinding(
            story.id, "invest-estimable",
            f"vague action(s) without numeric predicate: {joined}",
        )
    return None


def _check_small(story: UserStory) -> UserStoryFinding | None:
    comma_items = _comma_item_count(story.body)
    word_count = _word_count(story.body)
    if comma_items >= 4:
        return UserStoryFinding(
            story.id, "invest-small",
            f"I-want clause bundles {comma_items + 1}+ actions in a comma-list",
        )
    if word_count > 40:
        return UserStoryFinding(
            story.id, "invest-small",
            f"body too long for one iteration ({word_count} words; threshold > 40)",
        )
    return None


def _check_testable(story: UserStory) -> UserStoryFinding | None:
    subj = _hits(story.body, SUBJECTIVE_EXPERIENCE)
    if subj:
        joined = ", ".join(sorted(subj))
        return UserStoryFinding(
            story.id, "invest-testable",
            f"subjective-experience word(s) without testable predicate: {joined}",
        )
    return None


def _check_shape(story: UserStory) -> UserStoryFinding | None:
    body_lower = story.body.lower()
    has_role = bool(re.search(r"\bas a[n]?\b", body_lower))
    has_action = "i want" in body_lower
    has_benefit = "so that" in body_lower
    missing = []
    if not has_role:
        missing.append("'As a <role>'")
    if not has_action:
        missing.append("'I want <action>'")
    if not has_benefit:
        missing.append("'So that <benefit>'")
    if missing:
        return UserStoryFinding(
            story.id, "role-action-benefit",
            f"missing: {', '.join(missing)}",
        )
    return None


def _check_acceptance_criteria_pointer(story: UserStory) -> UserStoryFinding | None:
    if not AC_POINTER.search(story.body):
        return UserStoryFinding(
            story.id, "needs-acceptance-criteria",
            "no AC-NNN pointer present; route to /tc:review-acceptance-criteria",
        )
    return None


CHECKS = (
    _check_independent,
    _check_negotiable,
    _check_valuable,
    _check_estimable,
    _check_small,
    _check_testable,
    _check_shape,
    _check_acceptance_criteria_pointer,
)


def apply_checks(stories: list[UserStory]) -> list[UserStoryFinding]:
    findings: list[UserStoryFinding] = []
    for s in stories:
        for check in CHECKS:
            f = check(s)
            if f is not None:
                findings.append(f)
    findings.sort(key=lambda f: (f.story_id, f.dimension, f.detail))
    return findings


def compute_verdicts(
    stories: list[UserStory], findings: list[UserStoryFinding],
) -> dict[str, str]:
    by_story: dict[str, list[UserStoryFinding]] = {}
    for f in findings:
        by_story.setdefault(f.story_id, []).append(f)
    verdicts: dict[str, str] = {}
    for s in stories:
        fs = by_story.get(s.id, [])
        if not fs:
            verdicts[s.id] = "ready"
            continue
        has_shape_violation = any(f.dimension == "role-action-benefit" for f in fs)
        invest_count = sum(1 for f in fs if f.dimension.startswith("invest-"))
        if has_shape_violation or invest_count >= 3:
            verdicts[s.id] = "blocked"
        else:
            verdicts[s.id] = "needs-refinement"
    return verdicts


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

def _render_review(
    stories: list[UserStory],
    findings: list[UserStoryFinding],
    verdicts: dict[str, str],
) -> str:
    lines = ["# User Story Review", ""]
    if not stories:
        lines.append("_No user stories found in `documents/uploaded/`._")
        lines.append("")
        lines.append(
            "Drop one or more Markdown files containing `US-NNN: As a ... I want ... So that ...`"
        )
        lines.append("entries into `.test-commander/documents/uploaded/` and re-run.")
        lines.append("")
        return "\n".join(lines)

    counts: dict[str, int] = {}
    for f in findings:
        counts[f.dimension] = counts.get(f.dimension, 0) + 1

    verdict_counts = {"ready": 0, "needs-refinement": 0, "blocked": 0}
    for v in verdicts.values():
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"- Stories parsed: **{len(stories)}**")
    lines.append(f"- Findings: **{len(findings)}** across **{len(counts)}** dimensions")
    lines.append(
        "- Readiness: "
        f"ready={verdict_counts['ready']}, "
        f"needs-refinement={verdict_counts['needs-refinement']}, "
        f"blocked={verdict_counts['blocked']}"
    )
    lines.append("")
    if counts:
        lines.append("Findings per dimension:")
        lines.append("")
        for dim in sorted(counts.keys()):
            lines.append(f"- `{dim}`: {counts[dim]}")
        lines.append("")

    lines.append("## Findings")
    lines.append("")
    lines.append("| Story | Dimension | Trigger |")
    lines.append("| --- | --- | --- |")
    for f in findings:
        detail = f.detail.replace("|", "\\|")
        lines.append(f"| {f.story_id} | `{f.dimension}` | {detail} |")
    lines.append("")

    lines.append("## Per-story detail")
    lines.append("")
    findings_by_story: dict[str, list[UserStoryFinding]] = {}
    for f in findings:
        findings_by_story.setdefault(f.story_id, []).append(f)
    for s in stories:
        verdict = verdicts.get(s.id, "ready")
        lines.append(f"### {s.id} — verdict: `{verdict}`")
        lines.append("")
        lines.append(f"_Source: `{s.source_file}`_")
        lines.append("")
        lines.append("> " + s.body.replace("\n", "\n> "))
        lines.append("")
        story_findings = findings_by_story.get(s.id, [])
        if story_findings:
            lines.append("**Findings:**")
            lines.append("")
            for f in story_findings:
                lines.append(f"- `{f.dimension}` — {f.detail}")
            lines.append("")
        else:
            lines.append("_No mechanical findings; story is ready for the next stage._")
            lines.append("")

    lines.append("## Traceability")
    lines.append("")
    lines.append("Parsed story IDs (document order):")
    lines.append("")
    lines.append(", ".join(s.id for s in stories))
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

    stories = parse_workspace(workspace)
    findings = apply_checks(stories)
    verdicts = compute_verdicts(stories, findings)

    requirements_dir = workspace / "requirements"
    requirements_dir.mkdir(parents=True, exist_ok=True)
    review_path = requirements_dir / "user-story-review.md"
    review_path.write_text(_render_review(stories, findings, verdicts), encoding="utf-8")

    return ReviewResult(
        workspace=workspace,
        story_count=len(stories),
        findings=findings,
        review_path=review_path,
        verdicts=verdicts,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review user stories under .test-commander/documents/uploaded/ "
                    "and write the Phase 2 INVEST review artifact.",
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
    print(f"stories:          {result.story_count}")
    print(f"findings:         {len(result.findings)}")
    print(f"review:           {result.review_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
