#!/usr/bin/env python3
"""/tc:learn-from-tests helper - Phase 3 Step 3.6.

Walks the configured tests source root (default ``<workspace>/documents/
uploaded/tests/``) and extracts:

- pytest-style files (``test_*.py``, ``*_test.py``) parsed by stdlib
  ``ast`` for every ``test_<name>`` function plus the set of identifier
  references each test body contains;
- Playwright spec files (``*.spec.ts``) detected by extension, counted
  by regex against ``test(`` calls, but not parsed in v1.

Writes:

- ``<workspace>/product-knowledge/tests-coverage.md`` - overwritten
  byte-deterministically.
- The ``## From tests`` section in ``entities.md`` - covered classes
  from ``code-derived-model.md`` (requires Step 3.4's helper to have
  run). ``user-journeys.md``, ``assumptions.md``, and
  ``business-rules.md`` are NOT touched.
- Gap-signal questions appended to
  ``<workspace>/requirements/open-questions.md`` with the ``[<kind>]``
  prefix and the Phase-2 ``(source-id, question-text)`` dedup
  contract:
  - ``unsupported-test-runner`` for every ``*.spec.ts`` (always);
  - ``untested-function`` for public functions in
    ``code-derived-model.md`` not referenced by any test (requires
    Step 3.4's helper to have run).
- ``<workspace>/product-knowledge/system-model.md`` regenerated via
  the shared ``synthesize_system_model.py`` helper.

Per D18 the helper ships inside the plugin. Per D19 the detection
patterns are universal cores; project-specific tuning happens
through ``tc-knowledge.tests:`` in ``<workspace>/config.yaml``.

Exit codes:
    0 - tests-coverage written.
    2 - uninitialized workspace.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import extract_knowledge_from_code as code_mod
import synthesize_system_model as synth_mod

WORKSPACE_DIRNAME = ".test-commander"
SOURCE_LABEL = "tests"

DEFAULT_SOURCE_ROOT = "documents/uploaded/tests"
DEFAULT_IGNORED_PATHS = ("__pycache__", ".git", ".venv", "node_modules")

PYTEST_PATTERNS = ("test_*.py", "*_test.py")
PLAYWRIGHT_PATTERNS = ("*.spec.ts",)

# Playwright spec body regex for counting test() calls without parsing TS.
PLAYWRIGHT_TEST_RE = re.compile(r"\btest\s*\(\s*['\"`]([^'\"`]+)['\"`]")


class TestsError(Exception):
    pass


class UninitializedWorkspaceError(TestsError):
    pass


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PytestFile:
    rel_path: str
    test_count: int


@dataclass(frozen=True)
class PlaywrightFile:
    rel_path: str
    test_count: int  # Best-effort by regex.


@dataclass(frozen=True)
class TestFunction:
    name: str
    source_file: str
    line: int
    referenced_symbols: tuple[str, ...]


@dataclass(frozen=True)
class GapSignal:
    kind: str
    description: str
    source_file: str | None
    line: int | None


@dataclass
class Extensions:
    source_root: str = DEFAULT_SOURCE_ROOT
    ignored_paths: tuple[str, ...] = DEFAULT_IGNORED_PATHS


@dataclass
class TestsFindings:
    pytest_files: list[PytestFile] = field(default_factory=list)
    playwright_files: list[PlaywrightFile] = field(default_factory=list)
    test_functions: list[TestFunction] = field(default_factory=list)
    referenced_symbols: set[str] = field(default_factory=set)
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
    """Read ``tc-knowledge.tests:`` extensions from ``<workspace>/config.yaml``.

    Tolerant indentation-based parser; falls back to documented defaults
    when keys are absent. Recognized keys: ``source-root``,
    ``ignored-paths``.
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
        if pending_key is not None and section == "tests":
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

        if indent == 4 and section == "tests":
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
    if key == "source-root":
        ext.source_root = items[0]
    elif key == "ignored-paths":
        ext.ignored_paths = tuple(items)


# ---------------------------------------------------------------------------
# Source discovery
# ---------------------------------------------------------------------------


def _is_ignored(path: Path, root: Path, ignored: Iterable[str]) -> bool:
    rel_parts = path.relative_to(root).parts
    return any(part in ignored for part in rel_parts)


def discover_pytest(root: Path, ignored: Iterable[str]) -> list[Path]:
    if not root.is_dir():
        return []
    found: dict[Path, None] = {}
    for pattern in PYTEST_PATTERNS:
        for path in sorted(root.rglob(pattern)):
            if not path.is_file():
                continue
            if _is_ignored(path, root, ignored):
                continue
            found[path] = None
    return list(found.keys())


def discover_playwright(root: Path, ignored: Iterable[str]) -> list[Path]:
    if not root.is_dir():
        return []
    found: list[Path] = []
    for pattern in PLAYWRIGHT_PATTERNS:
        for path in sorted(root.rglob(pattern)):
            if not path.is_file():
                continue
            if _is_ignored(path, root, ignored):
                continue
            found.append(path)
    return found


