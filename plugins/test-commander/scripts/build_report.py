#!/usr/bin/env python3
"""/tc:report helper - Phase 7 Step 7.5.

Aggregates the whole workspace into a single living quality report and snapshots
it into a committed history. Writes
``<workspace>/quality-report/current-quality-report.md`` with every spec'd
section, then a full copy to
``<workspace>/quality-report/history/<YYYY-MM-DD-HHmm>.md``.

The report keeps three classes of content clearly separated, tagged inline:

- ``[fact]`` - a value measured directly from a workspace artifact.
- ``[interpretation]`` - synthesis a human (or Claude) adds; not measured.
- ``[review]`` - an item that needs human review before release.

Per the project's never-invent-metrics rule, every ``[fact]`` is read from an
artifact; a section with no source reads ``_None recorded._`` rather than a
guessed value. The ``[interpretation]`` and ``[review]`` sections carry
deterministic prompts for Claude to fill, not fabricated conclusions.

After writing the report, the helper rebuilds the traceability maps (best
effort) so ``test-map.md``'s ``Test result`` and ``Quality report`` columns
resolve from the run records and this report - the columns Phase 6 left
``pending`` (the resolution itself lives in ``traceability_map``, extended in
this step).

**Injected-clock determinism**: the report's timestamp and the history-snapshot
filename come from an injected ``now`` (the ``--now`` flag / parameter); tests
pass a fixed timestamp so the report and snapshot are byte-stable. Production
reads the wall clock. ``datetime.now()`` is never called at import or inline.

Per D18 the helper ships inside the plugin. Per D19 the section catalog is
universal.

Exit codes:
    0 - report written.
    2 - precondition failure (uninitialized workspace).
"""

from __future__ import annotations

import argparse
import contextlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import traceability_map

WORKSPACE_DIRNAME = ".test-commander"

SECTION_TITLES: tuple[str, ...] = (
    "Executive summary",
    "Coverage",
    "Requirements readiness",
    "Exploratory findings",
    "Automated regression status",
    "Known risks",
    "Known defects",
    "Open questions",
    "Automation health",
    "Flaky tests",
    "Evidence summary",
    "Traceability summary",
    "Recommendations",
    "Release readiness",
    "Recent changes",
)

STUB_MARKER = "_(empty until"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ReportError(Exception):
    pass


class UninitializedWorkspaceError(ReportError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class ReportOutcome:
    report_path: Path
    snapshot_path: Path
    latest_run_id: str | None
    section_count: int


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


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _is_real(text: str) -> bool:
    """True when an artifact carries real content (not the template stub)."""
    return bool(text.strip()) and STUB_MARKER not in text


@dataclass(frozen=True)
class RunData:
    run_id: str | None
    results: list[dict]

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.get("status") == "passed")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.get("status") == "failed")

    @property
    def flaky(self) -> int:
        return sum(1 for r in self.results if r.get("status") == "flaky")


def _latest_run(workspace: Path) -> RunData:
    records = sorted((workspace / "runs").glob("*/results.json"))
    if not records:
        return RunData(run_id=None, results=[])
    data = json.loads(records[-1].read_text(encoding="utf-8"))
    return RunData(run_id=data.get("run_id"), results=list(data.get("results", [])))


def _count(text: str, pattern: re.Pattern[str]) -> int:
    return len(pattern.findall(text)) if _is_real(text) else 0


# ---------------------------------------------------------------------------
# Section rendering
# ---------------------------------------------------------------------------

REQ_ROW_RE = re.compile(r"^\|\s*REQ-\d+\s*\|", re.MULTILINE)
OPEN_Q_RE = re.compile(r"^- \[", re.MULTILINE)
EVIDENCE_ROW_RE = re.compile(r"^\| evidence/", re.MULTILINE)


def _result_rows(results: list[dict], status: str) -> list[str]:
    lines: list[str] = []
    for r in sorted(results, key=lambda x: (x.get("requirement") or "", x.get("candidate") or "")):
        if r.get("status") != status:
            continue
        lines.append(
            f"| {r.get('requirement') or '_(none)_'} | {r.get('candidate') or '_(none)_'} | "
            f"{r.get('scenario', '')} |"
        )
    return lines


def _section(title: str, cls: str, body: list[str]) -> list[str]:
    out = [f"## {title} {cls}", ""]
    out.extend(body)
    out.append("")
    return out


