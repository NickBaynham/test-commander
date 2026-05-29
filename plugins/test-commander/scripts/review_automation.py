#!/usr/bin/env python3
"""/tc:review-automation helper - Phase 6 Step 6.5.

Reviews the generated Playwright specs under ``tests/e2e/*.spec.ts`` against a
deterministic six-category universal rubric, writes a per-spec verdict to
``<workspace>/automation-plan/review-summary.md``, and routes failures to
``<workspace>/requirements/open-questions.md`` as ``[automation-review]`` gap
signals (deduplicated by per-spec source-id + question text, the Phase-2
contract).

Universal rubric categories (D19):

- ``inline-test-data``    - a step passes a literal to ``.fill``/``.type`` instead
                            of reaching data through the fixture (D6).
- ``hardcoded-wait``      - the spec uses ``waitForTimeout``/``sleep``.
- ``missing-provenance``  - a ``test()`` has no ``// @req:``/``@cs:`` comment.
- ``weak-locator``        - a CSS/XPath selector (``.locator('#'``/``'.'``, ``xpath=``,
                            ``page.$``) instead of a role/label/test-id locator.
- ``untraceable-spec``    - the spec file is not linked in ``automation-map.md``.
- ``assertion-free``      - a ``test()`` contains no ``expect(`` call.

``review_automation()`` is the shared entry point: the standalone
``/tc:review-automation`` command and the ``/tc:automate`` generate-time
auto-run both call it.

Per D18 the helper ships inside the plugin. Mirrors ``review_bdd.py``: workspace
IO + rubric + summary verdict + open-questions append/dedup + CLI.

Exit codes:
    0 - review complete.
    2 - precondition failure (uninitialized workspace, no specs).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"

TEST_RE = re.compile(r"^\s*test\(")
PROVENANCE_RE = re.compile(r"@req:|@cs:")
EXPECT_RE = re.compile(r"\bexpect\(")
INLINE_DATA_RE = re.compile(r"\.(fill|type|selectOption)\(\s*['\"`]")
WAIT_RE = re.compile(r"waitForTimeout\(|\.sleep\(")
WEAK_LOCATOR_RE = re.compile(r"\.locator\(['\"`][.#\[]|xpath=|page\.\$\(")
SPEC_PATH_RE = re.compile(r"tests/e2e/[\w-]+\.spec\.ts")

MESSAGES: dict[str, str] = {
    "inline-test-data": (
        "inlines test data in a fill/type call; reach data through the fixture "
        "instead (D6)"
    ),
    "hardcoded-wait": (
        "uses a hardcoded wait; rely on Playwright auto-waiting and web-first "
        "assertions"
    ),
    "missing-provenance": (
        "has a test() with no // @req:/@cs: provenance comment, so it cannot be "
        "traced"
    ),
    "weak-locator": (
        "uses a CSS/XPath selector; prefer a role/label/test-id locator"
    ),
    "untraceable-spec": (
        "is not linked in automation-map.md; regenerate it via /tc:automate"
    ),
    "assertion-free": "has a test() with no expect() assertion",
}


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ReviewAutomationError(Exception):
    pass


class UninitializedWorkspaceError(ReviewAutomationError):
    pass


class SpecsMissingError(ReviewAutomationError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    category: str
    spec: str
    message: str


@dataclass
class ReviewOutcome:
    spec_count: int = 0
    finding_count: int = 0
    findings_by_spec: dict[str, list[Finding]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Workspace IO
# ---------------------------------------------------------------------------


def workspace_dir(project_root: Path) -> Path:
    ws = project_root / WORKSPACE_DIRNAME
    if not ws.is_dir():
        raise UninitializedWorkspaceError(
            f"not a Test Commander workspace: {project_root} "
            f"(no {WORKSPACE_DIRNAME}/). Run /tc:init first."
        )
    return ws


# ---------------------------------------------------------------------------
# Rubric
# ---------------------------------------------------------------------------


def _test_units(lines: list[str]) -> list[tuple[list[str], list[str]]]:
    """Split a spec into (lead-comments, body) units, one per test(). The lead
    is the contiguous ``//`` comment lines immediately above the ``test(`` line;
    the body runs to the next test() (excluding that test's lead comments)."""
    idxs = [i for i, ln in enumerate(lines) if TEST_RE.match(ln)]
    units: list[tuple[list[str], list[str]]] = []
    for k, ti in enumerate(idxs):
        j = ti - 1
        lead: list[str] = []
        while j >= 0 and lines[j].strip().startswith("//"):
            lead.insert(0, lines[j])
            j -= 1
        end = idxs[k + 1] if k + 1 < len(idxs) else len(lines)
        while end - 1 > ti and lines[end - 1].strip().startswith("//"):
            end -= 1
        units.append((lead, lines[ti:end]))
    return units


def review_spec_text(text: str, *, traceable: bool) -> set[str]:
    """Return the set of rubric categories a single spec violates."""
    lines = text.split("\n")
    categories: set[str] = set()

    if not traceable:
        categories.add("untraceable-spec")
    if WAIT_RE.search(text):
        categories.add("hardcoded-wait")
    if WEAK_LOCATOR_RE.search(text):
        categories.add("weak-locator")
    if INLINE_DATA_RE.search(text):
        categories.add("inline-test-data")

    for lead, body in _test_units(lines):
        if not any(PROVENANCE_RE.search(ln) for ln in lead):
            categories.add("missing-provenance")
        if not any(EXPECT_RE.search(ln) for ln in body):
            categories.add("assertion-free")
    return categories


# ---------------------------------------------------------------------------
# Automation-map (traceability)
# ---------------------------------------------------------------------------


def mapped_specs(workspace: Path) -> set[str]:
    path = workspace / "traceability" / "automation-map.md"
    if not path.is_file():
        return set()
    return set(SPEC_PATH_RE.findall(path.read_text(encoding="utf-8")))


# ---------------------------------------------------------------------------
# Review summary
# ---------------------------------------------------------------------------


def render_summary(outcome: ReviewOutcome) -> str:
    lines: list[str] = []
    lines.append("# Automation review")
    lines.append("")
    lines.append("_Generated by /tc:review-automation. One row per reviewed spec._")
    lines.append("")
    lines.append(f"- Specs: {outcome.spec_count}")
    lines.append(f"- Findings: {outcome.finding_count}")
    lines.append("")
    lines.append("| spec | verdict |")
    lines.append("| --- | --- |")
    for spec in sorted(outcome.findings_by_spec):
        findings = outcome.findings_by_spec[spec]
        if findings:
            cats = ", ".join(sorted({f.category for f in findings}))
            verdict = f"{len(findings)} finding(s) - categories: {cats}"
        else:
            verdict = "pass"
        lines.append(f"| {spec} | {verdict} |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Open-questions append + dedup (mirrors review_bdd)
# ---------------------------------------------------------------------------

OPEN_QUESTIONS_HEADER = "# Open questions"


def append_open_questions(workspace: Path, findings: list[Finding]) -> None:
    target = workspace / "requirements" / "open-questions.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.read_text(encoding="utf-8") if target.is_file() else ""
    if not existing.strip():
        existing = (
            f"{OPEN_QUESTIONS_HEADER}\n\n"
            "Append-only log of questions raised by tc-automate and other "
            "commands. Deduplicated by source-id + question text.\n"
        )

    existing_set: set[tuple[str, str]] = set()
    for line in existing.split("\n"):
        m = re.match(r"^- \[([^\]]+)\]\s+(.+)$", line)
        if m:
            existing_set.add((m.group(1).strip(), m.group(2).strip()))

    new_lines: list[str] = []
    for finding in findings:
        area = Path(finding.spec).stem.replace(".spec", "")
        source_id = f"tc-automate/automation-review-{area}"
        question = (
            f"[automation-review] {finding.category}: spec '{finding.spec}' "
            f"{finding.message}".rstrip(".") + "."
        )
        key = (source_id, question)
        if key in existing_set:
            continue
        existing_set.add(key)
        new_lines.append(f"- [{source_id}] {question}")

    if not new_lines:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        target.write_text(existing, encoding="utf-8")
        return
    body = existing.rstrip("\n") + "\n\n" + "\n".join(new_lines) + "\n"
    target.write_text(body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Shared entry point
# ---------------------------------------------------------------------------


def review_automation(project_root: Path) -> ReviewOutcome:
    """Review every spec under tests/e2e/, write the review summary, and route
    findings to open-questions. The shared code path /tc:review-automation runs
    standalone and /tc:automate auto-runs after generation."""
    workspace = workspace_dir(project_root)
    e2e_dir = project_root / "tests" / "e2e"
    specs = sorted(e2e_dir.glob("*.spec.ts")) if e2e_dir.is_dir() else []
    if not specs:
        raise SpecsMissingError(
            "no specs found under tests/e2e/. Run /tc:automate first."
        )

    traceable = mapped_specs(workspace)
    all_findings: list[Finding] = []
    outcome = ReviewOutcome()
    for path in specs:
        rel = f"tests/e2e/{path.name}"
        categories = review_spec_text(
            path.read_text(encoding="utf-8"), traceable=rel in traceable
        )
        findings = [Finding(c, rel, MESSAGES[c]) for c in sorted(categories)]
        outcome.spec_count += 1
        outcome.finding_count += len(findings)
        outcome.findings_by_spec[rel] = findings
        all_findings.extend(findings)

    summary_path = workspace / "automation-plan" / "review-summary.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(render_summary(outcome), encoding="utf-8")
    append_open_questions(workspace, all_findings)
    return outcome


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review generated specs under tests/e2e/ against the six-category "
            "universal rubric. Writes automation-plan/review-summary.md and "
            "routes failures to requirements/open-questions.md."
        ),
    )
    parser.add_argument(
        "project_root", nargs="?", default=".",
        help="Project root (default: current directory).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        outcome = review_automation(project_root)
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except SpecsMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"reviewed: {outcome.spec_count} spec(s) "
        f"({outcome.finding_count} finding(s))"
    )
    for spec, findings in sorted(outcome.findings_by_spec.items()):
        verdict = "pass" if not findings else f"{len(findings)} finding(s)"
        print(f"  - {spec}: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
