#!/usr/bin/env python3
"""/tc:learn-from-docs helper - Phase 3 Step 3.2.

Reads non-requirements ``*.md`` files under ``<workspace>/documents/uploaded/``
(a file is a requirements source iff it contains at least one ``REQ-\\d+``
token; this helper inverts that filter), applies the universal-core extraction
rules from the Step-3.2 partition table for five positive rubric dimensions
(entities, terms, user-journeys, business-rules, assumptions) plus two gap
signals (undefined-term, contradictory-rule), and writes:

- ``<workspace>/product-knowledge/documentation-model.md`` - overwritten
  byte-deterministically.
- The ``## From documents`` section in ``entities.md``, ``user-journeys.md``,
  ``business-rules.md``, ``assumptions.md`` - section-overwritten; sections
  from other ``## From <source>`` blocks are preserved.
- ``<workspace>/requirements/open-questions.md`` - appended with gap-signal
  questions, deduplicated by ``(source-id, question-text)``.
- ``<workspace>/product-knowledge/system-model.md`` - regenerated via the
  shared ``synthesize_system_model.py`` helper.

Per D18 the helper ships inside the plugin. Per D19 the keyword sets and
heading tokens are universal cores; projects extend them via
``tc-knowledge.documents:`` in ``<workspace>/config.yaml``.

Exit codes:
    0 - documentation-model written.
    2 - uninitialized workspace or other I/O failure.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

# Local-package import: the synthesizer lives next to this helper in the
# plugin's scripts/ directory and is on the test pythonpath.
import synthesize_system_model as synth_mod

WORKSPACE_DIRNAME = ".test-commander"
SOURCE_LABEL = "documents"

# Universal cores (D19).
ENTITY_HEADING_TOKENS = ("entit", "model", "noun", "glossary")
GLOSSARY_HEADING_TOKENS = ("glossary", "terminology")
JOURNEY_HEADING_TOKENS = ("journey", "flow", "walkthrough", "scenario")
RFC_2119_MODALS = ("must", "shall", "should", "may")
ASSUMPTION_MARKERS = ("assume", "expected", "presumed", "likely")
NEGATION_MARKERS = ("not", "never", "without")

REQ_TOKEN_RE = re.compile(r"\bREQ-\d+\b")
HEADING_RE = re.compile(r"^(#+)\s+(.+?)\s*$")
BOLDED_TERM_RE = re.compile(r"\*\*([A-Z][A-Za-z0-9_-]+)\*\*")
BULLET_BOLD_RE = re.compile(r"^\s*[-*]\s+\*\*([A-Z][A-Za-z0-9_-]+)\*\*")
NUMBERED_OR_BULLET_RE = re.compile(r"^\s*(?:\d+\.|[-*])\s+(.+?)\s*$")
TABLE_ROW_RE = re.compile(r"^\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|")


class DocsError(Exception):
    pass


class UninitializedWorkspaceError(DocsError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Entity:
    name: str
    source_file: str
    line: int


@dataclass(frozen=True)
class Term:
    term: str
    definition: str
    source_file: str
    line: int


@dataclass(frozen=True)
class Journey:
    title: str
    steps: tuple[str, ...]
    source_file: str
    line_start: int
    line_end: int


@dataclass(frozen=True)
class Rule:
    text: str
    modal: str
    subject: str
    source_file: str
    line: int


@dataclass(frozen=True)
class Assumption:
    text: str
    source_file: str
    line: int


@dataclass(frozen=True)
class GapSignal:
    kind: str
    description: str
    source_file: str | None
    line: int | None


@dataclass
class Extensions:
    entity_keywords: set[str] = field(default_factory=set)
    journey_headings: set[str] = field(default_factory=set)


@dataclass
class DocFindings:
    sources: list[tuple[str, int]]  # (rel_path, line_count)
    entities: list[Entity]
    terms: list[Term]
    journeys: list[Journey]
    rules: list[Rule]
    assumptions: list[Assumption]
    gaps: list[GapSignal]


# ---------------------------------------------------------------------------
# IO + workspace resolution
# ---------------------------------------------------------------------------


def workspace_dir(project_root: Path) -> Path:
    ws = project_root / WORKSPACE_DIRNAME
    if not ws.is_dir():
        raise UninitializedWorkspaceError(
            f"not a Test Commander workspace: {project_root} (no {WORKSPACE_DIRNAME}/)"
        )
    return ws


def documents_uploaded(workspace: Path) -> Path:
    return workspace / "documents" / "uploaded"


# ---------------------------------------------------------------------------
# Config
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
    """Read ``tc-knowledge.documents:`` extensions from ``<workspace>/config.yaml``.

    Tolerant indentation-based parser; the documented schema covers
    ``entity-keywords`` and ``journey-headings``. Missing keys yield empty
    extensions; the helper falls back to the universal core only.
    """
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
        if pending_key is not None and section == "documents":
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
            in_root = stripped == "tc-knowledge:"
            continue
        if not in_root:
            continue

        if indent == 2:
            commit()
            section = stripped[:-1].strip() if stripped.endswith(":") else None
            continue

        if indent == 4 and section is not None:
            commit()
            if ":" not in stripped:
                continue
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                items = _parse_inline_list(value) if value.startswith("[") else [value.strip("'\"")]
                if section == "documents":
                    _assign(ext, key, items)
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
    if key == "entity-keywords":
        ext.entity_keywords |= set(items)
    elif key == "journey-headings":
        ext.journey_headings |= set(items)


# ---------------------------------------------------------------------------
# Source discovery
# ---------------------------------------------------------------------------


def is_requirements_source(text: str) -> bool:
    return REQ_TOKEN_RE.search(text) is not None


def discover_sources(uploaded: Path) -> list[Path]:
    """Return every ``*.md`` in uploaded/ that is NOT a requirements source."""
    if not uploaded.is_dir():
        return []
    sources: list[Path] = []
    for path in sorted(uploaded.rglob("*.md")):
        # Skip workspace-template placeholder READMEs at the root of uploaded/.
        if path.name == "README.md" and path.parent == uploaded:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if is_requirements_source(text):
            continue
        sources.append(path)
    return sources


# ---------------------------------------------------------------------------
# Heading classification
# ---------------------------------------------------------------------------


def heading_text(line: str) -> str | None:
    m = HEADING_RE.match(line)
    return m.group(2) if m else None


def _contains_any(haystack: str, needles: Iterable[str]) -> bool:
    lowered = haystack.lower()
    return any(needle.lower() in lowered for needle in needles)


# ---------------------------------------------------------------------------
# Per-document extraction
# ---------------------------------------------------------------------------


def extract_one(path: Path, rel_path: str, ext: Extensions) -> dict[str, list]:
    """Extract every dimension from a single document.

    Returns a dict with keys: entities, terms, journeys, rules, assumptions.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    # First pass: collect heading ranges so we know which list belongs to which heading.
    headings = _heading_spans(lines)

    journey_tokens = list(JOURNEY_HEADING_TOKENS) + sorted(ext.journey_headings)
    entity_tokens = list(ENTITY_HEADING_TOKENS)
    glossary_tokens = list(GLOSSARY_HEADING_TOKENS)

    entities = _extract_entities(lines, headings, entity_tokens, rel_path, ext.entity_keywords)
    terms = _extract_terms(lines, headings, glossary_tokens, rel_path)
    journeys = _extract_journeys(lines, headings, journey_tokens, rel_path)
    journey_ranges = [(j.line_start, j.line_end) for j in journeys]
    rules = _extract_rules(lines, journey_ranges, rel_path)
    assumptions = _extract_assumptions(lines, rel_path)

    return {
        "entities": entities,
        "terms": terms,
        "journeys": journeys,
        "rules": rules,
        "assumptions": assumptions,
    }


