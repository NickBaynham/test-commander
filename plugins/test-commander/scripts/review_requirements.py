#!/usr/bin/env python3
"""/tc:review-requirements helper.

Reads `*.md` files in `<workspace>/documents/uploaded/` that declare
`REQ-NNN` markers, applies the Phase 2 mechanical rubric (16 dimensions,
per the partition table in planning/plan.md Step 2.2), and writes three
artifacts under `<workspace>/requirements/`:

- `requirements-review.md` (overwritten on every run)
- `requirements-inventory.md` (overwritten on every run)
- `open-questions.md` (appended, deduplicated by (req-id, question-text))

Per D18 the helper ships inside the plugin so consuming-project users can
invoke it after `claude plugin install`. Per D19 the keyword sets are
universal cores; projects extend them via `<workspace>/config.yaml`.

Exit codes:
    0 - review written
    2 - uninitialized workspace, REQ-ID collision, or malformed input
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

WORKSPACE_DIRNAME = ".test-commander"
REQ_PATTERN = re.compile(r"\bREQ-(\d{1,4})\b")
REQ_HEADER = re.compile(r"^(?:[-*]\s*)?REQ-(\d{1,4})\s*:\s*(.*)$", re.MULTILINE)

CORE_BUZZWORDS = {"robust", "seamless", "modern", "best-of-breed", "world-class", "leverage"}
CORE_VAGUE_PREDICATES = {"user-friendly", "easy", "intuitive", "fast", "slow"}
CORE_RFC2119 = {"shall", "must", "should"}
CORE_QUALITATIVE = {"quickly", "fast", "many", "few", "often", "soon", "slow", "rapidly"}
CORE_EDGE_KEYWORDS = {"except", "unless", "otherwise", "edge"}
CORE_FAILURE_KEYWORDS = {"invalid", "error", "fail", "missing", "declined", "rejected", "denied"}
CORE_SENSITIVE = {"password", "secret", "token", "credential", "key"}
CORE_CONSTRAINTS = {"length", "format", "encoding", "retention", "hashed", "encrypted", "tokenized"}
CORE_PERMISSION_VERBS = {"delete", "approve", "reject", "modify", "grant", "revoke"}
CORE_ROLE_QUALIFIERS = {"admin", "owner", "operator"}
CORE_NFR_ADJECTIVES = {"available", "secure", "performant", "scalable", "reliable"}
CORE_AMBIGUITY = {"reasonable", "appropriate", "sufficient", "robust", "seamless"}
CORE_RISK = {
    "plain text", "plaintext", "unencrypted", "raw password",
    "hardcoded credential", "default password",
}
CORE_SUBJECTIVE_VERBS = {"feel", "look", "match the brand", "delight", "inviting"}
CORE_AUTOMATION_MARKERS = {"automation candidate", "regression check", "automated"}
PERMISSION_MODALS = {"may", "can"}
OBLIGATION_MODALS = {"shall", "must", "require", "requires"}

STOPWORDS = {
    "shall", "must", "should", "users", "user", "the", "all", "may", "can",
    "require", "requires", "without", "any", "for", "and", "with", "are",
    "system", "they", "their", "from", "into", "this", "that", "have", "than",
    "permitted", "stored", "submit", "submits", "page", "pages", "view",
    "be", "is", "was", "will", "use", "used", "uses", "via", "but", "not",
    "an", "as", "at", "by", "in", "of", "on", "or", "to", "if",
}


# ---------------------------------------------------------------------------
# Exceptions and dataclasses
# ---------------------------------------------------------------------------

class RequirementsError(Exception):
    """Base class for review_requirements errors."""


class UninitializedWorkspaceError(RequirementsError):
    """Raised when `<project>/.test-commander/` does not exist."""


class RequirementCollisionError(RequirementsError):
    """Raised when two input files declare the same REQ-NNN."""


@dataclass
class Requirement:
    id: str
    body: str
    source_file: str


@dataclass
class Finding:
    req_id: str
    dimension: str
    detail: str


@dataclass
class OpenQuestion:
    req_id: str
    text: str

    def key(self) -> str:
        return f"{self.req_id}|{self.text.strip()}"


@dataclass
class Extensions:
    sensitive: set[str] = field(default_factory=set)
    compliance: set[str] = field(default_factory=set)
    permission_verbs: set[str] = field(default_factory=set)
    role_qualifiers: set[str] = field(default_factory=set)


@dataclass
class ReviewResult:
    workspace: Path
    requirements_count: int
    findings: list[Finding]
    open_questions: list[OpenQuestion]
    review_path: Path | None = None
    inventory_path: Path | None = None
    open_questions_path: Path | None = None


# ---------------------------------------------------------------------------
# Config / extensions
# ---------------------------------------------------------------------------

def _parse_yaml_list(value: str) -> list[str]:
    """Parse a bracketed inline list like `[a, b, "c d"]`."""
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
    """Read `tc-requirements:` extensions from `<workspace>/config.yaml`.

    Tolerant parser for the documented schema only. Unknown keys are ignored;
    a missing or malformed file yields empty extensions.
    """
    config_path = workspace / "config.yaml"
    ext = Extensions()
    if not config_path.is_file():
        return ext
    try:
        text = config_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ext

    lines = text.split("\n")
    in_tcr = False
    section: str | None = None
    pending_block_key: str | None = None
    pending_block_items: list[str] = []

    def commit_pending():
        nonlocal pending_block_key, pending_block_items
        if pending_block_key is not None and section is not None:
            _assign_extension(ext, section, pending_block_key, pending_block_items)
        pending_block_key = None
        pending_block_items = []

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))

        if indent == 0:
            commit_pending()
            section = None
            in_tcr = stripped == "tc-requirements:"
            continue
        if not in_tcr:
            continue

        if indent == 2:
            commit_pending()
            section = stripped[:-1].strip() if stripped.endswith(":") else None
            continue

        if indent == 4 and section is not None:
            commit_pending()
            if ":" not in stripped:
                continue
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                items = _parse_yaml_list(value) if value.startswith("[") else [value.strip("'\"")]
                _assign_extension(ext, section, key, items)
            else:
                pending_block_key = key
                pending_block_items = []
            continue

        if indent >= 6 and pending_block_key is not None and stripped.startswith("-"):
            item = stripped[1:].strip().strip("'\"")
            if item:
                pending_block_items.append(item)

    commit_pending()
    return ext


def _assign_extension(ext: Extensions, section: str, key: str, items: list[str]) -> None:
    if section == "data-rules" and key == "sensitive-keywords":
        ext.sensitive |= set(items)
    elif section == "risk" and key == "compliance-keywords":
        ext.compliance |= set(items)
    elif section == "roles-permissions" and key == "permission-verbs":
        ext.permission_verbs |= set(items)
    elif section == "roles-permissions" and key == "role-qualifiers":
        ext.role_qualifiers |= set(items)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def is_requirements_file(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    return bool(REQ_PATTERN.search(text))


def parse_file(path: Path) -> list[Requirement]:
    text = path.read_text(encoding="utf-8")
    matches = list(REQ_HEADER.finditer(text))
    reqs: list[Requirement] = []
    for i, m in enumerate(matches):
        rid = f"REQ-{int(m.group(1)):03d}"
        first_line = m.group(2).strip()
        next_start = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        continuation = text[m.end():next_start]
        continuation = re.sub(r"<!--.*?-->", "", continuation, flags=re.DOTALL)
        cont_lines: list[str] = []
        for ln in continuation.split("\n"):
            stripped = ln.strip()
            if stripped.startswith("## ") or stripped.startswith("# "):
                break
            if stripped:
                cont_lines.append(stripped)
        body = first_line
        if cont_lines:
            body = (first_line + " " + " ".join(cont_lines)).strip()
        reqs.append(Requirement(id=rid, body=body, source_file=path.name))
    return reqs


def parse_workspace(workspace: Path) -> tuple[list[Requirement], dict[str, list[str]]]:
    uploaded = workspace / "documents" / "uploaded"
    if not uploaded.is_dir():
        return [], {}
    all_reqs: list[Requirement] = []
    seen: dict[str, list[str]] = {}
    for md in sorted(uploaded.glob("*.md")):
        if not is_requirements_file(md):
            continue
        for r in parse_file(md):
            seen.setdefault(r.id, []).append(r.source_file)
            all_reqs.append(r)
    collisions = {rid: files for rid, files in seen.items() if len(files) > 1}
    return all_reqs, collisions


# ---------------------------------------------------------------------------
# Check helpers
# ---------------------------------------------------------------------------

def _contains_phrase(body: str, phrase: str) -> bool:
    """Case-insensitive containment check.

    Multi-token phrases match literally. Single tokens use word-boundary
    matching with an optional trailing `s` to handle simple plurals
    (`password` matches `passwords`, `key` matches `keys`).
    """
    p = phrase.lower()
    b = body.lower()
    if " " in p or "-" in p:
        return p in b
    return bool(re.search(rf"\b{re.escape(p)}s?\b", b))


def _hits(body: str, keywords: Iterable[str]) -> list[str]:
    return [k for k in keywords if _contains_phrase(body, k)]


_NUMERIC_THRESHOLD = re.compile(
    r"\b\d+(\.\d+)?\s*(%|ms|s|min|hr|hours?|days?|GB|MB|KB|requests?|users?)?\b"
)


def _has_numeric_threshold(body: str) -> bool:
    return bool(_NUMERIC_THRESHOLD.search(body))


def _has_any_modal(body: str, modals: Iterable[str]) -> bool:
    b = body.lower()
    return any(re.search(rf"\b{re.escape(m)}\b", b) for m in modals)


def _substantive_nouns(text: str) -> set[str]:
    tokens = re.findall(r"\b([a-z][a-z]{2,})\b", text.lower())
    return {t for t in tokens if t not in STOPWORDS}


# ---------------------------------------------------------------------------
# Per-dimension checks
# ---------------------------------------------------------------------------

def _check_clarity(req: Requirement) -> Finding | None:
    hits = _hits(req.body, CORE_BUZZWORDS)
    if hits:
        return Finding(req.id, "clarity", f"vague-marketing buzzword(s): {', '.join(sorted(hits))}")
    return None


def _check_testability(req: Requirement) -> Finding | None:
    vague = _hits(req.body, CORE_VAGUE_PREDICATES)
    if vague and not _has_numeric_threshold(req.body):
        joined = ", ".join(sorted(vague))
        return Finding(
            req.id, "testability",
            f"vague predicate(s) without numeric threshold: {joined}",
        )
    if not _has_any_modal(req.body, CORE_RFC2119):
        return Finding(req.id, "testability", "no RFC-2119 modal (shall/must/should)")
    return None


def _check_completeness(req: Requirement) -> Finding | None:
    tokens = req.body.split()
    if len(tokens) <= 10:
        return Finding(
            req.id, "completeness",
            f"body too short ({len(tokens)} tokens; threshold <= 10)",
        )
    return None


def _check_atomicity(req: Requirement) -> Finding | None:
    body_lower = req.body.lower()
    if re.search(r",\s*[^,]+,\s*[^,]+,?\s*(?:and|or)\s+", body_lower):
        return Finding(req.id, "atomicity", "comma-list joining 3+ items with and/or")
    pattern = r"\b\w+(?:s|ed|ing)?\b.+\band\b.+\b\w+(?:s|ed|ing)?\b"
    if re.search(pattern, body_lower) and body_lower.count(" and ") >= 2:
        return Finding(req.id, "atomicity", "multiple `and`-joined clauses")
    return None


def _check_measurability(req: Requirement) -> Finding | None:
    qual = _hits(req.body, CORE_QUALITATIVE)
    if qual and not _has_numeric_threshold(req.body):
        joined = ", ".join(sorted(qual))
        return Finding(
            req.id, "measurability",
            f"qualitative quantifier(s) without numeric threshold: {joined}",
        )
    return None


def _check_ac_quality(req: Requirement) -> Finding | None:
    has_ac_mention = re.search(r"\bacceptance criteria\b", req.body, re.IGNORECASE)
    has_ac_pointer = re.search(r"\bAC-\d+\b", req.body)
    if has_ac_mention and not has_ac_pointer:
        return Finding(
            req.id, "ac-quality",
            "mentions 'acceptance criteria' but no AC-NNN pointer present",
        )
    return None


def _check_edge_cases(req: Requirement) -> Finding | None:
    has_modal = (
        _has_any_modal(req.body, CORE_RFC2119)
        or _has_any_modal(req.body, PERMISSION_MODALS)
    )
    if has_modal and not _hits(req.body, CORE_EDGE_KEYWORDS):
        return Finding(req.id, "edge-cases", "no edge keyword (except/unless/otherwise/edge)")
    return None


def _check_negative_cases(req: Requirement) -> Finding | None:
    has_modal = (
        _has_any_modal(req.body, CORE_RFC2119)
        or _has_any_modal(req.body, PERMISSION_MODALS)
    )
    if has_modal and not _hits(req.body, CORE_FAILURE_KEYWORDS):
        return Finding(
            req.id, "negative-cases",
            "no failure keyword (invalid/error/fail/...)",
        )
    return None


def _check_data_rules(req: Requirement, ext: Extensions) -> Finding | None:
    sensitive = CORE_SENSITIVE | ext.sensitive
    hits = _hits(req.body, sensitive)
    if hits and not _hits(req.body, CORE_CONSTRAINTS):
        joined = ", ".join(sorted(hits))
        return Finding(
            req.id, "data-rules",
            f"sensitive-data keyword(s) without constraint: {joined}",
        )
    return None


def _check_roles_permissions(req: Requirement, ext: Extensions) -> Finding | None:
    verbs = CORE_PERMISSION_VERBS | ext.permission_verbs
    roles = CORE_ROLE_QUALIFIERS | ext.role_qualifiers
    verb_hits = _hits(req.body, verbs)
    if verb_hits and not _hits(req.body, roles):
        joined = ", ".join(sorted(verb_hits))
        return Finding(
            req.id, "roles-permissions",
            f"permission verb(s) without role qualifier: {joined}",
        )
    return None


def _check_nfrs(req: Requirement) -> Finding | None:
    hits = _hits(req.body, CORE_NFR_ADJECTIVES)
    if hits and not _has_numeric_threshold(req.body):
        joined = ", ".join(sorted(hits))
        return Finding(req.id, "nfrs", f"NFR adjective(s) without quantitative threshold: {joined}")
    return None


def _check_ambiguity(req: Requirement) -> Finding | None:
    hits = _hits(req.body, CORE_AMBIGUITY)
    if hits:
        joined = ", ".join(sorted(hits))
        return Finding(req.id, "ambiguity", f"ambiguity adjective(s): {joined}")
    return None


def _check_risk(req: Requirement, ext: Extensions) -> Finding | None:
    risk = CORE_RISK | ext.compliance
    hits = _hits(req.body, risk)
    if hits:
        joined = ", ".join(sorted(hits))
        return Finding(req.id, "risk", f"risk/compliance keyword(s): {joined}")
    return None


def _check_automation_suitability(req: Requirement) -> Finding | None:
    subjective = _hits(req.body, CORE_SUBJECTIVE_VERBS)
    markers = _hits(req.body, CORE_AUTOMATION_MARKERS)
    if subjective and markers:
        s = sorted(subjective)
        m = sorted(markers)
        return Finding(
            req.id, "automation-suitability",
            f"subjective verb(s) {s} with automation marker(s) {m}",
        )
    return None


def _cross_check_dependencies(reqs: list[Requirement]) -> tuple[list[Finding], list[OpenQuestion]]:
    """Detect broken references and cycles in REQ-NNN cross-references."""
    findings: list[Finding] = []
    questions: list[OpenQuestion] = []
    known_ids = {r.id for r in reqs}

    refs: dict[str, list[str]] = {}
    for r in reqs:
        targets = []
        for m in REQ_PATTERN.finditer(r.body):
            tid = f"REQ-{int(m.group(1)):03d}"
            if tid != r.id and tid not in targets:
                targets.append(tid)
        refs[r.id] = targets

    for rid, targets in refs.items():
        for t in targets:
            if t not in known_ids:
                detail = f"references {t} which does not exist"
                findings.append(Finding(rid, "dependencies", detail))
                questions.append(OpenQuestion(rid, f"{rid} {detail}"))

    # Cycle detection via DFS.
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {rid: WHITE for rid in refs}
    seen_cycles: set[tuple[str, ...]] = set()

    def dfs(node: str, path: list[str]) -> None:
        color[node] = GRAY
        path.append(node)
        for nxt in refs.get(node, []):
            if nxt not in color:
                continue
            if color[nxt] == GRAY:
                cycle_start = path.index(nxt)
                cycle = tuple(sorted(path[cycle_start:]))
                if cycle not in seen_cycles:
                    seen_cycles.add(cycle)
                    cycle_str = " -> ".join(path[cycle_start:] + [nxt])
                    findings.append(Finding(node, "dependencies", f"dependency cycle: {cycle_str}"))
            elif color[nxt] == WHITE:
                dfs(nxt, path)
        path.pop()
        color[node] = BLACK

    for rid in list(refs.keys()):
        if color.get(rid, BLACK) == WHITE:
            dfs(rid, [])

    return findings, questions


def _cross_check_consistency(reqs: list[Requirement]) -> tuple[list[Finding], list[OpenQuestion]]:
    """Detect pairs of requirements with shared subjects + opposing modals."""
    findings: list[Finding] = []
    questions: list[OpenQuestion] = []
    seen_pairs: set[tuple[str, str]] = set()

    nouns = {r.id: _substantive_nouns(r.body) for r in reqs}
    permits = {r.id: _has_any_modal(r.body, PERMISSION_MODALS) for r in reqs}
    obligates = {r.id: _has_any_modal(r.body, OBLIGATION_MODALS) for r in reqs}

    for i, a in enumerate(reqs):
        for b in reqs[i + 1:]:
            pair = tuple(sorted((a.id, b.id)))
            if pair in seen_pairs:
                continue
            opposing = (permits[a.id] and obligates[b.id]) or (permits[b.id] and obligates[a.id])
            if not opposing:
                continue
            shared = nouns[a.id] & nouns[b.id]
            if not shared:
                continue
            seen_pairs.add(pair)
            shared_str = ", ".join(sorted(shared))
            detail_a = f"opposing modals over shared subject(s) [{shared_str}] with {b.id}"
            detail_b = f"opposing modals over shared subject(s) [{shared_str}] with {a.id}"
            findings.append(Finding(a.id, "consistency", detail_a))
            findings.append(Finding(b.id, "consistency", detail_b))
            question = (
                f"{a.id} and {b.id} assert mutually-exclusive constraints over "
                f"[{shared_str}] - which is authoritative?"
            )
            questions.append(OpenQuestion(a.id, question))
    return findings, questions


def apply_checks(
    reqs: list[Requirement], ext: Extensions,
) -> tuple[list[Finding], list[OpenQuestion]]:
    findings: list[Finding] = []
    questions: list[OpenQuestion] = []

    for r in reqs:
        for check in (
            _check_clarity, _check_testability, _check_completeness,
            _check_atomicity, _check_measurability, _check_ac_quality,
            _check_edge_cases, _check_negative_cases,
            _check_nfrs, _check_ambiguity, _check_automation_suitability,
        ):
            f = check(r)
            if f is not None:
                findings.append(f)
        for f in (
            _check_data_rules(r, ext),
            _check_roles_permissions(r, ext),
            _check_risk(r, ext),
        ):
            if f is not None:
                findings.append(f)

    dep_findings, dep_questions = _cross_check_dependencies(reqs)
    cons_findings, cons_questions = _cross_check_consistency(reqs)
    findings.extend(dep_findings)
    findings.extend(cons_findings)
    questions.extend(dep_questions)
    questions.extend(cons_questions)

    findings.sort(key=lambda f: (f.req_id, f.dimension, f.detail))
    return findings, questions


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def _render_review(
    reqs: list[Requirement],
    findings: list[Finding],
    questions: list[OpenQuestion],
) -> str:
    lines = ["# Requirements Review", ""]
    if not reqs:
        lines.append("_No requirements found in `documents/uploaded/`._")
        lines.append("")
        lines.append("Drop one or more Markdown files containing `REQ-NNN: ...` entries into")
        lines.append("`.test-commander/documents/uploaded/` and re-run `/tc:review-requirements`.")
        lines.append("")
        return "\n".join(lines)

    counts: dict[str, int] = {}
    for f in findings:
        counts[f.dimension] = counts.get(f.dimension, 0) + 1

    lines.append("## Executive summary")
    lines.append("")
    lines.append(f"- Requirements parsed: **{len(reqs)}**")
    lines.append(f"- Findings: **{len(findings)}** across **{len(counts)}** dimensions")
    lines.append(f"- Open questions: **{len(questions)}**")
    lines.append("")
    if counts:
        lines.append("Findings per dimension:")
        lines.append("")
        for dim in sorted(counts.keys()):
            lines.append(f"- `{dim}`: {counts[dim]}")
        lines.append("")

    lines.append("## Findings")
    lines.append("")
    lines.append("| Requirement | Dimension | Trigger |")
    lines.append("| --- | --- | --- |")
    for f in findings:
        detail = f.detail.replace("|", "\\|")
        lines.append(f"| {f.req_id} | `{f.dimension}` | {detail} |")
    lines.append("")

    lines.append("## Per-requirement detail")
    lines.append("")
    findings_by_req: dict[str, list[Finding]] = {}
    for f in findings:
        findings_by_req.setdefault(f.req_id, []).append(f)
    for r in reqs:
        lines.append(f"### {r.id}")
        lines.append("")
        lines.append(f"_Source: `{r.source_file}`_")
        lines.append("")
        lines.append("> " + r.body.replace("\n", "\n> "))
        lines.append("")
        req_findings = findings_by_req.get(r.id, [])
        if req_findings:
            lines.append("**Findings:**")
            lines.append("")
            for f in req_findings:
                lines.append(f"- `{f.dimension}` — {f.detail}")
            lines.append("")
        else:
            lines.append("_No mechanical findings. Review with judgment._")
            lines.append("")

    if questions:
        lines.append("## Open questions")
        lines.append("")
        for q in questions:
            lines.append(f"- [{q.req_id}] {q.text}")
        lines.append("")

    lines.append("## Traceability")
    lines.append("")
    lines.append("Parsed requirement IDs (document order):")
    lines.append("")
    lines.append(", ".join(r.id for r in reqs))
    lines.append("")
    return "\n".join(lines)


def _render_inventory(reqs: list[Requirement]) -> str:
    lines = ["# Requirements Inventory", ""]
    if not reqs:
        lines.append("_No requirements parsed yet._")
        lines.append("")
        return "\n".join(lines)
    lines.append(f"Total: **{len(reqs)}** (in document order).")
    lines.append("")
    lines.append("| ID | Source | Body |")
    lines.append("| --- | --- | --- |")
    for r in reqs:
        body = r.body.replace("\n", " ").replace("|", "\\|")
        if len(body) > 120:
            body = body[:117] + "..."
        lines.append(f"| {r.id} | `{r.source_file}` | {body} |")
    lines.append("")
    return "\n".join(lines)


def _append_open_questions(path: Path, questions: list[OpenQuestion]) -> None:
    """Append new questions to open-questions.md, deduplicated by key."""
    header = (
        "# Open Questions\n\n"
        "Auto-generated by `/tc:review-requirements`. Each entry is a "
        "`[REQ-NNN] question text` line. The helper deduplicates by "
        "(REQ-NNN, text), so re-runs are safe.\n"
    )
    existing = ""
    if path.is_file():
        existing = path.read_text(encoding="utf-8")
    if "# Open Questions" not in existing:
        # Replace the template placeholder; preserve any other content the user added.
        existing = header + "\n"

    existing_keys: set[str] = set()
    for ln in existing.splitlines():
        m = re.match(r"-\s*\[(REQ-\d+)\]\s*(.*)$", ln.strip())
        if m:
            existing_keys.add(f"{m.group(1)}|{m.group(2).strip()}")

    new_lines: list[str] = []
    for q in questions:
        if q.key() in existing_keys:
            continue
        existing_keys.add(q.key())
        new_lines.append(f"- [{q.req_id}] {q.text}")

    if not new_lines and existing.endswith("\n"):
        path.write_text(existing, encoding="utf-8")
        return

    if not existing.endswith("\n"):
        existing += "\n"
    if new_lines:
        if not existing.rstrip().endswith("## Open"):
            existing += "\n"
        existing += "\n".join(new_lines) + "\n"
    path.write_text(existing, encoding="utf-8")


# ---------------------------------------------------------------------------
# Top-level entry
# ---------------------------------------------------------------------------

def review(project_root: Path) -> ReviewResult:
    """Run the review pipeline against a project root containing `.test-commander/`."""
    project_root = Path(project_root)
    workspace = project_root / WORKSPACE_DIRNAME
    if not workspace.is_dir():
        raise UninitializedWorkspaceError(
            f"workspace not found: {workspace} (run /tc:init first)"
        )

    reqs, collisions = parse_workspace(workspace)
    if collisions:
        first = next(iter(collisions))
        files = collisions[first]
        raise RequirementCollisionError(
            f"duplicate {first} declared in: {', '.join(files)}"
        )

    ext = load_extensions(workspace)
    findings, questions = apply_checks(reqs, ext)

    requirements_dir = workspace / "requirements"
    requirements_dir.mkdir(parents=True, exist_ok=True)

    review_path = requirements_dir / "requirements-review.md"
    inventory_path = requirements_dir / "requirements-inventory.md"
    open_q_path = requirements_dir / "open-questions.md"

    review_path.write_text(_render_review(reqs, findings, questions), encoding="utf-8")
    inventory_path.write_text(_render_inventory(reqs), encoding="utf-8")
    _append_open_questions(open_q_path, questions)

    return ReviewResult(
        workspace=workspace,
        requirements_count=len(reqs),
        findings=findings,
        open_questions=questions,
        review_path=review_path,
        inventory_path=inventory_path,
        open_questions_path=open_q_path,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Review requirements under .test-commander/documents/uploaded/ "
                    "and write the Phase 2 review artifacts.",
    )
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Path to the consuming project root (default: cwd).",
    )
    args = parser.parse_args(argv)

    try:
        result = review(Path(args.project_root))
    except UninitializedWorkspaceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except RequirementCollisionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"workspace:        {result.workspace}")
    print(f"requirements:     {result.requirements_count}")
    print(f"findings:         {len(result.findings)}")
    print(f"open questions:   {len(result.open_questions)}")
    print(f"review:           {result.review_path}")
    print(f"inventory:        {result.inventory_path}")
    print(f"open-questions:   {result.open_questions_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
