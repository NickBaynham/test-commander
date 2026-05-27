#!/usr/bin/env python3
"""/tc:learn-from-api helper - Phase 3 Step 3.5.

Recorded-playback mode (default) reads ``<workspace>/documents/uploaded/
recorded-api/responses.json`` (or the configured path) and extracts
``{method, path, status, headers, body}`` entries into structured findings.
Live mode (opt-in via ``tc-knowledge.api.mode: live``) issues real HTTP
requests against ``tc-knowledge.api.base-url``; pytest never enters live
mode - the helper refuses if ``PYTEST_CURRENT_TEST`` is in the
environment.

Writes:

- ``<workspace>/product-knowledge/api-model.md`` - overwritten
  byte-deterministically.
- The ``## From api`` section in ``entities.md`` (resources confirmed
  reachable at runtime) and ``business-rules.md`` (auth-required
  endpoints). ``user-journeys.md`` and ``assumptions.md`` are NOT
  touched.
- Gap-signal questions appended to
  ``<workspace>/requirements/open-questions.md`` with the ``[<kind>]``
  prefix and the Phase-2 ``(source-id, question-text)`` dedup contract.
- ``<workspace>/product-knowledge/system-model.md`` regenerated via
  the shared ``synthesize_system_model.py`` helper.

Per D18 the helper ships inside the plugin. Per D19 the dimension
detectors are universal cores; project-specific tuning happens
through ``tc-knowledge.api:`` in ``<workspace>/config.yaml``.

Exit codes:
    0 - api-model written.
    2 - uninitialized workspace, malformed config, or live mode under
        pytest.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import extract_knowledge_from_specs as specs_mod
import synthesize_system_model as synth_mod

WORKSPACE_DIRNAME = ".test-commander"
SOURCE_LABEL = "api"

DEFAULT_RECORDED_PATH = "documents/uploaded/recorded-api/responses.json"
PYTEST_ENV_VAR = "PYTEST_CURRENT_TEST"


class ApiError(Exception):
    pass


class UninitializedWorkspaceError(ApiError):
    pass


class LiveModeRefusedError(ApiError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Recording:
    method: str
    path: str
    status: int
    has_auth_header: bool
    response_keys: tuple[str, ...]  # top-level keys of the response body (JSON)
    source_file: str
    index: int  # 0-based index in the recordings list


@dataclass(frozen=True)
class GapSignal:
    kind: str
    description: str
    source_file: str | None
    line: int | None


@dataclass
class Extensions:
    mode: str = "recorded"
    recorded_path: str = DEFAULT_RECORDED_PATH
    base_url: str | None = None
    auth_header: str | None = None


@dataclass
class ApiFindings:
    recordings: list[Recording] = field(default_factory=list)
    auth_required: set[tuple[str, str]] = field(default_factory=set)
    gaps: list[GapSignal] = field(default_factory=list)


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
    """Read ``tc-knowledge.api:`` extensions from ``<workspace>/config.yaml``.

    Tolerant indentation-based parser; falls back to documented defaults
    when keys are absent.
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
        if pending_key is not None and section == "api":
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

        if indent == 4 and section == "api":
            commit()
            if ":" not in stripped:
                continue
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                if value.startswith("["):
                    items = _parse_inline_list(value)
                    _assign(ext, key, items)
                else:
                    _assign(ext, key, [value.strip("'\"")])
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
    if not items:
        return
    if key == "mode":
        ext.mode = items[0]
    elif key == "recorded-path":
        ext.recorded_path = items[0]
    elif key == "base-url":
        ext.base_url = items[0]
    elif key == "auth-header":
        ext.auth_header = items[0]


# ---------------------------------------------------------------------------
# Recorded-mode extraction
# ---------------------------------------------------------------------------


def _has_authorization_header(headers: object) -> bool:
    if not isinstance(headers, dict):
        return False
    return any(str(key).lower() == "authorization" for key in headers)


def _response_keys(body: object) -> tuple[str, ...]:
    if isinstance(body, dict):
        return tuple(sorted(str(k) for k in body))
    if isinstance(body, list) and body and isinstance(body[0], dict):
        # Treat top-level keys of the first element as the shape signature.
        return tuple(sorted(str(k) for k in body[0]))
    return ()


def load_recordings(workspace: Path, recorded_path: str) -> tuple[Path, list[dict]]:
    """Return (resolved_path, parsed_entries). Returns (path, []) when the
    recorded file is absent or fails to parse."""
    resolved = workspace / recorded_path
    if not resolved.is_file():
        return resolved, []
    try:
        data = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return resolved, []
    if not isinstance(data, list):
        return resolved, []
    return resolved, [entry for entry in data if isinstance(entry, dict)]


