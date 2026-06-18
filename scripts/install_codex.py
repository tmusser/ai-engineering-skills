#!/usr/bin/env python3
"""Install AI Engineering Skills for Codex."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from install_common import InstallerError, InstallerSpec, add_common_arguments, resolve_project_path, run_installer


def resolve_skill_target(args: argparse.Namespace) -> Path:
    if args.target == "user":
        return Path.home() / ".agents" / "skills"

    project_path = resolve_project_path(args)
    return project_path / ".agents" / "skills"


def resolve_support_root(args: argparse.Namespace) -> Path:
    if args.target == "user":
        return Path.home() / ".agents" / "ai-engineering-skills"

    project_path = resolve_project_path(args)
    return project_path / "docs" / "ai-engineering-skills"


SPEC = InstallerSpec(
    installer_id="codex",
    display_name="Codex",
    command_prefix="$",
    resolve_skill_target=resolve_skill_target,
    resolve_support_root=resolve_support_root,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install AI Engineering Skills into Codex skill folders."
    )
    add_common_arguments(
        parser,
        template_help="Also copy templates into a Codex-friendly support directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        return run_installer(SPEC, args)
    except InstallerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