def _heading_spans(lines: list[str]) -> list[tuple[int, str, int]]:
    """Return [(line_index_1based, heading_text, level), ...]."""
    spans: list[tuple[int, str, int]] = []
    for i, line in enumerate(lines, start=1):
        m = HEADING_RE.match(line)
        if m:
            spans.append((i, m.group(2), len(m.group(1))))
    return spans


def _section_range_for(
    line_num: int,
    spans: list[tuple[int, str, int]],
    all_len: int,
) -> tuple[int, int]:
    """Given the line of a heading, return the (start, end) inclusive range of its section.

    The section spans every subsequent line up to the next heading at the same
    or shallower level (deeper child headings remain part of the section).
    """
    current_level = next((level for span, _, level in spans if span == line_num), None)
    if current_level is None:
        return (line_num + 1, all_len)
    start = line_num + 1
    end = all_len
    for span_line, _, level in spans:
        if span_line > line_num and level <= current_level:
            end = span_line - 1
            break
    return start, end


def _extract_entities(
    lines: list[str],
    spans: list[tuple[int, str, int]],
    entity_tokens: list[str],
    rel_path: str,
    extension_keywords: set[str],
) -> list[Entity]:
    found: list[Entity] = []
    seen: set[tuple[str, int]] = set()
    for span_line, heading, _ in spans:
        if not _contains_any(heading, entity_tokens):
            continue
        start, end = _section_range_for(span_line, spans, len(lines))
        for i in range(start, end + 1):
            if i - 1 >= len(lines):
                break
            line = lines[i - 1]
            # Bullet with bolded entity name.
            m = BULLET_BOLD_RE.match(line)
            if m:
                name = m.group(1)
                key = (name, i)
                if key not in seen:
                    seen.add(key)
                    found.append(Entity(name=name, source_file=rel_path, line=i))
                continue
            # Table row whose first column is a single capitalized noun-ish phrase.
            tm = TABLE_ROW_RE.match(line)
            if tm:
                first = tm.group(1).strip()
                if (
                    first
                    and first[0].isupper()
                    and first not in {"Entity", "Term", "Name"}
                    and "-" not in first[:3]
                ):
                    key = (first, i)
                    if key not in seen:
                        seen.add(key)
                        found.append(Entity(name=first, source_file=rel_path, line=i))

    # Extension keywords: surface them as entity findings even outside entity sections.
    for keyword in sorted(extension_keywords):
        for i, line in enumerate(lines, start=1):
            if re.search(rf"\b{re.escape(keyword)}\b", line):
                key = (keyword, i)
                if key not in seen:
                    seen.add(key)
                    found.append(Entity(name=keyword, source_file=rel_path, line=i))
                break

    return found


