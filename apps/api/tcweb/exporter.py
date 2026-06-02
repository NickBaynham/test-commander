"""Static export of the console view (Phase 10 Step 10.6).

Exports the quality report, requirements, runs, evidence, and traceability as a
shareable static bundle — `data.json` (the structured data) and `index.html` (a
self-contained, dependency-free rendering). Read-only and deterministic: the
bundle is built from the index with sorted keys and no wall-clock timestamps, so
the same workspace yields byte-identical output. Writes only under
`.web/export/`, never a workspace artifact.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from tcweb import config, indexer, queries


def build_bundle(conn) -> dict:
    """Assemble the export payload from the index (deterministic)."""
    return {
        "quality_facts": queries.quality_facts(conn),
        "requirements": queries.requirements(conn),
        "runs": queries.runs(conn),
        "run_results": queries.run_results(conn),
        "evidence": queries.evidence(conn),
        "traceability": queries.traceability(conn),
        "sources": [
            "requirements/requirements-inventory.md",
            "quality-report/current-quality-report.md",
            "runs/<RUN-ID>/results.json",
            "evidence/evidence-index.md",
            "traceability/test-map.md",
        ],
    }


def _table(title: str, headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row) + "</tr>"
        for row in rows
    )
    return f"<h2>{html.escape(title)}</h2><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"  # noqa: E501


def render_html(bundle: dict) -> str:
    facts = bundle["quality_facts"]
    parts = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        "<title>Test Commander - quality export</title></head><body>",
        "<h1>Test Commander quality export</h1>",
        _table("Quality facts", ["fact", "value"],
               [[k, facts[k]] for k in sorted(facts)]),
        _table("Requirements", ["ID", "Source", "Body"],
               [[r["req_id"], r["source"], r["body"]] for r in bundle["requirements"]]),
        _table("Runs", ["Run", "Passed", "Failed", "Flaky"],
               [[r["run_id"], r["passed"], r["failed"], r["flaky"]] for r in bundle["runs"]]),
        _table("Traceability", ["Requirement", "Scenario", "Result"],
               [[r["requirement"], r["scenario"], r["result"]] for r in bundle["traceability"]]),
        _table("Evidence", ["Artifact", "Run", "Kind"],
               [[e["artifact"], e["run_id"], e["kind"]] for e in bundle["evidence"]]),
        "<footer>Sources: " + html.escape(", ".join(bundle["sources"])) + "</footer>",
        "</body></html>",
    ]
    return "\n".join(parts) + "\n"


def export(project_root: Path, out_dir: Path | None = None) -> list[Path]:
    """Write the export bundle. Returns the written paths."""
    ws = config.workspace_dir(Path(project_root))
    if not ws.is_dir():
        raise indexer.UninitializedWorkspaceError(
            f"not a Test Commander workspace: {project_root} (no .test-commander/)"
        )
    db_path = config.index_db_path(Path(project_root))
    if not db_path.is_file():
        indexer.rebuild(Path(project_root))
    conn = indexer.connect(db_path)
    try:
        bundle = build_bundle(conn)
    finally:
        conn.close()

    target = out_dir or (ws / ".web" / "export")
    target.mkdir(parents=True, exist_ok=True)
    data_path = target / "data.json"
    html_path = target / "index.html"
    data_path.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    html_path.write_text(render_html(bundle), encoding="utf-8")
    return [data_path, html_path]
