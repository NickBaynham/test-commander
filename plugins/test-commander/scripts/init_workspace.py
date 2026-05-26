#!/usr/bin/env python3
"""Initialize a Test Commander workspace inside a consuming project.

Copies the workspace template at `plugins/test-commander/templates/workspace/`
into `<project_root>/.test-commander/`. Idempotent: existing files in the
target are preserved (never overwritten); only missing files are created.

Per D18 the helper ships inside the plugin so consuming-project users can
invoke it after `claude plugin install`.

Exit codes:
    0  - workspace created or already present
    2  - invalid target (path exists and is not a directory)
"""

import argparse
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Resolve the bundled template relative to this script's location so the
# helper works whether running from the repo or from the installed plugin
# cache.
DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "workspace"
WORKSPACE_DIRNAME = ".test-commander"


@dataclass
class InitResult:
    workspace: Path
    created: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)


def init_workspace(
    project_root: Path,
    template_root: Path = DEFAULT_TEMPLATE,
) -> InitResult:
    """Copy the workspace template into `project_root/.test-commander/`.

    Idempotent. Existing destination files are skipped (recorded but not
    overwritten). Returns counts and paths.

    Raises:
        NotADirectoryError: target path exists and is not a directory.
        FileNotFoundError: template_root does not exist.
    """
    project_root = Path(project_root)
    template_root = Path(template_root)

    if project_root.exists() and not project_root.is_dir():
        raise NotADirectoryError(
            f"target {project_root} exists but is not a directory"
        )
    if not template_root.is_dir():
        raise FileNotFoundError(f"template not found at {template_root}")

    workspace = project_root / WORKSPACE_DIRNAME
    workspace.mkdir(parents=True, exist_ok=True)

    result = InitResult(workspace=workspace)
    for src in sorted(template_root.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(template_root)
        dest = workspace / rel
        if dest.exists():
            result.skipped.append(dest)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        result.created.append(dest)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Initialize a Test Commander workspace.",
    )
    parser.add_argument(
        "target",
        type=Path,
        nargs="?",
        default=Path.cwd(),
        help="Project root (default: current directory).",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE,
        help=f"Workspace template directory (default: bundled at {DEFAULT_TEMPLATE}).",
    )
    args = parser.parse_args(argv)

    try:
        result = init_workspace(args.target, template_root=args.template)
    except NotADirectoryError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    print(f"workspace: {result.workspace}")
    print(f"created:   {len(result.created)}")
    print(f"skipped:   {len(result.skipped)}")
    if result.created:
        print("\nNew files:")
        for path in result.created:
            print(f"  {path.relative_to(result.workspace)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