# ---------------------------------------------------------------------------
# Pytest AST extraction
# ---------------------------------------------------------------------------


def _collect_referenced_symbols(node: ast.AST) -> set[str]:
    """Return the set of ast.Name ids and ast.Attribute attr names used inside node."""
    symbols: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            symbols.add(child.id)
        elif isinstance(child, ast.Attribute):
            symbols.add(child.attr)
    return symbols


def extract_pytest(path: Path, rel_path: str) -> tuple[PytestFile, list[TestFunction]]:
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return PytestFile(rel_path=rel_path, test_count=0), []

    test_functions: list[TestFunction] = []
    for node in ast.walk(tree):
        is_def = isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        if is_def and node.name.startswith("test_"):
            symbols = _collect_referenced_symbols(node)
            test_functions.append(
                TestFunction(
                    name=node.name,
                    source_file=rel_path,
                    line=node.lineno,
                    referenced_symbols=tuple(sorted(symbols)),
                )
            )

    return (
        PytestFile(rel_path=rel_path, test_count=len(test_functions)),
        test_functions,
    )


# ---------------------------------------------------------------------------
# Playwright detection (count only; no parse in v1)
# ---------------------------------------------------------------------------


def extract_playwright(path: Path, rel_path: str) -> PlaywrightFile:
    text = path.read_text(encoding="utf-8")
    matches = PLAYWRIGHT_TEST_RE.findall(text)
    return PlaywrightFile(rel_path=rel_path, test_count=len(matches))


# ---------------------------------------------------------------------------
# Code cross-check
# ---------------------------------------------------------------------------


CODE_MODEL_GENERATED_MARKER = "Auto-generated by `/tc:learn-from-code`"


def _code_model_is_generated(workspace: Path) -> bool:
    target = workspace / "product-knowledge" / "code-derived-model.md"
    if not target.is_file():
        return False
    text = target.read_text(encoding="utf-8")
    if CODE_MODEL_GENERATED_MARKER not in text:
        return False
    return "no code source found" not in text.lower()


def detect_untested_functions(
    workspace: Path, referenced: set[str]
) -> tuple[list[GapSignal], list[str], list[str]]:
    """Cross-check parsed code against the set of symbols referenced by tests.

    Returns (gaps, covered_class_names, untested_class_names). When
    code-derived-model.md is not generated, returns ([], [], []).
    """
    if not _code_model_is_generated(workspace):
        return [], [], []

    # Reuse Step 3.4's parser to get structured classes + functions.
    ext = code_mod.load_extensions(workspace)
    findings = code_mod.aggregate(workspace, ext)

    gaps: list[GapSignal] = []
    for fn in findings.functions:
        plain_name = fn.name.split(".", 1)[1] if "." in fn.name else fn.name
        if plain_name.startswith("_"):
            continue
        if plain_name in referenced or fn.name in referenced:
            continue
        gaps.append(
            GapSignal(
                kind="untested-function",
                description=(
                    f"Public function '{fn.name}' in {fn.source_file} is not "
                    "referenced by any test"
                ),
                source_file=fn.source_file,
                line=fn.line,
            )
        )

    covered_classes: list[str] = []
    untested_classes: list[str] = []
    for cls in findings.classes:
        if cls.name in referenced:
            covered_classes.append(cls.name)
        else:
            untested_classes.append(cls.name)
    return gaps, sorted(set(covered_classes)), sorted(set(untested_classes))


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def aggregate(workspace: Path, ext: Extensions) -> tuple[TestsFindings, list[str], list[str]]:
    source_root = (workspace / ext.source_root).resolve()
    findings = TestsFindings()

    # Pytest files
    for path in discover_pytest(source_root, ext.ignored_paths):
        rel_path = str(path.relative_to(workspace))
        pyfile, test_fns = extract_pytest(path, rel_path)
        findings.pytest_files.append(pyfile)
        findings.test_functions.extend(test_fns)
        for fn in test_fns:
            findings.referenced_symbols.update(fn.referenced_symbols)

    # Playwright files
    for path in discover_playwright(source_root, ext.ignored_paths):
        rel_path = str(path.relative_to(workspace))
        findings.playwright_files.append(extract_playwright(path, rel_path))
        findings.gaps.append(
            GapSignal(
                kind="unsupported-test-runner",
                description=(
                    f"Playwright spec file {rel_path} detected but not parsed "
                    "in v1; only file-level counting is available"
                ),
                source_file=rel_path,
                line=1,
            )
        )

    # untested-function cross-check.
    untested_gaps, covered_classes, untested_classes = detect_untested_functions(
        workspace, findings.referenced_symbols
    )
    findings.gaps.extend(untested_gaps)
    return findings, covered_classes, untested_classes


