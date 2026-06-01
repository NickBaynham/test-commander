#!/usr/bin/env python3
"""/tc:run helper - Phase 7 Step 7.2.

Executes the generated automated suite and captures the results into a
per-run record. Two responsibilities, split by the hermetic boundary:

(a) **Execution.** In real use the helper shells out to ``npx playwright
    test`` (and, for the API path, the ``postman`` CLI) for the requested run
    mode, producing a Playwright JSON report. This path is **refused under
    pytest** via the ``PYTEST_CURRENT_TEST`` guard (the project's "no
    executable runtime in tests" property, Phase 3 Step 3.5 / Phase 4 Step 4.7
    pattern) with a message directing the caller to pass ``--report`` instead.

(b) **Ingestion.** The helper reads a Playwright JSON report - the recorded
    fixture under pytest, or the report execution just produced - and writes a
    per-run record under ``<workspace>/runs/<RUN-ID>/`` mapping each pass /
    fail / flaky result to its scenario, candidate, requirement, and spec via
    the ``@req:``/``@cs:`` provenance carried in the report and the Phase-6
    ``traceability/automation-map.md``.

Run modes (``smoke`` / ``regression`` / ``feature`` / ``failed-only`` /
``tagged``) select which results land in the record; ``feature`` needs
``--area`` and ``tagged`` needs ``--tag``.

**Injected-clock determinism.** The RUN-ID carries a timestamp, which would
break the byte-determinism every prior phase relies on. Resolution: ``run``
takes an injected ``now`` (the ``--now`` flag / parameter); tests pass a fixed
timestamp so the run record is byte-stable. Production reads the wall clock.
``datetime.now()`` is never called at import or inline - only as the default
inside ``run`` when ``now`` is omitted.

Upstream is **read-only**: the helper never mutates ``automation-map.md`` or
the generated specs. Evidence indexing (the ``tc-evidence`` indexer and the
``--no-index`` auto-run) ships in Step 7.3; 7.2 leaves a forward pointer.

Per D18 the helper ships inside the plugin. Per D19 the run modes and result
schema are universal; project tuning enters via ``<workspace>/config.yaml``
in later sub-steps.

Mirrors the sibling-helper skeleton (``generate_bdd.py``): workspace IO +
error hierarchy + load-source (the report) + per-result extraction + render +
orchestration + CLI.

Exit codes:
    0 - run captured.
    2 - precondition failure (uninitialized workspace, execution refused under
        pytest, missing report, invalid run mode).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"
PYTEST_ENV_VAR = "PYTEST_CURRENT_TEST"

RUN_MODES: tuple[str, ...] = ("all", "smoke", "regression", "feature", "failed-only", "tagged")

# Playwright test-level status -> universal result class.
STATUS_MAP: dict[str, str] = {
    "expected": "passed",
    "passed": "passed",
    "unexpected": "failed",
    "failed": "failed",
    "flaky": "flaky",
    "skipped": "skipped",
}

REQ_TAG_RE = re.compile(r"@req:(REQ-\d+)")
CS_TAG_RE = re.compile(r"@cs:(CS-\d{3}-\d{3})")
# Automation-map row: | REQ-NNN | CS-NNN-NNN | scenario | tests/e2e/<area>.spec.ts |
AUTOMATION_ROW_RE = re.compile(
    r"^\|\s*REQ-\d+\s*\|\s*(CS-\d{3}-\d{3})\s*\|[^|]*\|\s*(\S+\.spec\.ts)\s*\|"
)


def _unknown_mode_msg(mode: str) -> str:
    return f"unknown run mode: {mode!r} (choose from {', '.join(RUN_MODES)})"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class RunError(Exception):
    pass


class UninitializedWorkspaceError(RunError):
    pass


class ExecutionRefusedError(RunError):
    pass


class ReportMissingError(RunError):
    pass


class InvalidRunModeError(RunError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResultRecord:
    """One ingested Playwright result, joined to its provenance."""

    scenario: str
    status: str
    retries: int
    req_id: str | None
    cs_id: str | None
    spec: str | None
    tags: tuple[str, ...]
    attachments: tuple[str, ...]

    def sort_key(self) -> tuple[str, str, str]:
        return (self.req_id or "", self.cs_id or "", self.scenario)


@dataclass
class RunOutcome:
    run_id: str
    mode: str
    record_dir: Path
    records: list[ResultRecord] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.records)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.records if r.status == "passed")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.records if r.status == "failed")

    @property
    def flaky(self) -> int:
        return sum(1 for r in self.records if r.status == "flaky")

    @property
    def candidates(self) -> list[str]:
        return [r.cs_id for r in self.records if r.cs_id]


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


def load_automation_map(workspace: Path) -> dict[str, str]:
    """Parse traceability/automation-map.md into {cs_id -> spec path}. Empty
    when the map is absent (read-only; never written here)."""
    specs: dict[str, str] = {}
    path = workspace / "traceability" / "automation-map.md"
    if not path.is_file():
        return specs
    for line in path.read_text(encoding="utf-8").split("\n"):
        m = AUTOMATION_ROW_RE.match(line)
        if m:
            specs.setdefault(m.group(1), m.group(2))
    return specs


# ---------------------------------------------------------------------------
# Report ingestion
# ---------------------------------------------------------------------------


def _first(pattern: re.Pattern[str], tags: list[str]) -> str | None:
    for tag in tags:
        m = pattern.search(tag)
        if m:
            return m.group(1)
    return None


def parse_report(report_text: str, automated_by_cs: dict[str, str]) -> list[ResultRecord]:
    """Walk a Playwright JSON report into joined ResultRecords."""
    report = json.loads(report_text)
    records: list[ResultRecord] = []
    for suite in report.get("suites", []):
        suite_file = suite.get("file")
        for spec in suite.get("specs", []):
            tags = list(spec.get("tags", []))
            req_id = _first(REQ_TAG_RE, tags)
            cs_id = _first(CS_TAG_RE, tags)
            spec_path = automated_by_cs.get(cs_id or "", suite_file)
            for test in spec.get("tests", []):
                status = STATUS_MAP.get(test.get("status", ""), test.get("status", ""))
                results = test.get("results", [])
                retries = max((r.get("retry", 0) for r in results), default=0)
                attachments = tuple(
                    a["path"]
                    for r in results
                    for a in r.get("attachments", [])
                    if a.get("path")
                )
                records.append(
                    ResultRecord(
                        scenario=spec.get("title", ""),
                        status=status,
                        retries=retries,
                        req_id=req_id,
                        cs_id=cs_id,
                        spec=spec_path,
                        tags=tuple(tags),
                        attachments=attachments,
                    )
                )
    return records


def select(
    records: list[ResultRecord], mode: str, area: str | None, tag: str | None
) -> list[ResultRecord]:
    if mode not in RUN_MODES:
        raise InvalidRunModeError(_unknown_mode_msg(mode))
    if mode == "all":
        return list(records)
    if mode == "smoke":
        return [r for r in records if "@smoke" in r.tags]
    if mode == "regression":
        return [r for r in records if "@regression" in r.tags]
    if mode == "failed-only":
        return [r for r in records if r.status == "failed"]
    if mode == "feature":
        if not area:
            raise InvalidRunModeError("run mode 'feature' requires --area <slug>")
        return [r for r in records if f"@area:{area}" in r.tags]
    # tagged
    if not tag:
        raise InvalidRunModeError("run mode 'tagged' requires --tag <tag>")
    wanted = tag if tag.startswith("@") else f"@{tag}"
    return [r for r in records if wanted in r.tags]


# ---------------------------------------------------------------------------
# Execution (refused under pytest)
# ---------------------------------------------------------------------------


def _execute_playwright(workspace: Path, mode: str) -> str:
    """Shell out to the real runner and return the JSON report text. Refused
    under pytest so the suite never reaches a browser."""
    if os.environ.get(PYTEST_ENV_VAR):
        raise ExecutionRefusedError(
            "real test execution refused under pytest (PYTEST_CURRENT_TEST is set); "
            "pass --report <playwright-json> to ingest a recorded report"
        )
    # Real execution path (not exercised by the hermetic suite): run Playwright
    # and read the JSON report it writes. The framework lives at the project
    # root tests/ tree (Phase 6); execution is the operator's environment. The
    # live runtime is wired with the rest of the runtime in a later phase.
    raise ExecutionRefusedError(  # pragma: no cover
        "live Playwright execution is not wired in v1; pass --report <playwright-json> "
        "to ingest a report produced by 'npx playwright test --reporter=json'"
    )


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _md_cell(value: str | None) -> str:
    return value if value else "_(none)_"


def render_run_md(run_id: str, mode: str, now: datetime, records: list[ResultRecord]) -> str:
    passed = sum(1 for r in records if r.status == "passed")
    failed = sum(1 for r in records if r.status == "failed")
    flaky = sum(1 for r in records if r.status == "flaky")
    lines: list[str] = []
    lines.append(f"# Test run {run_id}")
    lines.append("")
    lines.append(f"- Mode: {mode}")
    lines.append(f"- Generated: {now.isoformat()} (injected clock)")
    lines.append(
        f"- Results: {len(records)} (passed: {passed}, failed: {failed}, flaky: {flaky})"
    )
    lines.append("")
    lines.append(
        "> Evidence indexing wires in Step 7.3 (`/tc:run` auto-runs the "
        "`tc-evidence` indexer; `--no-index` suppresses it)."
    )
    lines.append("")
    lines.append("| requirement | candidate | scenario | spec | result | retries |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for r in sorted(records, key=lambda x: x.sort_key()):
        lines.append(
            f"| {_md_cell(r.req_id)} | {_md_cell(r.cs_id)} | {r.scenario} | "
            f"{_md_cell(r.spec)} | {r.status} | {r.retries} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_results_json(run_id: str, mode: str, now: datetime, records: list[ResultRecord]) -> str:
    payload = {
        "run_id": run_id,
        "mode": mode,
        "generated": now.isoformat(),
        "results": [
            {
                "requirement": r.req_id,
                "candidate": r.cs_id,
                "scenario": r.scenario,
                "spec": r.spec,
                "status": r.status,
                "retries": r.retries,
                "tags": list(r.tags),
                "attachments": list(r.attachments),
            }
            for r in sorted(records, key=lambda x: x.sort_key())
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run(
    project_root: Path,
    *,
    mode: str = "all",
    now: datetime | None = None,
    report: Path | None = None,
    area: str | None = None,
    tag: str | None = None,
) -> RunOutcome:
    project_root = Path(project_root)
    workspace = workspace_dir(project_root)
    if mode not in RUN_MODES:
        raise InvalidRunModeError(_unknown_mode_msg(mode))
    now = now or datetime.now()  # injected in tests; wall clock in production

    if report is None:
        report_text = _execute_playwright(workspace, mode)
    else:
        report = Path(report)
        if not report.is_file():
            raise ReportMissingError(f"report not found: {report}")
        report_text = report.read_text(encoding="utf-8")

    automated_by_cs = load_automation_map(workspace)
    records = select(parse_report(report_text, automated_by_cs), mode, area, tag)

    run_id = f"RUN-{now:%Y%m%d-%H%M%S}"
    record_dir = workspace / "runs" / run_id
    record_dir.mkdir(parents=True, exist_ok=True)
    (record_dir / "run.md").write_text(
        render_run_md(run_id, mode, now, records), encoding="utf-8"
    )
    (record_dir / "results.json").write_text(
        render_results_json(run_id, mode, now, records), encoding="utf-8"
    )
    return RunOutcome(run_id=run_id, mode=mode, record_dir=record_dir, records=records)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the generated automated suite (or ingest a recorded Playwright "
            "JSON report) and write a per-run record under runs/<RUN-ID>/."
        ),
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    parser.add_argument(
        "--mode", default="all", choices=RUN_MODES, help="Run mode (default: all)."
    )
    parser.add_argument("--area", default=None, help="Feature area slug (for --mode feature).")
    parser.add_argument("--tag", default=None, help="Tag to filter by (for --mode tagged).")
    parser.add_argument(
        "--report",
        default=None,
        help="Ingest this Playwright JSON report instead of executing the suite.",
    )
    parser.add_argument(
        "--now",
        default=None,
        help="Injected clock (ISO 8601) for a deterministic RUN-ID. Defaults to now.",
    )
    args = parser.parse_args(argv if argv is not None else None)
    project_root = Path(args.project_root).resolve()
    now = datetime.fromisoformat(args.now) if args.now else None
    report = Path(args.report) if args.report else None

    try:
        outcome = run(
            project_root, mode=args.mode, now=now, report=report, area=args.area, tag=args.tag
        )
    except RunError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"run: {outcome.run_id} (mode: {outcome.mode}) - "
        f"{outcome.total} result(s): passed {outcome.passed}, "
        f"failed {outcome.failed}, flaky {outcome.flaky}"
    )
    print(f"  record: {outcome.record_dir.relative_to(project_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
