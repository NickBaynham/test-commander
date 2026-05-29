#!/usr/bin/env python3
"""/tc:generate-bdd helper - Phase 5 Step 5.2.

Turns Phase-4-enriched test-idea seeds into Gherkin ``.feature`` files with
full traceability. For each enriched ``<workspace>/test-ideas/REQ-NNN.md``
seed, every Phase-4 enrichment candidate (``CS-NNN-NNN``) becomes one Gherkin
``Scenario`` carrying machine-readable linkage tags (``@req:REQ-NNN``,
``@cs:CS-NNN-NNN``, optional ``@anomaly:<category>``) plus an ``@area:``
namespace tag and a universal class tag derived from the candidate type. The
helper writes:

- ``<workspace>/bdd/features/<area>.feature`` - the Gherkin feature.
- ``<workspace>/bdd/summaries/<area>.md`` - a per-feature summary.
- ``<workspace>/bdd/index.md`` - the feature index (scan-and-index sweep).

Pure generated reports - overwrite mode; byte-deterministic re-run against
unchanged inputs (everything is sorted: features by filename, scenarios by
``cs_id``, requirements/candidates lexicographically).

The helper is deterministic scaffolding; Claude refines the Given/When/Then
phrasing and promotes scenarios to ``Scenario Outline`` where data-driven,
per ``methodology/bdd-generation.md``. Review wiring (the generate-time
auto-run) ships in Step 5.3.

Per D18 the helper ships inside the plugin. Per D19 the shipped tag classes
are universal; project namespace values (``@area:``/``@risk:``/``@persona:``)
and ``tc-bdd.tags.extra-classes`` enter via ``<workspace>/config.yaml``.

Mirrors the Phase 4 helper-mirroring skeleton (``enrich_test_ideas.py``):
workspace IO + error hierarchy + load-source + per-source extraction + render
+ scan-and-index + orchestration + CLI. Unique work concentrates in the
enrichment-candidate parser, the Gherkin renderer, and the index sweep.

Exit codes:
    0 - generation complete.
    2 - precondition failure (uninitialized workspace, no enriched seeds).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from review_bdd import review_features

WORKSPACE_DIRNAME = ".test-commander"

# Universal class tag per candidate type (D19). happy/positive -> @smoke; the
# rest -> @regression. Tolerant of both the Phase-2 ("positive") and Phase-4
# ("happy") type vocabularies.
TYPE_CLASS: dict[str, str] = {
    "happy": "@smoke",
    "positive": "@smoke",
    "edge": "@regression",
    "negative": "@regression",
}
DEFAULT_CLASS = "@regression"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class GenerateBddError(Exception):
    pass


class UninitializedWorkspaceError(GenerateBddError):
    pass


class TestIdeasMissingError(GenerateBddError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Scenario:
    """Mirrors the enriched-test-idea candidate shape field-for-field, closing
    the cross-phase contract triangle (producer ``session_summary`` /
    ``enrich_test_ideas`` dataclass + producer tests + this consumer)."""

    req_id: str
    cs_id: str
    type: str
    title: str
    source: str
    linked_anomaly: str | None


@dataclass(frozen=True)
class Feature:
    req_id: str
    req_title: str
    area: str
    sessions: list[str]
    scenarios: list[Scenario]


@dataclass
class GenerateOutcome:
    feature_paths: list[Path] = field(default_factory=list)
    scenario_count: int = 0


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
# Enriched test-idea parsing
# ---------------------------------------------------------------------------

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
REQ_ID_RE = re.compile(r"^requirement_id:\s*(\S+)\s*$", re.MULTILINE)
REQ_TITLE_RE = re.compile(r"^requirement_title:\s*(.+?)\s*$", re.MULTILINE)
STATUS_RE = re.compile(r"^status:\s*(\S+)\s*$", re.MULTILINE)
PHASE4_SESSIONS_RE = re.compile(r"^phase_4_sessions:\s*\[(.*?)\]\s*$", re.MULTILINE)
ENRICHMENT_HEADER = "## Phase 4 enrichment"

# Candidate bullet shape emitted by enrich_test_ideas.render_session_subblock:
#   - **CS-001-001** (negative) - <title>
#       - source: `<source>`
#       - linked_anomaly: `<category>`
CANDIDATE_RE = re.compile(
    r"^- \*\*(CS-\d{3}-\d{3})\*\* \((\w+)\) - (.+?)\s*$", re.MULTILINE
)
SUBFIELD_RE = re.compile(r"^\s+- (source|linked_anomaly):\s*`?([^`]+?)`?\s*$")


def _frontmatter(text: str) -> str:
    match = FRONTMATTER_RE.match(text)
    return match.group(1) if match else ""


def is_enriched(path: Path) -> bool:
    fm = _frontmatter(path.read_text(encoding="utf-8"))
    status = STATUS_RE.search(fm)
    return bool(status and status.group(1) == "enriched")


def parse_scenarios(path: Path) -> list[Scenario]:
    """Parse the ``## Phase 4 enrichment`` candidate bullets into Scenarios.

    Recovers ``cs_id`` / ``type`` / ``title`` / ``source`` / ``linked_anomaly``
    for every candidate. Returns scenarios sorted by ``cs_id`` for determinism.
    """
    text = path.read_text(encoding="utf-8")
    fm = _frontmatter(text)
    req_id_match = REQ_ID_RE.search(fm)
    req_id = req_id_match.group(1) if req_id_match else path.stem

    enrichment = ""
    if ENRICHMENT_HEADER in text:
        enrichment = text.split(ENRICHMENT_HEADER, 1)[1]

    lines = enrichment.split("\n")
    scenarios: list[Scenario] = []
    for i, line in enumerate(lines):
        head = CANDIDATE_RE.match(line)
        if not head:
            continue
        cs_id, ctype, title = head.group(1), head.group(2), head.group(3)
        source = ""
        linked: str | None = None
        for sub in lines[i + 1:]:
            field_match = SUBFIELD_RE.match(sub)
            if not field_match:
                if sub.strip().startswith("- **CS-") or not sub.startswith(" "):
                    break
                continue
            if field_match.group(1) == "source":
                source = field_match.group(2)
            else:
                linked = field_match.group(2)
        scenarios.append(
            Scenario(
                req_id=req_id,
                cs_id=cs_id,
                type=ctype,
                title=title,
                source=source,
                linked_anomaly=linked,
            )
        )
    return sorted(scenarios, key=lambda s: s.cs_id)


def parse_feature(path: Path) -> Feature | None:
    text = path.read_text(encoding="utf-8")
    fm = _frontmatter(text)
    req_id_match = REQ_ID_RE.search(fm)
    title_match = REQ_TITLE_RE.search(fm)
    req_id = req_id_match.group(1) if req_id_match else path.stem
    req_title = title_match.group(1) if title_match else req_id
    sessions_match = PHASE4_SESSIONS_RE.search(fm)
    sessions = (
        [s.strip() for s in sessions_match.group(1).split(",") if s.strip()]
        if sessions_match
        else []
    )
    scenarios = parse_scenarios(path)
    if not scenarios:
        return None
    return Feature(
        req_id=req_id,
        req_title=req_title,
        area=area_slug(req_title),
        sessions=sorted(sessions),
        scenarios=scenarios,
    )


def area_slug(title: str) -> str:
    """Deterministic kebab-case slug from a requirement title. Universal: any
    run of non-alphanumeric characters collapses to a single hyphen."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "feature"


