#!/usr/bin/env python3
"""/tc:create-charter helper - Phase 4 Step 4.2.

Reads Phase-3 product-knowledge artifacts plus Phase-2 open-questions
and the project's risk-register to either accept an explicit
``--target``/``--mission`` charter scope OR auto-suggest one based on
the entity with the highest mention count. Writes a charter file to
``<workspace>/charters/<CH-NNN>.md`` with YAML frontmatter carrying
every CHARTER_REQUIRED_FIELDS key (the cross-phase contract from
Step 4.1) and a structured body (Mission / Target Area / Time-Box /
Risk Areas / Acceptance Criteria / Out of Scope / Phase 3 Sources).

This helper establishes the Phase 4 helper-mirroring skeleton that
Steps 4.3-4.5 will copy-rename. The differences between siblings
concentrate in source parsing and the per-command extraction logic;
workspace IO, config loading, ID allocation, and idempotency handling
are fungible.

Per D18 the helper ships inside the plugin. Per D19 the auto-suggestion
keyword sets ship as universal English / SaaS-vocabulary cores;
projects extend them via ``tc-explore.charters.{risk-keywords,
area-keywords}`` in ``<workspace>/config.yaml``.

Exit codes:
    0 - charter created OR existing charter preserved (idempotent skip).
    2 - uninitialized workspace, product-knowledge missing
        (Phase 3 not yet run), or other precondition failure.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"

# Required charter frontmatter fields. MUST match the
# CHARTER_REQUIRED_FIELDS list in tests/test_tc_explore_scaffold.py.
# The list IS the cross-phase contract per the Step 4.1 lesson.
CHARTER_REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "mission",
    "target",
    "time-box",
    "risk-areas",
    "acceptance-criteria",
)

DEFAULT_TIME_BOX = "60min"

# Universal-core risk-area keywords (D19). Project extensions via
# tc-explore.charters.risk-keywords union with these additively.
UNIVERSAL_RISK_KEYWORDS: tuple[str, ...] = (
    "security",
    "auth",
    "performance",
    "data-integrity",
    "accessibility",
    "compliance",
    "session",
    "permission",
    "token",
    "leak",
)

# Universal-core area keywords (D19). Project extensions via
# tc-explore.charters.area-keywords union with these additively.
UNIVERSAL_AREA_KEYWORDS: tuple[str, ...] = (
    "sign-in",
    "sign-out",
    "dashboard",
    "search",
    "upload",
    "profile",
    "settings",
    "session",
    "workspace",
)

# Open-questions kind prefixes from Phase 2 + Phase 3.
KIND_PREFIX_RE = re.compile(r"\[([a-z][a-z0-9-]*)\]")

# Bullet/bold extraction (mirrors Phase 3 synthesizer's ENTITY_BULLET_RE).
ENTITY_BULLET_RE = re.compile(r"^\s*-\s+\*\*([A-Z][A-Za-z0-9 _-]+?)\*\*", re.MULTILINE)

# Phase 3 cross-cutting section delimiter (same shape the Phase 3
# helpers established + the synthesizer parses).
SOURCE_SECTION_RE = re.compile(r"^## From ([a-z][a-z0-9-]*)\s*$", re.MULTILINE)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class CharterError(Exception):
    pass


class UninitializedWorkspaceError(CharterError):
    pass


class ProductKnowledgeMissingError(CharterError):
    pass


class NoSuggestionPossibleError(CharterError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class Extensions:
    risk_keywords: set[str] = field(default_factory=set)
    area_keywords: set[str] = field(default_factory=set)


@dataclass
class Suggestion:
    target: str
    mission: str
    risk_areas: list[str]
    acceptance_criteria: list[str]
    out_of_scope: list[str]


@dataclass
class Charter:
    id: str
    mission: str
    target: str
    time_box: str
    risk_areas: list[str]
    acceptance_criteria: list[str]
    out_of_scope: list[str]
    created_at: str
    phase_3_sources: list[str]


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


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


# ---------------------------------------------------------------------------
# Config extensions
# ---------------------------------------------------------------------------


def _parse_inline_list(value: str) -> list[str]:
    inner = value.strip()
    if inner.startswith("[") and inner.endswith("]"):
        inner = inner[1:-1]
    items: list[str] = []
    for raw in inner.split(","):
        item = raw.strip().strip("'\"")
        if item:
            items.append(item)
    return items


def load_extensions(workspace: Path) -> Extensions:
    """Read ``tc-explore.charters:`` extensions from ``<workspace>/config.yaml``.

    Tolerant indentation-based parser; falls back to universal cores when
    keys are absent. Mirrors the Phase 3 helpers' config-loading pattern.
    """
    ext = Extensions()
    config_path = workspace / "config.yaml"
    if not config_path.is_file():
        return ext
    try:
        text = config_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ext

    in_root = False
    section: str | None = None
    pending_key: str | None = None
    pending_items: list[str] = []

    def commit() -> None:
        nonlocal pending_key, pending_items
        if pending_key is not None and section == "charters":
            _assign(ext, pending_key, pending_items)
        pending_key = None
        pending_items = []

    for raw in text.split("\n"):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))

        if indent == 0:
            commit()
            section = None
            in_root = stripped == "tc-explore:"
            continue
        if not in_root:
            continue

        if indent == 2:
            commit()
            section = stripped[:-1].strip() if stripped.endswith(":") else None
            continue

        if indent == 4 and section == "charters":
            commit()
            if ":" not in stripped:
                continue
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                if value.startswith("["):
                    items = _parse_inline_list(value)
                    _assign(ext, key, items)
                else:
                    _assign(ext, key, [value.strip("'\"")])
            else:
                pending_key = key
                pending_items = []
            continue

        if indent >= 6 and pending_key is not None and stripped.startswith("-"):
            item = stripped[1:].strip().strip("'\"")
            if item:
                pending_items.append(item)

    commit()
    return ext


def _assign(ext: Extensions, key: str, items: list[str]) -> None:
    if not items:
        return
    if key == "risk-keywords":
        ext.risk_keywords |= set(items)
    elif key == "area-keywords":
        ext.area_keywords |= set(items)


# ---------------------------------------------------------------------------
# Phase-3 input parsing
# ---------------------------------------------------------------------------


# Marker phrases that indicate a per-source model is still the template stub
# OR a helper-written empty-run sentinel. Mirrors the synthesizer's
# EMPTY_RUN_MARKERS shape.
NOT_GENERATED_MARKERS: tuple[str, ...] = (
    "_(empty until phase 3 ships.)_",
    "_(empty until phase",
    "no narrative documents found",
)


def _is_generated(text: str) -> bool:
    if not text.strip():
        return False
    lowered = text.lower()
    return not any(marker in lowered for marker in NOT_GENERATED_MARKERS)


def assert_product_knowledge_generated(workspace: Path) -> list[str]:
    """Require at least one Phase 3 product-knowledge artifact has been
    generated; return the relative paths of every consumed artifact for
    the charter's phase_3_sources field."""
    pk = workspace / "product-knowledge"
    consumed: list[str] = []
    for relname in ("entities.md", "user-journeys.md", "system-model.md"):
        if _is_generated(_read_text(pk / relname)):
            consumed.append(f"product-knowledge/{relname}")
    if not consumed:
        raise ProductKnowledgeMissingError(
            "<workspace>/product-knowledge/ has not been populated yet. "
            "Run /tc:learn-from-docs (Phase 3) before /tc:create-charter."
        )
    # open-questions and risk-register are optional but cited when present.
    open_q = workspace / "requirements" / "open-questions.md"
    if _is_generated(_read_text(open_q)):
        consumed.append("requirements/open-questions.md")
    risk = workspace / "risk-register" / "risk-register.md"
    if _is_generated(_read_text(risk)):
        consumed.append("risk-register/risk-register.md")
    return consumed


