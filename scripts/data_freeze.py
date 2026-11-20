#!/usr/bin/env python3
"""Opt-in local data snapshots, provenance stamps, integrity checks and diffs."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

METADATA = ("source", "recipe", "environment")
ENTRY_KEYS = {"path", "role", "sha256", "bytes"}
MANIFEST_KEYS = {"schema_version", "created_at", "git", "files", "stamp", *METADATA}
MAX_TEXT_BYTES = 128_000


def digest(path: Path) -> tuple[str, int]:
    checksum = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            checksum.update(block)
            size += len(block)
    return checksum.hexdigest(), size


def safe_path(root: Path, value: str) -> Path:
    """Resolve portable relative file paths without following symlinks."""
    if root.is_symlink() or any(p.is_symlink() for p in root.parents):
        raise ValueError("path root traverses a symlink")
    path = PurePosixPath(value)
    if (not value or "\\" in value or ":" in value or path.is_absolute()
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise ValueError(f"unsafe relative path: {value!r}")
    result = root
    for part in path.parts:
        result = result / part
        if result.is_symlink():
            raise ValueError(f"symlink path: {value!r}")
    return result


def stamp(manifest: dict) -> str:
    payload = {key: manifest[key] for key in ("schema_version", "files", *METADATA)}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def git_state(root: Path) -> dict:
    def read(*args: str) -> str | None:
        result = subprocess.run(["git", "-C", str(root), *args],
                                text=True, capture_output=True, check=False)
        return result.stdout.strip() if result.returncode == 0 else None
    try:
        commit = read("rev-parse", "HEAD")
        status = read("status", "--porcelain")
    except OSError:
        commit, status = None, None
    return {"commit": commit, "dirty": None if status is None else bool(status)}


def freeze(root: Path, output: Path, inputs: list[str], context: list[str],
           metadata: dict) -> dict:
    # Validate the entire selection before creating a destination.
    rows = []
    seen = set()
    for role, paths in (("data", inputs), ("context", context)):
        for name in paths:
            source = safe_path(root, name)
            if name in seen:
                raise ValueError(f"duplicate selected path: {name}")
            if not source.is_file():
                raise ValueError(f"selected file missing: {name}")
            seen.add(name)
            rows.append((name, role, source))
    rows.sort()
    if output.exists() or output.is_symlink():
        raise ValueError(f"snapshot destination already exists: {output}")
    if any(parent.is_symlink() for parent in output.parents):
        raise ValueError("snapshot destination traverses a symlink")
    provenance = git_state(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive directory creation prevents concurrent freezes from replacing a snapshot.
    output.mkdir()
    try:
        manifest = {"schema_version": 1,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "git": provenance, **metadata, "files": []}
        for name, role, source in rows:
            target = safe_path(output / "files", name)
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as reader, target.open("xb") as writer:
                shutil.copyfileobj(reader, writer)
            checksum, size = digest(target)
            if digest(source) != (checksum, size):
                raise ValueError(f"source changed during capture: {name}; retry from stable inputs")
            manifest["files"].append({"path": name, "role": role,
                                      "sha256": checksum, "bytes": size})
        for row in manifest["files"]:
            if digest(safe_path(root, row["path"])) != (row["sha256"], row["bytes"]):
                raise ValueError(f"source changed during capture: {row['path']}")
        manifest["stamp"] = stamp(manifest)
        # Publish the manifest last. A partially written directory cannot pass check.
        with (output / "manifest.json").open("x", encoding="utf-8") as handle:
            json.dump(manifest, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        return {"status": "PASS", "snapshot": str(output), "stamp": manifest["stamp"],
                "files": len(rows)}
    except BaseException:
        shutil.rmtree(output)
        raise


def load_snapshot(snapshot: Path) -> tuple[dict, list[str]]:
    if snapshot.is_symlink() or any(p.is_symlink() for p in snapshot.parents):
        raise ValueError("snapshot path traverses a symlink")
    manifest_path = safe_path(snapshot, "manifest.json")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != MANIFEST_KEYS:
        raise ValueError("invalid snapshot manifest fields")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("unsupported snapshot schema")
    if any(not isinstance(data[k], str) or not data[k].strip() for k in METADATA):
        raise ValueError("source, recipe and environment must be nonempty strings")
    if not isinstance(data["created_at"], str):
        raise ValueError("invalid capture time")
    captured = datetime.fromisoformat(data["created_at"])
    if captured.tzinfo is None:
        raise ValueError("capture time must include timezone")
    git = data["git"]
    if (not isinstance(git, dict) or set(git) != {"commit", "dirty"}
            or (git["commit"] is not None and not isinstance(git["commit"], str))
            or (git["dirty"] is not None and type(git["dirty"]) is not bool)):
        raise ValueError("invalid git provenance")
    if not isinstance(data["files"], list) or not data["files"]:
        raise ValueError("snapshot must include data files")
    seen = set()
    has_data = False
    issues = []
    for row in data["files"]:
        if not isinstance(row, dict) or set(row) != ENTRY_KEYS:
            raise ValueError("invalid snapshot entry")
        name = row["path"]
        if not isinstance(name, str):
            raise ValueError("invalid entry path")
        target = safe_path(snapshot / "files", name)
        if name in seen or row["role"] not in ("data", "context"):
            raise ValueError("duplicate path or invalid role")
        seen.add(name)
        has_data |= row["role"] == "data"
        checksum = row["sha256"]
        if (not isinstance(checksum, str) or len(checksum) != 64
                or any(c not in "0123456789abcdef" for c in checksum)
                or type(row["bytes"]) is not int or row["bytes"] < 0):
            raise ValueError("invalid hash or byte count")
        if not target.is_file():
            issues.append(f"MISSING: {name}")
        elif digest(target) != (checksum, row["bytes"]):
            issues.append(f"CHANGED: {name}")
    if not has_data:
        raise ValueError("snapshot must include at least one data input")
    if data["stamp"] != stamp(data):
        issues.append("STAMP_MISMATCH")
    return data, issues


def check(snapshot: Path, root: Path | None) -> dict:
    data, issues = load_snapshot(snapshot)
    if root is not None:
        for row in data["files"]:
            target = safe_path(root, row["path"])
            if not target.is_file():
                issues.append(f"LIVE_MISSING: {row['path']}")
            elif digest(target) != (row["sha256"], row["bytes"]):
                issues.append(f"LIVE_CHANGED: {row['path']}")
    return {"status": "REVIEW_REQUIRED" if issues else "PASS",
            "stamp": data["stamp"], "issues": issues}


def compare(before: Path, after: Path, text: bool) -> dict:
    old, old_issues = load_snapshot(before)
    new, new_issues = load_snapshot(after)
    if old_issues or new_issues:
        return {"status": "REVIEW_REQUIRED",
                "issues": {"before": old_issues, "after": new_issues}}
    left = {row["path"]: row for row in old["files"]}
    right = {row["path"]: row for row in new["files"]}
    changes = []
    for name in sorted(left.keys() | right.keys()):
        if left.get(name) == right.get(name):
            continue
        kind = "added" if name not in left else "removed" if name not in right else "changed"
        change = {"path": name, "change": kind,
                  "before": left.get(name), "after": right.get(name)}
        if text and name in left and name in right:
            if max(left[name]["bytes"], right[name]["bytes"]) > MAX_TEXT_BYTES:
                change["text_diff_skipped"] = "file exceeds 128000 bytes"
            else:
                a = safe_path(before / "files", name).read_bytes()
                b = safe_path(after / "files", name).read_bytes()
                try:
                    if b"\0" in a or b"\0" in b:
                        raise UnicodeError("binary data")
                    lines = list(difflib.unified_diff(
                        a.decode("utf-8").splitlines(keepends=True),
                        b.decode("utf-8").splitlines(keepends=True),
                        fromfile="before/" + name, tofile="after/" + name))
                    change["text_diff"] = "".join(lines[:200])
                    change["text_diff_truncated"] = len(lines) > 200
                except UnicodeError:
                    change["text_diff_skipped"] = "binary or non-UTF-8 input"
        changes.append(change)
    metadata = {key: {"before": old[key], "after": new[key]}
                for key in METADATA if old[key] != new[key]}
    return {"status": "PASS", "before_stamp": old["stamp"], "after_stamp": new["stamp"],
            "changes": changes, "metadata_changes": metadata}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    sub = parser.add_subparsers(dest="command", required=True)
    capture = sub.add_parser("freeze", help="Copy explicitly selected inputs into a new snapshot")
    capture.add_argument("--root", type=Path, default=Path.cwd())
    capture.add_argument("--input", action="append", required=True)
    capture.add_argument("--context", action="append", default=[])
    capture.add_argument("--output", type=Path, required=True)
    for key in METADATA:
        capture.add_argument("--" + key, required=True)
    inspect = sub.add_parser("check", help="Check snapshot integrity and optionally live inputs")
    inspect.add_argument("snapshot", type=Path)
    inspect.add_argument("--live-root", type=Path)
    diff = sub.add_parser("diff", help="Compare two intact snapshots")
    diff.add_argument("before", type=Path)
    diff.add_argument("after", type=Path)
    diff.add_argument("--text", action="store_true", help="Include bounded UTF-8 diffs")
    args = parser.parse_args(argv)
    try:
        if args.command == "freeze":
            metadata = {k: getattr(args, k) for k in METADATA}
            if any(not value.strip() for value in metadata.values()):
                raise ValueError("provenance fields must be nonempty")
            result = freeze(args.root.resolve(), args.output.absolute(),
                            args.input, args.context, metadata)
        elif args.command == "check":
            result = check(args.snapshot.absolute(),
                           args.live_root.resolve() if args.live_root else None)
        else:
            result = compare(args.before.absolute(), args.after.absolute(), args.text)
    except (OSError, ValueError, TypeError) as exc:
        print(f"data freeze input error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"DATA FREEZE: {result['status']}")
        print(json.dumps({k: v for k, v in result.items() if k != "status"},
                         indent=2, ensure_ascii=False))
    return 3 if result["status"] == "REVIEW_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