# ---------------------------------------------------------------------------
# Config extensions
# ---------------------------------------------------------------------------


def load_extra_classes(workspace: Path) -> list[str]:
    """Read ``tc-bdd.tags.extra-classes`` from ``<workspace>/config.yaml``.

    Returns the configured class tags (each normalised to a leading ``@``) to
    union with the universal core. Tolerant: any read/parse error yields no
    extensions.
    """
    config_path = workspace / "config.yaml"
    if not config_path.is_file():
        return []
    try:
        import yaml

        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return []
    try:
        raw = data["tc-bdd"]["tags"]["extra-classes"]
    except (KeyError, TypeError):
        return []
    if isinstance(raw, str):
        raw = [raw]
    out: list[str] = []
    for item in raw:
        tag = str(item).strip()
        if not tag:
            continue
        out.append(tag if tag.startswith("@") else f"@{tag}")
    return out


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def scenario_tags(scenario: Scenario, area: str, extra_classes: list[str]) -> list[str]:
    tags = [f"@area:{area}", f"@req:{scenario.req_id}", f"@cs:{scenario.cs_id}"]
    tags.append(TYPE_CLASS.get(scenario.type, DEFAULT_CLASS))
    if scenario.linked_anomaly:
        tags.append("@exploratory")
        tags.append(f"@anomaly:{scenario.linked_anomaly}")
    for cls in extra_classes:
        if cls not in tags:
            tags.append(cls)
    return tags