def parse_entities(entities_text: str) -> list[str]:
    """Return the list of bolded entity names appearing across every
    ``## From <source>`` section, with duplicates preserved (so we can
    count per-source mentions later)."""
    return ENTITY_BULLET_RE.findall(entities_text)


def parse_journey_titles(journeys_text: str) -> list[str]:
    """Return the bolded journey titles from ``## From documents``."""
    return ENTITY_BULLET_RE.findall(journeys_text)


def count_mentions(name: str, *bodies: str) -> int:
    pattern = re.compile(rf"\b{re.escape(name)}\b", re.IGNORECASE)
    return sum(len(pattern.findall(body)) for body in bodies)


# ---------------------------------------------------------------------------
# Suggestion logic
# ---------------------------------------------------------------------------


def auto_suggest(
    workspace: Path,
    ext: Extensions,
) -> Suggestion:
    """Pick the entity with the highest total mention count across
    entities.md + user-journeys.md + open-questions.md. Ties broken
    alphabetically (lower name wins) for deterministic output.
    """
    pk = workspace / "product-knowledge"
    entities_text = _read_text(pk / "entities.md")
    journeys_text = _read_text(pk / "user-journeys.md")
    open_q_text = _read_text(workspace / "requirements" / "open-questions.md")

    entities = list(dict.fromkeys(parse_entities(entities_text)))
    if not entities:
        raise NoSuggestionPossibleError(
            "No entities extracted from product-knowledge/entities.md; "
            "cannot auto-suggest a charter target. Re-run with --target "
            "or --mission, or run /tc:learn-from-docs to populate entities."
        )

    mention_scores: dict[str, int] = {}
    for ent in entities:
        score = count_mentions(ent, entities_text, journeys_text, open_q_text)
        mention_scores[ent] = score

    # Highest score wins; ties broken alphabetically (lowest name first).
    ranked = sorted(entities, key=lambda e: (-mention_scores[e], e))
    top = ranked[0]

    target = f"{top}-related endpoints and pages"
    mission = (
        f"Discover whether the {top} flow behaves correctly under the documented "
        f"risk conditions extracted from product-knowledge."
    )
    risk_areas = derive_risk_areas(workspace, ext)
    acceptance_criteria = [
        f"Every {top} endpoint returns documented status codes for the happy path.",
        f"Authentication is correctly required for every {top} endpoint that should require it.",
        "At least one anomaly per universal category is documented or explained away.",
    ]
    out_of_scope = [
        "Visual styling and theming (deferred to Phase 6 automation).",
        "Cross-workspace permission propagation (separate charter scope).",
    ]
    return Suggestion(
        target=target,
        mission=mission,
        risk_areas=risk_areas,
        acceptance_criteria=acceptance_criteria,
        out_of_scope=out_of_scope,
    )