def extract_recordings(workspace: Path, ext: Extensions) -> ApiFindings:
    findings = ApiFindings()
    resolved, entries = load_recordings(workspace, ext.recorded_path)
    if not entries:
        return findings
    rel_path = str(resolved.relative_to(workspace))
    for index, entry in enumerate(entries):
        method = entry.get("method")
        path = entry.get("path")
        status = entry.get("status")
        if not isinstance(method, str) or not isinstance(path, str):
            continue
        if not isinstance(status, int):
            try:
                status = int(status)
            except (TypeError, ValueError):
                continue
        headers = entry.get("headers")
        has_auth = _has_authorization_header(headers)
        body = entry.get("body")
        keys = _response_keys(body)
        recording = Recording(
            method=method.upper(),
            path=path,
            status=status,
            has_auth_header=has_auth,
            response_keys=keys,
            source_file=rel_path,
            index=index,
        )
        findings.recordings.append(recording)

        # auth-required dimension: Authorization header present OR 401/403
        # response without one.
        if has_auth or status in (401, 403):
            findings.auth_required.add((recording.method, recording.path))

    return findings


# ---------------------------------------------------------------------------
# Spec cross-check
# ---------------------------------------------------------------------------


SPEC_MODEL_GENERATED_MARKER = "Auto-generated by `/tc:learn-from-specs`"


def _spec_model_is_generated(workspace: Path) -> bool:
    target = workspace / "product-knowledge" / "spec-derived-model.md"
    if not target.is_file():
        return False
    text = target.read_text(encoding="utf-8")
    if SPEC_MODEL_GENERATED_MARKER not in text:
        return False
    return "no spec found" not in text.lower()


def detect_spec_gaps(workspace: Path, recordings: list[Recording]) -> list[GapSignal]:
    """Cross-check recorded ``(method, path, status)`` against the spec model.

    Returns gaps when the spec model is generated; returns ``[]`` otherwise
    (cannot cross-check without a spec).
    """
    if not _spec_model_is_generated(workspace):
        return []

    # Reuse Step 3.3's parser to get structured endpoints with their
    # declared statuses.
    spec_findings = specs_mod.aggregate(workspace)
    spec_index: dict[tuple[str, str], tuple[str, ...]] = {
        (ep.method, ep.path): ep.statuses for ep in spec_findings.endpoints
    }

    gaps: list[GapSignal] = []
    for rec in recordings:
        key = (rec.method, rec.path)
        if key not in spec_index:
            gaps.append(
                GapSignal(
                    kind="unspecified-endpoint",
                    description=(
                        f"Recorded request {rec.method} {rec.path} returned "
                        f"status {rec.status} but the spec does not declare "
                        "this endpoint"
                    ),
                    source_file=rec.source_file,
                    line=rec.index + 1,
                )
            )
            continue
        declared = spec_index[key]
        if not declared:
            # Spec declares no responses for this endpoint - the
            # unspecified-status gap on the spec side already covers it.
            continue
        if str(rec.status) not in declared:
            gaps.append(
                GapSignal(
                    kind="mismatched-status",
                    description=(
                        f"Recorded request {rec.method} {rec.path} returned "
                        f"status {rec.status}; the spec declares {sorted(declared)} "
                        "for this endpoint"
                    ),
                    source_file=rec.source_file,
                    line=rec.index + 1,
                )
            )
    return gaps


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def aggregate(workspace: Path, ext: Extensions) -> ApiFindings:
    findings = extract_recordings(workspace, ext)
    findings.gaps.extend(detect_spec_gaps(workspace, findings.recordings))
    return findings


# ---------------------------------------------------------------------------
# Per-source render (api-model.md)
# ---------------------------------------------------------------------------


def _status_family(status: int) -> str:
    if 200 <= status < 300:
        return "2xx"
    if 300 <= status < 400:
        return "3xx"
    if 400 <= status < 500:
        return "4xx"
    if 500 <= status < 600:
        return "5xx"
    return "other"


