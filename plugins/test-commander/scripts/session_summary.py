#!/usr/bin/env python3
"""/tc:session-summary helper - Phase 4 Step 4.4.

Reads ``<workspace>/exploration-notes/<SESS-ID>.md`` (required, refused
with precondition error pointing at ``/tc:explore`` when missing) and
synthesizes a per-session summary at ``<workspace>/sessions/<SESS-ID>.md``
plus an ``<workspace>/sessions/index.md`` ledger listing every session.

The summary aggregates the exploration note's Observations table by
``event_type``, the Anomalies table by ``category`` and ``severity``,
the Charter Coverage matrix into a one-line verdict, and the Evidence
index. It then extracts ``CandidateScenario`` entries with a shape
forward-compatible with Step 4.5's enrichment input: one candidate per
anomaly (typed ``negative``); one candidate per ``partial`` /
``unobserved`` coverage verdict (typed ``edge``); plus happy-path
candidates derived from successful flows (network requests returning
2xx that touch a charter target keyword).

Mirrors the Phase 4 helper-mirroring skeleton from Steps 4.2 + 4.3:
workspace IO + error hierarchy + load-source + per-source extraction
+ aggregate + render + orchestration + CLI. The skeleton transferred
~95% verbatim from explore.py; the unique work is exploration-note
markdown parsing and candidate synthesis.

Per D18 the helper ships inside the plugin. Per D19 the candidate
type universal core (``happy`` / ``edge`` / ``negative``) carries no
domain vocabulary.

Exit codes:
    0 - session summary written.
    2 - uninitialized workspace, missing exploration note, or other
        precondition failure.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"

EVENT_TYPES: tuple[str, ...] = (
    "page_load",
    "click",
    "fill",
    "screenshot",
    "console_message",
    "network_request",
)

ANOMALY_CATEGORIES: tuple[str, ...] = (
    "slow-response",
    "console-error",
    "broken-link",
    "missing-evidence",
    "auth-mismatch",
    "unexpected-state",
)

SEVERITY_CORE: tuple[str, ...] = ("low", "medium", "high", "critical")

# Universal candidate-scenario types (D19). Mirrors Phase 2's
# ``tc-test-idea/v1`` candidate shape so Step 4.5 can map these to
# REQ-ID seeds without translation.
CANDIDATE_TYPES: tuple[str, ...] = ("happy", "edge", "negative")

COVERAGE_VERDICTS: tuple[str, ...] = ("observed", "partial", "unobserved")


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class SummaryError(Exception):
    pass


class UninitializedWorkspaceError(SummaryError):
    pass


class ExplorationNoteMissingError(SummaryError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ObservationRow:
    source_index: int
    timestamp: str
    event_type: str
    page_url: str
    action: str
    result: str


@dataclass(frozen=True)
class AnomalyRow:
    category: str
    severity: str
    page_url: str
    reproduction: str
    evidence: str  # screenshot id or "_(none)_"


@dataclass(frozen=True)
class EvidenceRow:
    screenshot_id: str
    page_url: str
    caption: str
    reference: str


@dataclass(frozen=True)
class CoverageRow:
    criterion: str
    verdict: str  # observed / partial / unobserved


@dataclass(frozen=True)
class CandidateScenario:
    id: str
    title: str
    type: str  # happy / edge / negative
    source: str  # SESS-ID:<source_index> or coverage-AC reference
    linked_anomaly: str | None


@dataclass
class ParsedNote:
    session_id: str
    charter_id: str
    charter_target: str
    started_at: str
    source_file: str
    observations: list[ObservationRow] = field(default_factory=list)
    anomalies: list[AnomalyRow] = field(default_factory=list)
    evidence: list[EvidenceRow] = field(default_factory=list)
    coverage: list[CoverageRow] = field(default_factory=list)


@dataclass
class Charter:
    id: str
    target: str
    mission: str
    acceptance_criteria: list[str]


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
# Charter loading (slim version - only need a few fields)
# ---------------------------------------------------------------------------


CHARTER_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
SCALAR_FIELD_RE = re.compile(r"^([a-z][a-z0-9_-]*):\s*(.+?)\s*$", re.MULTILINE)
LIST_FIELD_BLOCK_RE = re.compile(
    r"^([a-z][a-z0-9_-]*):\s*\n((?:  - .+\n)+)", re.MULTILINE
)
LIST_ITEM_RE = re.compile(r"^  - (.+)$", re.MULTILINE)


def load_charter(workspace: Path, charter_id: str) -> Charter:
    target = workspace / "charters" / f"{charter_id}.md"
    if not target.is_file():
        # Charter missing is not fatal here - we already have the resolved
        # charter ID from the exploration note. Return a stub.
        return Charter(id=charter_id, target="(charter file not found)", mission="",
                       acceptance_criteria=[])
    text = target.read_text(encoding="utf-8")
    match = CHARTER_FRONTMATTER_RE.match(text)
    if not match:
        return Charter(id=charter_id, target="(charter frontmatter unparseable)",
                       mission="", acceptance_criteria=[])
    fm = match.group(1)
    scalars: dict[str, str] = {}
    for sc in SCALAR_FIELD_RE.finditer(fm):
        scalars[sc.group(1)] = sc.group(2).strip()
    lists: dict[str, list[str]] = {}
    for lst in LIST_FIELD_BLOCK_RE.finditer(fm):
        items = [item.group(1).strip() for item in LIST_ITEM_RE.finditer(lst.group(2))]
        lists[lst.group(1)] = items
    return Charter(
        id=charter_id,
        target=scalars.get("target", ""),
        mission=scalars.get("mission", ""),
        acceptance_criteria=lists.get("acceptance-criteria", []),
    )


# ---------------------------------------------------------------------------
# Exploration-note parsing
# ---------------------------------------------------------------------------


SESSION_TITLE_RE = re.compile(
    r"^#\s+(SESS-\d{8}-\d{3})\s*-\s*(?:exploration note|session summary) for\s+(\S+)",
    re.MULTILINE,
)
CHARTER_BULLET_RE = re.compile(
    r"^- Charter:\s*`([^`]+)`\s*-\s*(.+?)\s*$", re.MULTILINE
)
STARTED_AT_RE = re.compile(r"^- Started at:\s*(.+?)\s*$", re.MULTILINE)
SOURCE_BULLET_RE = re.compile(r"^- Source:\s*`([^`]+)`\s*$", re.MULTILINE)

# Table-row regex: matches a markdown table row whose first cell is a
# numeric source-index (Observations) or a category (Anomalies).
TABLE_ROW_RE = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*$", re.MULTILINE)


def _split_table_row(row: str) -> list[str]:
    parts = [p.strip() for p in row.strip().strip("|").split("|")]
    return parts


def parse_exploration_note(path: Path) -> ParsedNote:
    """Parse the structured markdown the Step 4.3 helper wrote."""
    if not path.is_file():
        raise ExplorationNoteMissingError(
            f"exploration note not found: {path}. Run /tc:explore to "
            f"generate one for this session."
        )
    text = path.read_text(encoding="utf-8")

    title_match = SESSION_TITLE_RE.search(text)
    if not title_match:
        raise ExplorationNoteMissingError(
            f"exploration note {path} does not begin with the expected "
            "title heading; cannot parse"
        )
    session_id = title_match.group(1)
    charter_id = title_match.group(2)

    charter_match = CHARTER_BULLET_RE.search(text)
    charter_target = charter_match.group(2) if charter_match else ""

    started_match = STARTED_AT_RE.search(text)
    started_at = started_match.group(1) if started_match else ""

    source_match = SOURCE_BULLET_RE.search(text)
    source_file = source_match.group(1) if source_match else ""

    observations = _parse_observations_table(text)
    anomalies = _parse_anomalies_table(text)
    evidence = _parse_evidence_table(text)
    coverage = _parse_coverage_table(text)

    return ParsedNote(
        session_id=session_id,
        charter_id=charter_id,
        charter_target=charter_target,
        started_at=started_at,
        source_file=source_file,
        observations=observations,
        anomalies=anomalies,
        evidence=evidence,
        coverage=coverage,
    )


def _section_body(text: str, heading: str, next_heading_pattern: str = r"^## ") -> str:
    """Return the body of a ``## <heading>`` section up to the next ``## ``."""
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1) if m else ""