def _extract_terms(
    lines: list[str],
    spans: list[tuple[int, str, int]],
    glossary_tokens: list[str],
    rel_path: str,
) -> list[Term]:
    found: list[Term] = []
    glossary_ranges: list[tuple[int, int]] = []
    for span_line, heading, _ in spans:
        if _contains_any(heading, glossary_tokens):
            glossary_ranges.append(_section_range_for(span_line, spans, len(lines)))

    def in_glossary(line_num: int) -> bool:
        return any(start <= line_num <= end for start, end in glossary_ranges)

    # Definition-list shape: "Term" on one line, ": definition" on the next.
    for i in range(len(lines) - 1):
        line = lines[i]
        next_line = lines[i + 1]
        line_num = i + 1
        if not line.strip() or line.lstrip().startswith(("#", "|", ":", "-", "*", ">")):
            continue
        # Allow word + optional whitespace; the value must be a single noun-ish phrase.
        if not re.fullmatch(r"[A-Z][A-Za-z0-9_ -]+", line.strip()):
            continue
        if not next_line.startswith(": "):
            continue
        term = line.strip()
        definition = next_line[2:].strip()
        if term in {"Entity", "Term", "Name"}:
            continue
        found.append(Term(term=term, definition=definition, source_file=rel_path, line=line_num))

    # Glossary-table shape: rows under a glossary heading.
    for start, end in glossary_ranges:
        for i in range(start, end + 1):
            if i - 1 >= len(lines):
                break
            line = lines[i - 1]
            m = TABLE_ROW_RE.match(line)
            if not m:
                continue
            term_cell = m.group(1).strip()
            def_cell = m.group(2).strip()
            if not term_cell or not def_cell:
                continue
            if term_cell in {"Term", "Name", "Entity", "---"} or def_cell.startswith("---"):
                continue
            if not term_cell[0].isupper():
                continue
            found.append(Term(term=term_cell, definition=def_cell, source_file=rel_path, line=i))

    return found


def _extract_journeys(
    lines: list[str],
    spans: list[tuple[int, str, int]],
    journey_tokens: list[str],
    rel_path: str,
) -> list[Journey]:
    found: list[Journey] = []
    for span_line, heading, _ in spans:
        if not _contains_any(heading, journey_tokens):
            continue
        start, end = _section_range_for(span_line, spans, len(lines))
        steps: list[str] = []
        last_step_line = span_line
        for i in range(start, end + 1):
            if i - 1 >= len(lines):
                break
            m = NUMBERED_OR_BULLET_RE.match(lines[i - 1])
            if m:
                steps.append(m.group(1).strip())
                last_step_line = i
        if steps:
            found.append(
                Journey(
                    title=heading,
                    steps=tuple(steps),
                    source_file=rel_path,
                    line_start=span_line,
                    line_end=last_step_line,
                )
            )
    return found


