"""Artifact indexer for the web console (Phase 10 Step 10.2).

Walks a `.test-commander/` workspace into the SQLite index. The workspace is
authoritative; `rebuild()` drops and repopulates every table, so the index is
always reconstructible and holds no state the workspace lacks. Indexing never
writes to a workspace artifact — only to the derived index DB.

Parsers mirror the real producer formats (review_requirements,
traceability_render, run_tests, build_report, journal).
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from tcweb import config, db

ROW_RE = re.compile(r"^\|(.+)\|\s*$")
ID_ROW_RE = {
    "REQ": re.compile(r"REQ-\d"),
    "EVIDENCE": re.compile(r"evidence/"),
}
JOURNAL_ENTRY_RE = re.compile(r"^##\s+([0-9:]{8})\s+[—-]\s+(.*)$")
FACT_PATTERNS = {
    "requirements": re.compile(r"Requirements inventoried:\s*(\d+)"),
    "open_questions": re.compile(r"(\d+) open question"),
    "risks": re.compile(r"(\d+) risk\(s\)"),
    "evidence": re.compile(r"(\d+) evidence artifact"),
}
PFF_RE = re.compile(r"passed:\s*(\d+),\s*failed:\s*(\d+),\s*flaky:\s*(\d+)")
AUTOMATION_RE = re.compile(r"(\d+) of (\d+) scenario\(s\) automated")

connect = db.connect


# ---------------------------------------------------------------------------
# Cell parsing
# ---------------------------------------------------------------------------


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _data_rows(text: str, kind: str) -> list[list[str]]:
    matcher = ID_ROW_RE[kind]
    out: list[list[str]] = []
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = _cells(line)
        if cells and matcher.match(cells[0]):
            out.append(cells)
    return out


def _strip_backticks(value: str) -> str:
    return value.strip().strip("`")


# ---------------------------------------------------------------------------
# Per-artifact indexers
# ---------------------------------------------------------------------------


def _index_requirements(ws: Path, conn: sqlite3.Connection) -> int:
    path = ws / "requirements" / "requirements-inventory.md"
    if not path.is_file():
        return 0
    n = 0
    for cells in _data_rows(path.read_text(encoding="utf-8"), "REQ"):
        if len(cells) < 3:
            continue
        conn.execute(
            "INSERT OR REPLACE INTO requirements(req_id, source, body) VALUES (?, ?, ?)",
            (cells[0], _strip_backticks(cells[1]), cells[2]),
        )
        n += 1
    return n


def _index_runs(ws: Path, conn: sqlite3.Connection) -> tuple[int, int]:
    runs_dir = ws / "runs"
    runs = results = 0
    for results_json in sorted(runs_dir.glob("RUN-*/results.json")) if runs_dir.is_dir() else []:
        data = json.loads(results_json.read_text(encoding="utf-8"))
        rows = data.get("results", [])
        counts = {"passed": 0, "failed": 0, "flaky": 0}
        for r in rows:
            counts[r.get("status", "")] = counts.get(r.get("status", ""), 0) + 1
        conn.execute(
            "INSERT OR REPLACE INTO runs(run_id, mode, generated, passed, failed, flaky) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (data.get("run_id"), data.get("mode"), data.get("generated"),
             counts["passed"], counts["failed"], counts["flaky"]),
        )
        runs += 1
        for r in rows:
            conn.execute(
                "INSERT INTO run_results(run_id, requirement, candidate, scenario, spec, "
                "status, retries) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (data.get("run_id"), r.get("requirement"), r.get("candidate"),
                 r.get("scenario"), r.get("spec"), r.get("status"), r.get("retries", 0)),
            )
            results += 1
    return runs, results


def _index_evidence(ws: Path, conn: sqlite3.Connection) -> int:
    path = ws / "evidence" / "evidence-index.md"
    if not path.is_file():
        return 0
    n = 0
    for cells in _data_rows(path.read_text(encoding="utf-8"), "EVIDENCE"):
        if len(cells) < 4:
            continue
        conn.execute(
            "INSERT INTO evidence(artifact, run_id, candidate, kind) VALUES (?, ?, ?, ?)",
            (cells[0], cells[1], cells[2], cells[3]),
        )
        n += 1
    return n


def _index_journal(ws: Path, conn: sqlite3.Connection) -> int:
    journal_dir = ws / "journal"
    n = 0
    for day_file in sorted(journal_dir.glob("*.md")) if journal_dir.is_dir() else []:
        day = day_file.stem
        for line in day_file.read_text(encoding="utf-8").splitlines():
            m = JOURNAL_ENTRY_RE.match(line)
            if m:
                conn.execute(
                    "INSERT INTO journal(day, timestamp, title) VALUES (?, ?, ?)",
                    (day, m.group(1), m.group(2).strip()),
                )
                n += 1
    return n


def _index_traceability(ws: Path, conn: sqlite3.Connection) -> int:
    path = ws / "traceability" / "test-map.md"
    if not path.is_file():
        return 0
    n = 0
    for cells in _data_rows(path.read_text(encoding="utf-8"), "REQ"):
        if len(cells) < 6:
            continue
        conn.execute(
            "INSERT INTO traceability(requirement, test_idea, scenario, automated_test, "
            "result, quality_report) VALUES (?, ?, ?, ?, ?, ?)",
            (cells[0], cells[1], cells[2], _strip_backticks(cells[3]), cells[4], cells[5]),
        )
        n += 1
    return n


def _index_quality_facts(ws: Path, conn: sqlite3.Connection) -> int:
    path = ws / "quality-report" / "current-quality-report.md"
    if not path.is_file():
        return 0
    text = path.read_text(encoding="utf-8")
    facts: dict[str, str] = {}
    for key, pattern in FACT_PATTERNS.items():
        m = pattern.search(text)
        if m:
            facts[key] = m.group(1)
    pff = PFF_RE.search(text)
    if pff:
        facts["passed"], facts["failed"], facts["flaky"] = pff.group(1), pff.group(2), pff.group(3)
    auto = AUTOMATION_RE.search(text)
    if auto:
        facts["automated"], facts["automatable"] = auto.group(1), auto.group(2)
    for key, value in facts.items():
        conn.execute(
            "INSERT OR REPLACE INTO quality_facts(key, value) VALUES (?, ?)", (key, value)
        )
    return len(facts)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def index_workspace(ws: Path, conn: sqlite3.Connection) -> dict[str, int]:
    """Populate a fresh schema from the workspace. Returns per-table counts."""
    db.init_schema(conn)
    runs, run_results = _index_runs(ws, conn)
    counts = {
        "requirements": _index_requirements(ws, conn),
        "runs": runs,
        "run_results": run_results,
        "evidence": _index_evidence(ws, conn),
        "journal": _index_journal(ws, conn),
        "traceability": _index_traceability(ws, conn),
        "quality_facts": _index_quality_facts(ws, conn),
    }
    conn.commit()
    return counts


class UninitializedWorkspaceError(Exception):
    pass


def rebuild(project_root: Path) -> dict[str, int]:
    """Rebuild the index for a project from scratch. Returns per-table counts."""
    ws = config.workspace_dir(Path(project_root))
    if not ws.is_dir():
        raise UninitializedWorkspaceError(
            f"not a Test Commander workspace: {project_root} (no .test-commander/)"
        )
    conn = connect(config.index_db_path(Path(project_root)))
    try:
        return index_workspace(ws, conn)
    finally:
        conn.close()