def render_api_model(findings: ApiFindings) -> str:
    lines: list[str] = []
    lines.append("# API-Derived Model")
    lines.append("")
    lines.append(
        "Auto-generated by `/tc:learn-from-api`. Re-running overwrites this "
        "file byte-deterministically. Edits will not survive a re-run."
    )
    lines.append("")

    if not findings.recordings:
        lines.append("## Source recordings")
        lines.append("")
        lines.append("_No recorded API responses found._")
        lines.append("")
        lines.append(
            "Default recorded path: "
            "`documents/uploaded/recorded-api/responses.json`. Configure via "
            "`tc-knowledge.api.recorded-path` in `<workspace>/config.yaml`. "
            "Live mode is opt-in via `tc-knowledge.api.mode: live` and is "
            "refused under pytest."
        )
        lines.append("")
        return "\n".join(lines).rstrip("\n") + "\n"

    # Source
    lines.append("## Source recordings")
    lines.append("")
    source_file = findings.recordings[0].source_file
    lines.append("| Path | Entries |")
    lines.append("| --- | --- |")
    lines.append(f"| {source_file} | {len(findings.recordings)} |")
    lines.append("")

    # Live endpoints
    lines.append("## Live endpoints")
    lines.append("")
    lines.append("| Endpoint | Status | Family | Source |")
    lines.append("| --- | --- | --- | --- |")
    for rec in sorted(findings.recordings, key=lambda r: (r.path, r.method, r.index)):
        lines.append(
            f"| {rec.method} {rec.path} | {rec.status} | "
            f"{_status_family(rec.status)} | {rec.source_file}:{rec.index + 1} |"
        )
    lines.append("")

    # Response shapes
    lines.append("## Response shapes")
    lines.append("")
    shapes: dict[tuple[str, str], tuple[int, tuple[str, ...]]] = {}
    for rec in findings.recordings:
        if rec.response_keys:
            shapes[(rec.method, rec.path)] = (rec.status, rec.response_keys)
    if shapes:
        lines.append("| Endpoint | Status | Top-level keys |")
        lines.append("| --- | --- | --- |")
        for (method, path), (status, keys) in sorted(shapes.items()):
            lines.append(f"| {method} {path} | {status} | {', '.join(keys)} |")
    else:
        lines.append("_No JSON response bodies in the recordings._")
    lines.append("")

    # Auth-required
    lines.append("## Auth-required endpoints")
    lines.append("")
    if findings.auth_required:
        lines.append("Endpoints inferred to require authentication (request carried "
                     "an `Authorization` header OR response returned 401/403 without "
                     "one):")
        lines.append("")
        for method, path in sorted(findings.auth_required):
            lines.append(f"- **{method} {path}** - auth-required")
    else:
        lines.append("_No auth-required endpoints inferred from the recordings._")
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
# Cross-cutting render
# ---------------------------------------------------------------------------


def _resource_from_path(spec_path: str) -> str:
    for segment in spec_path.strip("/").split("/"):
        if segment and not segment.startswith("{"):
            return segment
    return spec_path


def render_api_entities_section(findings: ApiFindings) -> str:
    if not findings.recordings:
        return ""
    by_resource: dict[str, list[Recording]] = {}
    for rec in findings.recordings:
        by_resource.setdefault(_resource_from_path(rec.path), []).append(rec)
    lines: list[str] = []
    for resource in sorted(by_resource):
        recs = by_resource[resource]
        methods = sorted({r.method for r in recs})
        first = min(recs, key=lambda r: r.index)
        lines.append(
            f"- **{resource}** - confirmed reachable; observed methods "
            f"{', '.join(methods)} ({first.source_file}:{first.index + 1})"
        )
    return "\n".join(lines)


def render_api_rules_section(findings: ApiFindings) -> str:
    if not findings.auth_required:
        return ""
    lines: list[str] = []
    for method, path in sorted(findings.auth_required):
        lines.append(
            f"- Endpoint **{method} {path}** requires authentication "
            "(inferred from recorded `Authorization` header or 401/403 "
            "response without one)"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cross-cutting file IO (mirrors 3.2/3.3/3.4)
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
# Open-questions append (mirrors 3.4's [kind] prefix convention)
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
        source_id = "tc-knowledge/learn-from-api"
        question = f"[{gap.kind}] {gap.description.rstrip('.')}."
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
    ext = load_extensions(workspace)

    # Live mode refusal under pytest. The helper detects pytest via the
    # PYTEST_CURRENT_TEST env var (pytest sets it for every test); refuses
    # before issuing any network call. v1 does not yet implement live
    # probing; only recorded mode is reachable.
    if ext.mode == "live":
        if os.environ.get(PYTEST_ENV_VAR):
            raise LiveModeRefusedError(
                "live mode refused under pytest (PYTEST_CURRENT_TEST is set); "
                "use mode: recorded for tests"
            )
        raise LiveModeRefusedError(
            "live mode is not implemented in v1; use mode: recorded"
        )

    findings = aggregate(workspace, ext)

    # 1. api-model.md
    api_model = workspace / "product-knowledge" / "api-model.md"
    api_model.parent.mkdir(parents=True, exist_ok=True)
    api_model.write_text(render_api_model(findings), encoding="utf-8")

    # 2. cross-cutting: entities + business-rules only (when non-empty bodies).
    update_cross_cutting(
        workspace, "entities.md", render_api_entities_section(findings)
    )
    update_cross_cutting(
        workspace, "business-rules.md", render_api_rules_section(findings)
    )

    # 3. open-questions
    append_open_questions(workspace, findings.gaps)

    # 4. synthesizer
    synth_mod.synthesize(project_root)

    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract knowledge from recorded API responses in "
            "<workspace>/documents/uploaded/recorded-api/ and populate "
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
    except LiveModeRefusedError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