def _parse_observations_table(text: str) -> list[ObservationRow]:
    body = _section_body(text, "Observations")
    rows: list[ObservationRow] = []
    for line in body.split("\n"):
        line = line.strip()
        if not line.startswith("|") or line.startswith("| #"):
            continue
        if line.startswith("| ---"):
            continue
        parts = _split_table_row(line)
        if len(parts) < 6:
            continue
        idx_str, timestamp, event_type, page_url, action, result = parts[:6]
        if not idx_str.isdigit():
            continue
        rows.append(
            ObservationRow(
                source_index=int(idx_str),
                timestamp=timestamp,
                event_type=event_type,
                page_url=page_url,
                action=action,
                result=result,
            )
        )
    return rows


def _parse_anomalies_table(text: str) -> list[AnomalyRow]:
    body = _section_body(text, "Anomalies")
    rows: list[AnomalyRow] = []
    table_seen_header = False
    for line in body.split("\n"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        if line.startswith("| Category"):
            table_seen_header = True
            continue
        if line.startswith("| ---"):
            continue
        if not table_seen_header:
            continue
        parts = _split_table_row(line)
        if len(parts) < 5:
            continue
        category, severity, page_url, repro, evidence = parts[:5]
        if category not in ANOMALY_CATEGORIES:
            continue
        rows.append(
            AnomalyRow(
                category=category,
                severity=severity,
                page_url=page_url,
                reproduction=repro,
                evidence=evidence,
            )
        )
    return rows


def _parse_evidence_table(text: str) -> list[EvidenceRow]:
    body = _section_body(text, "Evidence")
    rows: list[EvidenceRow] = []
    for line in body.split("\n"):
        line = line.strip()
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        if line.startswith("| Screenshot"):
            continue
        parts = _split_table_row(line)
        if len(parts) < 4:
            continue
        screenshot_id, page_url, caption, reference = parts[:4]
        if not screenshot_id.startswith("S-"):
            continue
        rows.append(
            EvidenceRow(
                screenshot_id=screenshot_id,
                page_url=page_url,
                caption=caption,
                reference=reference.strip("`"),
            )
        )
    return rows


def _parse_coverage_table(text: str) -> list[CoverageRow]:
    body = _section_body(text, "Charter Coverage")
    rows: list[CoverageRow] = []
    for line in body.split("\n"):
        line = line.strip()
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        if line.startswith("| #"):
            continue
        parts = _split_table_row(line)
        if len(parts) < 3:
            continue
        idx_str, criterion, verdict_cell = parts[:3]
        if not idx_str.isdigit():
            continue
        # Verdict cell is rendered as ``**observed**`` etc.
        verdict = verdict_cell.strip().strip("*").strip().lower()
        if verdict not in COVERAGE_VERDICTS:
            continue
        rows.append(CoverageRow(criterion=criterion, verdict=verdict))
    return rows


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def aggregate_observations(observations: list[ObservationRow]) -> dict[str, int]:
    counts: dict[str, int] = {et: 0 for et in EVENT_TYPES}
    for obs in observations:
        if obs.event_type in counts:
            counts[obs.event_type] += 1
    return counts


def aggregate_anomalies_by_category(anomalies: list[AnomalyRow]) -> dict[str, int]:
    counts: dict[str, int] = {cat: 0 for cat in ANOMALY_CATEGORIES}
    for anom in anomalies:
        if anom.category in counts:
            counts[anom.category] += 1
    return counts


def aggregate_anomalies_by_severity(anomalies: list[AnomalyRow]) -> dict[str, int]:
    counts: dict[str, int] = {sev: 0 for sev in SEVERITY_CORE}
    for anom in anomalies:
        sev = anom.severity.strip().lower()
        if sev in counts:
            counts[sev] += 1
    return counts


def aggregate_coverage(coverage: list[CoverageRow]) -> dict[str, int]:
    counts: dict[str, int] = {v: 0 for v in COVERAGE_VERDICTS}
    for row in coverage:
        if row.verdict in counts:
            counts[row.verdict] += 1
    return counts


def compute_duration(observations: list[ObservationRow]) -> str:
    """Return a human-readable duration string from first to last
    observation timestamp."""
    if len(observations) < 2:
        return "n/a (insufficient observations)"
    first_ts = _parse_iso_timestamp(observations[0].timestamp)
    last_ts = _parse_iso_timestamp(observations[-1].timestamp)
    if first_ts is None or last_ts is None:
        return "n/a (unparseable timestamps)"
    seconds = (last_ts - first_ts).total_seconds()
    if seconds < 0:
        seconds = 0
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m {secs}s ({seconds:.1f}s total)"


def _parse_iso_timestamp(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        cleaned = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Candidate Scenario synthesis
# ---------------------------------------------------------------------------


def _session_seq_for_id(session_id: str) -> str:
    """Return the last NNN of SESS-YYYYMMDD-NNN for use in CS IDs."""
    m = re.search(r"-(\d{3})$", session_id)
    return m.group(1) if m else "000"


def synthesize_candidates(
    parsed: ParsedNote,
) -> list[CandidateScenario]:
    """Synthesize candidate scenarios from the exploration session:

    - One ``negative`` candidate per anomaly (sorted by category for stable
      ordering).
    - One ``edge`` candidate per ``partial`` / ``unobserved`` coverage verdict
      (in source order).
    - Up to three ``happy`` candidates drawn from successful network requests
      hitting distinct paths (sorted by source_index).

    Deterministic CS IDs: ``CS-<session-NNN>-<seq>`` where seq is the
    1-based ordinal across the candidate list.
    """
    candidates: list[CandidateScenario] = []
    session_nnn = _session_seq_for_id(parsed.session_id)
    seq = 0

    def next_id() -> str:
        nonlocal seq
        seq += 1
        return f"CS-{session_nnn}-{seq:03d}"

    # 1. Negative candidates from anomalies.
    sorted_anomalies = sorted(parsed.anomalies, key=lambda a: a.category)
    for anom in sorted_anomalies:
        title = f"Reproduce {anom.category} on {anom.page_url or '(no page)'}"
        candidates.append(
            CandidateScenario(
                id=next_id(),
                title=title,
                type="negative",
                source=f"{parsed.session_id}:anomaly:{anom.category}",
                linked_anomaly=anom.category,
            )
        )

    # 2. Edge candidates from partial/unobserved coverage verdicts.
    for idx, cov in enumerate(parsed.coverage, start=1):
        if cov.verdict in ("partial", "unobserved"):
            title = (
                f"Follow-up exploration to fully cover acceptance criterion #{idx}: "
                f"'{cov.criterion[:80]}'"
            )
            candidates.append(
                CandidateScenario(
                    id=next_id(),
                    title=title,
                    type="edge",
                    source=f"{parsed.session_id}:coverage:AC{idx}:{cov.verdict}",
                    linked_anomaly=None,
                )
            )

    # 3. Happy candidates from successful network requests on distinct paths.
    seen_paths: set[str] = set()
    for obs in parsed.observations:
        if obs.event_type != "network_request":
            continue
        # The action is "METHOD path -> status" per the explore renderer.
        m = re.match(r"^(GET|POST|PUT|PATCH|DELETE)\s+(\S+)\s+->\s+(\d{3})", obs.action)
        if not m:
            continue
        method, path, status = m.group(1), m.group(2), int(m.group(3))
        if not (200 <= status < 300):
            continue
        key = f"{method} {path}"
        if key in seen_paths:
            continue
        seen_paths.add(key)
        title = f"Happy path: {method} {path} returns {status}"
        candidates.append(
            CandidateScenario(
                id=next_id(),
                title=title,
                type="happy",
                source=f"{parsed.session_id}:obs:{obs.source_index}",
                linked_anomaly=None,
            )
        )
        if len(seen_paths) >= 3:
            break

    return candidates


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def render_summary(
    parsed: ParsedNote,
    charter: Charter,
    candidates: list[CandidateScenario],
) -> str:
    obs_counts = aggregate_observations(parsed.observations)
    anom_by_cat = aggregate_anomalies_by_category(parsed.anomalies)
    anom_by_sev = aggregate_anomalies_by_severity(parsed.anomalies)
    cov_counts = aggregate_coverage(parsed.coverage)
    duration = compute_duration(parsed.observations)

    lines: list[str] = []
    lines.append(f"# {parsed.session_id} - session summary for {charter.id}")
    lines.append("")
    lines.append(
        "> Auto-generated by `/tc:session-summary`. Pure generated report - "
        "re-running against the same exploration note produces byte-identical "
        "bytes."
    )
    lines.append("")

    # Session
    lines.append("## Session")
    lines.append("")
    lines.append(f"- Session: `{parsed.session_id}`")
    lines.append(f"- Charter: `{charter.id}` - {charter.target}")
    if charter.mission:
        lines.append(f"- Mission: {charter.mission}")
    lines.append(f"- Started at: {parsed.started_at}")
    lines.append(f"- Duration: {duration}")
    lines.append(f"- Source: `{parsed.source_file}`")
    lines.append(f"- Exploration note: `exploration-notes/{parsed.session_id}.md`")
    lines.append("")

    # Observation Summary
    lines.append("## Observation Summary")
    lines.append("")
    total_obs = sum(obs_counts.values())
    lines.append(f"Total observations: **{total_obs}**.")
    lines.append("")
    lines.append("| event_type | Count |")
    lines.append("| --- | --- |")
    for event_type in EVENT_TYPES:
        lines.append(f"| {event_type} | {obs_counts[event_type]} |")
    lines.append("")

    # Anomaly Summary
    lines.append("## Anomaly Summary")
    lines.append("")
    total_anom = sum(anom_by_cat.values())
    lines.append(f"Total anomalies: **{total_anom}**.")
    lines.append("")
    lines.append("By category:")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("| --- | --- |")
    for category in ANOMALY_CATEGORIES:
        lines.append(f"| {category} | {anom_by_cat[category]} |")
    lines.append("")
    lines.append("By severity:")
    lines.append("")
    lines.append("| Severity | Count |")
    lines.append("| --- | --- |")
    for sev in SEVERITY_CORE:
        lines.append(f"| {sev} | {anom_by_sev[sev]} |")
    lines.append("")

    # Charter Coverage Summary
    lines.append("## Charter Coverage Summary")
    lines.append("")
    total_acs = sum(cov_counts.values())
    lines.append(
        f"Total acceptance criteria: **{total_acs}**. "
        f"Verdicts: **{cov_counts['observed']}** observed, "
        f"**{cov_counts['partial']}** partial, "
        f"**{cov_counts['unobserved']}** unobserved."
    )
    lines.append("")
    if parsed.coverage:
        lines.append("| # | Acceptance Criterion | Verdict |")
        lines.append("| --- | --- | --- |")
        for idx, cov in enumerate(parsed.coverage, start=1):
            criterion = cov.criterion.replace("|", "\\|")
            lines.append(f"| {idx} | {criterion} | **{cov.verdict}** |")
    else:
        lines.append("_The charter declared no acceptance criteria._")
    lines.append("")

    # Evidence
    lines.append("## Evidence")
    lines.append("")
    lines.append(f"Total screenshots: **{len(parsed.evidence)}**.")
    lines.append("")
    if parsed.evidence:
        lines.append("| Screenshot | Page | Caption | Reference |")
        lines.append("| --- | --- | --- | --- |")
        for ev in parsed.evidence:
            caption = ev.caption.replace("|", "\\|")
            page_url = ev.page_url.replace("|", "\\|")
            lines.append(
                f"| {ev.screenshot_id} | {page_url} | {caption} | `{ev.reference}` |"
            )
    else:
        lines.append("_No screenshots captured in this session._")
    lines.append("")

    # Candidate Scenarios
    lines.append("## Candidate Scenarios")
    lines.append("")
    lines.append(
        "Forward-compatible with Step 4.5's enrichment input "
        "(`tc-test-idea/v1` candidates shape). Step 4.5 (`/tc:test-ideas`) "
        "maps these candidates to Phase-2 REQ-IDs via charter-coverage "
        "cross-reference. Each entry carries the four stable fields "
        "Step 4.5 reads: `title`, `type`, `source`, and (optional) "
        "`linked_anomaly`."
    )
    lines.append("")
    if candidates:
        for cand in candidates:
            lines.append(f"### {cand.id}")
            lines.append("")
            lines.append(f"- title: {cand.title}")
            lines.append(f"- type: {cand.type}")
            lines.append(f"- source: `{cand.source}`")
            if cand.linked_anomaly:
                lines.append(f"- linked_anomaly: {cand.linked_anomaly}")
            lines.append("")
    else:
        lines.append(
            "_No candidate scenarios synthesized "
            "(no anomalies, no coverage gaps, no successful flows)._"
        )
        lines.append("")

    # Executive Narrative (Claude judgment layer completes this)
    lines.append("## Executive Narrative")
    lines.append("")
    lines.append(
        "_Mechanical synthesis complete. The Claude judgment layer completes "
        "this section with: (1) anomaly severity calibration relative to the "
        "consuming project's risk model; (2) candidate-scenario prioritization "
        "by risk x coverage gap; (3) partial-coverage follow-up recommendations "
        "(accept-as-best-effort or author a follow-up charter); (4) cross-source "
        "correlation with Phase 3 product-knowledge artifacts. See "
        "`methodology/session-based-test-management.md` for the judgment layer._"
    )
    lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------
# Sessions index
# ---------------------------------------------------------------------------


SESSION_FILENAME_RE = re.compile(r"^SESS-\d{8}-\d{3}\.md$")
INDEX_ROW_RE = re.compile(
    r"^- `(SESS-\d{8}-\d{3})` - charter `(\S+)`",
    re.MULTILINE,
)


def update_sessions_index(workspace: Path) -> None:
    """Scan every ``<workspace>/sessions/SESS-*.md`` and rebuild
    ``index.md`` as a one-line-per-session ledger sorted by SESS-ID."""
    sessions_dir = workspace / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    rows: list[tuple[str, str]] = []
    for entry in sorted(sessions_dir.iterdir()):
        if not entry.is_file():
            continue
        if not SESSION_FILENAME_RE.match(entry.name):
            continue
        text = entry.read_text(encoding="utf-8")
        title_match = SESSION_TITLE_RE.search(text)
        charter_id = title_match.group(2) if title_match else "(unknown)"
        # Pull duration from the body if present.
        dur_match = re.search(r"^- Duration:\s*(.+?)\s*$", text, re.MULTILINE)
        anom_match = re.search(r"^Total anomalies:\s*\*\*(\d+)\*\*", text, re.MULTILINE)
        verdict_match = re.search(
            r"^Verdicts:\s*\*\*(\d+)\*\*\s*observed,\s*\*\*(\d+)\*\*\s*partial,\s*"
            r"\*\*(\d+)\*\*\s*unobserved",
            text,
            re.MULTILINE,
        )
        parts = [f"`{entry.stem}`", f"charter `{charter_id}`"]
        if dur_match:
            parts.append(f"duration {dur_match.group(1)}")
        if anom_match:
            parts.append(f"anomalies={anom_match.group(1)}")
        if verdict_match:
            parts.append(
                f"coverage={verdict_match.group(1)}o/"
                f"{verdict_match.group(2)}p/"
                f"{verdict_match.group(3)}u"
            )
        rows.append((entry.stem, " - ".join(parts)))

    lines: list[str] = []
    lines.append("# Sessions index")
    lines.append("")
    lines.append(
        "Auto-generated by `/tc:session-summary`. Re-scans every "
        "`sessions/SESS-*.md` on each invocation. One row per session, "
        "sorted by SESS-ID (chronological by the YYYYMMDD prefix)."
    )
    lines.append("")
    if rows:
        for _, row in rows:
            lines.append(f"- {row}")
    else:
        lines.append("_No sessions summarized yet._")
    lines.append("")
    index_path = sessions_dir / "index.md"
    index_path.write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


@dataclass
class RunResult:
    session_id: str
    summary_path: Path
    candidates_count: int


def run(project_root: Path, *, session_id: str) -> RunResult:
    workspace = workspace_dir(project_root)
    note_path = workspace / "exploration-notes" / f"{session_id}.md"
    if not note_path.is_file():
        raise ExplorationNoteMissingError(
            f"exploration note not found: exploration-notes/{session_id}.md. "
            f"Run /tc:explore --charter <CH-ID> to generate one for this session."
        )

    parsed = parse_exploration_note(note_path)
    charter = load_charter(workspace, parsed.charter_id)
    candidates = synthesize_candidates(parsed)

    sessions_dir = workspace / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    summary_path = sessions_dir / f"{session_id}.md"
    summary_path.write_text(render_summary(parsed, charter, candidates), encoding="utf-8")

    update_sessions_index(workspace)

    return RunResult(
        session_id=session_id,
        summary_path=summary_path,
        candidates_count=len(candidates),
    )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Synthesize a per-session summary from an exploration note. "
            "Reads exploration-notes/<SESS-ID>.md and writes "
            "sessions/<SESS-ID>.md plus sessions/index.md."
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
        required=True,
        help="Session ID to summarize (e.g. SESS-20260528-600).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        result = run(project_root, session_id=args.session)
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ExplorationNoteMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"session summary written: {result.session_id} "
        f"({result.candidates_count} candidate scenarios) at {result.summary_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
