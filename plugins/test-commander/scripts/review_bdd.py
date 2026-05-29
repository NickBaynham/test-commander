#!/usr/bin/env python3
"""/tc:review-bdd helper - Phase 5 Step 5.3.

Reviews Gherkin ``.feature`` files under ``<workspace>/bdd/features/`` against
a deterministic six-category universal rubric, writes a verdict into each
feature's ``<workspace>/bdd/summaries/<area>.md`` summary, and routes failures
to ``<workspace>/requirements/open-questions.md`` as ``[bdd-review]`` gap
signals (deduplicated by per-area source-id + question text, the Phase-2
contract).

Universal rubric categories (D19):

- ``ambiguous-step``      - a step uses vague words (``something``, ``it works``).
- ``missing-tag``         - a scenario has no ``@area:`` namespace tag.
- ``untraceable``         - a scenario has no ``@req:``/``@cs:`` linkage tag.
- ``ui-coupled-step``     - a step describes clicks / selectors / URLs.
- ``missing-examples``    - a ``Scenario Outline`` has no ``Examples:`` table.
- ``conjunction-overload``- a step chains multiple behaviors with ``and``.

``review_features()`` is the shared entry point: the standalone ``/tc:review-bdd``
command and the ``/tc:generate-bdd`` generate-time auto-run both call it.

Project extensions to the rubric union via ``tc-bdd.review.rubric-extensions``
in ``<workspace>/config.yaml`` (extra vague / ui tokens).

Per D18 the helper ships inside the plugin. Mirrors the ``_review_session()``
rubric pattern from Phase 4's ``explore.py`` and the open-questions append +
dedup pattern from Phase 2/3.

Exit codes:
    0 - review complete.
    2 - precondition failure (uninitialized workspace, no feature files).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"

STEP_KEYWORDS = {"Given", "When", "Then", "And", "But"}

VAGUE_RE = re.compile(
    r"\b(something|stuff|somehow|works|appropriately|properly|correctly)\b", re.I
)
UI_RE = re.compile(
    r"\b(click|clicks|clicked|button|navigate|navigates|url|selector|xpath|css)\b", re.I
)

MESSAGES: dict[str, str] = {
    "ambiguous-step": (
        "has a vague step; name the concrete subject and expected outcome "
        "instead of words like 'something' or 'it works'"
    ),
    "missing-tag": "has no @area: namespace tag; add @area:<feature>",
    "untraceable": (
        "has no @req:/@cs: linkage tag, so it cannot be traced to a requirement "
        "or candidate"
    ),
    "ui-coupled-step": (
        "describes UI mechanics (clicks, selectors, URLs) instead of behavior"
    ),
    "missing-examples": "is a Scenario Outline with no Examples: table",
    "conjunction-overload": (
        "chains multiple behaviors in one step; split into atomic steps"
    ),
}


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ReviewBddError(Exception):
    pass


class UninitializedWorkspaceError(ReviewBddError):
    pass


class FeaturesMissingError(ReviewBddError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedScenario:
    name: str
    is_outline: bool
    tags: list[str]
    steps: list[str]
    has_examples: bool


@dataclass(frozen=True)
class Finding:
    category: str
    scenario: str
    message: str


@dataclass
class ReviewOutcome:
    feature_count: int = 0
    finding_count: int = 0
    findings_by_feature: dict[str, list[Finding]] = field(default_factory=dict)


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
# Config extensions
# ---------------------------------------------------------------------------


def load_rubric_extensions(workspace: Path) -> tuple[list[str], list[str]]:
    """Read ``tc-bdd.review.rubric-extensions`` -> (extra_vague, extra_ui)."""
    config_path = workspace / "config.yaml"
    if not config_path.is_file():
        return [], []
    try:
        import yaml

        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        ext = data["tc-bdd"]["review"]["rubric-extensions"]
    except Exception:
        return [], []
    vague = [str(t) for t in ext.get("vague-words", [])] if isinstance(ext, dict) else []
    ui = [str(t) for t in ext.get("ui-words", [])] if isinstance(ext, dict) else []
    return vague, ui


# ---------------------------------------------------------------------------
# Feature parsing
# ---------------------------------------------------------------------------


SCENARIO_RE = re.compile(r"^(Scenario Outline|Scenario):\s*(.*)$")


def parse_feature_file(path: Path) -> list[ParsedScenario]:
    """Parse a ``.feature`` file into scenarios with tags, steps, and
    examples-presence. Tags are the contiguous ``@`` lines preceding a
    Scenario; feature-level tags are not propagated (the v1 rubric checks
    per-scenario tags)."""
    scenarios: list[ParsedScenario] = []
    pending_tags: list[str] = []
    name = ""
    is_outline = False
    tags: list[str] = []
    steps: list[str] = []
    has_examples = False
    open_scenario = False

    def close() -> None:
        nonlocal open_scenario
        if open_scenario:
            scenarios.append(
                ParsedScenario(name, is_outline, list(tags), list(steps), has_examples)
            )
        open_scenario = False

    for raw in path.read_text(encoding="utf-8").split("\n"):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("@"):
            close()
            pending_tags.extend(stripped.split())
            continue
        if stripped.startswith("Feature:"):
            close()
            pending_tags = []
            continue
        match = SCENARIO_RE.match(stripped)
        if match:
            close()
            is_outline = match.group(1) == "Scenario Outline"
            name = match.group(2).strip()
            tags = pending_tags
            pending_tags = []
            steps = []
            has_examples = False
            open_scenario = True
            continue
        if not open_scenario:
            continue
        if stripped.startswith("Examples:"):
            has_examples = True
        elif stripped.split(" ", 1)[0] in STEP_KEYWORDS:
            steps.append(stripped)
    close()
    return scenarios


# ---------------------------------------------------------------------------
# Rubric
# ---------------------------------------------------------------------------


def review_scenario(
    sc: ParsedScenario, vague_re: re.Pattern, ui_re: re.Pattern
) -> list[Finding]:
    findings: list[Finding] = []

    def add(category: str) -> None:
        findings.append(Finding(category, sc.name, MESSAGES[category]))

    if not any(t.startswith("@area:") for t in sc.tags):
        add("missing-tag")
    if not any(t.startswith("@req:") or t.startswith("@cs:") for t in sc.tags):
        add("untraceable")
    if sc.is_outline and not sc.has_examples:
        add("missing-examples")
    if any(vague_re.search(step) for step in sc.steps):
        add("ambiguous-step")
    if any(ui_re.search(step) for step in sc.steps):
        add("ui-coupled-step")
    if any(step.lower().count(" and ") >= 2 for step in sc.steps):
        add("conjunction-overload")
    return findings


def review_one(
    path: Path, vague_re: re.Pattern, ui_re: re.Pattern
) -> list[Finding]:
    findings: list[Finding] = []
    for sc in parse_feature_file(path):
        findings.extend(review_scenario(sc, vague_re, ui_re))
    return findings


# ---------------------------------------------------------------------------
# Summary verdict + open-questions
# ---------------------------------------------------------------------------

VERDICT_RE = re.compile(r"^- Review verdict: .*$", re.MULTILINE)


def update_summary_verdict(summaries_dir: Path, area: str, findings: list[Finding]) -> None:
    path = summaries_dir / f"{area}.md"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if findings:
        cats = ", ".join(sorted({f.category for f in findings}))
        verdict = f"{len(findings)} finding(s) - categories: {cats}"
    else:
        verdict = "pass"
    new = VERDICT_RE.sub(f"- Review verdict: {verdict}", text)
    if new != text:
        path.write_text(new, encoding="utf-8")


OPEN_QUESTIONS_HEADER = "# Open questions"


def append_open_questions(workspace: Path, gaps: list[tuple[str, Finding]]) -> None:
    target = workspace / "requirements" / "open-questions.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.read_text(encoding="utf-8") if target.is_file() else ""
    if not existing.strip():
        existing = (
            f"{OPEN_QUESTIONS_HEADER}\n\n"
            "Append-only log of questions raised by tc-bdd and other commands. "
            "Deduplicated by source-id + question text.\n"
        )

    existing_set: set[tuple[str, str]] = set()
    for line in existing.split("\n"):
        m = re.match(r"^- \[([^\]]+)\]\s+(.+)$", line)
        if m:
            existing_set.add((m.group(1).strip(), m.group(2).strip()))

    new_lines: list[str] = []
    for area, finding in gaps:
        source_id = f"tc-bdd/bdd-review-{area}"
        question = (
            f"[bdd-review] {finding.category}: scenario '{finding.scenario}' "
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


def review_features(project_root: Path) -> ReviewOutcome:
    """Review every feature under bdd/features/, update summary verdicts, and
    route findings to open-questions. The shared code path /tc:review-bdd runs
    standalone and /tc:generate-bdd auto-runs after generation."""
    workspace = workspace_dir(project_root)
    features_dir = workspace / "bdd" / "features"
    feats = sorted(features_dir.glob("*.feature")) if features_dir.is_dir() else []
    if not feats:
        raise FeaturesMissingError(
            "no feature files found under bdd/features/. "
            "Run /tc:generate-bdd first."
        )

    vague_extra, ui_extra = load_rubric_extensions(workspace)
    vague_re = (
        re.compile(VAGUE_RE.pattern + "|" + "|".join(re.escape(t) for t in vague_extra), re.I)
        if vague_extra
        else VAGUE_RE
    )
    ui_re = (
        re.compile(UI_RE.pattern + "|" + "|".join(re.escape(t) for t in ui_extra), re.I)
        if ui_extra
        else UI_RE
    )

    summaries_dir = workspace / "bdd" / "summaries"
    gaps: list[tuple[str, Finding]] = []
    outcome = ReviewOutcome()
    for path in feats:
        area = path.stem
        findings = review_one(path, vague_re, ui_re)
        update_summary_verdict(summaries_dir, area, findings)
        for finding in findings:
            gaps.append((area, finding))
        outcome.feature_count += 1
        outcome.finding_count += len(findings)
        outcome.findings_by_feature[area] = findings

    append_open_questions(workspace, gaps)
    return outcome


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Review Gherkin feature files under bdd/features/ against the "
            "six-category universal rubric. Writes verdicts into bdd/summaries/ "
            "and routes failures to requirements/open-questions.md."
        ),
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root (default: current directory).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        outcome = review_features(project_root)
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FeaturesMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"reviewed: {outcome.feature_count} feature(s) "
        f"({outcome.finding_count} finding(s))"
    )
    for area, findings in sorted(outcome.findings_by_feature.items()):
        verdict = "pass" if not findings else f"{len(findings)} finding(s)"
        print(f"  - {area}: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
