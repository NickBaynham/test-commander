#!/usr/bin/env python3
"""/tc:analyze-results helper - Phase 7 Step 7.4.

Triages the results of a test run. Reads a ``runs/<RUN-ID>/results.json``
record (the machine-readable record ``/tc:run`` writes), classifies every
non-passed result against a universal triage rubric, detects flaky tests from
the recorded pass-on-retry signal, writes a per-run ``analysis.md``, and routes
confirmed gaps to ``requirements/open-questions.md`` as deduplicated
``[test-analysis]`` signals.

Design reference: ``agentic-playwright-automation:investigate-playwright-failure``
(the failure-triage rubric). Mirrors the ``review_*`` rubric pattern -
mechanical signals decide the category; Claude adds the judgment layer.

The universal triage rubric (one category per non-passed result):

- ``flaky`` - the test passed on retry (the recorded ``flaky`` status / a
  pass-on-retry). Detected from status, not from the error text.
- ``environment`` - the failure error names an infrastructure / network /
  timeout signal (connection refused, navigation timeout, target closed).
- ``test-defect`` - the failure error names a locator / selector / strict-mode
  problem (the test, not the product, is wrong).
- ``product-defect`` - the default for a genuine assertion failure: the product
  behaved differently from what the scenario asserts.

Deterministic: the analysis is derived from the run record (no clock), so a
re-run over an unchanged record is byte-identical, and the open-questions
routing dedups by ``(source-id, question)`` (the Phase-2 contract), so the same
scenario+category is one open question, not one-per-run.

Per D18 the helper ships inside the plugin. Per D19 the rubric vocabulary is
universal.

Exit codes:
    0 - analysis written.
    2 - precondition failure (uninitialized workspace, no run records).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"

# Mechanical triage signals over the failure error text. Order = precedence.
ENVIRONMENT_RE = re.compile(
    r"econnrefused|enotfound|etimedout|net::|connection refused|navigation (?:timeout|failed)|"
    r"target (?:closed|crashed)|timed out waiting for|navigating to",
    re.I,
)
TEST_DEFECT_RE = re.compile(
    r"locator|selector|strict mode|element is not|no (?:node|element)s? found|"
    r"waiting for (?:selector|locator)|tobevisible|tobeenabled|resolved to \d+ elements",
    re.I,
)

# Per-category open-questions message (the gap the signal records).
MESSAGES: dict[str, str] = {
    "product-defect": (
        "failed on an assertion mismatch - confirm the expected behavior or fix the product"
    ),
    "test-defect": (
        "failed on a locator/selector problem - the test needs fixing, not the product"
    ),
    "environment": (
        "failed on an environment/timeout signal - verify the target environment before re-running"
    ),
    "flaky": (
        "is flaky (passed on retry) - investigate the non-determinism before trusting it"
    ),
}


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class AnalyzeError(Exception):
    pass


class UninitializedWorkspaceError(AnalyzeError):
    pass


class RunRecordMissingError(AnalyzeError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Classification:
    req_id: str | None
    cs_id: str | None
    scenario: str
    status: str
    category: str

    def sort_key(self) -> tuple[str, str, str]:
        return (self.req_id or "", self.cs_id or "", self.scenario)


@dataclass
class AnalyzeOutcome:
    run_id: str
    classifications: list[Classification] = field(default_factory=list)

    def count(self, category: str) -> int:
        return sum(1 for c in self.classifications if c.category == category)


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


def _latest_run_id(workspace: Path) -> str:
    records = sorted((workspace / "runs").glob("*/results.json"))
    if not records:
        raise RunRecordMissingError(
            "no run records found under runs/. Run /tc:run first."
        )
    return records[-1].parent.name


def _load_record(workspace: Path, run_id: str) -> dict:
    path = workspace / "runs" / run_id / "results.json"
    if not path.is_file():
        raise RunRecordMissingError(
            f"no run record for {run_id} (expected runs/{run_id}/results.json). "
            "Run /tc:run first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Triage
# ---------------------------------------------------------------------------


def classify(status: str, error: str | None) -> str | None:
    """Return the triage category for a result, or None if it passed."""
    if status == "flaky":
        return "flaky"
    if status != "failed":
        return None
    text = error or ""
    if ENVIRONMENT_RE.search(text):
        return "environment"
    if TEST_DEFECT_RE.search(text):
        return "test-defect"
    return "product-defect"


def triage(record: dict) -> list[Classification]:
    classifications: list[Classification] = []
    for result in record.get("results", []):
        category = classify(result.get("status", ""), result.get("error"))
        if category is None:
            continue
        classifications.append(
            Classification(
                req_id=result.get("requirement"),
                cs_id=result.get("candidate"),
                scenario=result.get("scenario", ""),
                status=result.get("status", ""),
                category=category,
            )
        )
    return sorted(classifications, key=lambda c: c.sort_key())


# ---------------------------------------------------------------------------
# Rendering + open-questions
# ---------------------------------------------------------------------------


def _md_cell(value: str | None) -> str:
    return value if value else "_(none)_"


def render_analysis(run_id: str, classifications: list[Classification]) -> str:
    by_cat = sorted({c.category for c in classifications})
    counts = ", ".join(f"{cat}: {sum(1 for c in classifications if c.category == cat)}"
                       for cat in by_cat) or "none"
    lines: list[str] = []
    lines.append(f"# Test analysis {run_id}")
    lines.append("")
    lines.append(f"- Triaged: {len(classifications)} non-passed result(s) ({counts})")
    lines.append("")
    if not classifications:
        lines.append("_No failures or flaky tests in this run._")
        lines.append("")
        return "\n".join(lines)
    lines.append("| requirement | candidate | scenario | result | classification |")
    lines.append("| --- | --- | --- | --- | --- |")
    for c in classifications:
        lines.append(
            f"| {_md_cell(c.req_id)} | {_md_cell(c.cs_id)} | {c.scenario} | "
            f"{c.status} | {c.category} |"
        )
    lines.append("")
    return "\n".join(lines)


OPEN_QUESTIONS_HEADER = "# Open questions"
EXISTING_RE = re.compile(r"^- \[([^\]]+)\]\s+(.+)$")


def append_open_questions(workspace: Path, classifications: list[Classification]) -> None:
    target = workspace / "requirements" / "open-questions.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.read_text(encoding="utf-8") if target.is_file() else ""
    if not existing.strip():
        existing = (
            f"{OPEN_QUESTIONS_HEADER}\n\n"
            "Append-only log of questions raised by tc-run and other commands. "
            "Deduplicated by source-id + question text.\n"
        )

    existing_set: set[tuple[str, str]] = set()
    for line in existing.split("\n"):
        m = EXISTING_RE.match(line)
        if m:
            existing_set.add((m.group(1).strip(), m.group(2).strip()))

    new_lines: list[str] = []
    for c in classifications:
        source_id = f"tc-run/test-analysis-{c.cs_id or c.scenario}"
        question = (
            f"[test-analysis] {c.category}: scenario '{c.scenario}' "
            f"{MESSAGES[c.category]}".rstrip(".") + "."
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
# Entry point
# ---------------------------------------------------------------------------


def analyze(project_root: Path, *, run_id: str | None = None) -> AnalyzeOutcome:
    project_root = Path(project_root)
    workspace = workspace_dir(project_root)
    run_id = run_id or _latest_run_id(workspace)
    record = _load_record(workspace, run_id)

    classifications = triage(record)
    (workspace / "runs" / run_id / "analysis.md").write_text(
        render_analysis(run_id, classifications), encoding="utf-8"
    )
    append_open_questions(workspace, classifications)
    return AnalyzeOutcome(run_id=run_id, classifications=classifications)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Triage a test run: classify failures (product-defect / test-defect "
            "/ environment / flaky), write runs/<RUN-ID>/analysis.md, and route "
            "[test-analysis] gap signals to requirements/open-questions.md."
        ),
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    parser.add_argument(
        "--run-id", default=None, help="The RUN-ID to analyze (default: the latest run)."
    )
    args = parser.parse_args(argv if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        outcome = analyze(project_root, run_id=args.run_id)
    except AnalyzeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    cats = ", ".join(
        f"{cat}: {outcome.count(cat)}"
        for cat in ("product-defect", "test-defect", "environment", "flaky")
        if outcome.count(cat)
    ) or "no failures"
    print(f"analyzed: {outcome.run_id} - {len(outcome.classifications)} triaged ({cats})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
