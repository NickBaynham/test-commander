#!/usr/bin/env python3
"""/tc:quality-gate helper - Phase 7 Step 7.6.

Evaluates the latest run and the quality report against project-defined
thresholds and returns a release-readiness verdict: PASS / WARN / FAIL, with a
per-criterion breakdown written to ``<workspace>/quality-report/quality-gate.md``.

The criteria, evaluated over the latest ``runs/<RUN-ID>/results.json`` record
and ``requirements/open-questions.md``:

- **pass rate** (``passed / total``) must be ``>= min-pass-rate`` - else FAIL.
- **failed tests** must be ``<= max-failed`` - else FAIL.
- **flaky tests** must be ``<= max-flaky`` - else WARN.
- **open questions** must be ``<= max-open-questions`` - else WARN.

The overall verdict is the worst per-criterion verdict (PASS < WARN < FAIL).
Release-readiness reads only measured values - it never invents a metric.

Thresholds are project-tunable via ``tc-quality-report.gate.thresholds`` in
``<workspace>/config.yaml`` (any unset key keeps its default).

Deterministic: the verdict is derived from the run record and open questions
(no clock), so a re-run over unchanged inputs is byte-identical.

Per D18 the helper ships inside the plugin. Per D19 the criteria are universal;
only the thresholds are project-tuned.

Exit codes:
    0 - gate evaluated; verdict PASS or WARN.
    1 - gate evaluated; verdict FAIL (non-zero so CI can branch on it).
    2 - precondition failure (uninitialized workspace, no quality report).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"
STUB_MARKER = "_(empty until"

DEFAULT_THRESHOLDS: dict[str, float] = {
    "min-pass-rate": 1.0,
    "max-failed": 0,
    "max-flaky": 0,
    "max-open-questions": 0,
}

SEVERITY = {"PASS": 0, "WARN": 1, "FAIL": 2}
OPEN_Q_RE = re.compile(r"^- \[", re.MULTILINE)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class GateError(Exception):
    pass


class UninitializedWorkspaceError(GateError):
    pass


class ReportMissingError(GateError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Criterion:
    name: str
    measured: str
    threshold: str
    verdict: str


@dataclass
class GateOutcome:
    verdict: str
    criteria: list[Criterion] = field(default_factory=list)
    verdict_path: Path | None = None


# ---------------------------------------------------------------------------
# Workspace IO + config
# ---------------------------------------------------------------------------


def workspace_dir(project_root: Path) -> Path:
    ws = project_root / WORKSPACE_DIRNAME
    if not ws.is_dir():
        raise UninitializedWorkspaceError(
            f"not a Test Commander workspace: {project_root} "
            f"(no {WORKSPACE_DIRNAME}/). Run /tc:init first."
        )
    return ws


def load_thresholds(workspace: Path) -> dict[str, float]:
    """Read ``tc-quality-report.gate.thresholds`` merged over the defaults.

    Tolerant: any read/parse error or unknown key keeps the default."""
    thresholds = dict(DEFAULT_THRESHOLDS)
    config_path = workspace / "config.yaml"
    if not config_path.is_file():
        return thresholds
    try:
        import yaml

        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        configured = data["tc-quality-report"]["gate"]["thresholds"]
    except Exception:
        return thresholds
    if not isinstance(configured, dict):
        return thresholds
    for name, value in configured.items():
        if name in thresholds:
            try:
                thresholds[name] = float(value)
            except (TypeError, ValueError):
                continue
    return thresholds


def _report_is_generated(workspace: Path) -> bool:
    report = workspace / "quality-report" / "current-quality-report.md"
    if not report.is_file():
        return False
    return STUB_MARKER not in report.read_text(encoding="utf-8")


def _latest_run(workspace: Path) -> dict:
    records = sorted((workspace / "runs").glob("*/results.json"))
    if not records:
        return {}
    return json.loads(records[-1].read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------


def _fmt(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.2f}"


def evaluate(run: dict, open_questions: int, thresholds: dict[str, float]) -> list[Criterion]:
    results = run.get("results", [])
    total = len(results)
    passed = sum(1 for r in results if r.get("status") == "passed")
    failed = sum(1 for r in results if r.get("status") == "failed")
    flaky = sum(1 for r in results if r.get("status") == "flaky")
    rate = passed / total if total else 1.0

    return [
        Criterion(
            "pass rate", "n/a" if not total else f"{rate:.2f}",
            f">= {_fmt(thresholds['min-pass-rate'])}",
            "PASS" if (not total or rate >= thresholds["min-pass-rate"]) else "FAIL",
        ),
        Criterion(
            "failed tests", str(failed), f"<= {_fmt(thresholds['max-failed'])}",
            "PASS" if failed <= thresholds["max-failed"] else "FAIL",
        ),
        Criterion(
            "flaky tests", str(flaky), f"<= {_fmt(thresholds['max-flaky'])}",
            "PASS" if flaky <= thresholds["max-flaky"] else "WARN",
        ),
        Criterion(
            "open questions", str(open_questions),
            f"<= {_fmt(thresholds['max-open-questions'])}",
            "PASS" if open_questions <= thresholds["max-open-questions"] else "WARN",
        ),
    ]


def overall(criteria: list[Criterion]) -> str:
    worst = max((SEVERITY[c.verdict] for c in criteria), default=0)
    return {0: "PASS", 1: "WARN", 2: "FAIL"}[worst]


def render_verdict(verdict: str, criteria: list[Criterion]) -> str:
    lines = [f"# Quality gate: {verdict}", ""]
    lines.append(
        "Evaluated against `tc-quality-report.gate.thresholds` "
        "(defaults apply where unset)."
    )
    lines.append("")
    lines.append("| criterion | measured | threshold | verdict |")
    lines.append("| --- | --- | --- | --- |")
    for c in criteria:
        lines.append(f"| {c.name} | {c.measured} | {c.threshold} | {c.verdict} |")
    lines.append("")
    lines.append(f"Overall: **{verdict}**")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def gate(project_root: Path) -> GateOutcome:
    project_root = Path(project_root)
    workspace = workspace_dir(project_root)
    if not _report_is_generated(workspace):
        raise ReportMissingError(
            "no quality report found (quality-report/current-quality-report.md "
            "is absent or still the template stub). Run /tc:report first."
        )

    thresholds = load_thresholds(workspace)
    run = _latest_run(workspace)
    open_q_text = ""
    oq_path = workspace / "requirements" / "open-questions.md"
    if oq_path.is_file():
        open_q_text = oq_path.read_text(encoding="utf-8")
    open_questions = len(OPEN_Q_RE.findall(open_q_text)) if STUB_MARKER not in open_q_text else 0

    criteria = evaluate(run, open_questions, thresholds)
    verdict = overall(criteria)
    verdict_path = workspace / "quality-report" / "quality-gate.md"
    verdict_path.parent.mkdir(parents=True, exist_ok=True)
    verdict_path.write_text(render_verdict(verdict, criteria), encoding="utf-8")
    return GateOutcome(verdict=verdict, criteria=criteria, verdict_path=verdict_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate the latest run and quality report against "
            "tc-quality-report.gate.thresholds and return PASS / WARN / FAIL."
        ),
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    args = parser.parse_args(argv if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        outcome = gate(project_root)
    except GateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"quality gate: {outcome.verdict}")
    for c in outcome.criteria:
        print(f"  {c.name}: {c.measured} ({c.threshold}) -> {c.verdict}")
    return 1 if outcome.verdict == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
