"""Step 9.5 - /tc:generate-infographic.

Aggregates the quality report's headline facts into an infographic brief + spec
(Markdown plus a structured data block), carrying only measured facts with a
cited-sources footer. Asserts: uninitialized refused; no quality report refused
(pointing at /tc:report); the seeded report yields a brief + spec of measured
facts; byte-stable; and a metric absent from the report is never invented.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
FIXTURE = REPO / "tests" / "fixtures" / "seeded-visuals"

import generate_infographic  # noqa: E402
import visualize  # noqa: E402


def seed_workspace(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    shutil.copytree(FIXTURE, project / ".test-commander")
    return project


def test_uninitialized_refused(tmp_path: Path):
    with pytest.raises(visualize.UninitializedWorkspaceError):
        generate_infographic.generate_infographic(tmp_path / "nope")


def test_no_quality_report_refused(tmp_path: Path):
    project = seed_workspace(tmp_path)
    (project / ".test-commander" / "quality-report" / "current-quality-report.md").unlink()
    with pytest.raises(visualize.MissingSourceError) as exc:
        generate_infographic.generate_infographic(project)
    assert "/tc:report" in str(exc.value)


def test_brief_and_spec_carry_measured_facts(tmp_path: Path):
    project = seed_workspace(tmp_path)
    written = generate_infographic.generate_infographic(project)
    names = {p.name for p in written}
    assert names == {"quality-brief.md", "quality-spec.md"}
    info_dir = project / ".test-commander" / "visuals" / "infographic"
    brief = (info_dir / "quality-brief.md").read_text(encoding="utf-8")
    spec = (info_dir / "quality-spec.md").read_text(encoding="utf-8")
    # Measured facts from the seeded report.
    assert "3" in brief, "requirements inventoried"
    assert "passed" in brief.lower() and "failed" in brief.lower()
    # The spec carries a structured data block.
    assert "```" in spec, "spec must carry a fenced structured data block"
    assert "requirements: 3" in spec
    assert "passed: 1" in spec and "failed: 1" in spec and "flaky: 1" in spec
    # Both cite the source.
    assert "> Sources:" in brief and "quality-report/current-quality-report.md" in brief
    assert "> Sources:" in spec


def test_byte_stable_rerun(tmp_path: Path):
    project = seed_workspace(tmp_path)
    first = {p.name: p.read_bytes() for p in generate_infographic.generate_infographic(project)}
    second = {p.name: p.read_bytes() for p in generate_infographic.generate_infographic(project)}
    assert first == second


def test_absent_metric_not_invented(tmp_path: Path):
    """A metric the report does not state must not appear in the spec."""
    project = seed_workspace(tmp_path)
    report = project / ".test-commander" / "quality-report" / "current-quality-report.md"
    text = report.read_text(encoding="utf-8")
    # Drop the automation-health line.
    text = "\n".join(
        line for line in text.splitlines() if "scenario(s) automated" not in line
    )
    report.write_text(text, encoding="utf-8")
    spec = generate_infographic.generate_infographic(project)
    spec_text = next(p for p in spec if p.name == "quality-spec.md").read_text(encoding="utf-8")
    assert "automated:" not in spec_text, "an absent metric must not be invented"
