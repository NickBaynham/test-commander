#!/usr/bin/env python3
"""Verify Test Commander skill manifests.

Walks plugins/test-commander/skills/<name>/SKILL.md, parses YAML frontmatter,
and reports each skill as PRESENT, MISSING, MALFORMED, or UNEXPECTED.

Exit code:
    0 - every expected skill is PRESENT and no MALFORMED found
    1 - any expected skill is MISSING or any MALFORMED found

UNEXPECTED skills warn but do not affect the exit code.

The expected skill set is filtered by --phase: only skills whose owning
phase is <= the cap are required to be PRESENT. The default cap is
bumped as later phases ship.
"""

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKILLS_ROOT = REPO_ROOT / "plugins" / "test-commander" / "skills"

# Mirror of the TC-Owned Skill Catalog in planning/plan.md. Kept in sync by
# code review; we deliberately do not parse the plan to avoid brittleness.
CATALOG: dict[str, float] = {
    "tc-core": 1,
    "tc-requirements": 2,
    "tc-knowledge": 3,
    "tc-explore": 4,
    "tc-bdd": 5,
    "tc-traceability": 5,
    "tc-build-framework": 6,
    "tc-automation-plan": 6,
    "tc-automate": 6,
    "tc-test-data": 6,
    "tc-run": 7,
    "tc-quality-report": 7,
    "tc-evidence": 7,
    "tc-learning": 8,
    "tc-visualize": 9,
    "tc-web": 10,
    "tc-governance": 10.5,
    "tc-mcp": 11,
    "tc-sandbox": 12,
    "tc-continuous-quality": 13,
}

# Bumped as phases land. Through Phase 6 — tc-core (Phase 1), tc-requirements
# (Phase 2), tc-knowledge (Phase 3), tc-explore (Phase 4), tc-bdd +
# tc-traceability (Phase 5), and the four Phase 6 automation skills
# (tc-build-framework, tc-automation-plan, tc-automate, tc-test-data) are all
# shipped.
DEFAULT_PHASE_CAP: float = 6

KEBAB_CASE = re.compile(r"[a-z][a-z0-9-]*")
FRONTMATTER_BLOCK = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
NAME_LINE = re.compile(r"^name:\s*(\S+)\s*$", re.MULTILINE)
DESCRIPTION_LINE = re.compile(r"^description:\s*(.+?)\s*$", re.MULTILINE)


@dataclass
class ParseResult:
    ok: bool = False
    name: str = ""
    description: str = ""
    reason: str = ""


@dataclass
class SkillReport:
    status: str  # PRESENT | MISSING | MALFORMED | UNEXPECTED
    phase: float | None = None
    reason: str = ""


def parse_frontmatter(skill_md: Path, expected_name: str) -> ParseResult:
    """Read SKILL.md, extract the YAML frontmatter, and validate the basics."""
    if not skill_md.exists():
        return ParseResult(reason="missing SKILL.md")
    text = skill_md.read_text(encoding="utf-8")
    block = FRONTMATTER_BLOCK.match(text)
    if not block:
        return ParseResult(reason="missing or invalid frontmatter")
    body = block.group(1)
    name_match = NAME_LINE.search(body)
    desc_match = DESCRIPTION_LINE.search(body)
    if not name_match:
        return ParseResult(reason="frontmatter missing name")
    name = name_match.group(1)
    if not KEBAB_CASE.fullmatch(name):
        return ParseResult(reason=f"name {name!r} is not kebab-case")
    if name != expected_name:
        return ParseResult(
            reason=f"name {name!r} does not match directory {expected_name!r}"
        )
    if not desc_match:
        return ParseResult(reason="frontmatter missing description")
    description = desc_match.group(1).strip()
    if not description:
        return ParseResult(reason="empty description")
    return ParseResult(ok=True, name=name, description=description)


def walk_skills(
    skills_root: Path,
    catalog: dict[str, float],
    phase_cap: float | None = None,
) -> dict[str, SkillReport]:
    """Classify every expected and on-disk skill."""
    results: dict[str, SkillReport] = {}
    expected = {
        name: phase
        for name, phase in catalog.items()
        if phase_cap is None or phase <= phase_cap
    }
    on_disk: dict[str, Path] = {}
    if skills_root.exists():
        for child in skills_root.iterdir():
            if child.is_dir():
                on_disk[child.name] = child
    for name, phase in expected.items():
        if name not in on_disk:
            results[name] = SkillReport(
                status="MISSING", phase=phase, reason="skill directory absent"
            )
            continue
        parsed = parse_frontmatter(on_disk[name] / "SKILL.md", expected_name=name)
        if parsed.ok:
            results[name] = SkillReport(status="PRESENT", phase=phase)
        else:
            results[name] = SkillReport(
                status="MALFORMED", phase=phase, reason=parsed.reason
            )
    for name in on_disk:
        if name in results:
            continue
        if name in catalog:
            results[name] = SkillReport(
                status="UNEXPECTED",
                phase=catalog[name],
                reason="ahead of schedule",
            )
        else:
            results[name] = SkillReport(
                status="UNEXPECTED", phase=None, reason="not in catalog"
            )
    return results


def report(results: dict[str, SkillReport]) -> tuple[str, int]:
    """Render the per-skill report and compute the exit code."""
    counts = {"PRESENT": 0, "MISSING": 0, "MALFORMED": 0, "UNEXPECTED": 0}
    lines = []
    failed = False
    for name in sorted(results.keys()):
        r = results[name]
        counts[r.status] += 1
        phase_str = f"phase {r.phase}" if r.phase is not None else "phase ?"
        reason_str = f" - {r.reason}" if r.reason else ""
        lines.append(f"  {name:<26} {r.status:<11} ({phase_str}){reason_str}")
        if r.status in ("MISSING", "MALFORMED"):
            failed = True
    summary = (
        f"PRESENT={counts['PRESENT']} "
        f"MISSING={counts['MISSING']} "
        f"MALFORMED={counts['MALFORMED']} "
        f"UNEXPECTED={counts['UNEXPECTED']}"
    )
    verdict = "FAIL" if failed else "OK"
    lines.append("")
    lines.append(f"verify_skills: {verdict} ({summary})")
    return "\n".join(lines), (1 if failed else 0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify Test Commander skill manifests."
    )
    parser.add_argument(
        "--phase",
        type=float,
        default=DEFAULT_PHASE_CAP,
        help=(
            f"Verify skills with phase <= N. Default {DEFAULT_PHASE_CAP}. "
            "Use a larger value to require completeness through a later phase."
        ),
    )
    parser.add_argument(
        "--skills-root",
        type=Path,
        default=DEFAULT_SKILLS_ROOT,
        help="Override the skills directory (default: plugins/test-commander/skills).",
    )
    args = parser.parse_args(argv)
    results = walk_skills(args.skills_root, CATALOG, phase_cap=args.phase)
    text, exit_code = report(results)
    print(text)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