def _extract_rules(
    lines: list[str],
    journey_ranges: list[tuple[int, int]],
    rel_path: str,
) -> list[Rule]:
    def in_journey(line_num: int) -> bool:
        return any(start <= line_num <= end for start, end in journey_ranges)

    found: list[Rule] = []
    for i, line in enumerate(lines, start=1):
        if in_journey(i):
            continue
        if not line.strip() or line.lstrip().startswith(("#", "|", ">", ":")):
            continue
        # Build a lowercase scan view; find modal occurrences.
        lowered = line.lower()
        modal_match = None
        for modal in RFC_2119_MODALS:
            m = re.search(rf"\b{modal}\b", lowered)
            if m and (modal_match is None or m.start() < modal_match[1]):
                modal_match = (modal, m.start())
        if modal_match is None:
            continue
        modal, idx = modal_match
        subject_raw = lowered[:idx]
        subject = re.sub(r"[^\w\s]", " ", subject_raw).strip()
        stopwords = {"the", "and", "that", "this"}
        words = [w for w in subject.split() if len(w) >= 3 and w not in stopwords]
        subject_anchor = words[-1] if words else subject
        text_clean = line.strip().lstrip("-*").strip()
        found.append(
            Rule(
                text=text_clean,
                modal=modal,
                subject=subject_anchor,
                source_file=rel_path,
                line=i,
            )
        )
    return found


def _extract_assumptions(lines: list[str], rel_path: str) -> list[Assumption]:
    found: list[Assumption] = []
    for i, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith(("#", "|", ":", "-", "*", ">")):
            continue
        lowered = line.lower()
        if any(re.search(rf"\b{m}\b", lowered) for m in ASSUMPTION_MARKERS):
            text_clean = line.strip().lstrip("-*").strip()
            found.append(Assumption(text=text_clean, source_file=rel_path, line=i))
    return found


# ---------------------------------------------------------------------------
# Cross-document gap detection
# ---------------------------------------------------------------------------


def detect_gaps(
    sources: list[tuple[Path, str]],
    all_entities: list[Entity],
    all_terms: list[Term],
    all_rules: list[Rule],
) -> list[GapSignal]:
    """Cross-document detection: undefined-term, contradictory-rule."""
    gaps: list[GapSignal] = []
    defined = {t.term.lower() for t in all_terms}

    # undefined-term path A: capitalized noun phrase appearing in >=2 documents.
    docs_per_entity: dict[str, set[str]] = {}
    for ent in all_entities:
        docs_per_entity.setdefault(ent.name, set()).add(ent.source_file)
    for name, docs in sorted(docs_per_entity.items()):
        if len(docs) >= 2 and name.lower() not in defined:
            first = next((e for e in all_entities if e.name == name), None)
            gaps.append(
                GapSignal(
                    kind="undefined-term",
                    description=(
                        f"Term '{name}' appears in {len(docs)} documents but is not "
                        "defined in any glossary or definition list"
                    ),
                    source_file=first.source_file if first else None,
                    line=first.line if first else None,
                )
            )

    # undefined-term path B: bolded term in prose, not in glossary, not already flagged.
    flagged = {g.description for g in gaps}
    bolded: dict[str, tuple[str, int]] = {}
    for path, rel in sources:
        text = path.read_text(encoding="utf-8")
        for m in BOLDED_TERM_RE.finditer(text):
            term = m.group(1)
            if term in bolded:
                continue
            line_num = text[: m.start()].count("\n") + 1
            bolded[term] = (rel, line_num)
    for term, (src, line) in sorted(bolded.items()):
        if term.lower() in defined:
            continue
        description = (
            f"Bolded term '{term}' is used in prose but is not defined in any "
            "glossary or definition list"
        )
        already = any(g.description.startswith(f"Term '{term}'") for g in gaps)
        if already or description in flagged:
            continue
        gaps.append(
            GapSignal(
                kind="undefined-term",
                description=description,
                source_file=src,
                line=line,
            )
        )

    # contradictory-rule: rules sharing a subject anchor, one with a negation modifier, one without.
    by_subject: dict[str, list[Rule]] = {}
    for rule in all_rules:
        by_subject.setdefault(rule.subject, []).append(rule)
    for subject, group in by_subject.items():
        if len(group) < 2:
            continue
        positives = [r for r in group if not _has_negation(r.text)]
        negatives = [r for r in group if _has_negation(r.text)]
        if positives and negatives:
            p, n = positives[0], negatives[0]
            gaps.append(
                GapSignal(
                    kind="contradictory-rule",
                    description=(
                        f"Rules contradict on subject '{subject}': '{p.text}' "
                        f"(line {p.line}) vs '{n.text}' (line {n.line})"
                    ),
                    source_file=p.source_file,
                    line=p.line,
                )
            )

    return gaps