# ---------------------------------------------------------------------------
# Per-source render (tests-coverage.md)
# ---------------------------------------------------------------------------


def render_tests_model(
    findings: TestsFindings,
    covered_classes: list[str],
    untested_classes: list[str],
) -> str:
    lines: list[str] = []
    lines.append("# Tests Coverage")
    lines.append("")
    lines.append(
        "Auto-generated by `/tc:learn-from-tests`. Re-running overwrites this "
        "file byte-deterministically. Edits will not survive a re-run."
    )
    lines.append("")

    if not findings.pytest_files and not findings.playwright_files:
        lines.append("## Source files")
        lines.append("")
        lines.append("_No tests found._")
        lines.append("")
        lines.append(
            "Default source root: `documents/uploaded/tests`. Configurable "
            "via `tc-knowledge.tests.source-root`. v1 parses pytest-style "
            "Python (`test_*.py`, `*_test.py`); Playwright spec files "
            "(`*.spec.ts`) are detected and counted but not parsed."
        )
        lines.append("")
        return "\n".join(lines).rstrip("\n") + "\n"

    # Source files summary
    lines.append("## Source files")
    lines.append("")
    lines.append("| File | Runner | Tests |")
    lines.append("| --- | --- | --- |")
    for pyfile in sorted(findings.pytest_files, key=lambda f: f.rel_path):
        lines.append(f"| {pyfile.rel_path} | pytest | {pyfile.test_count} |")
    for pwfile in sorted(findings.playwright_files, key=lambda f: f.rel_path):
        runner = "playwright (counted, not parsed)"
        lines.append(f"| {pwfile.rel_path} | {runner} | {pwfile.test_count} |")
    lines.append("")

    # Test functions
    lines.append("## Test functions")
    lines.append("")
    if findings.test_functions:
        lines.append("| Function | Source |")
        lines.append("| --- | --- |")
        for fn in sorted(findings.test_functions, key=lambda f: (f.source_file, f.line)):
            lines.append(f"| {fn.name} | {fn.source_file}:{fn.line} |")
    else:
        lines.append("_No pytest-style test functions extracted._")
    lines.append("")

    # Covered symbols (aggregate)
    lines.append("## Covered symbols (aggregate)")
    lines.append("")
    if findings.referenced_symbols:
        lines.append(
            "Identifiers referenced anywhere in any pytest test body. "
            "Compared against code-derived-model.md to drive the "
            "untested-function cross-check when available."
        )
        lines.append("")
        symbols = sorted(findings.referenced_symbols)
        lines.append(", ".join(f"`{s}`" for s in symbols))
    else:
        lines.append("_No symbols referenced by any test._")
    lines.append("")

    # Class coverage
    if covered_classes or untested_classes:
        lines.append("## Class coverage (vs code-derived-model.md)")
        lines.append("")
        if covered_classes:
            lines.append("**Covered classes:**")
            lines.append("")
            for name in covered_classes:
                lines.append(f"- {name}")
            lines.append("")
        if untested_classes:
            lines.append("**Classes not referenced by any test:**")
            lines.append("")
            for name in untested_classes:
                lines.append(f"- {name}")
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
# Cross-cutting render (entities only)
# ---------------------------------------------------------------------------


def render_tests_entities_section(covered_classes: list[str], untested_classes: list[str]) -> str:
    if not covered_classes and not untested_classes:
        return ""
    lines: list[str] = []
    for name in covered_classes:
        lines.append(f"- **{name}** - exercised by at least one test (confidence: covered)")
    for name in untested_classes:
        lines.append(f"- **{name}** - no test references the class (confidence: uncovered)")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Cross-cutting file IO (mirrors prior helpers)
# ---------------------------------------------------------------------------


CROSS_CUTTING_TITLES: dict[str, tuple[str, str]] = {
    "entities.md": (
        "Entities",
        "Cross-source entity index. Each `## From <source>` section is "
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
# Open-questions append (mirrors prior helpers' [kind] prefix convention)
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
        source_id = "tc-knowledge/learn-from-tests"
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
    findings, covered_classes, untested_classes = aggregate(workspace, ext)

    # 1. tests-coverage.md
    coverage = workspace / "product-knowledge" / "tests-coverage.md"
    coverage.parent.mkdir(parents=True, exist_ok=True)
    coverage.write_text(
        render_tests_model(findings, covered_classes, untested_classes),
        encoding="utf-8",
    )

    # 2. cross-cutting: entities only (when there's anything to write).
    update_cross_cutting(
        workspace,
        "entities.md",
        render_tests_entities_section(covered_classes, untested_classes),
    )

    # 3. open-questions
    append_open_questions(workspace, findings.gaps)

    # 4. synthesizer
    synth_mod.synthesize(project_root)

    return 0


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Extract test-coverage signal from pytest and Playwright sources "
            "under the configured root (default <workspace>/documents/"
            "uploaded/tests/) and populate <workspace>/product-knowledge/."
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
