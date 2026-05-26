#!/usr/bin/env python3
"""Markdown link checker. Scans .md files in the repo and verifies relative-link targets exist."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", "dist", "build", ".pdm-build"}
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "tel:"))


def strip_fragment(target: str) -> str:
    return target.split("#", 1)[0]


def check_file(md_path: Path) -> list[str]:
    errors: list[str] = []
    text = md_path.read_text(encoding="utf-8")
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in LINK_RE.finditer(line):
            target = match.group(2).strip()
            if not target or is_external(target) or target.startswith("#"):
                continue
            target_path = strip_fragment(target)
            if not target_path:
                continue
            resolved = (md_path.parent / target_path).resolve()
            if not resolved.exists():
                rel = md_path.relative_to(REPO_ROOT)
                errors.append(f"{rel}: broken link -> {target}")
    return errors


def find_markdown_files() -> list[Path]:
    files: list[Path] = []
    for root, dirs, names in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            if name.endswith(".md"):
                files.append(Path(root) / name)
    files.sort()
    return files


def main() -> int:
    md_files = find_markdown_files()
    all_errors: list[str] = []
    for f in md_files:
        all_errors.extend(check_file(f))
    if all_errors:
        for err in all_errors:
            print(err)
        print(f"\n{len(all_errors)} broken link(s) across {len(md_files)} files.")
        return 1
    print(f"Checked {len(md_files)} files. No broken links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