def _has_negation(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(token)}\b", lowered) for token in NEGATION_MARKERS)


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def aggregate(sources: list[Path], workspace: Path, ext: Extensions) -> DocFindings:
    findings = DocFindings(
        sources=[],
        entities=[],
        terms=[],
        journeys=[],
        rules=[],
        assumptions=[],
        gaps=[],
    )
    rel_pairs: list[tuple[Path, str]] = []
    for path in sources:
        rel_path = str(path.relative_to(workspace))
        line_count = path.read_text(encoding="utf-8").count("\n") + 1
        findings.sources.append((rel_path, line_count))
        per = extract_one(path, rel_path, ext)
        findings.entities.extend(per["entities"])
        findings.terms.extend(per["terms"])
        findings.journeys.extend(per["journeys"])
        findings.rules.extend(per["rules"])
        findings.assumptions.extend(per["assumptions"])
        rel_pairs.append((path, rel_path))

    findings.gaps = detect_gaps(rel_pairs, findings.entities, findings.terms, findings.rules)
    return findings


# ---------------------------------------------------------------------------
# Render: documentation-model.md (per-source)
# ---------------------------------------------------------------------------


def render_documentation_model(findings: DocFindings) -> str:
    lines: list[str] = []
    lines.append("# Documentation-Derived Model")
    lines.append("")
    lines.append(
        "Auto-generated by `/tc:learn-from-docs`. Re-running overwrites this file "
        "byte-deterministically. Edits will not survive a re-run."
    )
    lines.append("")

    # Source documents
    lines.append("## Source documents")
    lines.append("")
    if not findings.sources:
        lines.append("_No narrative documents found in `documents/uploaded/`._")
        lines.append("")
        lines.append(
            "A file is treated as a narrative document iff it does not contain "
            "any `REQ-NNN` token; files with `REQ-NNN` markers are handled by "
            "`/tc:review-requirements` (Phase 2) instead."
        )
        lines.append("")
        return "\n".join(lines).rstrip("\n") + "\n"
    lines.append("| Path | Lines |")
    lines.append("| --- | --- |")
    for rel_path, line_count in findings.sources:
        lines.append(f"| {rel_path} | {line_count} |")
    lines.append("")

    # Entities
    lines.append("## Entities")
    lines.append("")
    if findings.entities:
        lines.append("| Entity | Source |")
        lines.append("| --- | --- |")
        for ent in sorted(findings.entities, key=lambda e: (e.name, e.source_file, e.line)):
            lines.append(f"| {ent.name} | {ent.source_file}:{ent.line} |")
    else:
        lines.append("_No entities extracted._")
    lines.append("")

    # Terms
    lines.append("## Terms")
    lines.append("")
    if findings.terms:
        lines.append("| Term | Definition | Source |")
        lines.append("| --- | --- | --- |")
        for term in sorted(findings.terms, key=lambda t: (t.term, t.source_file, t.line)):
            definition = term.definition.replace("|", "\\|")
            lines.append(f"| {term.term} | {definition} | {term.source_file}:{term.line} |")
    else:
        lines.append("_No glossary or definition-list terms extracted._")
    lines.append("")

    # User journeys
    lines.append("## User journeys")
    lines.append("")
    if findings.journeys:
        for journey in sorted(findings.journeys, key=lambda j: (j.source_file, j.line_start)):
            lines.append(
                f"### {journey.title} ({journey.source_file}:"
                f"{journey.line_start}-{journey.line_end})"
            )
            lines.append("")
            for step in journey.steps:
                lines.append(f"- {step}")
            lines.append("")
    else:
        lines.append("_No journeys extracted._")
        lines.append("")

    # Business rules
    lines.append("## Business rules")
    lines.append("")
    if findings.rules:
        lines.append("| Modal | Rule | Source |")
        lines.append("| --- | --- | --- |")
        for rule in sorted(
            findings.rules, key=lambda r: (r.source_file, r.line, r.modal)
        ):
            text = rule.text.replace("|", "\\|")
            lines.append(f"| {rule.modal} | {text} | {rule.source_file}:{rule.line} |")
    else:
        lines.append("_No RFC-2119-modal business rules extracted._")
    lines.append("")

    # Assumptions
    lines.append("## Assumptions")
    lines.append("")
    lines.append(
        "Assumptions are statements containing assumption markers "
        "(`assume`, `expected`, `presumed`, `likely`) with no direct citation in "
        "the source. They are flagged distinctly from confirmed facts."
    )
    lines.append("")
    if findings.assumptions:
        for assumption in sorted(
            findings.assumptions, key=lambda a: (a.source_file, a.line)
        ):
            lines.append(
                f"- {assumption.text} (source: {assumption.source_file}:"
                f"{assumption.line}; no direct citation)"
            )
    else:
        lines.append("_No assumptions extracted._")
    lines.append("")

    # Gap signals
    lines.append("## Gap signals (routed to `requirements/open-questions.md`)")
    lines.append("")
    if findings.gaps:
        for gap in sorted(
            findings.gaps,
            key=lambda g: (g.kind, g.source_file or "", g.line or 0),
        ):
            citation = ""
            if gap.source_file and gap.line:
                citation = f" ({gap.source_file}:{gap.line})"
            lines.append(f"- **{gap.kind}**: {gap.description}{citation}")
    else:
        lines.append("_No gap signals detected._")
    lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"


