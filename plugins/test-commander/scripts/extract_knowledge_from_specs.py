#!/usr/bin/env python3
"""/tc:learn-from-specs helper - Phase 3 Step 3.3.

Auto-detects OpenAPI 3 specs (``.yaml`` / ``.yml`` / ``.openapi.json``) and
Postman v2.1 collections (``*.postman_collection.json``) under
``<workspace>/documents/uploaded/`` and parses each into structured
``endpoints / schemas / auth-schemes`` findings with ``<path>:<line>``
provenance.

Writes:

- ``<workspace>/product-knowledge/spec-derived-model.md`` - overwritten
  byte-deterministically.
- The ``## From specs`` section in ``entities.md`` (endpoints contribute
  as resources) and ``business-rules.md`` (auth schemes contribute as
  rules). ``user-journeys.md`` and ``assumptions.md`` are NOT touched;
  specs have neither journeys nor inferred assumptions.
- Gap-signal questions appended to
  ``<workspace>/requirements/open-questions.md`` with the Phase-2
  ``(source-id, question-text)`` dedup contract.
- ``<workspace>/product-knowledge/system-model.md`` regenerated via the
  shared ``synthesize_system_model.py`` helper.

This helper mirrors Step 3.2's skeleton (per the helper-mirroring pattern
from Phase 2 Step 2.3's lesson). The differences from 3.2 concentrate in
source-format detection, the per-format extractors, and the gap
detectors.

Exit codes:
    0 - spec-derived-model written.
    2 - uninitialized workspace.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

# Local-package import; same convention 3.2 uses for the synthesizer.
import synthesize_system_model as synth_mod
import yaml

WORKSPACE_DIRNAME = ".test-commander"
SOURCE_LABEL = "specs"

OPENAPI_YAML_GLOBS = ("openapi.yaml", "openapi.yml", "*.openapi.yaml", "*.openapi.yml")
OPENAPI_JSON_GLOBS = ("openapi.json", "*.openapi.json")
POSTMAN_GLOBS = ("*.postman_collection.json",)

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "options", "head", "trace")


class SpecsError(Exception):
    pass


class UninitializedWorkspaceError(SpecsError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Endpoint:
    method: str
    path: str
    operation_id: str | None
    summary: str
    source_file: str
    line: int


@dataclass(frozen=True)
class Schema:
    name: str
    type_field: str | None
    ref: str | None
    source_file: str
    line: int


@dataclass(frozen=True)
class AuthScheme:
    name: str
    type_field: str
    scheme: str | None
    source_file: str
    line: int


@dataclass(frozen=True)
class GapSignal:
    kind: str
    description: str
    source_file: str | None
    line: int | None


@dataclass
class SpecFindings:
    sources: list[tuple[str, str]] = field(default_factory=list)  # (rel_path, kind)
    endpoints: list[Endpoint] = field(default_factory=list)
    schemas: list[Schema] = field(default_factory=list)
    auth_schemes: list[AuthScheme] = field(default_factory=list)
    gaps: list[GapSignal] = field(default_factory=list)


# ---------------------------------------------------------------------------
# IO + workspace resolution (mirrors 3.2)
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
# Source discovery
# ---------------------------------------------------------------------------


def discover_specs(uploaded: Path) -> list[tuple[Path, str]]:
    """Return [(path, kind), ...] for every detected spec. kind: openapi | postman."""
    if not uploaded.is_dir():
        return []
    found: dict[Path, str] = {}

    def collect(globs: tuple[str, ...], kind: str) -> None:
        for glob in globs:
            for path in uploaded.rglob(glob):
                if path.is_file() and path not in found:
                    found[path] = kind

    collect(OPENAPI_YAML_GLOBS, "openapi-yaml")
    collect(OPENAPI_JSON_GLOBS, "openapi-json")
    collect(POSTMAN_GLOBS, "postman")
    return sorted(found.items(), key=lambda pair: str(pair[0]))


# ---------------------------------------------------------------------------
# OpenAPI extraction
# ---------------------------------------------------------------------------


def _line_of(text: str, pattern: str, after_line: int = 0) -> int:
    """Best-effort line number of the first match of pattern in text, after
    ``after_line``. Returns 1 if no match.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines[after_line:], start=after_line + 1):
        if pattern in line:
            return i
    return 1


