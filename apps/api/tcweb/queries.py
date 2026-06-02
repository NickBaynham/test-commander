"""Read queries over the SQLite index (Phase 10 Step 10.3).

Every function is read-only: it reads the derived index and returns plain dicts
for the API to serialize. Each page payload names the workspace artifact(s) it
was rendered from (the "cite your source" invariant).
"""

from __future__ import annotations

import sqlite3


def _dicts(conn: sqlite3.Connection, sql: str) -> list[dict]:
    return [dict(row) for row in conn.execute(sql).fetchall()]


def requirements(conn: sqlite3.Connection) -> list[dict]:
    return _dicts(conn, "SELECT req_id, source, body FROM requirements ORDER BY req_id")


def runs(conn: sqlite3.Connection) -> list[dict]:
    return _dicts(
        conn,
        "SELECT run_id, mode, generated, passed, failed, flaky FROM runs ORDER BY run_id DESC",
    )


def run_results(conn: sqlite3.Connection) -> list[dict]:
    return _dicts(
        conn,
        "SELECT run_id, requirement, candidate, scenario, spec, status, retries "
        "FROM run_results ORDER BY run_id DESC, candidate",
    )


def evidence(conn: sqlite3.Connection) -> list[dict]:
    return _dicts(conn, "SELECT artifact, run_id, candidate, kind FROM evidence ORDER BY artifact")


def journal(conn: sqlite3.Connection) -> list[dict]:
    return _dicts(
        conn, "SELECT day, timestamp, title FROM journal ORDER BY day DESC, timestamp DESC"
    )


def traceability(conn: sqlite3.Connection) -> list[dict]:
    return _dicts(
        conn,
        "SELECT requirement, test_idea, scenario, automated_test, result, quality_report "
        "FROM traceability ORDER BY requirement, test_idea",
    )


def quality_facts(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute("SELECT key, value FROM quality_facts").fetchall()
    return {row["key"]: row["value"] for row in rows}


def quality_report(conn: sqlite3.Connection) -> dict:
    return {
        "facts": quality_facts(conn),
        "source": "quality-report/current-quality-report.md",
    }


def dashboard(conn: sqlite3.Connection) -> dict:
    facts = quality_facts(conn)
    run_rows = runs(conn)
    latest = run_rows[0] if run_rows else None
    return {
        "requirements": int(facts.get("requirements", "0")),
        "open_questions": int(facts.get("open_questions", "0")),
        "risks": int(facts.get("risks", "0")),
        "latest_run": latest,
        "source": [
            "requirements/requirements-inventory.md",
            "quality-report/current-quality-report.md",
            "runs/<RUN-ID>/results.json",
        ],
    }