# ---------------------------------------------------------------------------
# Render: cross-cutting section bodies
# ---------------------------------------------------------------------------


def render_documents_entities_section(findings: DocFindings) -> str:
    if not findings.entities:
        return "_No entities extracted from documents._"
    lines: list[str] = []
    for ent in sorted(findings.entities, key=lambda e: (e.name, e.source_file, e.line)):
        lines.append(f"- **{ent.name}** ({ent.source_file}:{ent.line})")
    return "\n".join(lines)


def render_documents_journeys_section(findings: DocFindings) -> str:
    if not findings.journeys:
        return "_No journeys extracted from documents._"
    lines: list[str] = []
    for journey in sorted(findings.journeys, key=lambda j: (j.source_file, j.line_start)):
        lines.append(
            f"- **{journey.title}** ({journey.source_file}:"
            f"{journey.line_start}-{journey.line_end}) - "
            f"{len(journey.steps)} steps"
        )
    return "\n".join(lines)


def render_documents_rules_section(findings: DocFindings) -> str:
    if not findings.rules:
        return "_No business rules extracted from documents._"
    lines: list[str] = []
    for rule in sorted(findings.rules, key=lambda r: (r.source_file, r.line)):
        text = rule.text
        lines.append(f"- _{rule.modal}_: {text} ({rule.source_file}:{rule.line})")
    return "\n".join(lines)


def render_documents_assumptions_section(findings: DocFindings) -> str:
    if not findings.assumptions:
        return "_No assumptions extracted from documents._"
    lines: list[str] = []
    for assumption in sorted(findings.assumptions, key=lambda a: (a.source_file, a.line)):
        lines.append(
            f"- {assumption.text} ({assumption.source_file}:{assumption.line}; "
            "no direct citation)"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cross-cutting file IO with section-overwrite semantics
# ---------------------------------------------------------------------------


CROSS_CUTTING_TITLES: dict[str, tuple[str, str]] = {
    "entities.md": (
        "Entities",
        "Cross-source entity index. Each `## From <source>` section is "
        "regenerated by its owning `/tc:learn-from-*` command; sections from "
        "other commands are preserved across re-runs.",
    ),
    "user-journeys.md": (
        "User Journeys",
        "Cross-source user-journey index. Each `## From <source>` section is "
        "regenerated by its owning `/tc:learn-from-*` command; sections from "
        "other commands are preserved across re-runs.",
    ),
    "business-rules.md": (
        "Business Rules",
        "Cross-source business-rule index. Each `## From <source>` section is "
        "regenerated by its owning `/tc:learn-from-*` command; sections from "
        "other commands are preserved across re-runs.",
    ),
    "assumptions.md": (
        "Assumptions",
        "Cross-source assumption index. Each entry is flagged distinctly from "
        "confirmed facts (no direct citation in the source). Each "
        "`## From <source>` section is regenerated by its owning "
        "`/tc:learn-from-*` command; sections from other commands are "
        "preserved across re-runs.",
    ),
}

SOURCE_ORDER = ("documents", "specs", "code", "api", "tests")


def update_cross_cutting(
    workspace: Path,
    filename: str,
    section_body: str,
) -> None:
    """Section-overwrite the ``## From documents`` block in a cross-cutting file."""
    target = workspace / "product-knowledge" / filename
    title, preamble = CROSS_CUTTING_TITLES[filename]
    sections = synth_mod.parse_source_sections(_read_text(target))
    sections[SOURCE_LABEL] = section_body.strip()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_render_cross_cutting(title, preamble, sections), encoding="utf-8")