def render_report(workspace: Path, now: datetime) -> str:
    run = _latest_run(workspace)
    inventory = _read(workspace / "requirements" / "requirements-inventory.md")
    open_q = _read(workspace / "requirements" / "open-questions.md")
    evidence = _read(workspace / "evidence" / "evidence-index.md")
    risks = _read(workspace / "risk-register" / "risk-register.md")
    test_map = _read(workspace / "traceability" / "test-map.md")
    review_summary = _read(workspace / "automation-plan" / "review-summary.md")
    sessions_dir = workspace / "sessions"
    sessions = sorted(sessions_dir.glob("*.md")) if sessions_dir.is_dir() else []
    session_count = sum(1 for p in sessions if _is_real(_read(p)))

    req_count = _count(inventory, REQ_ROW_RE)
    open_count = _count(open_q, OPEN_Q_RE)
    evidence_count = _count(evidence, EVIDENCE_ROW_RE)
    run_label = run.run_id or "_no run yet_"

    lines: list[str] = []
    lines.append("# Current Quality Report")
    lines.append("")
    lines.append(f"- Generated: {now.isoformat()} (injected clock)")
    lines.append("")
    lines.append("## How to read this report")
    lines.append("")
    lines.append("- **[fact]** - measured directly from a workspace artifact.")
    lines.append("- **[interpretation]** - synthesis a human or Claude adds; not a measured value.")
    lines.append("- **[review]** - an item that needs human review before release.")
    lines.append("")

    lines += _section(
        "Executive summary", "[interpretation]",
        [
            f"_[fact]_ {req_count} requirement(s); latest run {run_label} "
            f"(passed: {run.passed}, failed: {run.failed}, flaky: {run.flaky}); "
            f"{open_count} open question(s).",
            "",
            "_[interpretation] Claude summarizes overall quality posture from the facts below._",
        ],
    )
    lines += _section(
        "Coverage", "[fact]",
        [f"Requirements inventoried: {req_count}. See `traceability/requirements-map.md`."],
    )
    lines += _section(
        "Requirements readiness", "[review]",
        [f"{req_count} requirement(s) inventoried.",
         "_[review] confirm each requirement is testable and has acceptance criteria._"],
    )
    lines += _section(
        "Exploratory findings", "[fact]",
        [f"{session_count} exploration session summary(ies) recorded."
         if session_count else "_None recorded._"],
    )

    regression: list[str] = [
        f"Latest run: {run_label} - "
        f"passed: {run.passed}, failed: {run.failed}, flaky: {run.flaky}.",
    ]
    if run.results:
        regression.append("")
        regression.append("| requirement | candidate | scenario |")
        regression.append("| --- | --- | --- |")
        regression.extend(
            f"| {r.get('requirement') or '_(none)_'} | {r.get('candidate') or '_(none)_'} | "
            f"{r.get('scenario', '')} | ({r.get('status')})"
            for r in sorted(run.results,
                            key=lambda x: (x.get("requirement") or "", x.get("candidate") or ""))
        )
    lines += _section("Automated regression status", "[fact]", regression)

    lines += _section(
        "Known risks", "[fact]",
        [f"{_count(risks, REQ_ROW_RE)} risk(s) in the register."
         if _is_real(risks) else "_None recorded._"],
    )

    defects = _result_rows(run.results, "failed")
    lines += _section(
        "Known defects", "[fact]",
        (["| requirement | candidate | scenario |", "| --- | --- | --- |", *defects]
         if defects else ["_No failing tests in the latest run._"]),
    )
    lines += _section(
        "Open questions", "[review]",
        [f"{open_count} open question(s) in `requirements/open-questions.md`.",
         "_[review] resolve the open questions that block release._"],
    )
    lines += _section(
        "Automation health", "[fact]",
        ["See `automation-plan/review-summary.md`."
         if _is_real(review_summary) else "_No automation review recorded._"],
    )

    flaky = _result_rows(run.results, "flaky")
    lines += _section(
        "Flaky tests", "[fact]",
        (["| requirement | candidate | scenario |", "| --- | --- | --- |", *flaky]
         if flaky else ["_No flaky tests in the latest run._"]),
    )
    lines += _section(
        "Evidence summary", "[fact]",
        [f"{evidence_count} artifact(s) indexed in `evidence/evidence-index.md`."
         if evidence_count else "_No evidence recorded._"],
    )
    lines += _section(
        "Traceability summary", "[fact]",
        ["See `traceability/test-map.md` for the requirement -> result chain."
         if _is_real(test_map) else "_Traceability map not yet generated._"],
    )
    lines += _section(
        "Recommendations", "[interpretation]",
        ["_[interpretation] Claude proposes next actions from the facts above._"],
    )
    lines += _section(
        "Release readiness", "[review]",
        ["_[interpretation] run `/tc:quality-gate` for a PASS/WARN/FAIL verdict against "
         "project thresholds._",
         "_[review] a human signs off on release readiness._"],
    )

    runs = sorted((workspace / "runs").glob("*/results.json"))
    recent = [f"- {p.parent.name}" for p in runs[-5:]]
    lines += _section(
        "Recent changes", "[fact]",
        (["Recent runs:", *recent] if recent else ["_No runs recorded yet._"]),
    )
    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def build_report(project_root: Path, *, now: datetime | None = None) -> ReportOutcome:
    project_root = Path(project_root)
    workspace = workspace_dir(project_root)
    now = now or datetime.now()  # injected in tests; wall clock in production

    quality_dir = workspace / "quality-report"
    history_dir = quality_dir / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    report_text = render_report(workspace, now)
    report_path = quality_dir / "current-quality-report.md"
    report_path.write_text(report_text, encoding="utf-8")
    snapshot_path = history_dir / f"{now:%Y-%m-%d-%H%M}.md"
    snapshot_path.write_text(report_text, encoding="utf-8")

    # Now that runs/ and quality-report/ are populated, resolve the test-map's
    # Test result + Quality report columns. Best effort: skip when the upstream
    # traceability input (the requirements inventory) is not yet generated.
    _skip = (
        traceability_map.InventoryMissingError,
        traceability_map.UninitializedWorkspaceError,
    )
    with contextlib.suppress(_skip):
        traceability_map.traceability_map(project_root)

    return ReportOutcome(
        report_path=report_path,
        snapshot_path=snapshot_path,
        latest_run_id=_latest_run(workspace).run_id,
        section_count=len(SECTION_TITLES),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate the workspace into quality-report/current-quality-report.md "
            "and snapshot it to quality-report/history/."
        ),
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    parser.add_argument(
        "--now", default=None, help="Injected clock (ISO 8601) for deterministic output."
    )
    args = parser.parse_args(argv if argv is not None else None)
    project_root = Path(args.project_root).resolve()
    now = datetime.fromisoformat(args.now) if args.now else None

    try:
        outcome = build_report(project_root, now=now)
    except ReportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"report: {outcome.report_path.relative_to(project_root)}")
    print(f"  snapshot: {outcome.snapshot_path.relative_to(project_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
