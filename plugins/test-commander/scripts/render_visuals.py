#!/usr/bin/env python3
"""/tc:render-visuals - Phase 9 Step 9.6.

Walks ``<workspace>/visuals/mermaid/*.md``, extracts each Mermaid block, and
renders it to ``visuals/svg/<name>.svg`` and ``visuals/png/<name>.png`` via the
Mermaid CLI (``mmdc``).

This is the **only** command in tc-visualize that shells out. The real CLI
invocation is **refused under pytest** via the ``PYTEST_CURRENT_TEST`` guard (the
project's hermetic-boundary pattern, as in ``run_tests.py``), so the suite
asserts the Mermaid-block extraction and the planned output paths, never a
rendered binary. When the CLI is absent the command **degrades gracefully**: it
reports the missing CLI and exits 0 without rendering, so a missing ``mmdc``
never breaks a workflow.

Reuses the shared engine in ``visualize`` (workspace resolution + error types).
Per D18 the helper ships inside the plugin.

Exit codes:
    0 - rendered, or gracefully skipped because the CLI is absent.
    2 - precondition failure (uninitialized workspace or no Mermaid sources).
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess  # noqa: S404 - guarded; never reached under pytest
import sys
from dataclasses import dataclass, field
from pathlib import Path

import visualize

PYTEST_ENV_VAR = "PYTEST_CURRENT_TEST"
MERMAID_BLOCK_RE = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)


class RenderRefusedError(visualize.VisualizeError):
    pass


@dataclass
class RenderResult:
    rendered: list[Path] = field(default_factory=list)
    cli_missing: bool = False


def extract_mermaid(text: str) -> str | None:
    """Return the first Mermaid block body, or None if there is none."""
    m = MERMAID_BLOCK_RE.search(text)
    return m.group(1).strip() if m else None


def plan_visuals(workspace: Path) -> list[tuple[Path, Path, Path]]:
    """Plan (mermaid-source, svg-output, png-output) for every visuals/mermaid/*.md."""
    mermaid_dir = workspace / "visuals" / "mermaid"
    svg_dir = workspace / "visuals" / "svg"
    png_dir = workspace / "visuals" / "png"
    plans: list[tuple[Path, Path, Path]] = []
    for src in sorted(mermaid_dir.glob("*.md")) if mermaid_dir.is_dir() else []:
        plans.append((src, svg_dir / f"{src.stem}.svg", png_dir / f"{src.stem}.png"))
    return plans


def mmdc_available() -> bool:
    """Whether the Mermaid CLI (mmdc) is on PATH. Monkeypatched in tests."""
    return shutil.which("mmdc") is not None


def _invoke_mmdc(src: Path, out: Path) -> None:
    """Shell out to mmdc to render one diagram. Refused under pytest."""
    if os.environ.get(PYTEST_ENV_VAR):
        raise RenderRefusedError(
            "real Mermaid rendering refused under pytest (PYTEST_CURRENT_TEST is set); "
            "the suite asserts the Mermaid source and planned paths, never a binary"
        )
    out.parent.mkdir(parents=True, exist_ok=True)  # pragma: no cover
    subprocess.run(  # pragma: no cover
        ["mmdc", "-i", str(src), "-o", str(out)], check=True
    )


def render_visuals(project_root: Path) -> RenderResult:
    """Render every Mermaid source to SVG + PNG, or skip gracefully if no CLI."""
    workspace = visualize.workspace_dir(project_root)
    plans = plan_visuals(workspace)
    if not plans:
        raise visualize.MissingSourceError(
            "no Mermaid sources under visuals/mermaid/; run /tc:visualize first"
        )
    if not mmdc_available():
        return RenderResult(rendered=[], cli_missing=True)
    rendered: list[Path] = []
    for src, svg, png in plans:
        _invoke_mmdc(src, svg)
        _invoke_mmdc(src, png)
        rendered.extend([svg, png])
    return RenderResult(rendered=rendered, cli_missing=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render visuals/mermaid/*.md to SVG/PNG via the Mermaid CLI.",
    )
    parser.add_argument(
        "project_root", nargs="?", default=".", help="Project root (default: current directory)."
    )
    args = parser.parse_args(argv if argv is not None else None)
    project_root = Path(args.project_root).resolve()
    try:
        result = render_visuals(project_root)
    except visualize.VisualizeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if result.cli_missing:
        print(
            "mermaid CLI (mmdc) not found; skipped rendering. "
            "Install it via 'make install' (or 'npm install -g @mermaid-js/mermaid-cli')."
        )
        return 0
    print(f"rendered: {len(result.rendered)} file(s) under visuals/svg/ and visuals/png/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
