#!/usr/bin/env python3
"""Optional reviewed file-purpose ledger: propose, query, and check.

This is navigation metadata, never a substitute for source reads, authority,
the context-section index, or a fresh-session handoff trust check.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

DEFAULT_LEDGER = Path(".ai-context/file-ledger.json")
VERSION = 1
MAX_ENTRIES = 500
MAX_BYTES = 2_000_000
MAX_FILE_BYTES = 32_000_000
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
WORDS = re.compile(r"[a-z0-9]+")
KINDS = {"contract", "evidence", "continuation", "decision", "test",
         "guidance", "implementation", "other"}
FIELDS = {"path", "kind", "purpose", "use_when", "related", "sha256"}
STOPWORDS = {"a", "an", "and", "by", "for", "in", "of", "on", "or", "the", "to",
             "with", "work", "fix", "file"}
TRACKED_TYPES = {".py", ".md", ".js", ".jsx", ".ts", ".tsx", ".json",
                 ".yml", ".yaml", ".toml", ".sh", ".sql", ".rs", ".go"}
EXCLUDE_DIRS = {".git", ".ai-context", "__pycache__", "node_modules", "vendor",
                "dist", "build", "generated"}
SECRET_NAMES = {".env", ".env.local", "credentials.json", "secrets.json"}


def source_path(root: Path, raw: str, *, require_file: bool) -> Path:
    """Reject traversal, symlink traversal and files outside the working root."""
    if not isinstance(raw, str) or not raw or "\\" in raw:
        raise ValueError(f"unsafe file ledger path: {raw!r}")
    p = PurePosixPath(raw)
    if p.is_absolute() or p.as_posix() != raw or any(
        part in {"", ".", ".."} for part in raw.split("/")
    ):
        raise ValueError(f"unsafe file ledger path: {raw!r}")
    target = root
    for part in p.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError(f"file ledger path traverses symlink: {raw}")
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"file ledger path escapes root: {raw}")
    if require_file and not target.is_file():
        raise ValueError(f"not a regular file: {raw}")
    if target.exists() and not target.is_file():
        raise ValueError(f"not a regular file: {raw}")
    return target


def file_hash(path: Path) -> str:
    """Hash bytes without copying source contents to the ledger."""
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f"file too large to index (>32 MB): {path.name}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(131072), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def kind_hint(raw: str) -> str:
    """Filename convention only; it does not establish actual authority."""
    name = PurePosixPath(raw).name.casefold()
    if name == "spec.md":
        return "contract"
    if name == "verify.md":
        return "evidence"
    if name == "handoff.md":
        return "continuation"
    if name == "decisions.md":
        return "decision"
    if raw.startswith("tests/") or name.startswith("test_"):
        return "test"
    if name.endswith(".md"):
        return "guidance"
    if PurePosixPath(raw).suffix.lower() in {".py", ".js", ".jsx", ".ts",
                                               ".tsx", ".go", ".rs", ".sql", ".sh"}:
        return "implementation"
    return "other"


def discover_tracked(root: Path) -> list[str]:
    """Discover only version-controlled text-like paths, never untracked files."""
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached"],
        capture_output=True, check=False,
    )
    if result.returncode:
        raise ValueError("cannot discover tracked files; use --path in a non-git project")
    found: list[str] = []
    for token in result.stdout.split(b"\0"):
        if not token:
            continue
        try:
            raw = token.decode("utf-8")
        except UnicodeDecodeError:
            continue
        p = PurePosixPath(raw)
        if (set(p.parts) & EXCLUDE_DIRS or p.name.casefold() in SECRET_NAMES
                or p.name.casefold().startswith(".env.")
                or p.suffix.lower() not in TRACKED_TYPES):
            continue
        try:
            file = source_path(root, raw, require_file=True)
            if file.stat().st_size > MAX_FILE_BYTES:
                continue
        except (OSError, ValueError):
            continue
        found.append(raw)
    return sorted(set(found))


def read_ledger(path: Path, root: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"file ledger not found: {path}")
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("file ledger exceeds 2 MB")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"file ledger must be UTF-8 JSON: {exc}") from exc
    if not isinstance(data, dict) or set(data) != {"schema_version", "approved", "entries"}:
        raise ValueError("file ledger must have exactly schema_version, approved, entries")
    if type(data["schema_version"]) is not int or data["schema_version"] != VERSION:
        raise ValueError("unsupported file ledger schema version")
    if type(data["approved"]) is not bool:
        raise ValueError("approved must be boolean")
    entries = data["entries"]
    if not isinstance(entries, list) or not entries or len(entries) > MAX_ENTRIES:
        raise ValueError(f"entries must contain 1-{MAX_ENTRIES} file records")
    seen: set[str] = set()
    for row in entries:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ValueError("each file record must contain exactly the six documented fields")
        raw = row["path"]
        source_path(root, raw, require_file=False)
        if raw in seen:
            raise ValueError(f"duplicate file ledger path: {raw}")
        seen.add(raw)
        if row["kind"] not in KINDS:
            raise ValueError(f"unknown file kind: {raw}")
        purpose = row["purpose"]
        if not isinstance(purpose, str) or len(purpose) > 500:
            raise ValueError(f"invalid file purpose: {raw}")
        for field in ("use_when", "related"):
            values = row[field]
            if (not isinstance(values, list) or len(values) > 32
                    or any(not isinstance(v, str) or not v.strip() or len(v) > 160 for v in values)
                    or len(set(values)) != len(values)):
                raise ValueError(f"invalid {field} for {raw}")
        for reference in row["related"]:
            source_path(root, reference, require_file=False)
            if reference == raw:
                raise ValueError(f"file cannot reference itself: {raw}")
        if not isinstance(row["sha256"], str) or not DIGEST.fullmatch(row["sha256"]):
            raise ValueError(f"invalid sha256 for {raw}")
    return data


def propose(root: Path, paths: list[str], tracked: bool, previous: Path | None) -> dict:
    previous_rows: dict[str, dict] = {}
    if previous is not None:
        prior = read_ledger(previous, root)
        previous_rows = {row["path"]: row for row in prior["entries"]}
    if tracked:
        paths = [*paths, *discover_tracked(root)]
    paths = sorted(set(paths) | set(previous_rows))
    if not paths:
        raise ValueError("propose requires --path, --tracked, or --from-ledger")
    if len(paths) > MAX_ENTRIES:
        raise ValueError(f"proposal has {len(paths)} files; select at most {MAX_ENTRIES} relevant files")
    output = []
    for raw in paths:
        target = source_path(root, raw, require_file=raw not in previous_rows)
        prior = previous_rows.get(raw)
        # Preserve a missing previously recorded file for human review, never erase it.
        digest = file_hash(target) if target.is_file() else prior["sha256"]
        output.append({
            "path": raw,
            "kind": prior["kind"] if prior else kind_hint(raw),
            "purpose": prior["purpose"] if prior else "",
            "use_when": prior["use_when"] if prior else [],
            "related": prior["related"] if prior else [],
            "sha256": digest,
        })
    return {"schema_version": VERSION, "approved": False, "entries": output}


def freshness(root: Path, row: dict) -> str:
    """Per-file freshness so unrelated changes do not invalidate a query."""
    target = source_path(root, row["path"], require_file=False)
    if not target.is_file():
        return "MISSING"
    try:
        return "CURRENT" if file_hash(target) == row["sha256"] else "STALE"
    except (OSError, ValueError):
        return "UNREADABLE"


def content_issues(row: dict) -> list[str]:
    issues = []
    if not row["purpose"].strip() or row["purpose"].strip().lower() in {"tbd", "_tbd_"}:
        issues.append(f"{row['path']}: purpose not reviewed")
    if not row["use_when"]:
        issues.append(f"{row['path']}: use_when tags not reviewed")
    return issues


def relevance(row: dict, words: set[str]) -> int:
    """Purely lexical discovery; no semantic sufficiency claim."""
    def overlap(text: str) -> int:
        return len(words & set(WORDS.findall(text.casefold())))
    return (
        5 * sum(overlap(tag) for tag in row["use_when"])
        + 3 * overlap(row["purpose"])
        + overlap(row["path"])
    )


def evaluate(root: Path, data: dict, query: str | None, limit: int) -> dict:
    warnings: list[str] = []
    if not data["approved"]:
        warnings.append("ledger is unapproved; review purpose and use_when, then set approved=true")
    if query is None:
        rows = data["entries"]
    else:
        terms = set(WORDS.findall(query.casefold())) - STOPWORDS
        if not terms:
            raise ValueError("query must contain a meaningful search term")
        candidates = [(relevance(row, terms), row) for row in data["entries"]]
        candidates = [(score, row) for score, row in candidates if score > 0]
        candidates.sort(key=lambda item: (-item[0], item[1]["path"]))
        rows = [row for score, row in candidates[:limit]]
        if not candidates:
            warnings.append("no matching ledger paths; inspect live repository before proceeding")
    matches = []
    for row in rows:
        state = freshness(root, row)
        issues = content_issues(row)
        if state != "CURRENT":
            warnings.append(f"{row['path']}: {state}; recheck source and refresh ledger")
        warnings.extend(issues)
        matches.append({
            "path": row["path"], "kind": row["kind"], "purpose": row["purpose"],
            "use_when": row["use_when"], "related": row["related"],
            "freshness": state,
        })
    status = "REVIEW_REQUIRED" if warnings else "PASS"
    return {
        "status": status,
        "query": query,
        "matches": matches if data["approved"] else [],
        "warnings": list(dict.fromkeys(warnings)),
        "scope": "Navigation only: always read selected live files and run resume-trust separately",
    }


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER,
                        help="Ledger path relative to --root (default .ai-context/file-ledger.json)")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    subs = parser.add_subparsers(dest="command", required=True)
    proposal = subs.add_parser("propose", help="Generate an unapproved navigation proposal")
    proposal.add_argument("--path", action="append", default=[], help="One exact file (repeatable)")
    proposal.add_argument("--tracked", action="store_true", help="Include tracked text-like files")
    proposal.add_argument("--from-ledger", type=Path, help="Retain descriptions while refreshing hashes")
    proposal.add_argument("--output", type=Path, help="Output, defaults to --ledger; refuses overwrite")
    lookup = subs.add_parser("query", help="Return a small set of reviewed paths")
    lookup.add_argument("task", nargs="+")
    lookup.add_argument("--limit", type=int, default=5)
    subs.add_parser("check", help="Check approval, metadata completeness and all indexed hashes")
    args = parser.parse_args(argv)
    root = args.root.expanduser().resolve()
    ledger = args.ledger if args.ledger.is_absolute() else root / args.ledger
    try:
        if args.command == "propose":
            source = args.from_ledger
            if source is not None and not source.is_absolute():
                source = root / source
            output = args.output if args.output is not None else ledger
            if not output.is_absolute():
                output = root / output
            if output.exists():
                raise ValueError(f"refusing to overwrite existing proposal: {output}")
            result = propose(root, args.path, args.tracked, source)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            report = {"status": "PROPOSED", "output": str(output), "files": len(result["entries"]),
                      "approved": False}
        else:
            if not ledger.exists():
                if args.command == "check":
                    report = {"status": "NOT_APPLICABLE", "matches": [], "warnings": [],
                              "scope": "No file ledger; optional feature"}
                else:
                    report = {"status": "REVIEW_REQUIRED", "matches": [],
                              "warnings": ["file ledger absent; create and review one first"]}
            else:
                data = read_ledger(ledger, root)
                if args.command == "query":
                    if not 1 <= args.limit <= 20:
                        raise ValueError("--limit must be from 1 to 20")
                    report = evaluate(root, data, " ".join(args.task), args.limit)
                else:
                    report = evaluate(root, data, None, MAX_ENTRIES)
    except (OSError, ValueError) as exc:
        print(f"file ledger input error: {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"FILE LEDGER: {report['status']}")
        for row in report.get("matches", []):
            print(f"- {row['path']} [{row['freshness']}]: {row['purpose']} ({row['kind']})")
        for warning in report.get("warnings", []):
            print(f"- REVIEW_REQUIRED: {warning}")
        if "output" in report:
            print(f"- Proposal: {report['output']} ({report['files']} files; unapproved)")
        print("This is an index of navigation hints, not source authority or loaded context.")
    return 0 if report["status"] in {"PASS", "NOT_APPLICABLE", "PROPOSED"} else 3


if __name__ == "__main__":
    raise SystemExit(cli())