def render_feature(feature: Feature, extra_classes: list[str]) -> str:
    lines: list[str] = []
    lines.append(f"# Generated by /tc:generate-bdd from test-ideas/{feature.req_id}.md")
    if feature.sessions:
        lines.append(f"# Source candidates: {', '.join(feature.sessions)}")
    lines.append(
        "# Deterministic scaffold - refine Given/When/Then phrasing and promote to"
    )
    lines.append("# Scenario Outline where data-driven, per methodology/bdd-generation.md.")
    lines.append("")
    lines.append(f"@area:{feature.area}")
    lines.append(f"Feature: {feature.req_title}")
    lines.append("")
    for scenario in feature.scenarios:
        tags = scenario_tags(scenario, feature.area, extra_classes)
        lines.append("  " + " ".join(tags))
        lines.append(f"  Scenario: {scenario.title}")
        lines.append(
            f'    Given an account in the "{feature.req_title}" context'
        )
        lines.append(
            f'    When the {scenario.type} behavior "{scenario.title}" is exercised'
        )
        lines.append(
            f'    Then the outcome described by "{scenario.title}" holds'
        )
        lines.append("")
    return "\n".join(lines)


def render_summary(feature: Feature) -> str:
    cs_ids = ", ".join(s.cs_id for s in feature.scenarios)
    lines: list[str] = []
    lines.append(f"# BDD summary - {feature.area}")
    lines.append("")
    lines.append(f"_Source: `test-ideas/{feature.req_id}.md`_")
    lines.append("")
    lines.append(f"- Feature: {feature.req_title}")
    lines.append(f"- Requirement: {feature.req_id}")
    lines.append(f"- Scenarios: {len(feature.scenarios)}")
    lines.append(f"- Candidates realized: {cs_ids}")
    if feature.sessions:
        lines.append(f"- Sessions: {', '.join(feature.sessions)}")
    lines.append("- Review verdict: (pending /tc:review-bdd)")
    lines.append("")
    lines.append("## Scenarios")
    lines.append("")
    lines.append("| scenario | req | cs | type | linked_anomaly |")
    lines.append("| --- | --- | --- | --- | --- |")
    for s in feature.scenarios:
        lines.append(
            f"| {s.title} | {s.req_id} | {s.cs_id} | {s.type} | "
            f"{s.linked_anomaly or '-'} |"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Feature index (scan-and-index sweep)
# ---------------------------------------------------------------------------

# Index parser regexes - branch for every shape this helper produces:
# scenario tag lines carry @req:/@cs:; the feature title is the `Feature:` line.
INDEX_REQ_RE = re.compile(r"@req:(REQ-\d+)")
INDEX_CS_RE = re.compile(r"@cs:(CS-\d{3}-\d{3})")
INDEX_SCENARIO_RE = re.compile(r"^\s*Scenario:", re.MULTILINE)


def rebuild_index(features_dir: Path) -> str:
    rows: list[tuple[str, int, str, str]] = []
    for path in sorted(features_dir.glob("*.feature")):
        text = path.read_text(encoding="utf-8")
        scenarios = len(INDEX_SCENARIO_RE.findall(text))
        reqs = ", ".join(sorted(set(INDEX_REQ_RE.findall(text))))
        cs = ", ".join(sorted(set(INDEX_CS_RE.findall(text))))
        rows.append((path.name, scenarios, reqs, cs))

    lines: list[str] = []
    lines.append("# BDD feature index")
    lines.append("")
    lines.append("_Rebuilt by /tc:generate-bdd. Lists every feature under bdd/features/._")
    lines.append("")
    lines.append("| feature | scenarios | requirements | candidates |")
    lines.append("| --- | --- | --- | --- |")
    for name, scenarios, reqs, cs in rows:
        lines.append(f"| {name} | {scenarios} | {reqs} | {cs} |")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Discovery + orchestration
# ---------------------------------------------------------------------------


def discover_enriched(workspace: Path, req_id: str | None) -> list[Path]:
    test_ideas_dir = workspace / "test-ideas"
    if not test_ideas_dir.is_dir():
        raise TestIdeasMissingError(
            "no enriched test-idea seeds found under test-ideas/. "
            "Run /tc:requirements-to-tests then /tc:test-ideas first."
        )
    if req_id is not None:
        path = test_ideas_dir / f"{req_id}.md"
        if not path.is_file() or not is_enriched(path):
            raise TestIdeasMissingError(
                f"no enriched test-idea seed for {req_id}. "
                "Run /tc:test-ideas first."
            )
        return [path]
    paths = [
        p for p in sorted(test_ideas_dir.glob("REQ-*.md"))
        if p.is_file() and is_enriched(p)
    ]
    if not paths:
        raise TestIdeasMissingError(
            "no enriched test-idea seeds found under test-ideas/. "
            "Run /tc:test-ideas first (after /tc:requirements-to-tests)."
        )
    return paths


def run(
    project_root: Path, *, req_id: str | None = None, no_review: bool = False
) -> GenerateOutcome:
    workspace = workspace_dir(project_root)
    seeds = discover_enriched(workspace, req_id)
    extra_classes = load_extra_classes(workspace)

    features_dir = workspace / "bdd" / "features"
    summaries_dir = workspace / "bdd" / "summaries"
    features_dir.mkdir(parents=True, exist_ok=True)
    summaries_dir.mkdir(parents=True, exist_ok=True)

    outcome = GenerateOutcome()
    for seed in seeds:
        feature = parse_feature(seed)
        if feature is None:
            continue
        feature_path = features_dir / f"{feature.area}.feature"
        feature_path.write_text(render_feature(feature, extra_classes), encoding="utf-8")
        (summaries_dir / f"{feature.area}.md").write_text(
            render_summary(feature), encoding="utf-8"
        )
        outcome.feature_paths.append(feature_path)
        outcome.scenario_count += len(feature.scenarios)

    (workspace / "bdd" / "index.md").write_text(
        rebuild_index(features_dir), encoding="utf-8"
    )

    # Auto-run the shared BDD review sub-mode unless suppressed.
    if not no_review:
        review_features(project_root)
    return outcome


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate Gherkin feature files from Phase-4-enriched test-idea "
            "seeds. Writes bdd/features/<area>.feature, bdd/summaries/<area>.md, "
            "and rebuilds bdd/index.md."
        ),
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root (default: current directory).",
    )
    parser.add_argument(
        "--req",
        default=None,
        help="Generate for a single REQ-ID. If omitted, every enriched seed.",
    )
    parser.add_argument(
        "--no-review",
        action="store_true",
        help="Suppress the generate-time BDD review sub-mode (/tc:review-bdd).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        outcome = run(project_root, req_id=args.req, no_review=args.no_review)
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except TestIdeasMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"features: {len(outcome.feature_paths)} "
        f"(scenarios: {outcome.scenario_count})"
    )
    for path in outcome.feature_paths:
        print(f"  - {path.relative_to(project_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
