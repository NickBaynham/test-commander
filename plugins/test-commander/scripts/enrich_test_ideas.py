#!/usr/bin/env python3
"""/tc:test-ideas helper - Phase 4 Step 4.5.

Reads ``<workspace>/sessions/<SESS-ID>.md`` (one or all) and the Phase-2
seeded ``<workspace>/test-ideas/<REQ-ID>.md`` files, and **enriches** each
seed whose REQ-ID is covered by the session via charter-coverage keyword
cross-reference.

Enrichment contract per planning/plan.md Step 4.5:

- Preserves every Phase-2 frontmatter key byte-for-byte (schema,
  requirement_id, requirement_title, source, ac_review_present,
  phase_2_findings, candidates, generated_by).
- Bumps ``status: seed`` -> ``status: enriched`` on enriched files.
- Adds/merges ``phase_4_sessions: [SESS-ID, ...]`` (sorted, deduplicated).
- Appends a ``## Phase 4 enrichment`` body section with one ``### <SESS-ID>``
  sub-block per contributing session. The sub-block carries each candidate
  scenario mapped to this REQ-ID (id / title / type / source / linked
  anomaly).
- Idempotent: re-running with the same session against the same workspace
  is byte-stable; existing sub-blocks are skipped.
- Refuses uninitialized workspace (exit 2), missing sessions (exit 2,
  pointing at ``/tc:session-summary``), missing test-idea seeds (exit 2,
  pointing at ``/tc:requirements-to-tests``).

Per D18 the helper ships inside the plugin. Per D19 the keyword matching
uses universal English stems only; project-specific domain vocabulary
enters via Phase 2's seeded requirements (user-supplied) and Phase 4's
charters (user-authored or auto-suggested from product-knowledge).

Mirrors the Phase 4 helper-mirroring skeleton from Steps 4.2-4.4: workspace
IO + error hierarchy + load-source + per-source extraction + aggregate +
render + orchestration + CLI. Unique work concentrates in session-summary
parsing, REQ-ID coverage matching, and frontmatter-preserving merge.

Exit codes:
    0 - enrichment complete (or no-op when nothing to do).
    2 - precondition failure (uninitialized workspace, missing sessions,
        missing test-idea seeds).
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"
SCHEMA_VERSION = "tc-test-idea/v1"

# Universal candidate-scenario types (D19). Mirrors session_summary.CANDIDATE_TYPES
# verbatim per the Step 4.4 lesson on three-layer cross-phase contracts:
# producer dataclass + producer tests + consumer parser must all agree.
CANDIDATE_TYPES: tuple[str, ...] = ("happy", "edge", "negative")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class EnrichError(Exception):
    pass


class UninitializedWorkspaceError(EnrichError):
    pass


class SessionsMissingError(EnrichError):
    pass


class TestIdeasMissingError(EnrichError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CandidateScenario:
    """Mirrors session_summary.CandidateScenario field-for-field. Per the
    Step 4.4 lesson, the consumer's dataclass closes the third side of
    the cross-phase contract triangle (producer dataclass + producer
    tests + consumer parser)."""

    id: str
    title: str
    type: str
    source: str
    linked_anomaly: str | None


@dataclass(frozen=True)
class ParsedSession:
    session_id: str
    charter_id: str
    charter_target: str
    charter_mission: str
    acceptance_criteria: list[str]
    candidates: list[CandidateScenario] = field(default_factory=list)


@dataclass(frozen=True)
class TestIdea:
    req_id: str
    path: Path
    frontmatter_lines: list[str]
    body: str
    requirement_body: str  # the verbatim requirement text from the body


@dataclass
class EnrichmentOutcome:
    enriched_count: int = 0
    skipped_count: int = 0
    untouched_count: int = 0
    enriched_paths: list[Path] = field(default_factory=list)


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
# Session-summary parsing
# ---------------------------------------------------------------------------


SESSION_TITLE_RE = re.compile(
    r"^#\s+(SESS-\d{8}-\d{3})\s*-\s*session summary for\s+(\S+)",
    re.MULTILINE,
)
CHARTER_BULLET_RE = re.compile(
    r"^- Charter:\s*`([^`]+)`\s*-\s*(.+?)\s*$", re.MULTILINE
)
MISSION_BULLET_RE = re.compile(r"^- Mission:\s*(.+?)\s*$", re.MULTILINE)

CANDIDATE_BLOCK_RE = re.compile(
    r"^### (CS-\d{3}-\d{3})\s*\n((?:- .+\n)+)", re.MULTILINE
)
CANDIDATE_FIELD_RE = re.compile(r"^- ([a-z][a-z0-9_]*):\s*(.+?)\s*$", re.MULTILINE)


def _section_body(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1) if m else ""


def parse_session_summary(path: Path) -> ParsedSession:
    text = path.read_text(encoding="utf-8")
    title_match = SESSION_TITLE_RE.search(text)
    if not title_match:
        raise SessionsMissingError(
            f"session summary {path} does not begin with the expected "
            "title heading; cannot parse"
        )
    session_id = title_match.group(1)
    charter_id = title_match.group(2)

    charter_match = CHARTER_BULLET_RE.search(text)
    charter_target = charter_match.group(2) if charter_match else ""

    mission_match = MISSION_BULLET_RE.search(text)
    charter_mission = mission_match.group(1) if mission_match else ""

    coverage_body = _section_body(text, "Charter Coverage Summary")
    acceptance_criteria = _parse_acceptance_criteria(coverage_body)

    candidates_body = _section_body(text, "Candidate Scenarios")
    candidates = _parse_candidates(candidates_body)

    return ParsedSession(
        session_id=session_id,
        charter_id=charter_id,
        charter_target=charter_target,
        charter_mission=charter_mission,
        acceptance_criteria=acceptance_criteria,
        candidates=candidates,
    )


def _parse_acceptance_criteria(body: str) -> list[str]:
    """Extract the criterion column from the coverage matrix."""
    rows: list[str] = []
    for line in body.split("\n"):
        line = line.strip()
        if not line.startswith("|") or line.startswith("| ---") or line.startswith("| #"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 3:
            continue
        idx_str, criterion, _verdict = parts[:3]
        if not idx_str.isdigit():
            continue
        rows.append(criterion)
    return rows


def _parse_candidates(body: str) -> list[CandidateScenario]:
    """Parse ``### CS-NNN-NNN`` sub-sections with ``- field: value`` bullets.

    Per the Step 4.4 lesson, the producer renders each candidate as an
    independently-citable sub-section so this consumer can grep for field
    names without depending on table column positions.
    """
    out: list[CandidateScenario] = []
    for match in CANDIDATE_BLOCK_RE.finditer(body):
        cs_id = match.group(1)
        block = match.group(2)
        fields_by_name: dict[str, str] = {}
        for fm in CANDIDATE_FIELD_RE.finditer(block):
            fields_by_name[fm.group(1)] = fm.group(2).strip()
        title = fields_by_name.get("title", "")
        cand_type = fields_by_name.get("type", "")
        source = fields_by_name.get("source", "").strip("`")
        linked = fields_by_name.get("linked_anomaly")
        out.append(
            CandidateScenario(
                id=cs_id,
                title=title,
                type=cand_type,
                source=source,
                linked_anomaly=linked,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Test-idea seed parsing
# ---------------------------------------------------------------------------


REQ_ID_RE = re.compile(r"^REQ-\d+\.md$")
SEED_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse_test_idea(path: Path) -> TestIdea:
    text = path.read_text(encoding="utf-8")
    match = SEED_FRONTMATTER_RE.match(text)
    if not match:
        raise TestIdeasMissingError(
            f"test-idea seed {path} missing YAML frontmatter; "
            "regenerate with /tc:requirements-to-tests"
        )
    fm_block = match.group(1)
    body = text[match.end() :]
    req_id_match = re.search(r"^requirement_id:\s*(\S+)\s*$", fm_block, re.MULTILINE)
    req_id = req_id_match.group(1) if req_id_match else path.stem
    requirement_body = _extract_requirement_body(body)
    return TestIdea(
        req_id=req_id,
        path=path,
        frontmatter_lines=fm_block.split("\n"),
        body=body,
        requirement_body=requirement_body,
    )


def _extract_requirement_body(seed_body: str) -> str:
    """Pull the verbatim requirement text from the ``## Requirement`` section."""
    match = re.search(
        r"^##\s+Requirement\s*$\n(.*?)(?=^##\s+|\Z)",
        seed_body,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return ""
    block = match.group(1)
    # The Phase 2 seed quotes the body with a leading ``> ``. Strip the
    # quote prefix and the ``_Source: ...` line.
    lines: list[str] = []
    for raw in block.split("\n"):
        line = raw.strip()
        if not line or line.startswith("_Source:"):
            continue
        if line.startswith(">"):
            line = line[1:].strip()
        lines.append(line)
    return " ".join(lines)


# ---------------------------------------------------------------------------
# Coverage matching
# ---------------------------------------------------------------------------

# Tokens dropped during keyword matching. Kept small: only obviously
# non-discriminating requirements-vocabulary words. Universal English /
# software-engineering vocabulary only per D19.
STOPWORDS: frozenset[str] = frozenset({
    "shall", "system", "user", "users", "their", "this", "that",
    "with", "from", "into", "than", "able", "such", "feature", "data",
    "value", "values", "input", "output", "result", "results", "based",
    "default", "when", "what", "where", "while", "rather", "between",
    "using", "must", "every", "each", "some", "more", "less", "above",
    "below", "after", "before", "should", "would", "could",
    "page", "pages",
})

KEYWORD_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    """Return the set of significant tokens in ``text``: lowercase
    alphanumeric runs of length >= 4 excluding STOPWORDS. Hyphens split
    into separate tokens (``sign-in`` -> ``sign`` + ``in``)."""
    return {t for t in KEYWORD_RE.findall(text.lower())
            if len(t) >= 4 and t not in STOPWORDS}


def _stem(token: str) -> str:
    """Five-character prefix used for stem-matching. ``authenticated`` and
    ``authentication`` both stem to ``authe``; ``session`` and ``sessions``
    both stem to ``sessi``."""
    return token[:5]


def session_keywords(session: ParsedSession) -> set[str]:
    """Union of significant tokens drawn from the charter mission, target,
    each acceptance criterion, and every candidate title + source."""
    parts: list[str] = [
        session.charter_mission,
        session.charter_target,
    ]
    parts.extend(session.acceptance_criteria)
    for cand in session.candidates:
        parts.append(cand.title)
        parts.append(cand.source)
        if cand.linked_anomaly:
            parts.append(cand.linked_anomaly)
    return _tokens(" ".join(parts))


def req_matches_session(idea: TestIdea, sess_stems: set[str]) -> bool:
    """True when the requirement body shares at least one stem with the
    session's keyword set. Stem-matching means ``authentication`` (req)
    matches ``authenticated`` (charter) and ``session`` matches ``sessions``.
    """
    req_stems = {_stem(t) for t in _tokens(idea.requirement_body)}
    return bool(req_stems & sess_stems)


# ---------------------------------------------------------------------------
# Frontmatter merge
# ---------------------------------------------------------------------------


def _split_inline_list(value: str) -> list[str]:
    inner = value.strip().strip("[]")
    if not inner:
        return []
    return [s.strip() for s in inner.split(",") if s.strip()]


def merge_phase_4_sessions(
    existing_lines: list[str], new_session_id: str
) -> tuple[list[str], bool]:
    """Insert or update the ``phase_4_sessions:`` key in frontmatter lines.

    Returns (new_lines, newly_added). ``newly_added`` is True when the
    SESS-ID was not previously present (used for skip/enrich accounting).
    Insertion point: after ``status:`` so the new key appears right next to
    the modified status, mirroring the natural Phase-2 -> Phase-4 enrichment
    locality. The sessions list is sorted and deduplicated.

    Pre-scans the frontmatter for an existing ``phase_4_sessions:`` line.
    When present, only that line is rewritten; no insertion happens. When
    absent, a new line is inserted after the first ``status:`` line. This
    asymmetric pre-scan + insert is what prevents duplicate key emission
    on idempotent re-run (the first cut hit this on Step 4.5; see Phase 4
    Lessons learned).
    """
    sessions_re = re.compile(r"^phase_4_sessions:\s*(.*)\s*$")
    has_existing = any(sessions_re.match(line) for line in existing_lines)

    new_lines: list[str] = []
    inserted = False
    newly_added = True
    for line in existing_lines:
        match = sessions_re.match(line)
        if match:
            existing_ids = _split_inline_list(match.group(1))
            if new_session_id in existing_ids:
                newly_added = False
            merged = sorted(set(existing_ids) | {new_session_id})
            new_lines.append(f"phase_4_sessions: [{', '.join(merged)}]")
            continue
        new_lines.append(line)
        if not has_existing and not inserted and re.match(r"^status:\s*", line):
            new_lines.append(f"phase_4_sessions: [{new_session_id}]")
            inserted = True
    if not has_existing and not inserted:
        new_lines.append(f"phase_4_sessions: [{new_session_id}]")
    return new_lines, newly_added


def flip_status(existing_lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in existing_lines:
        if re.match(r"^status:\s*seed\s*$", line):
            out.append("status: enriched")
        else:
            out.append(line)
    return out


# ---------------------------------------------------------------------------
# Body merge
# ---------------------------------------------------------------------------


PHASE_4_HEADER = "## Phase 4 enrichment"
SESSION_SUBBLOCK_RE = re.compile(
    r"^###\s+(SESS-\d{8}-\d{3})\s*$", re.MULTILINE
)


def render_session_subblock(
    session: ParsedSession,
    candidates: list[CandidateScenario],
) -> str:
    lines: list[str] = []
    lines.append(f"### {session.session_id}")
    lines.append("")
    lines.append(
        f"Charter `{session.charter_id}` - {session.charter_target}"
    )
    lines.append("")
    if candidates:
        lines.append(
            f"This session contributed **{len(candidates)}** candidate "
            "scenario(s) mapped to this requirement via charter-coverage "
            "keyword cross-reference. Refine these into BDD scenarios "
            "(Phase 5) or executable tests (Phase 6) once the candidate "
            "selection has been validated against project-specific risk."
        )
        lines.append("")
        for cand in candidates:
            lines.append(f"- **{cand.id}** ({cand.type}) - {cand.title}")
            lines.append(f"  - source: `{cand.source}`")
            if cand.linked_anomaly:
                lines.append(f"  - linked_anomaly: `{cand.linked_anomaly}`")
    else:
        lines.append(
            "_This session covered the requirement via charter overlap but "
            "produced no candidate scenarios (no anomalies, no coverage gaps, "
            "no successful flows)._"
        )
    lines.append("")
    return "\n".join(lines)


def merge_body(body: str, session: ParsedSession, subblock: str) -> tuple[str, bool]:
    """Merge ``subblock`` into ``body`` under the ``## Phase 4 enrichment``
    section. Returns (new_body, newly_added). Existing sub-blocks for the
    same SESS-ID are left untouched (idempotent)."""
    if PHASE_4_HEADER in body:
        # Locate the existing Phase 4 enrichment section.
        section_match = re.search(
            rf"^{re.escape(PHASE_4_HEADER)}\s*$\n(.*?)(?=^##\s+|\Z)",
            body,
            re.MULTILINE | re.DOTALL,
        )
        if section_match:
            section_body = section_match.group(1)
            existing_ids = SESSION_SUBBLOCK_RE.findall(section_body)
            if session.session_id in existing_ids:
                return body, False
            # Append the new sub-block at the end of the existing section.
            new_section_body = section_body.rstrip("\n") + "\n\n" + subblock
            new_section_body = new_section_body.rstrip("\n") + "\n"
            new_body = (
                body[: section_match.start(1)]
                + new_section_body
                + body[section_match.end(1) :]
            )
            return new_body, True
    # No existing enrichment section - append at end.
    stripped = body.rstrip("\n")
    new_body = (
        stripped
        + "\n\n"
        + PHASE_4_HEADER
        + "\n\n"
        + subblock.rstrip("\n")
        + "\n"
    )
    return new_body, True


# ---------------------------------------------------------------------------
# Enrichment orchestration
# ---------------------------------------------------------------------------


def enrich_seed_with_session(
    idea: TestIdea, session: ParsedSession
) -> tuple[str, bool]:
    """Produce the enriched file text for ``idea`` against ``session``.

    Returns (new_text, newly_enriched). ``newly_enriched`` is False when
    the session was already present in ``phase_4_sessions`` AND the body
    already had a sub-block for it - that is, the idempotent re-run case.
    """
    fm_lines = list(idea.frontmatter_lines)
    fm_lines = flip_status(fm_lines)
    fm_lines, added_session_key = merge_phase_4_sessions(fm_lines, session.session_id)
    subblock = render_session_subblock(session, session.candidates)
    new_body, added_body = merge_body(idea.body, session, subblock)
    new_text = "---\n" + "\n".join(fm_lines) + "\n---\n" + new_body
    return new_text, added_session_key or added_body


def discover_sessions(workspace: Path, session_id: str | None) -> list[Path]:
    sessions_dir = workspace / "sessions"
    if not sessions_dir.is_dir():
        raise SessionsMissingError(
            "no session summaries found under sessions/. "
            "Run /tc:session-summary --session <SESS-ID> first."
        )
    if session_id is not None:
        path = sessions_dir / f"{session_id}.md"
        if not path.is_file():
            raise SessionsMissingError(
                f"session summary not found: sessions/{session_id}.md. "
                "Run /tc:session-summary --session <SESS-ID> first."
            )
        return [path]
    paths = sorted(
        p
        for p in sessions_dir.glob("SESS-*.md")
        if p.is_file()
    )
    if not paths:
        raise SessionsMissingError(
            "no session summaries found under sessions/. "
            "Run /tc:session-summary --session <SESS-ID> first."
        )
    return paths


def discover_test_ideas(workspace: Path) -> list[TestIdea]:
    test_ideas_dir = workspace / "test-ideas"
    if not test_ideas_dir.is_dir():
        raise TestIdeasMissingError(
            "no test-idea seeds found under test-ideas/. "
            "Run /tc:requirements-to-tests first."
        )
    paths = [p for p in sorted(test_ideas_dir.glob("REQ-*.md")) if p.is_file()]
    if not paths:
        raise TestIdeasMissingError(
            "no REQ-*.md test-idea seeds found under test-ideas/. "
            "Run /tc:requirements-to-tests first."
        )
    return [parse_test_idea(p) for p in paths]


def run(
    project_root: Path,
    *,
    session_id: str | None,
) -> EnrichmentOutcome:
    workspace = workspace_dir(project_root)
    session_paths = discover_sessions(workspace, session_id)
    ideas = discover_test_ideas(workspace)

    outcome = EnrichmentOutcome()
    touched: set[Path] = set()
    skipped: set[Path] = set()

    for session_path in session_paths:
        session = parse_session_summary(session_path)
        sess_stems = {_stem(t) for t in session_keywords(session)}
        for idea in ideas:
            if not req_matches_session(idea, sess_stems):
                continue
            current_text = idea.path.read_text(encoding="utf-8")
            current_idea = parse_test_idea(idea.path)
            new_text, newly = enrich_seed_with_session(current_idea, session)
            if new_text == current_text:
                skipped.add(idea.path)
                continue
            idea.path.write_text(new_text, encoding="utf-8")
            touched.add(idea.path)
            if newly:
                outcome.enriched_paths.append(idea.path)

    outcome.enriched_count = len(set(outcome.enriched_paths))
    outcome.skipped_count = len(skipped - touched)
    outcome.untouched_count = (
        len(ideas) - len({p for p in touched | skipped})
    )
    return outcome


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Enrich Phase-2 test-idea seeds with session-derived candidate "
            "scenarios. Reads sessions/<SESS-ID>.md and test-ideas/<REQ-ID>.md "
            "and writes back the enriched test-idea files in place."
        ),
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root (default: current directory).",
    )
    parser.add_argument(
        "--session",
        default=None,
        help=(
            "Specific SESS-ID to use as the enrichment source. If omitted, "
            "every session under <workspace>/sessions/ is processed."
        ),
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        outcome = run(project_root, session_id=args.session)
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except SessionsMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except TestIdeasMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"enriched: {outcome.enriched_count} "
        f"(skipped: {outcome.skipped_count}, "
        f"untouched: {outcome.untouched_count})"
    )
    for path in outcome.enriched_paths:
        print(f"  - {path.relative_to(project_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