def _render_cross_cutting(title: str, preamble: str, sections: dict[str, str]) -> str:
    lines: list[str] = [f"# {title}", "", preamble, ""]
    for source in SOURCE_ORDER:
        body = sections.get(source, "").strip()
        if not body:
            continue
        lines.append(f"## From {source}")
        lines.append("")
        lines.append(body)
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


# ---------------------------------------------------------------------------
# Open-questions append with dedup
# ---------------------------------------------------------------------------


OPEN_QUESTIONS_HEADER = "# Open questions"


def append_open_questions(workspace: Path, gaps: list[GapSignal]) -> None:
    """Append gap-derived open questions, deduplicated by (source-id, question-text)."""
    target = workspace / "requirements" / "open-questions.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = _read_text(target)
    if not existing.strip():
        existing = (
            f"{OPEN_QUESTIONS_HEADER}\n\n"
            "Append-only log of questions raised by tc-knowledge and other "
            "commands. Deduplicated by source-id + question text.\n"
        )

    existing_set: set[tuple[str, str]] = set()
    for line in existing.split("\n"):
        m = re.match(r"^- \[([^\]]+)\]\s+(.+)$", line)
        if m:
            existing_set.add((m.group(1).strip(), m.group(2).strip()))

    new_lines: list[str] = []
    for gap in gaps:
        source_id = "tc-knowledge/learn-from-docs"
        question = gap.description.rstrip(".") + "."
        key = (source_id, question)
        if key in existing_set:
            continue
        existing_set.add(key)
        new_lines.append(f"- [{source_id}] {question}")

    if not new_lines:
        # Still ensure the header exists in the file.
        if existing.endswith("\n"):
            target.write_text(existing, encoding="utf-8")
        else:
            target.write_text(existing + "\n", encoding="utf-8")
        return

    body = existing.rstrip("\n") + "\n\n" + "\n".join(new_lines) + "\n"
    target.write_text(body, encoding="utf-8")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run(project_root: Path) -> int:
    workspace = workspace_dir(project_root)
    ext = load_extensions(workspace)
    uploaded = documents_uploaded(workspace)
    sources = discover_sources(uploaded)
    findings = aggregate(sources, workspace, ext)

    # 1. documentation-model.md (per-source, overwrite)
    doc_model = workspace / "product-knowledge" / "documentation-model.md"
    doc_model.parent.mkdir(parents=True, exist_ok=True)
    doc_model.write_text(render_documentation_model(findings), encoding="utf-8")

    # 2. cross-cutting section-overwrites (only when sources were found; on the
    # empty path we still want sibling sections preserved, so we still overwrite
    # the documents section with an empty marker).
    update_cross_cutting(
        workspace, "entities.md", render_documents_entities_section(findings)
    )
    update_cross_cutting(
        workspace, "user-journeys.md", render_documents_journeys_section(findings)
    )
    update_cross_cutting(
        workspace, "business-rules.md", render_documents_rules_section(findings)
    )
    update_cross_cutting(
        workspace, "assumptions.md", render_documents_assumptions_section(findings)
    )

    # 3. open-questions append (idempotent)
    append_open_questions(workspace, findings.gaps)

    # 4. shared synthesizer regenerates system-model.md
    synth_mod.synthesize(project_root)

    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract knowledge from narrative documents in "
            "<workspace>/documents/uploaded/ and populate "
            "<workspace>/product-knowledge/."
        ),
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
        return run(project_root)
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
