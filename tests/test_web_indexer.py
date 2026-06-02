"""Step 10.2 - the FastAPI artifact indexer + /tc:web-index-artifacts.

Walks a .test-commander/ workspace into the SQLite index (requirements, runs,
run results, evidence, journal, traceability, quality facts). The workspace is
authoritative; the index is rebuildable from scratch. Drives the indexer against
the seeded-web fixture.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "apps" / "api"))
sys.path.insert(0, str(REPO / "plugins" / "test-commander" / "scripts"))
FIXTURE = REPO / "tests" / "fixtures" / "seeded-web"

import tcweb.config as config  # noqa: E402
import tcweb.indexer as indexer  # noqa: E402
import web_index_artifacts  # noqa: E402


def seed_project(tmp_path: Path) -> Path:
    project = tmp_path / "proj"
    shutil.copytree(FIXTURE, project / ".test-commander")
    return project


def rows(conn, sql: str) -> list:
    return list(conn.execute(sql).fetchall())


# ---------------------------------------------------------------------------
# Indexing populates the expected rows
# ---------------------------------------------------------------------------


def test_index_populates_every_table(tmp_path: Path):
    project = seed_project(tmp_path)
    counts = indexer.rebuild(project)
    conn = indexer.connect(config.index_db_path(project))

    assert counts["requirements"] == 3
    assert {r[0] for r in rows(conn, "SELECT req_id FROM requirements")} == {
        "REQ-001", "REQ-002", "REQ-003"
    }

    assert counts["runs"] == 1
    run = rows(conn, "SELECT run_id, passed, failed, flaky FROM runs")[0]
    assert run[0] == "RUN-20260601-093000"
    assert (run[1], run[2], run[3]) == (1, 1, 1)

    assert counts["run_results"] == 3
    statuses = {r[0] for r in rows(conn, "SELECT status FROM run_results")}
    assert statuses == {"passed", "failed", "flaky"}

    assert counts["evidence"] >= 1
    assert counts["journal"] >= 2  # two timestamped entries in the day file
    assert counts["traceability"] == 4
    facts = dict(rows(conn, "SELECT key, value FROM quality_facts"))
    assert facts.get("requirements") == "3"
    assert facts.get("passed") == "1"
    conn.close()


def test_index_is_rebuildable_and_deterministic(tmp_path: Path):
    project = seed_project(tmp_path)
    first = indexer.rebuild(project)
    second = indexer.rebuild(project)  # full rebuild, no leftover state
    assert first == second


def test_changed_artifact_reindexes(tmp_path: Path):
    project = seed_project(tmp_path)
    indexer.rebuild(project)
    # Append a requirement to the inventory and re-index.
    inv = project / ".test-commander" / "requirements" / "requirements-inventory.md"
    inv.write_text(
        inv.read_text(encoding="utf-8")
        + "| REQ-004 | `requirements.md` | The account shall reset its password. |\n",
        encoding="utf-8",
    )
    counts = indexer.rebuild(project)
    assert counts["requirements"] == 4


def test_index_does_not_mutate_the_workspace(tmp_path: Path):
    project = seed_project(tmp_path)
    ws = project / ".test-commander"
    before = {
        p.relative_to(ws): p.read_bytes()
        for p in sorted(ws.rglob("*"))
        if p.is_file() and ".web" not in p.relative_to(ws).parts
    }
    indexer.rebuild(project)
    after = {
        p.relative_to(ws): p.read_bytes()
        for p in sorted(ws.rglob("*"))
        if p.is_file() and ".web" not in p.relative_to(ws).parts
    }
    assert after == before, "indexing must not mutate workspace artifacts"


# ---------------------------------------------------------------------------
# /tc:web-index-artifacts helper
# ---------------------------------------------------------------------------


def test_web_index_artifacts_uninitialized_refused(tmp_path: Path):
    rc = web_index_artifacts.main([str(tmp_path / "nope")])
    assert rc == 2


def test_web_index_artifacts_builds_index(tmp_path: Path):
    project = seed_project(tmp_path)
    rc = web_index_artifacts.main([str(project)])
    assert rc == 0
    assert config.index_db_path(project).is_file()
