#!/usr/bin/env python3
"""Stamp and verify HANDOFF.md against deterministic Git workspace state."""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

PASS = 0
STALE = 2
REVIEW_REQUIRED = 3

COMMIT_RE = re.compile(r"(?im)^-\s*Snapshot commit:\s*`?([^`\s]+)`?\s*$")
FINGERPRINT_RE = re.compile(r"(?im)^-\s*Workspace fingerprint:\s*`?([^`\s]+)`?\s*$")
VALID_FINGERPRINT_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class GitError(RuntimeError):
    """Raised when git state cannot be inspected safely."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("stamp", "check", "snapshot"),
        help="stamp HANDOFF.md, check it, or print the current freshness anchors",
    )
    parser.add_argument(
        "--handoff",
        default="HANDOFF.md",
        help="Repository-relative handoff path (default: HANDOFF.md).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Repository root. Defaults to git rev-parse --show-toplevel from the current directory.",
    )
    return parser.parse_args(argv)


def run_git(root: Path | None, args: list[str]) -> bytes:
    command = ["git"]
    if root is not None:
        command.extend(["-C", str(root)])
    command.extend(args)
    try:
        result = subprocess.run(command, capture_output=True, check=True)
    except OSError as exc:
        raise GitError(f"unable to run git: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace").strip()
        detail = f": {stderr}" if stderr else ""
        raise GitError(f"git {' '.join(args)} failed{detail}") from exc
    return result.stdout


def resolve_root(explicit_root: Path | None) -> Path:
    if explicit_root is not None:
        root = explicit_root.resolve()
        run_git(root, ["rev-parse", "--show-toplevel"])
        return root
    output = run_git(None, ["rev-parse", "--show-toplevel"])
    return Path(output.decode("utf-8").strip()).resolve()


def normalize_handoff_path(raw_path: str) -> str:
    candidate = raw_path.strip().replace("\\", "/")
    pure = PurePosixPath(candidate)
    if not candidate or pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError("--handoff must be a safe repository-relative path")
    return pure.as_posix()


def current_commit(root: Path) -> str:
    return run_git(root, ["rev-parse", "HEAD"]).decode("ascii").strip()


def update_hash(hasher: Any, label: bytes, payload: bytes) -> None:
    hasher.update(label)
    hasher.update(len(payload).to_bytes(8, "big"))
    hasher.update(payload)


def workspace_fingerprint(root: Path, handoff_path: str) -> str:
    """Hash index state, unstaged diff, and untracked files, excluding the handoff itself."""
    hasher = hashlib.sha256()
    handoff_bytes = os.fsencode(handoff_path)

    index_output = run_git(root, ["ls-files", "--stage", "-z"])
    for record in index_output.split(b"\0"):
        if not record:
            continue
        try:
            metadata, path = record.split(b"\t", 1)
        except ValueError as exc:
            raise GitError("unable to parse git index state") from exc
        if path == handoff_bytes:
            continue
        update_hash(hasher, b"index\0", metadata + b"\t" + path)

    diff_output = run_git(
        root,
        [
            "diff",
            "--binary",
            "--no-ext-diff",
            "--",
            ".",
            f":(exclude){handoff_path}",
        ],
    )
    update_hash(hasher, b"worktree-diff\0", diff_output)

    untracked_output = run_git(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    untracked_paths = sorted(path for path in untracked_output.split(b"\0") if path)
    for path_bytes in untracked_paths:
        if path_bytes == handoff_bytes:
            continue
        relative = os.fsdecode(path_bytes)
        absolute = root / relative
        update_hash(hasher, b"untracked-path\0", path_bytes)
        try:
            if absolute.is_symlink():
                update_hash(hasher, b"symlink\0", os.fsencode(os.readlink(absolute)))
            elif absolute.is_file():
                file_hash = hashlib.sha256()
                with absolute.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        file_hash.update(chunk)
                update_hash(hasher, b"file\0", file_hash.digest())
            else:
                update_hash(hasher, b"missing\0", b"")
        except OSError as exc:
            raise GitError(f"unable to hash untracked path {relative}: {exc}") from exc

    return f"sha256:{hasher.hexdigest()}"


def read_anchors(path: Path) -> tuple[str | None, str | None]:
    text = path.read_text(encoding="utf-8")
    commit_match = COMMIT_RE.search(text)
    fingerprint_match = FINGERPRINT_RE.search(text)
    commit = commit_match.group(1) if commit_match else None
    fingerprint = fingerprint_match.group(1) if fingerprint_match else None
    return commit, fingerprint


def replace_anchor(text: str, pattern: re.Pattern[str], label: str, value: str) -> str:
    if not pattern.search(text):
        raise ValueError(f"missing freshness anchor: {label}")
    return pattern.sub(f"- {label}: `{value}`", text, count=1)


def stamp_handoff(root: Path, handoff_path: str) -> int:
    path = root / handoff_path
    if not path.is_file():
        print(f"HANDOFF FRESHNESS: REVIEW_REQUIRED\n- missing handoff: {handoff_path}", file=sys.stderr)
        return REVIEW_REQUIRED

    commit = current_commit(root)
    fingerprint = workspace_fingerprint(root, handoff_path)
    text = path.read_text(encoding="utf-8")
    try:
        text = replace_anchor(text, COMMIT_RE, "Snapshot commit", commit)
        text = replace_anchor(text, FINGERPRINT_RE, "Workspace fingerprint", fingerprint)
    except ValueError as exc:
        print(f"HANDOFF FRESHNESS: REVIEW_REQUIRED\n- {exc}", file=sys.stderr)
        return REVIEW_REQUIRED

    path.write_text(text, encoding="utf-8")
    print("HANDOFF FRESHNESS: STAMPED")
    print(f"- snapshot commit: {commit}")
    print(f"- workspace fingerprint: {fingerprint}")
    return PASS


def check_handoff(root: Path, handoff_path: str) -> int:
    path = root / handoff_path
    if not path.is_file():
        print(f"HANDOFF FRESHNESS: REVIEW_REQUIRED\n- missing handoff: {handoff_path}")
        return REVIEW_REQUIRED

    try:
        snapshot_commit, snapshot_fingerprint = read_anchors(path)
    except OSError as exc:
        print(f"HANDOFF FRESHNESS: REVIEW_REQUIRED\n- unable to read {handoff_path}: {exc}")
        return REVIEW_REQUIRED

    if not snapshot_commit or snapshot_commit.lower() in {"_tbd_", "tbd"}:
        print("HANDOFF FRESHNESS: REVIEW_REQUIRED\n- missing or unstamped Snapshot commit")
        return REVIEW_REQUIRED
    if not snapshot_fingerprint or not VALID_FINGERPRINT_RE.fullmatch(snapshot_fingerprint):
        print("HANDOFF FRESHNESS: REVIEW_REQUIRED\n- missing or invalid Workspace fingerprint")
        return REVIEW_REQUIRED

    commit = current_commit(root)
    fingerprint = workspace_fingerprint(root, handoff_path)
    if fingerprint != snapshot_fingerprint:
        print("HANDOFF FRESHNESS: STALE")
        print("- workspace state changed after the handoff snapshot")
        print(f"- snapshot commit: {snapshot_commit}")
        print(f"- current commit: {commit}")
        print(f"- snapshot fingerprint: {snapshot_fingerprint}")
        print(f"- current fingerprint: {fingerprint}")
        print("- action: re-read live project state and regenerate HANDOFF.md before resuming")
        return STALE

    print("HANDOFF FRESHNESS: PASS")
    print(f"- snapshot commit: {snapshot_commit}")
    print(f"- current commit: {commit}")
    print("- workspace fingerprint matches")
    if commit != snapshot_commit:
        print("- note: HEAD moved, but non-handoff repository state still matches the snapshot")
    return PASS


def snapshot(root: Path, handoff_path: str) -> int:
    print(f"Snapshot commit: {current_commit(root)}")
    print(f"Workspace fingerprint: {workspace_fingerprint(root, handoff_path)}")
    return PASS


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        root = resolve_root(args.root)
        handoff_path = normalize_handoff_path(args.handoff)
        if args.command == "stamp":
            return stamp_handoff(root, handoff_path)
        if args.command == "check":
            return check_handoff(root, handoff_path)
        return snapshot(root, handoff_path)
    except (GitError, ValueError) as exc:
        print(f"HANDOFF FRESHNESS: REVIEW_REQUIRED\n- {exc}", file=sys.stderr)
        return REVIEW_REQUIRED


if __name__ == "__main__":
    raise SystemExit(main())