def derive_risk_areas(workspace: Path, ext: Extensions) -> list[str]:
    """Extract risk-area candidates from risk-register entries that match
    any universal-core OR project-extended risk keyword."""
    risk_text = _read_text(workspace / "risk-register" / "risk-register.md")
    if not risk_text.strip():
        return _default_risk_areas()
    keywords = set(UNIVERSAL_RISK_KEYWORDS) | ext.risk_keywords
    matches: list[str] = []
    for line in risk_text.split("\n"):
        stripped = line.lstrip("- *").strip()
        if not stripped or stripped.startswith("#"):
            continue
        lowered = stripped.lower()
        if any(kw.lower() in lowered for kw in keywords):
            matches.append(stripped)
    if not matches:
        return _default_risk_areas()
    return matches


def _default_risk_areas() -> list[str]:
    return [
        "Authentication / authorization boundaries",
        "Session lifecycle and token leakage",
        "Performance under documented load thresholds",
        "Input validation on user-supplied data",
    ]


def explicit_charter(
    workspace: Path,
    *,
    target: str | None,
    mission: str | None,
    ext: Extensions,
) -> Suggestion:
    """Build a charter scope from explicit --target/--mission arguments."""
    if target is None and mission is None:
        # Caller ensures one of these is non-None when calling this path.
        raise ValueError("either target or mission must be supplied")
    chosen_target = target or (mission[:80] if mission else "")
    chosen_mission = mission or (
        f"Discover whether the {chosen_target} behaves correctly under the documented "
        f"risk conditions."
    )
    return Suggestion(
        target=chosen_target,
        mission=chosen_mission,
        risk_areas=derive_risk_areas(workspace, ext),
        acceptance_criteria=[
            f"Every flow under '{chosen_target}' completes the happy path "
            "with documented status codes.",
            "Authentication is correctly enforced for every endpoint that should require it.",
            "At least one anomaly per universal category is documented or explained away.",
        ],
        out_of_scope=[
            "Visual styling and theming (deferred to Phase 6 automation).",
        ],
    )


# ---------------------------------------------------------------------------
# ID allocation + idempotency
# ---------------------------------------------------------------------------


CHARTER_FILENAME_RE = re.compile(r"^CH-(\d+)\.md$")


