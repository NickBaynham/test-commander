#!/usr/bin/env python3
"""/tc:generate-infographic - Phase 9 Step 9.5.

Aggregates the quality report's headline facts into an infographic **brief**
(a human/Claude-facing narrative + layout hints, following
``frontend-design:frontend-design`` panel patterns) and a **spec** (a structured
data block of the measured facts). Neither is a binary; richer rendering is
``/tc:render-visuals``' job.

Generate-and-cite, never invent: every number comes from a measured ``[fact]``
in ``quality-report/current-quality-report.md``; a metric the report does not
state never appears. Both files carry a ``> Sources:`` footer.

Reuses the shared engine in ``visualize`` (workspace resolution, the
stub-refusing source reader, and the error types). Per D18 the helper ships
inside the plugin.

Exit codes:
    0 - brief + spec generated.
    2 - precondition failure (uninitialized workspace or no quality report).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import visualize

REPORT_REL = "quality-report/current-quality-report.md"

# Each metric: (key, regex, group-count). Only metrics the report states appear.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("requirements", re.compile(r"Requirements inventoried:\s*(\d+)")),
    ("latest_run", re.compile(r"(RUN-\d+-\d+)")),
    ("passed_failed_flaky", re.compile(r"passed:\s*(\d+),\s*failed:\s*(\d+),\s*flaky:\s*(\d+)")),
    ("open_questions", re.compile(r"(\d+) open question")),
    ("risks", re.compile(r"(\d+) risk\(s\)")),
    ("automation", re.compile(r"(\d+) of (\d+) scenario\(s\) automated")),
    ("evidence", re.compile(r"(\d+) evidence artifact")),
]


def parse_quality_facts(report_text: str) -> dict[str, object]:
    """Extract the measured headline facts, preserving a stable key order."""
    facts: dict[str, object] = {}
    for key, pattern in _PATTERNS:
        m = pattern.search(report_text)
        if not m:
            continue
        if key == "passed_failed_flaky":
            facts["passed"] = int(m.group(1))
            facts["failed"] = int(m.group(2))
            facts["flaky"] = int(m.group(3))
        elif key == "automation":
            facts["automated"] = int(m.group(1))
            facts["automatable"] = int(m.group(2))
        elif key == "latest_run":
            facts["latest_run"] = m.group(1)
        else:
            facts[key] = int(m.group(1))
    return facts


def _sources_footer() -> str:
    return f"> Sources: `{REPORT_REL}`"


def render_brief(facts: dict[str, object]) -> str:
    """A narrative + panel hints for the quality infographic."""
    out = [
        "# Quality posture - infographic brief",
        "",
        "A one-screen summary of the project's current quality posture, drawn "
        "only from the latest quality report. Use it to brief the layout in "
        "`/tc:render-visuals` or a design tool.",
        "",
        "## Headline stats",
        "",
    ]
    if "requirements" in facts:
        out.append(f"- **{facts['requirements']}** requirements inventoried")
    if "passed" in facts:
        out.append(
            f"- Latest run: **{facts['passed']}** passed, **{facts['failed']}** failed, "
            f"**{facts['flaky']}** flaky"
        )
    if "automated" in facts:
        out.append(
            f"- **{facts['automated']}** of **{facts['automatable']}** scenarios automated"
        )
    if "risks" in facts:
        out.append(f"- **{facts['risks']}** risks in the register")
    if "open_questions" in facts:
        out.append(f"- **{facts['open_questions']}** open questions")
    if "evidence" in facts:
        out.append(f"- **{facts['evidence']}** evidence artifacts")
    out += [
        "",
        "## Suggested panels",
        "",
        "1. A hero stat (requirements inventoried) with the latest-run pass/fail "
        "split as a small bar.",
        "2. An automation-coverage donut (automated / automatable).",
        "3. A risk + open-questions callout strip.",
        "",
        _sources_footer(),
    ]
    return "\n".join(out) + "\n"


def render_spec(facts: dict[str, object]) -> str:
    """The structured data block + layout spec for the quality infographic."""
    out = [
        "# Quality posture - infographic spec",
        "",
        "The measured facts behind the brief, as a structured data block. Every "
        "value is a `[fact]` from the quality report; a metric the report does "
        "not state is omitted, never invented.",
        "",
        "```yaml",
    ]
    order = [
        "requirements",
        "latest_run",
        "passed",
        "failed",
        "flaky",
        "automated",
        "automatable",
        "risks",
        "open_questions",
        "evidence",
    ]
    for key in order:
        if key in facts:
            out.append(f"{key}: {facts[key]}")
    out += ["```", "", _sources_footer()]
    return "\n".join(out) + "\n"


def generate_infographic(project_root: Path) -> list[Path]:
    """Write the infographic brief + spec from the quality report."""
    workspace = visualize.workspace_dir(project_root)
    report = visualize.read_source(workspace, REPORT_REL, "/tc:report")
    facts = parse_quality_facts(report)
    out_dir = workspace / "visuals" / "infographic"
    out_dir.mkdir(parents=True, exist_ok=True)
    brief_path = out_dir / "quality-brief.md"
    spec_path = out_dir / "quality-spec.md"
    brief_path.write_text(render_brief(facts), encoding="utf-8")
    spec_path.write_text(render_spec(facts), encoding="utf-8")
    return [brief_path, spec_path]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the quality infographic brief + spec from the quality report.",
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    args = parser.parse_args(argv if argv is not None else None)
    project_root = Path(args.project_root).resolve()
    try:
        written = generate_infographic(project_root)
    except visualize.VisualizeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"generated: {len(written)} infographic file(s) under visuals/infographic/")
    for p in written:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
