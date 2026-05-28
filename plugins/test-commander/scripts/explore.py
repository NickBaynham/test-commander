#!/usr/bin/env python3
"""/tc:explore helper - Phase 4 Step 4.3.

Reads a Phase-4 charter file at ``<workspace>/charters/<CH-ID>.md``
(required) plus a recorded Playwright MCP session at the configured
path (default ``<workspace>/documents/uploaded/recorded-sessions/<CH-
ID>.json``). Parses every event into a structured ``Observation``,
classifies anomalies into the universal categories, computes a
charter-coverage matrix, runs the internal exploration-review sub-mode
(suppressible with ``--no-review``), and writes
``<workspace>/exploration-notes/<SESS-ID>.md`` byte-deterministically.

Mirrors the Phase 4 helper-mirroring skeleton established in Step 4.2
(``create_charter.py``). Differences from 4.2: per-source extraction
operates on JSON events instead of Markdown bodies; idempotency is
overwrite (pure generated report) rather than skip-not-overwrite;
session-ID allocation derives from the recorded session's first event
timestamp so re-runs against the same recording produce the same SESS-
ID. Live-mode refusal under pytest mirrors Phase 3 Step 3.5 verbatim.

Per D18 the helper ships inside the plugin. Per D19 the anomaly
categories ship as universal cores; project extensions enter through
``tc-explore.exploration:`` in ``<workspace>/config.yaml``.

Exit codes:
    0 - exploration note written.
    2 - uninitialized workspace, missing charter, missing recording,
        live mode under pytest, or other precondition failure.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"
SOURCE_LABEL = "exploration"

DEFAULT_RECORDED_DIR = "documents/uploaded/recorded-sessions"
PYTEST_ENV_VAR = "PYTEST_CURRENT_TEST"

# Universal cores (D19). Project extensions union additively via
# tc-explore.exploration.* in <workspace>/config.yaml.
ANOMALY_CATEGORIES: tuple[str, ...] = (
    "slow-response",
    "console-error",
    "broken-link",
    "missing-evidence",
    "auth-mismatch",
    "unexpected-state",
)

SEVERITY_CORE: tuple[str, ...] = ("low", "medium", "high", "critical")

EVENT_TYPES: tuple[str, ...] = (
    "page_load",
    "click",
    "fill",
    "screenshot",
    "console_message",
    "network_request",
    "anomaly",
)

# Trigger words that, when present in an acceptance criterion but absent
# from observed events, downgrade the coverage verdict to ``partial``.
# These are universal English words indicating a specific scenario the
# AC requires.
TRIGGER_WORDS_NEEDING_OBSERVATION: frozenset[str] = frozenset(
    {
        "expiration",
        "expired",
        "expire",
        "leak",
        "leakage",
        "concurrent",
        "race",
        "timeout",
        "timed-out",
        "rollback",
    }
)

STOPWORDS: frozenset[str] = frozenset(
    {
        "with", "from", "into", "that", "this", "than", "what", "when", "where",
        "have", "been", "were", "will", "should", "would", "and", "for", "the",
        "valid", "response", "body", "their", "they", "them", "back",
        "during",
    }
)

URL_PATH_RE = re.compile(r"/[a-zA-Z][a-zA-Z0-9/{}_-]+")
WORD_RE = re.compile(r"\b[a-z]{4,}\b")

SCREENSHOT_ADJACENCY_SECONDS = 3.0


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ExploreError(Exception):
    pass


class UninitializedWorkspaceError(ExploreError):
    pass


class CharterMissingError(ExploreError):
    pass


class RecordedSessionMissingError(ExploreError):
    pass


class LiveModeRefusedError(ExploreError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Observation:
    timestamp: str
    event_type: str
    page_url: str
    action: str
    result: str
    screenshot_id: str | None
    source_index: int  # 0-based index into the recorded events list


@dataclass(frozen=True)
class Evidence:
    screenshot_id: str
    page_url: str
    caption: str
    source_index: int


@dataclass(frozen=True)
class Anomaly:
    category: str
    severity: str
    page_url: str
    reproduction: str
    screenshot_id: str | None
    timestamp: str
    source_index: int


@dataclass(frozen=True)
class CoverageVerdict:
    criterion: str
    status: str  # observed / partial / unobserved
    matched_paths: tuple[str, ...]
    matched_keywords: tuple[str, ...]


@dataclass(frozen=True)
class GapSignal:
    kind: str
    description: str
    source_file: str | None
    line: int | None


@dataclass
class Extensions:
    mode: str = "recorded"
    recorded_path: str = DEFAULT_RECORDED_DIR
    mcp_endpoint: str | None = None
    target_url: str | None = None


@dataclass
class Charter:
    id: str
    target: str
    mission: str
    acceptance_criteria: list[str]


@dataclass
class ExploreFindings:
    charter: Charter
    session_id: str
    session_started_at: str
    source_file: str  # relative path of the recorded-session.json
    observations: list[Observation] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    anomalies: list[Anomaly] = field(default_factory=list)
    coverage: list[CoverageVerdict] = field(default_factory=list)
    gaps: list[GapSignal] = field(default_factory=list)


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
    """Read ``tc-explore.exploration:`` extensions from ``<workspace>/config.yaml``."""
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
        if pending_key is not None and section == "exploration":
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

        if indent == 4 and section == "exploration":
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
    if key == "mode":
        ext.mode = items[0]
    elif key == "recorded-path":
        ext.recorded_path = items[0]
    elif key == "mcp-endpoint":
        ext.mcp_endpoint = items[0]
    elif key == "target-url":
        ext.target_url = items[0]


# ---------------------------------------------------------------------------
# Charter loading
# ---------------------------------------------------------------------------


CHARTER_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
SCALAR_FIELD_RE = re.compile(r"^([a-z][a-z0-9_-]*):\s*(.+?)\s*$", re.MULTILINE)
LIST_FIELD_BLOCK_RE = re.compile(
    r"^([a-z][a-z0-9_-]*):\s*\n((?:  - .+\n)+)", re.MULTILINE
)
LIST_ITEM_RE = re.compile(r"^  - (.+)$", re.MULTILINE)


def load_charter(workspace: Path, charter_id: str) -> Charter:
    """Read and parse a charter file from <workspace>/charters/<CH-ID>.md."""
    target = workspace / "charters" / f"{charter_id}.md"
    if not target.is_file():
        raise CharterMissingError(
            f"charter file not found: charters/{charter_id}.md. "
            f"Run /tc:create-charter to allocate one."
        )
    text = target.read_text(encoding="utf-8")
    match = CHARTER_FRONTMATTER_RE.match(text)
    if not match:
        raise CharterMissingError(
            f"charter file {target} missing YAML frontmatter; cannot parse."
        )
    fm = match.group(1)

    # Scalar fields.
    scalars: dict[str, str] = {}
    for sc_match in SCALAR_FIELD_RE.finditer(fm):
        scalars[sc_match.group(1)] = sc_match.group(2).strip()

    # List fields.
    lists: dict[str, list[str]] = {}
    for lst_match in LIST_FIELD_BLOCK_RE.finditer(fm):
        key = lst_match.group(1)
        block = lst_match.group(2)
        items = [item.group(1).strip() for item in LIST_ITEM_RE.finditer(block)]
        lists[key] = items

    target_value = scalars.get("target", "")
    mission = scalars.get("mission", "")
    acceptance_criteria = lists.get("acceptance-criteria", [])
    return Charter(
        id=charter_id,
        target=target_value,
        mission=mission,
        acceptance_criteria=acceptance_criteria,
    )


# ---------------------------------------------------------------------------
# Recorded session loading
# ---------------------------------------------------------------------------


def resolve_recorded_path(workspace: Path, ext: Extensions, charter_id: str) -> Path:
    """Resolve the recorded session JSON path for the given charter ID."""
    base = workspace / ext.recorded_path
    return base / f"{charter_id}.json"


def load_recorded_session(
    workspace: Path,
    ext: Extensions,
    charter_id: str,
) -> tuple[Path, list[dict]]:
    target = resolve_recorded_path(workspace, ext, charter_id)
    if not target.is_file():
        raise RecordedSessionMissingError(
            f"recorded session file not found: {target.relative_to(workspace)}. "
            f"Place a recording at the configured path or set "
            f"tc-explore.exploration.recorded-path in <workspace>/config.yaml."
        )
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecordedSessionMissingError(
            f"failed to parse recorded session at {target}: {exc}"
        ) from exc
    if not isinstance(data, list):
        raise RecordedSessionMissingError(
            f"recorded session at {target} must be a JSON list; got {type(data).__name__}"
        )
    return target, data


# ---------------------------------------------------------------------------
# Per-event extraction
# ---------------------------------------------------------------------------


def extract_observations(entries: list[dict]) -> list[Observation]:
    obs: list[Observation] = []
    for idx, entry in enumerate(entries):
        event_type = entry.get("event_type", "")
        if event_type not in EVENT_TYPES:
            continue
        if event_type == "anomaly":
            # Anomalies surface in their own list, not as observations.
            continue
        action = entry.get("action") or entry.get("level") or ""
        # network_request entries derive their "action" from method + path.
        if event_type == "network_request":
            method = entry.get("method", "")
            path = entry.get("path", "")
            status = entry.get("status", "")
            action = f"{method} {path} -> {status}".strip()
        elif event_type == "fill":
            selector = entry.get("selector", "")
            value = entry.get("value_redacted", "")
            action = f"fill {selector} = {value}".strip()
        elif event_type == "click":
            selector = entry.get("selector", "")
            action_value = entry.get("action", "")
            action = (action_value or f"click {selector}").strip()
        elif event_type == "console_message":
            level = entry.get("level", "")
            message = entry.get("message", "")
            action = f"console.{level}: {message}".strip()
        result = entry.get("result", "")
        if not result and event_type == "screenshot":
            result = entry.get("caption", "")
        if not result and event_type == "network_request":
            result = f"{entry.get('status', '')}"
        obs.append(
            Observation(
                timestamp=entry.get("timestamp", ""),
                event_type=event_type,
                page_url=entry.get("page_url", ""),
                action=action,
                result=str(result),
                screenshot_id=entry.get("screenshot_id"),
                source_index=idx,
            )
        )
    return obs


def extract_evidence(entries: list[dict]) -> list[Evidence]:
    evid: list[Evidence] = []
    for idx, entry in enumerate(entries):
        if entry.get("event_type") != "screenshot":
            continue
        sid = entry.get("screenshot_id")
        if not sid:
            continue
        evid.append(
            Evidence(
                screenshot_id=sid,
                page_url=entry.get("page_url", ""),
                caption=entry.get("caption", ""),
                source_index=idx,
            )
        )
    return evid


def extract_anomalies(entries: list[dict]) -> list[Anomaly]:
    out: list[Anomaly] = []
    for idx, entry in enumerate(entries):
        if entry.get("event_type") != "anomaly":
            continue
        payload = entry.get("anomaly")
        if not isinstance(payload, dict):
            continue
        category = payload.get("category", "")
        if category not in ANOMALY_CATEGORIES:
            continue
        out.append(
            Anomaly(
                category=category,
                severity=payload.get("severity", "low"),
                page_url=payload.get("page_url", entry.get("page_url", "")),
                reproduction=payload.get("reproduction", ""),
                screenshot_id=payload.get("screenshot_id"),
                timestamp=entry.get("timestamp", ""),
                source_index=idx,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Coverage assessment
# ---------------------------------------------------------------------------


def _build_observed_corpus(
    observations: list[Observation],
    anomalies: list[Anomaly],
    evidence: list[Evidence],
) -> tuple[set[str], str]:
    urls: set[str] = set()
    parts: list[str] = []
    for obs in observations:
        if obs.page_url:
            urls.add(obs.page_url.lower())
            parts.append(obs.page_url.lower())
        if obs.action:
            parts.append(obs.action.lower())
        if obs.result:
            parts.append(obs.result.lower())
    for anom in anomalies:
        parts.append(anom.category)
        parts.append(anom.reproduction.lower())
        if anom.page_url:
            urls.add(anom.page_url.lower())
            parts.append(anom.page_url.lower())
    for ev in evidence:
        parts.append(ev.caption.lower())
        if ev.page_url:
            urls.add(ev.page_url.lower())
    return urls, " ".join(parts)


def assess_coverage(
    criterion: str,
    observed_urls: set[str],
    observed_text: str,
) -> CoverageVerdict:
    text_lower = criterion.lower()
    paths_in_ac = sorted(set(URL_PATH_RE.findall(text_lower)))
    matched_paths = [p for p in paths_in_ac if any(p in u for u in observed_urls)]

    triggers_in_ac = [w for w in TRIGGER_WORDS_NEEDING_OBSERVATION if w in text_lower]
    triggers_observed = [w for w in triggers_in_ac if w in observed_text]
    has_trigger_gap = bool(triggers_in_ac) and not triggers_observed

    cleaned = URL_PATH_RE.sub("", text_lower)
    words = set(WORD_RE.findall(cleaned)) - STOPWORDS
    matched_words = sorted([w for w in words if w in observed_text])

    if has_trigger_gap:
        # Specific scenario triggers absent -> at best partial.
        status = "partial" if (matched_paths or matched_words) else "unobserved"
    else:
        denominator = len(paths_in_ac) + len(words)
        numerator = len(matched_paths) + len(matched_words)
        if denominator == 0:
            status = "unobserved"
        else:
            ratio = numerator / denominator
            if ratio >= 0.5:
                status = "observed"
            elif ratio > 0:
                status = "partial"
            else:
                status = "unobserved"

    return CoverageVerdict(
        criterion=criterion,
        status=status,
        matched_paths=tuple(matched_paths),
        matched_keywords=tuple(matched_words),
    )


# ---------------------------------------------------------------------------
# Gap signal detection + review sub-mode
# ---------------------------------------------------------------------------


def _parse_iso_timestamp(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        # Handle trailing 'Z' as UTC.
        cleaned = ts.replace("Z", "+00:00") if ts.endswith("Z") else ts
        return datetime.fromisoformat(cleaned)
    except ValueError:
        return None


def detect_missing_evidence(
    anomalies: list[Anomaly],
    entries: list[dict],
    source_file: str,
) -> list[GapSignal]:
    """Anomaly without an adjacent screenshot event within ±3 seconds OR
    without a non-null ``screenshot_id`` field in the anomaly payload."""
    screenshot_ts: list[datetime] = []
    for entry in entries:
        if entry.get("event_type") != "screenshot":
            continue
        parsed = _parse_iso_timestamp(entry.get("timestamp", ""))
        if parsed is not None:
            screenshot_ts.append(parsed)

    gaps: list[GapSignal] = []
    for anom in anomalies:
        if anom.screenshot_id:
            continue  # has an explicit evidence link
        anom_ts = _parse_iso_timestamp(anom.timestamp)
        if anom_ts is None:
            continue
        adjacent = any(
            abs((scr - anom_ts).total_seconds()) <= SCREENSHOT_ADJACENCY_SECONDS
            for scr in screenshot_ts
        )
        if adjacent:
            continue
        gaps.append(
            GapSignal(
                kind="exploration-review",
                description=(
                    f"missing-evidence: anomaly at {anom.timestamp} carries no "
                    f"screenshot_id and no screenshot event was captured within "
                    f"+/- 3 seconds of the anomaly timestamp"
                ),
                source_file=source_file,
                line=anom.source_index + 1,
            )
        )
    return gaps


def detect_coverage_shortfall(coverage: list[CoverageVerdict]) -> list[GapSignal]:
    """Acceptance criteria marked ``unobserved`` after the full session."""
    gaps: list[GapSignal] = []
    for verdict in coverage:
        if verdict.status == "unobserved":
            gaps.append(
                GapSignal(
                    kind="exploration-review",
                    description=(
                        f"charter-coverage-shortfall: acceptance criterion "
                        f"'{verdict.criterion}' is unobserved by this session"
                    ),
                    source_file=None,
                    line=None,
                )
            )
    return gaps


def review_session(
    workspace: Path,
    findings: ExploreFindings,
    entries: list[dict],
) -> list[GapSignal]:
    gaps: list[GapSignal] = []
    gaps.extend(detect_missing_evidence(findings.anomalies, entries, findings.source_file))
    gaps.extend(detect_coverage_shortfall(findings.coverage))
    return gaps


# ---------------------------------------------------------------------------
# Session ID allocation
# ---------------------------------------------------------------------------


SESSION_FILENAME_RE = re.compile(r"^SESS-(\d{8})-(\d+)\.md$")


def allocate_session_id(workspace: Path, started_at: str) -> str:
    """Allocate ``SESS-YYYYMMDD-NNN``.

    The date prefix is the day of the recorded session's first event;
    the NNN suffix is deterministically derived from the first event's
    time-of-day so the same recording always produces the same SESS-ID
    across re-runs. NNN is ``(hour*60 + minute) % 1000`` — fits in three
    digits, stable per (date, hour, minute), good enough for v1 where
    cross-machine reproducibility matters more than handling multiple
    recordings within the same minute.

    Live mode (future) can swap this for a wall-clock-based allocator
    that scans existing SESS-IDs and increments; recorded mode needs
    stability, which is the test contract."""
    parsed = _parse_iso_timestamp(started_at)
    if parsed is None:
        # Fall back to UTC today; shouldn't happen for well-formed input.
        from datetime import UTC
        from datetime import datetime as _dt
        parsed = _dt.now(UTC)
    date_str = parsed.strftime("%Y%m%d")
    nnn = (parsed.hour * 60 + parsed.minute) % 1000
    return f"SESS-{date_str}-{nnn:03d}"


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def render_exploration_note(findings: ExploreFindings) -> str:
    lines: list[str] = []
    lines.append(f"# {findings.session_id} - exploration note for {findings.charter.id}")
    lines.append("")
    lines.append(
        "> Auto-generated by `/tc:explore`. Pure generated report - re-running "
        "against the same recorded session produces byte-identical bytes. "
        "Real edits belong in the session summary written by `/tc:session-summary`."
    )
    lines.append("")

    # Session header
    lines.append("## Session")
    lines.append("")
    lines.append(f"- Charter: `{findings.charter.id}` - {findings.charter.target}")
    lines.append(f"- Started at: {findings.session_started_at}")
    lines.append(f"- Source: `{findings.source_file}`")
    lines.append(f"- Observations: {len(findings.observations)}")
    lines.append(f"- Anomalies: {len(findings.anomalies)}")
    lines.append(f"- Evidence (screenshots): {len(findings.evidence)}")
    lines.append("")

    # Observations
    lines.append("## Observations")
    lines.append("")
    lines.append("| # | Timestamp | event_type | Page | Action | Result |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for obs in findings.observations:
        action = obs.action.replace("|", "\\|").replace("\n", " ")
        result = obs.result.replace("|", "\\|").replace("\n", " ")
        page = obs.page_url.replace("|", "\\|")
        lines.append(
            f"| {obs.source_index} | {obs.timestamp} | {obs.event_type} | "
            f"{page} | {action} | {result} |"
        )
    lines.append("")
    lines.append("Provenance: each row cites `<source>:<source_index + 1>` against "
                 f"`{findings.source_file}`.")
    lines.append("")

    # Anomalies summary
    lines.append("## Anomalies")
    lines.append("")
    if findings.anomalies:
        # Group by category for the summary header.
        by_cat: dict[str, int] = {}
        for anom in findings.anomalies:
            by_cat[anom.category] = by_cat.get(anom.category, 0) + 1
        lines.append("Count by category:")
        lines.append("")
        for cat in ANOMALY_CATEGORIES:
            if cat in by_cat:
                lines.append(f"- **{cat}**: {by_cat[cat]}")
        lines.append("")
        lines.append("| Category | Severity | Page | Reproduction | Evidence |")
        lines.append("| --- | --- | --- | --- | --- |")
        for anom in findings.anomalies:
            repro = anom.reproduction.replace("|", "\\|").replace("\n", " ")
            evid = anom.screenshot_id or "_(none)_"
            page = anom.page_url.replace("|", "\\|")
            lines.append(
                f"| {anom.category} | {anom.severity} | {page} | {repro} | {evid} |"
            )
    else:
        lines.append("_No anomalies detected in this session._")
    lines.append("")

    # Evidence index
    lines.append("## Evidence")
    lines.append("")
    if findings.evidence:
        lines.append("| Screenshot | Page | Caption | Reference |")
        lines.append("| --- | --- | --- | --- |")
        for ev in findings.evidence:
            cap = ev.caption.replace("|", "\\|").replace("\n", " ")
            page = ev.page_url.replace("|", "\\|")
            ref = f"evidence/screenshots/{ev.screenshot_id}.png"
            lines.append(f"| {ev.screenshot_id} | {page} | {cap} | `{ref}` |")
    else:
        lines.append("_No screenshots captured in this session._")
    lines.append("")

    # Charter Coverage matrix
    lines.append("## Charter Coverage")
    lines.append("")
    if findings.coverage:
        lines.append("| # | Acceptance Criterion | Verdict |")
        lines.append("| --- | --- | --- |")
        for idx, verdict in enumerate(findings.coverage, start=1):
            criterion = verdict.criterion.replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {idx} | {criterion} | **{verdict.status}** |")
    else:
        lines.append("_The charter declared no acceptance criteria._")
    lines.append("")

    # Gap signals (informational; routing happens in append_open_questions)
    if findings.gaps:
        lines.append("## Review findings (routed to `requirements/open-questions.md`)")
        lines.append("")
        for gap in findings.gaps:
            citation = ""
            if gap.source_file and gap.line:
                citation = f" (`{gap.source_file}:{gap.line}`)"
            lines.append(f"- **[{gap.kind}]** {gap.description}{citation}")
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------
# Open questions append (dedup; mirrors Phase 3 pattern)
# ---------------------------------------------------------------------------


OPEN_QUESTIONS_HEADER = "# Open questions"


def append_open_questions(workspace: Path, gaps: list[GapSignal]) -> None:
    target = workspace / "requirements" / "open-questions.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_text(target)
    if not existing.strip():
        existing = (
            f"{OPEN_QUESTIONS_HEADER}\n\n"
            "Append-only log of questions raised by tc-explore and other commands. "
            "Deduplicated by source-id + question text.\n"
        )

    existing_set: set[tuple[str, str]] = set()
    for line in existing.split("\n"):
        m = re.match(r"^- \[([^\]]+)\]\s+(.+)$", line)
        if m:
            existing_set.add((m.group(1).strip(), m.group(2).strip()))

    new_lines: list[str] = []
    for gap in gaps:
        source_id = "tc-explore/explore-review"
        question = f"[{gap.kind}] {gap.description.rstrip('.')}."
        key = (source_id, question)
        if key in existing_set:
            continue
        existing_set.add(key)
        new_lines.append(f"- [{source_id}] {question}")

    if not new_lines:
        if not existing.endswith("\n"):
            existing += "\n"
        target.write_text(existing, encoding="utf-8")
        return

    body = existing.rstrip("\n") + "\n\n" + "\n".join(new_lines) + "\n"
    target.write_text(body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run(
    project_root: Path,
    *,
    charter_id: str,
    no_review: bool,
) -> ExploreFindings:
    workspace = workspace_dir(project_root)
    ext = load_extensions(workspace)

    # Live-mode refusal mirrors Phase 3 Step 3.5 verbatim.
    if ext.mode == "live":
        if os.environ.get(PYTEST_ENV_VAR):
            raise LiveModeRefusedError(
                "live mode refused under pytest (PYTEST_CURRENT_TEST is set); "
                "use mode: recorded for tests"
            )
        raise LiveModeRefusedError(
            "live mode is not implemented in v1; use mode: recorded"
        )

    charter = load_charter(workspace, charter_id)
    source_path, entries = load_recorded_session(workspace, ext, charter_id)
    if not entries:
        raise RecordedSessionMissingError(
            f"recorded session at {source_path} is empty; nothing to explore"
        )

    observations = extract_observations(entries)
    evidence = extract_evidence(entries)
    anomalies = extract_anomalies(entries)

    started_at = entries[0].get("timestamp", "")
    session_id = allocate_session_id(workspace, started_at)
    source_file_rel = str(source_path.relative_to(workspace))

    observed_urls, observed_text = _build_observed_corpus(observations, anomalies, evidence)
    coverage = [
        assess_coverage(ac, observed_urls, observed_text)
        for ac in charter.acceptance_criteria
    ]

    findings = ExploreFindings(
        charter=charter,
        session_id=session_id,
        session_started_at=started_at,
        source_file=source_file_rel,
        observations=observations,
        evidence=evidence,
        anomalies=anomalies,
        coverage=coverage,
        gaps=[],
    )

    if not no_review:
        findings.gaps = review_session(workspace, findings, entries)

    # Write the exploration note.
    notes_dir = workspace / "exploration-notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    note_path = notes_dir / f"{session_id}.md"
    note_path.write_text(render_exploration_note(findings), encoding="utf-8")

    # Append review gap signals to open-questions (unless --no-review).
    if not no_review:
        append_open_questions(workspace, findings.gaps)

    return findings


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Drive a recorded (or live) Playwright MCP exploration session "
            "against a charter and produce a structured exploration note."
        ),
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root (default: current directory).",
    )
    parser.add_argument(
        "--charter",
        required=True,
        help="Charter ID to explore (e.g. CH-001).",
    )
    parser.add_argument(
        "--no-review",
        action="store_true",
        help=(
            "Suppress the internal exploration-review sub-mode. No "
            "[exploration-review] gap signals will be appended to "
            "requirements/open-questions.md."
        ),
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        findings = run(
            project_root,
            charter_id=args.charter,
            no_review=args.no_review,
        )
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except CharterMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RecordedSessionMissingError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except LiveModeRefusedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"exploration note written: {findings.session_id} "
        f"({len(findings.observations)} observations, "
        f"{len(findings.anomalies)} anomalies, "
        f"{len(findings.evidence)} screenshots, "
        f"{len(findings.gaps)} review findings)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