def allocate_next_id(workspace: Path) -> str:
    charters_dir = workspace / "charters"
    charters_dir.mkdir(parents=True, exist_ok=True)
    max_n = 0
    for entry in charters_dir.iterdir():
        if not entry.is_file():
            continue
        m = CHARTER_FILENAME_RE.match(entry.name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"CH-{max_n + 1:03d}"


def find_existing_charter(workspace: Path, target: str) -> Path | None:
    """Return the path of an existing charter whose target field matches
    ``target`` case-insensitively. The match is exact on the frontmatter
    ``target:`` field value (no substring matching - keeps idempotency
    deterministic)."""
    charters_dir = workspace / "charters"
    if not charters_dir.is_dir():
        return None
    needle = target.strip().lower()
    for entry in sorted(charters_dir.iterdir()):
        if not entry.is_file():
            continue
        if not CHARTER_FILENAME_RE.match(entry.name):
            continue
        text = entry.read_text(encoding="utf-8")
        m = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
        if not m:
            continue
        target_match = re.search(r"^target:\s*(.+?)\s*$", m.group(1), re.MULTILINE)
        if target_match and target_match.group(1).strip().lower() == needle:
            return entry
    return None


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def render_charter(charter: Charter) -> str:
    lines: list[str] = []
    lines.append("---")
    lines.append(f"id: {charter.id}")
    lines.append(f"mission: {charter.mission}")
    lines.append(f"target: {charter.target}")
    lines.append(f"time-box: {charter.time_box}")
    lines.append("risk-areas:")
    for risk in charter.risk_areas:
        lines.append(f"  - {risk}")
    lines.append("acceptance-criteria:")
    for ac in charter.acceptance_criteria:
        lines.append(f"  - {ac}")
    lines.append(f"created_at: {charter.created_at}")
    lines.append("phase_3_sources:")
    for source in charter.phase_3_sources:
        lines.append(f"  - {source}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {charter.id} - {charter.target}")
    lines.append("")
    lines.append(
        "> Auto-generated by `/tc:create-charter`. Re-running with the same "
        "`--target` preserves user edits below the body; `--new-id` forces a "
        "fresh allocation."
    )
    lines.append("")
    lines.append("## Mission")
    lines.append("")
    lines.append(charter.mission)
    lines.append("")
    lines.append("## Target Area")
    lines.append("")
    lines.append(charter.target)
    lines.append("")
    lines.append("## Time-Box")
    lines.append("")
    lines.append(f"{charter.time_box}. Within this time-box the exploration should "
                 "produce at least one observation per acceptance criterion and "
                 "capture screenshots at every significant page transition.")
    lines.append("")
    lines.append("## Risk Areas")
    lines.append("")
    for risk in charter.risk_areas:
        lines.append(f"- {risk}")
    lines.append("")
    lines.append("## Acceptance Criteria")
    lines.append("")
    for i, ac in enumerate(charter.acceptance_criteria, start=1):
        lines.append(f"{i}. {ac}")
    lines.append("")
    lines.append("## Out of Scope")
    lines.append("")
    if charter.out_of_scope:
        for item in charter.out_of_scope:
            lines.append(f"- {item}")
    else:
        lines.append("_None recorded; refine during exploration._")
    lines.append("")
    lines.append("## Phase 3 Sources")
    lines.append("")
    for source in charter.phase_3_sources:
        lines.append(f"- `{source}`")
    lines.append("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


@dataclass
class RunResult:
    created: int = 0
    skipped: int = 0
    charter_id: str = ""
    path: Path | None = None


def run(
    project_root: Path,
    *,
    target: str | None,
    mission: str | None,
    new_id: bool,
) -> RunResult:
    workspace = workspace_dir(project_root)
    phase_3_sources = assert_product_knowledge_generated(workspace)
    ext = load_extensions(workspace)

    if target is not None or mission is not None:
        suggestion = explicit_charter(workspace, target=target, mission=mission, ext=ext)
    else:
        suggestion = auto_suggest(workspace, ext)

    # Idempotency: skip if an existing charter has the same target, unless
    # --new-id forces a fresh allocation.
    if not new_id:
        existing = find_existing_charter(workspace, suggestion.target)
        if existing is not None:
            m = CHARTER_FILENAME_RE.match(existing.name)
            charter_id = f"CH-{m.group(1)}" if m else existing.stem
            return RunResult(
                created=0,
                skipped=1,
                charter_id=charter_id,
                path=existing,
            )

    new_charter_id = allocate_next_id(workspace)
    charter = Charter(
        id=new_charter_id,
        mission=suggestion.mission,
        target=suggestion.target,
        time_box=DEFAULT_TIME_BOX,
        risk_areas=suggestion.risk_areas,
        acceptance_criteria=suggestion.acceptance_criteria,
        out_of_scope=suggestion.out_of_scope,
        created_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        phase_3_sources=phase_3_sources,
    )

    target_path = workspace / "charters" / f"{new_charter_id}.md"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(render_charter(charter), encoding="utf-8")
    return RunResult(
        created=1,
        skipped=0,
        charter_id=new_charter_id,
        path=target_path,
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create a Phase 4 exploration charter under "
            "<workspace>/charters/<CH-NNN>.md. Auto-suggests a target from "
            "product-knowledge when neither --target nor --mission is supplied."
        ),
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root (default: current directory).",
    )
    parser.add_argument("--target", help="Explicit target area for the charter.")
    parser.add_argument("--mission", help="Explicit mission statement for the charter.")
    parser.add_argument(
        "--new-id",
        action="store_true",
        help=(
            "Force fresh CH-NNN allocation even if an existing charter shares "
            "the same target."
        ),
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        result = run(
            project_root,
            target=args.target,
            mission=args.mission,
            new_id=args.new_id,
        )
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ProductKnowledgeMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except NoSuggestionPossibleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if result.created:
        print(f"created: 1  skipped: 0  -> {result.charter_id} at {result.path}")
    else:
        print(
            f"created: 0  skipped: 1  -> {result.charter_id} already exists at {result.path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
