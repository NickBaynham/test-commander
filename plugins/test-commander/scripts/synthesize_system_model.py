#!/usr/bin/env python3
"""Shared synthesizer: rewrite ``<workspace>/product-knowledge/system-model.md``.

Invoked at the end of every Phase 3 ``/tc:learn-from-*`` command. Reads the
current state of the per-source model files (``documentation-model.md``,
``spec-derived-model.md``, ``code-derived-model.md``, ``api-model.md``,
``tests-coverage.md``) plus the cross-cutting artifacts (``entities.md``,
``user-journeys.md``, ``business-rules.md``, ``assumptions.md``) and rewrites
``system-model.md`` from a deterministic template.

Idempotency contract: same inputs => byte-identical output. Sources that have
not yet been ingested are omitted from the "Sources ingested" list; their
absence yields a partial synthesis that grows monotonically as the other
``/tc:learn-from-*`` commands run.

Exit codes:
    0 - system-model.md written
    2 - uninitialized workspace
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"
PRODUCT_KNOWLEDGE = "product-knowledge"

# Source order in every render. Stable across runs.
SOURCE_ORDER: tuple[str, ...] = ("documents", "specs", "code", "api", "tests")

# Per-source model files and the command that owns each.
PER_SOURCE_MODELS: dict[str, tuple[str, str]] = {
    "documents": ("documentation-model.md", "/tc:learn-from-docs"),
    "specs": ("spec-derived-model.md", "/tc:learn-from-specs"),
    "code": ("code-derived-model.md", "/tc:learn-from-code"),
    "api": ("api-model.md", "/tc:learn-from-api"),
    "tests": ("tests-coverage.md", "/tc:learn-from-tests"),
}

# Cross-cutting artifacts (each populated as sections by the learn-from-* helpers).
CROSS_CUTTING = (
    "entities.md",
    "user-journeys.md",
    "business-rules.md",
    "assumptions.md",
)

# Stub marker: every workspace-template product-knowledge stub carries this.
TEMPLATE_STUB_MARKER = "_(empty until Phase 3 ships.)_"

# Empty-path markers a helper writes when its source tree contained no items.
# A per-source model carrying any of these still counts as 'not ingested' from
# the synthesizer's perspective, so the partial synthesis is honest.
EMPTY_RUN_MARKERS = (
    "no narrative documents found",
    "no spec found",
    "no code source found",
    "no recorded api responses found",
    "no tests found",
)

SOURCE_SECTION_RE = re.compile(r"^## From ([a-z][a-z0-9-]*)\s*$", re.MULTILINE)
ENTITY_BULLET_RE = re.compile(r"^\s*-\s+\*\*([A-Z][A-Za-z0-9 _-]+?)\*\*", re.MULTILINE)
JOURNEY_BULLET_RE = re.compile(r"^\s*-\s+\*\*([^*]+?)\*\*", re.MULTILINE)


class SynthesizerError(Exception):
    pass


class UninitializedWorkspaceError(SynthesizerError):
    pass


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------


def workspace_dir(project_root: Path) -> Path:
    ws = project_root / WORKSPACE_DIRNAME
    if not ws.is_dir():
        raise UninitializedWorkspaceError(
            f"not a Test Commander workspace: {project_root} (no {WORKSPACE_DIRNAME}/)"
        )
    return ws


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def _is_generated(text: str) -> bool:
    """A per-source model file counts as 'generated' iff a helper has written
    real content. The template stub and any helper-written empty-run sentinel
    both count as not-generated, so the synthesizer renders an honest picture.
    """
    if not text.strip():
        return False
    if TEMPLATE_STUB_MARKER in text:
        return False
    lowered = text.lower()
    return not any(marker in lowered for marker in EMPTY_RUN_MARKERS)


# ---------------------------------------------------------------------------
# Parsing the current state of product-knowledge/
# ---------------------------------------------------------------------------


def detect_ingested_sources(workspace: Path) -> list[str]:
    """Return the list of sources whose per-source model has been generated."""
    pk = workspace / PRODUCT_KNOWLEDGE
    ingested: list[str] = []
    for source in SOURCE_ORDER:
        filename, _ = PER_SOURCE_MODELS[source]
        if _is_generated(_read_text(pk / filename)):
            ingested.append(source)
    return ingested


def parse_source_sections(text: str) -> dict[str, str]:
    """Parse ``## From <source>`` blocks out of a cross-cutting artifact."""
    sections: dict[str, str] = {}
    matches = list(SOURCE_SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        source = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[source] = text[start:end].strip()
    return sections


def aggregate_cross_cutting(workspace: Path) -> dict[str, dict[str, str]]:
    """For each cross-cutting file, return ``{source: section_body}``."""
    pk = workspace / PRODUCT_KNOWLEDGE
    aggregate: dict[str, dict[str, str]] = {}
    for filename in CROSS_CUTTING:
        text = _read_text(pk / filename)
        aggregate[filename] = parse_source_sections(text)
    return aggregate


# ---------------------------------------------------------------------------
# Summaries
# ---------------------------------------------------------------------------


def _count_bullets(body: str) -> int:
    """Count Markdown list items in a section body."""
    return sum(1 for line in body.splitlines() if re.match(r"^\s*[-*]\s+\S", line))


def summarize_dimension(
    aggregate: dict[str, dict[str, str]],
    filename: str,
) -> tuple[int, list[tuple[str, int]]]:
    """Return (total_count, [(source, count_from_source), ...]) for one cross-cutting file."""
    per_source = aggregate.get(filename, {})
    rows: list[tuple[str, int]] = []
    for source in SOURCE_ORDER:
        count = _count_bullets(per_source.get(source, ""))
        if count:
            rows.append((source, count))
    total = sum(count for _, count in rows)
    return total, rows


def extract_bolded_names(
    aggregate: dict[str, dict[str, str]],
    filename: str,
    pattern: re.Pattern[str],
) -> dict[str, set[str]]:
    """Return ``{name: {source, ...}}`` of bolded names per source for one cross-cutting file."""
    per_source = aggregate.get(filename, {})
    result: dict[str, set[str]] = {}
    for source in SOURCE_ORDER:
        body = per_source.get(source, "")
        for m in pattern.finditer(body):
            name = m.group(1).strip()
            result.setdefault(name, set()).add(source)
    return result


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def render_no_sources() -> str:
    return (
        "# System Model\n"
        "\n"
        "Auto-generated by the `tc-knowledge` synthesizer. Regenerated by every "
        "`/tc:learn-from-*` command from the current state of the per-source "
        "model files and cross-cutting artifacts.\n"
        "\n"
        "## Sources ingested\n"
        "\n"
        "_No source has been ingested yet._ Run any `/tc:learn-from-*` command to "
        "populate this section.\n"
    )


def render(workspace: Path) -> str:
    ingested = detect_ingested_sources(workspace)
    if not ingested:
        return render_no_sources()

    aggregate = aggregate_cross_cutting(workspace)

    lines: list[str] = []
    lines.append("# System Model")
    lines.append("")
    lines.append(
        "Auto-generated by the `tc-knowledge` synthesizer. Regenerated by every "
        "`/tc:learn-from-*` command from the current state of the per-source "
        "model files and cross-cutting artifacts."
    )
    lines.append("")

    # Sources ingested
    lines.append("## Sources ingested")
    lines.append("")
    for source in ingested:
        filename, command = PER_SOURCE_MODELS[source]
        lines.append(
            f"- **{source}** - via `{command}`. See "
            f"[{filename}]({filename})."
        )
    lines.append("")

    # Cross-source summary
    lines.append("## Cross-source summary")
    lines.append("")

    summary_specs = (
        ("Entities", "entities.md", ENTITY_BULLET_RE),
        ("User journeys", "user-journeys.md", JOURNEY_BULLET_RE),
        ("Business rules", "business-rules.md", None),
        ("Assumptions", "assumptions.md", None),
    )
    for title, filename, name_pattern in summary_specs:
        total, rows = summarize_dimension(aggregate, filename)
        lines.append(f"### {title} ({total})")
        lines.append("")
        if not rows:
            lines.append("_No findings from any ingested source yet._")
            lines.append("")
            continue
        if name_pattern is not None:
            names = extract_bolded_names(aggregate, filename, name_pattern)
            for name in sorted(names):
                source_list = ", ".join(sorted(names[name]))
                lines.append(f"- **{name}** (from {source_list})")
            lines.append("")
        for source, count in rows:
            lines.append(f"- From _{source}_: {count}")
        lines.append("")
        lines.append(f"See [{filename}]({filename}) for the full per-source list.")
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


def synthesize(project_root: Path) -> Path:
    """Render and write system-model.md. Returns the written path."""
    workspace = workspace_dir(project_root)
    target = workspace / PRODUCT_KNOWLEDGE / "system-model.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(workspace), encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate <workspace>/product-knowledge/system-model.md."
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root (default: current directory).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    project_root = Path(args.project_root).resolve()

    try:
        target = synthesize(project_root)
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"system-model.md regenerated at {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