def _line_of_yaml_path_block(text: str, path: str, method: str | None = None) -> int:
    """Line number where a path or method block begins in an OpenAPI YAML."""
    lines = text.splitlines()
    path_line = 0
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith(f"{path}:"):
            path_line = i
            break
    if not path_line or method is None:
        return path_line or 1
    method_lower = method.lower()
    for i in range(path_line, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith(f"{method_lower}:"):
            return i + 1
    return path_line


def _line_of_named_block(text: str, parent: str, child: str) -> int:
    """Line number of ``<child>:`` inside the first occurrence of ``<parent>:``."""
    lines = text.splitlines()
    parent_line = 0
    for i, line in enumerate(lines, start=1):
        if line.lstrip().startswith(f"{parent}:") and (
            not line.lstrip().endswith(":") or len(line.strip()) == len(parent) + 1
        ):
            parent_line = i
            break
    if not parent_line:
        return 1
    for i in range(parent_line, len(lines)):
        if lines[i].lstrip().startswith(f"{child}:"):
            return i + 1
    return parent_line


def extract_openapi(path: Path, rel_path: str) -> SpecFindings:
    """Parse an OpenAPI 3 document (YAML or JSON) and extract findings."""
    text = path.read_text(encoding="utf-8")
    findings = SpecFindings()

    if path.suffix.lower() == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return findings
    else:
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError:
            return findings

    if not isinstance(data, dict):
        return findings

    # Endpoints
    paths = data.get("paths") or {}
    if isinstance(paths, dict):
        for spec_path, methods in paths.items():
            if not isinstance(methods, dict):
                continue
            for method, op in methods.items():
                if method.lower() not in HTTP_METHODS or not isinstance(op, dict):
                    continue
                op_id_raw = op.get("operationId")
                operation_id = op_id_raw if isinstance(op_id_raw, str) else None
                summary = op.get("summary") if isinstance(op.get("summary"), str) else ""
                line = _line_of_yaml_path_block(text, str(spec_path), method)
                findings.endpoints.append(
                    Endpoint(
                        method=method.upper(),
                        path=str(spec_path),
                        operation_id=operation_id,
                        summary=summary,
                        source_file=rel_path,
                        line=line,
                    )
                )

                # Gap: unspecified-status
                responses = op.get("responses")
                if not isinstance(responses, dict) or not responses:
                    findings.gaps.append(
                        GapSignal(
                            kind="unspecified-status",
                            description=(
                                f"Endpoint {method.upper()} {spec_path} declares no "
                                "responses; the spec does not document any status "
                                "code"
                            ),
                            source_file=rel_path,
                            line=line,
                        )
                    )
                elif set(responses.keys()) <= {"default"}:
                    findings.gaps.append(
                        GapSignal(
                            kind="unspecified-status",
                            description=(
                                f"Endpoint {method.upper()} {spec_path} declares only "
                                "a 'default' response; no explicit success or error "
                                "status is documented"
                            ),
                            source_file=rel_path,
                            line=line,
                        )
                    )

    # Schemas
    components = data.get("components") or {}
    schemas = components.get("schemas") if isinstance(components, dict) else None
    if isinstance(schemas, dict):
        for name, schema in schemas.items():
            if not isinstance(schema, dict):
                continue
            type_field = schema.get("type") if isinstance(schema.get("type"), str) else None
            ref = schema.get("$ref") if isinstance(schema.get("$ref"), str) else None
            line = _line_of_named_block(text, "schemas", name)
            findings.schemas.append(
                Schema(
                    name=name,
                    type_field=type_field,
                    ref=ref,
                    source_file=rel_path,
                    line=line,
                )
            )
            if type_field is None and ref is None:
                findings.gaps.append(
                    GapSignal(
                        kind="schema-without-type",
                        description=(
                            f"Schema '{name}' declares neither a 'type' nor a "
                            "'$ref'; the shape of values matching this schema is "
                            "ambiguous"
                        ),
                        source_file=rel_path,
                        line=line,
                    )
                )

    # Security schemes
    sec_schemes = (
        components.get("securitySchemes") if isinstance(components, dict) else None
    )
    if isinstance(sec_schemes, dict):
        for name, scheme in sec_schemes.items():
            if not isinstance(scheme, dict):
                continue
            type_field = scheme.get("type") if isinstance(scheme.get("type"), str) else ""
            scheme_field = scheme.get("scheme") if isinstance(scheme.get("scheme"), str) else None
            line = _line_of_named_block(text, "securitySchemes", name)
            findings.auth_schemes.append(
                AuthScheme(
                    name=name,
                    type_field=type_field,
                    scheme=scheme_field,
                    source_file=rel_path,
                    line=line,
                )
            )

    return findings


# ---------------------------------------------------------------------------
# Postman collection extraction
# ---------------------------------------------------------------------------


def _line_of_json_match(text: str, needle: str) -> int:
    for i, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return i
    return 1


def _walk_postman_items(items: list, parent_label: str = "") -> Iterable[tuple[str, dict]]:
    for item in items:
        if not isinstance(item, dict):
            continue
        label = item.get("name", "") if isinstance(item.get("name"), str) else ""
        full_label = f"{parent_label}/{label}".strip("/") if label else parent_label
        if isinstance(item.get("item"), list):
            yield from _walk_postman_items(item["item"], full_label)
            continue
        request = item.get("request")
        if isinstance(request, dict):
            yield full_label, request


def _postman_path_from_url(url) -> str:
    if isinstance(url, str):
        path_part = url.split("?", 1)[0]
        if "://" in path_part:
            after_scheme = path_part.split("://", 1)[1]
            path_part = "/" + after_scheme.split("/", 1)[1] if "/" in after_scheme else "/"
        elif not path_part.startswith("/"):
            path_part = "/" + path_part.lstrip("{}")
        return _strip_postman_variables(path_part)
    if isinstance(url, dict):
        segments = url.get("path")
        if isinstance(segments, list):
            joined = "/" + "/".join(str(seg) for seg in segments)
            return _strip_postman_variables(joined)
        raw = url.get("raw")
        if isinstance(raw, str):
            return _postman_path_from_url(raw)
    return "/"


def _strip_postman_variables(path: str) -> str:
    """Drop leading {{base_url}} style segments to leave just the path."""
    if path.startswith("/{{") and "}}" in path:
        rest = path.split("}}", 1)[1]
        return rest if rest.startswith("/") else "/" + rest
    return path


def extract_postman(path: Path, rel_path: str) -> SpecFindings:
    findings = SpecFindings()
    text = path.read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return findings
    if not isinstance(data, dict):
        return findings
    items = data.get("item")
    if not isinstance(items, list):
        return findings

    seen_auth: set[str] = set()
    for label, request in _walk_postman_items(items):
        method = request.get("method")
        if not isinstance(method, str):
            continue
        url = request.get("url")
        endpoint_path = _postman_path_from_url(url)
        line = _line_of_json_match(text, f'"name": "{label}"') if label else 1
        findings.endpoints.append(
            Endpoint(
                method=method.upper(),
                path=endpoint_path,
                operation_id=label or None,
                summary=label,
                source_file=rel_path,
                line=line,
            )
        )

        # Schemas from raw JSON body shape (top-level keys).
        body = request.get("body")
        if isinstance(body, dict) and body.get("mode") == "raw":
            raw = body.get("raw")
            if isinstance(raw, str) and raw.strip().startswith("{"):
                try:
                    shape = json.loads(raw)
                except json.JSONDecodeError:
                    shape = None
                if isinstance(shape, dict):
                    name = f"{label or method}Body".replace(" ", "")
                    keys = ", ".join(sorted(shape.keys()))
                    findings.schemas.append(
                        Schema(
                            name=name,
                            type_field="object",
                            ref=None,
                            source_file=rel_path,
                            line=_line_of_json_match(text, '"raw"'),
                        )
                    )
                    # Capture key set as an embedded note (no separate dataclass slot).
                    findings.schemas[-1].__dict__["_keys"] = keys

        # Auth-schemes: collect distinct request.auth.type values.
        auth = request.get("auth")
        if isinstance(auth, dict):
            auth_type = auth.get("type")
            if isinstance(auth_type, str) and auth_type not in seen_auth:
                seen_auth.add(auth_type)
                findings.auth_schemes.append(
                    AuthScheme(
                        name=f"postman-{auth_type}",
                        type_field=auth_type,
                        scheme=auth_type,
                        source_file=rel_path,
                        line=_line_of_json_match(text, f'"type": "{auth_type}"'),
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def aggregate(workspace: Path) -> SpecFindings:
    uploaded = documents_uploaded(workspace)
    sources = discover_specs(uploaded)
    findings = SpecFindings()
    for path, kind in sources:
        rel_path = str(path.relative_to(workspace))
        findings.sources.append((rel_path, kind))
        if kind == "postman":
            per = extract_postman(path, rel_path)
        else:
            per = extract_openapi(path, rel_path)
        findings.endpoints.extend(per.endpoints)
        findings.schemas.extend(per.schemas)
        findings.auth_schemes.extend(per.auth_schemes)
        findings.gaps.extend(per.gaps)
    return findings


# ---------------------------------------------------------------------------
# Per-source render (spec-derived-model.md)
# ---------------------------------------------------------------------------


def render_spec_model(findings: SpecFindings) -> str:
    lines: list[str] = []
    lines.append("# Spec-Derived Model")
    lines.append("")
    lines.append(
        "Auto-generated by `/tc:learn-from-specs`. Re-running overwrites this "
        "file byte-deterministically. Edits will not survive a re-run."
    )
    lines.append("")

    lines.append("## Source specs")
    lines.append("")
    if not findings.sources:
        lines.append("_No spec found in `documents/uploaded/`._")
        lines.append("")
        lines.append(
            "Recognized formats: `openapi.yaml`, `openapi.yml`, `*.openapi.json`, "
            "and Postman v2.1 collections (`*.postman_collection.json`). Auto-"
            "detected from the file extension."
        )
        lines.append("")
        return "\n".join(lines).rstrip("\n") + "\n"
    lines.append("| Path | Format |")
    lines.append("| --- | --- |")
    for rel_path, kind in findings.sources:
        lines.append(f"| {rel_path} | {kind} |")
    lines.append("")

    # Endpoints
    lines.append("## Endpoints")
    lines.append("")
    if findings.endpoints:
        lines.append("| Endpoint | Operation | Source |")
        lines.append("| --- | --- | --- |")
        for ep in sorted(
            findings.endpoints, key=lambda e: (e.path, e.method, e.line)
        ):
            op = ep.operation_id or ep.summary or ""
            lines.append(
                f"| {ep.method} {ep.path} | {op} | {ep.source_file}:{ep.line} |"
            )
    else:
        lines.append("_No endpoints extracted._")
    lines.append("")

    # Schemas
    lines.append("## Schemas")
    lines.append("")
    if findings.schemas:
        lines.append("| Schema | Type | $ref | Source |")
        lines.append("| --- | --- | --- | --- |")
        for schema in sorted(findings.schemas, key=lambda s: (s.name, s.source_file)):
            type_str = schema.type_field or ""
            ref_str = schema.ref or ""
            lines.append(
                f"| {schema.name} | {type_str} | {ref_str} | "
                f"{schema.source_file}:{schema.line} |"
            )
    else:
        lines.append("_No schemas extracted._")
    lines.append("")

    # Auth schemes
    lines.append("## Auth schemes")
    lines.append("")
    if findings.auth_schemes:
        lines.append("| Name | Type | Scheme | Source |")
        lines.append("| --- | --- | --- | --- |")
        for auth in sorted(
            findings.auth_schemes, key=lambda a: (a.name, a.source_file)
        ):
            scheme_str = auth.scheme or ""
            lines.append(
                f"| {auth.name} | {auth.type_field} | {scheme_str} | "
                f"{auth.source_file}:{auth.line} |"
            )
    else:
        lines.append("_No auth schemes extracted._")
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
# Cross-cutting section bodies (only entities + business-rules)
# ---------------------------------------------------------------------------


def _resource_from_path(spec_path: str) -> str:
    """Return the first non-templated segment of an HTTP path as the resource name."""
    for segment in spec_path.strip("/").split("/"):
        if segment and not segment.startswith("{"):
            return segment
    return spec_path


def render_specs_entities_section(findings: SpecFindings) -> str:
    if not findings.endpoints:
        return "_No endpoints extracted from specs._"
    # Group endpoints by resource name; show each as a single bullet with the
    # method list and the first citation.
    resources: dict[str, list[Endpoint]] = {}
    for ep in findings.endpoints:
        resources.setdefault(_resource_from_path(ep.path), []).append(ep)
    lines: list[str] = []
    for resource in sorted(resources):
        eps = resources[resource]
        first = min(eps, key=lambda e: (e.source_file, e.line))
        methods = sorted({e.method for e in eps})
        lines.append(
            f"- **{resource}** - resource exposing {', '.join(methods)} "
            f"({first.source_file}:{first.line})"
        )
    return "\n".join(lines)


def render_specs_rules_section(findings: SpecFindings) -> str:
    if not findings.auth_schemes:
        return "_No auth schemes extracted from specs._"
    lines: list[str] = []
    for auth in sorted(findings.auth_schemes, key=lambda a: (a.name, a.source_file)):
        scheme_str = f" ({auth.scheme})" if auth.scheme else ""
        lines.append(
            f"- Auth scheme **{auth.name}** of type {auth.type_field}{scheme_str} "
            f"applies to protected endpoints ({auth.source_file}:{auth.line})"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cross-cutting file IO with section-overwrite semantics
# (mirrors 3.2's update_cross_cutting; same shared SOURCE_ORDER)
# ---------------------------------------------------------------------------


CROSS_CUTTING_TITLES: dict[str, tuple[str, str]] = {
    "entities.md": (
        "Entities",
        "Cross-source entity index. Each `## From <source>` section is "
        "regenerated by its owning `/tc:learn-from-*` command; sections from "
        "other commands are preserved across re-runs.",
    ),
    "business-rules.md": (
        "Business Rules",
        "Cross-source business-rule index. Each `## From <source>` section is "
        "regenerated by its owning `/tc:learn-from-*` command; sections from "
        "other commands are preserved across re-runs.",
    ),
}

SOURCE_ORDER = ("documents", "specs", "code", "api", "tests")


def update_cross_cutting(workspace: Path, filename: str, section_body: str) -> None:
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
# Open-questions append (dedup, mirrors 3.2)
# ---------------------------------------------------------------------------


OPEN_QUESTIONS_HEADER = "# Open questions"


def append_open_questions(workspace: Path, gaps: list[GapSignal]) -> None:
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
        source_id = "tc-knowledge/learn-from-specs"
        question = gap.description.rstrip(".") + "."
        key = (source_id, question)
        if key in existing_set:
            continue
        existing_set.add(key)
        new_lines.append(f"- [{source_id}] {question}")

    if not new_lines:
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
    findings = aggregate(workspace)

    # 1. spec-derived-model.md
    spec_model = workspace / "product-knowledge" / "spec-derived-model.md"
    spec_model.parent.mkdir(parents=True, exist_ok=True)
    spec_model.write_text(render_spec_model(findings), encoding="utf-8")

    # 2. cross-cutting section-overwrites (entities + business-rules only)
    update_cross_cutting(workspace, "entities.md", render_specs_entities_section(findings))
    update_cross_cutting(
        workspace, "business-rules.md", render_specs_rules_section(findings)
    )

    # 3. open-questions
    append_open_questions(workspace, findings.gaps)

    # 4. synthesizer
    synth_mod.synthesize(project_root)

    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract knowledge from OpenAPI specs and Postman collections in "
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
