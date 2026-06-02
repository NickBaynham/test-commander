#!/usr/bin/env python3
"""/tc:visualize and the shared diagram engine - Phase 9 Step 9.2.

The umbrella command (`/tc:visualize`) regenerates the full visual set, and this
module owns the **shared render engine** every `/tc:diagram-*` command reuses:

- ``render_diagram_doc`` - wrap Mermaid body lines in a titled doc with a
  ``> Sources:`` citation footer.
- ``render_flowchart`` - emit a deterministic Mermaid ``flowchart`` from nodes
  and edges (both sorted, so output is byte-stable).
- ``render_diagram`` - the graph-kind convenience that ties the two together and
  writes ``<workspace>/visuals/mermaid/<name>.md``.
- ``read_source`` - read a required source artifact, refusing a missing or
  stub-only file with a message that points at the producing command.

Two disciplines govern every generator (D19 keeps the shipped vocabulary
universal):

- **Generate-and-cite, never invent.** A diagram is rendered only from committed
  workspace artifacts, and every file carries a ``> Sources:`` footer.
- **Mermaid text is the source of truth.** Generators emit deterministic
  Markdown only; rendering to SVG/PNG is ``/tc:render-visuals``' job.

Per D18 the helper ships inside the plugin.

Exit codes:
    0 - visual(s) generated.
    2 - precondition failure (uninitialized workspace or a missing source).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"
STUB_MARKER = "_(empty until"

JOURNEY_RE = re.compile(r"^- \*\*(.+?)\*\*", re.MULTILINE)
ENTITY_BULLET_RE = re.compile(r"^- \*\*(.+?)\*\*", re.MULTILINE)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class VisualizeError(Exception):
    pass


class UninitializedWorkspaceError(VisualizeError):
    pass


class MissingSourceError(VisualizeError):
    pass


# ---------------------------------------------------------------------------
# Workspace IO
# ---------------------------------------------------------------------------


def workspace_dir(project_root: Path) -> Path:
    ws = Path(project_root) / WORKSPACE_DIRNAME
    if not ws.is_dir():
        raise UninitializedWorkspaceError(
            f"not a Test Commander workspace: {project_root} "
            f"(no {WORKSPACE_DIRNAME}/). Run /tc:init first."
        )
    return ws


def read_source(workspace: Path, rel: str, producer: str) -> str:
    """Read a required source artifact, refusing a missing or stub-only file."""
    path = workspace / rel
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    if not text.strip() or STUB_MARKER in text:
        raise MissingSourceError(
            f"source {rel} is missing or empty; run {producer} first to populate it"
        )
    return text


# ---------------------------------------------------------------------------
# Shared Mermaid engine
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Node:
    node_id: str
    label: str


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    label: str = ""


def mermaid_id(prefix: str, label: str) -> str:
    """A deterministic, Mermaid-safe identifier derived from a label."""
    slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return f"{prefix}_{slug}" if slug else prefix


def _esc(label: str) -> str:
    """Escape a Mermaid node/edge label so quotes cannot break the syntax."""
    return label.replace('"', "'").replace("\n", " ").strip()


def render_flowchart(nodes: list[Node], edges: list[Edge], direction: str = "TD") -> list[str]:
    """Emit a deterministic Mermaid flowchart body (nodes then edges, sorted)."""
    lines = [f"flowchart {direction}"]
    for n in sorted(set(nodes), key=lambda x: x.node_id):
        lines.append(f'    {n.node_id}["{_esc(n.label)}"]')
    for e in sorted(set(edges), key=lambda x: (x.src, x.dst, x.label)):
        if e.label:
            lines.append(f"    {e.src} -->|{_esc(e.label)}| {e.dst}")
        else:
            lines.append(f"    {e.src} --> {e.dst}")
    return lines


def render_diagram_doc(
    title: str, intro: str, mermaid_lines: list[str], sources: list[str]
) -> str:
    """Wrap Mermaid body lines in a titled Markdown doc with a Sources footer."""
    out = [f"# {title}", "", intro, "", "```mermaid"]
    out.extend(mermaid_lines)
    out.append("```")
    out.append("")
    out.append("> Sources: " + ", ".join(f"`{s}`" for s in sources))
    return "\n".join(out) + "\n"


def write_visual(workspace: Path, name: str, text: str) -> Path:
    """Write a Mermaid source doc to visuals/mermaid/<name>.md (overwrite)."""
    dest = workspace / "visuals" / "mermaid" / f"{name}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    return dest


def render_diagram(
    workspace: Path,
    name: str,
    *,
    title: str,
    intro: str,
    nodes: list[Node],
    edges: list[Edge],
    sources: list[str],
    direction: str = "TD",
) -> Path:
    """The graph-kind convenience: flowchart body + doc wrapper + write."""
    body = render_flowchart(nodes, edges, direction)
    doc = render_diagram_doc(title, intro, body, sources)
    return write_visual(workspace, name, doc)


def render_sequence(
    participants: list[str], messages: list[tuple[str, str, str]], note: str = ""
) -> list[str]:
    """Emit a Mermaid sequenceDiagram. Message order is preserved (it is meaningful)."""
    lines = ["sequenceDiagram"]
    for p in participants:
        lines.append(f"    participant {p}")
    if note:
        lines.append(f"    Note over {participants[-1]}: {_esc(note)}")
    for src, dst, msg in messages:
        lines.append(f"    {src}->>{dst}: {_esc(msg)}")
    return lines


def render_state(transitions: list[tuple[str, str]]) -> list[str]:
    """Emit a Mermaid stateDiagram-v2 from (src, dst) transitions, sorted."""
    lines = ["stateDiagram-v2"]
    for src, dst in sorted(set(transitions)):
        lines.append(f"    {src} --> {dst}")
    return lines


# ---------------------------------------------------------------------------
# Source parsers
# ---------------------------------------------------------------------------


def parse_journeys(user_journeys_text: str) -> list[str]:
    """Return user-journey titles in document order."""
    return JOURNEY_RE.findall(user_journeys_text)


def section_body(text: str, heading_prefix: str) -> str:
    """Return the body of the first ``### <heading_prefix>...`` section."""
    pattern = re.compile(
        rf"^### {re.escape(heading_prefix)}.*?$\n(.*?)(?=^#{{2,3}} |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(text)
    return m.group(1) if m else ""


def parse_entities(system_model_text: str) -> list[str]:
    """Return entity names from the system model's Entities section, sorted."""
    body = section_body(system_model_text, "Entities")
    return sorted(set(ENTITY_BULLET_RE.findall(body)))


TEST_MAP_ROW_RE = re.compile(r"^\| REQ-\d+ \|", re.MULTILINE)


def parse_test_map_results(test_map_text: str) -> list[str]:
    """Return the distinct Test-result values present in the test map, sorted."""
    results: set[str] = set()
    for line in test_map_text.splitlines():
        if not TEST_MAP_ROW_RE.match(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 5:
            results.add(cells[4].lower())
    return sorted(results)


# ---------------------------------------------------------------------------
# diagram-flow
# ---------------------------------------------------------------------------


def diagram_flow(project_root: Path) -> Path:
    """Render a user-journey flow diagram from user-journeys + system-model."""
    workspace = workspace_dir(project_root)
    journeys_text = read_source(
        workspace, "product-knowledge/user-journeys.md", "/tc:learn-from-docs"
    )
    model_text = read_source(
        workspace, "product-knowledge/system-model.md", "/tc:learn-from-docs"
    )
    journeys = parse_journeys(journeys_text)
    entities = parse_entities(model_text)

    nodes = [Node("user", "User")]
    edges: list[Edge] = []
    system_label = "System: " + ", ".join(entities) if entities else "System"
    nodes.append(Node("system", system_label))
    for title in journeys:
        jid = mermaid_id("j", title)
        nodes.append(Node(jid, title))
        edges.append(Edge("user", jid))
        edges.append(Edge(jid, "system"))

    intro = (
        "User-journey flow: each journey the product supports, drawn from the "
        "knowledge base. Generated by `/tc:diagram-flow`; never invents a journey "
        "or entity absent from its sources."
    )
    return render_diagram(
        workspace,
        "flow",
        title="User journey flow",
        intro=intro,
        nodes=nodes,
        edges=edges,
        sources=[
            "product-knowledge/user-journeys.md",
            "product-knowledge/system-model.md",
        ],
    )


# ---------------------------------------------------------------------------
# Structural diagrams (Step 9.3)
# ---------------------------------------------------------------------------


def diagram_sequence(project_root: Path) -> Path:
    """Render a sequence diagram of the user's journeys against the system."""
    workspace = workspace_dir(project_root)
    journeys_text = read_source(
        workspace, "product-knowledge/user-journeys.md", "/tc:learn-from-docs"
    )
    model_text = read_source(
        workspace, "product-knowledge/system-model.md", "/tc:learn-from-docs"
    )
    journeys = parse_journeys(journeys_text)
    entities = parse_entities(model_text)
    messages = [("User", "System", title) for title in journeys]
    note = ", ".join(entities)
    body = render_sequence(["User", "System"], messages, note=note)
    intro = (
        "Sequence of the journeys the user initiates against the system. "
        "Generated by `/tc:diagram-sequence` from the knowledge base; each "
        "message is a journey named in its source."
    )
    doc = render_diagram_doc(
        "User journey sequence",
        intro,
        body,
        ["product-knowledge/user-journeys.md", "product-knowledge/system-model.md"],
    )
    return write_visual(workspace, "sequence", doc)


def diagram_state(project_root: Path) -> Path:
    """Render the scenario result lifecycle from the test map."""
    workspace = workspace_dir(project_root)
    test_map_text = read_source(
        workspace, "traceability/test-map.md", "/tc:traceability-map"
    )
    results = parse_test_map_results(test_map_text)
    transitions: list[tuple[str, str]] = [("[*]", "Pending")]
    for result in results:
        if result == "pending":
            continue
        transitions.append(("Pending", result.capitalize()))
    body = render_state(transitions)
    intro = (
        "Scenario result lifecycle: the states a scenario's result moves "
        "through, drawn from the test map. Generated by `/tc:diagram-state`; "
        "only states present in the map are shown."
    )
    doc = render_diagram_doc(
        "Scenario result lifecycle", intro, body, ["traceability/test-map.md"]
    )
    return write_visual(workspace, "state", doc)


def diagram_architecture(project_root: Path) -> Path:
    """Render a system architecture diagram from the system-model entities."""
    workspace = workspace_dir(project_root)
    model_text = read_source(
        workspace, "product-knowledge/system-model.md", "/tc:learn-from-docs"
    )
    entities = parse_entities(model_text)
    nodes = [Node("system", "System")]
    edges: list[Edge] = []
    for name in entities:
        eid = mermaid_id("e", name)
        nodes.append(Node(eid, name))
        edges.append(Edge("system", eid, "comprises"))
    intro = (
        "System architecture: the entities the product comprises, drawn from "
        "the system model. Generated by `/tc:diagram-architecture`; never "
        "invents an entity absent from the model."
    )
    return render_diagram(
        workspace,
        "architecture",
        title="System architecture",
        intro=intro,
        nodes=nodes,
        edges=edges,
        sources=["product-knowledge/system-model.md"],
    )


# ---------------------------------------------------------------------------
# /tc:visualize umbrella
# ---------------------------------------------------------------------------

# (name, generator). Grows as 9.4-9.5 ship their generators.
GENERATORS: list[tuple[str, object]] = [
    ("flow", diagram_flow),
    ("sequence", diagram_sequence),
    ("state", diagram_state),
    ("architecture", diagram_architecture),
]


def visualize(project_root: Path) -> list[Path]:
    """Regenerate every diagram whose source is present; skip the rest."""
    workspace_dir(project_root)  # refuse uninitialized up front
    written: list[Path] = []
    for _name, gen in GENERATORS:
        try:
            written.append(gen(project_root))
        except MissingSourceError:
            continue
    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate the Test Commander visual set from workspace artifacts.",
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    args = parser.parse_args(argv if argv is not None else None)
    project_root = Path(args.project_root).resolve()
    try:
        written = visualize(project_root)
    except VisualizeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"generated: {len(written)} visual(s) under visuals/mermaid/")
    for p in written:
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
