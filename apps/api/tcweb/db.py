"""SQLite schema and connection for the web-console index (Phase 10).

The index is a rebuildable derivative of the committed `.test-commander/`
workspace. Every table is dropped and recreated on each rebuild, so the index
never holds state the workspace lacks.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE requirements (
    req_id TEXT PRIMARY KEY,
    source TEXT,
    body   TEXT
);
CREATE TABLE runs (
    run_id    TEXT PRIMARY KEY,
    mode      TEXT,
    generated TEXT,
    passed    INTEGER,
    failed    INTEGER,
    flaky     INTEGER
);
CREATE TABLE run_results (
    run_id      TEXT,
    requirement TEXT,
    candidate   TEXT,
    scenario    TEXT,
    spec        TEXT,
    status      TEXT,
    retries     INTEGER
);
CREATE TABLE evidence (
    artifact  TEXT,
    run_id    TEXT,
    candidate TEXT,
    kind      TEXT
);
CREATE TABLE journal (
    day       TEXT,
    timestamp TEXT,
    title     TEXT
);
CREATE TABLE traceability (
    requirement    TEXT,
    test_idea      TEXT,
    scenario       TEXT,
    automated_test TEXT,
    result         TEXT,
    quality_report TEXT
);
CREATE TABLE quality_facts (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""

TABLES = (
    "requirements",
    "runs",
    "run_results",
    "evidence",
    "journal",
    "traceability",
    "quality_facts",
)


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Drop and recreate every table (a rebuild starts from a clean slate)."""
    for table in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.executescript(SCHEMA)
    conn.commit()
