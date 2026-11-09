#!/usr/bin/env python3
"""Check selected UTF-8 context files against a local byte budget, not API tokens."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from context_sufficiency import check_sufficiency, safe_source
from context_sections import check_headings
from context_manifest import load_manifest
from context_proof_provenance import check_recorded_proofs

DEFAULT_MAX_BYTES = 60_000


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="UTF-8 files; use '-' once for stdin")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root for source checks")
    parser.add_argument("--require-source", action="append", default=[], metavar="PATH",
                        help="Require this repository-relative source in selected input (repeatable)")
    parser.add_argument("--require-proof", action="append", default=[], metavar="TEXT",
                        help="Require this literal proof/acceptance anchor in selected input (repeatable)")
    parser.add_argument("--require-heading", action="append", default=[], metavar="FILE::Heading",
                        help="Require a full Markdown section in selected context (repeatable)")
    parser.add_argument("--manifest", type=Path, help="Use a reviewed, SPEC-pinned context manifest")
    parser.add_argument("--proof-mode", choices=("literal", "recorded"), default="literal",
                        help="Literal presence (default), or exact recorded PASS command evidence")
    parser.add_argument("--verification-source", default="VERIFY.md", metavar="PATH",
                        help="Repository-relative authoritative verification file (recorded mode)")
    return parser.parse_args(argv)


def measure(paths: list[str]) -> tuple[list[dict[str, object]], int, list[tuple[str, str]]]:
    entries: list[dict[str, object]] = []
    total = 0
    payloads: list[tuple[str, str]] = []
    seen_stdin = False
    for name in paths:
        if name == "-":
            if seen_stdin:
                raise ValueError("stdin ('-') may be used only once")
            seen_stdin = True
            data = sys.stdin.buffer.read()
            label = "<stdin>"
        else:
            path = Path(name)
            if not path.is_file():
                raise ValueError(f"not a regular file: {name}")
            try:
                data = path.read_bytes()
            except OSError as exc:
                raise ValueError(f"cannot read {name}: {exc}") from exc
            label = name
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"not UTF-8: {label}") from exc
        size = len(data)
        total += size
        entries.append({"path": label, "bytes": size})
        payloads.append((label, text))
    return entries, total, payloads


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.max_bytes <= 0:
        print("error: --max-bytes must be positive", file=sys.stderr)
        return 2
    try:
        entries, total, payloads = measure(args.paths)
        manifest_warnings: list[str] = []
        if args.manifest:
            if any(label != "<stdin>" and Path(label).resolve() == args.manifest.resolve()
                   for label, _ in payloads):
                raise ValueError("--manifest must not be included as selected context")
            manifest, manifest_warnings = load_manifest(args.manifest, args.root)
            args.require_source = list(dict.fromkeys([*args.require_source, *manifest["required_sources"]]))
            args.require_heading = list(dict.fromkeys([*args.require_heading, *manifest["required_headings"]]))
            args.require_proof = list(dict.fromkeys([*args.require_proof, *manifest["required_proofs"]]))
        if any(not anchor for anchor in args.require_proof):
            raise ValueError("--require-proof must not be empty")
        if args.proof_mode == "recorded" and not args.require_proof:
            raise ValueError("--proof-mode recorded requires --require-proof or manifest proof anchors")
        for name in args.require_source:
            safe_source(args.root, name)
        literal_proofs = args.require_proof if args.proof_mode == "literal" else []
        sufficiency = (check_sufficiency(payloads, args.root, args.require_source, literal_proofs)
                       if args.require_source or args.require_proof or args.require_heading else None)
        if args.proof_mode == "recorded":
            proofs, proof_warnings = check_recorded_proofs(
                payloads, args.root, args.verification_source, args.require_proof
            )
            sufficiency["proofs"] = proofs
            sufficiency["warnings"].extend(proof_warnings)
            sufficiency["proof_mode"] = "recorded"
            sufficiency["verification_source"] = args.verification_source
        if args.require_heading:
            # A pending/stale proposal cannot pass even if the selected context
            # happens to contain the named sections. Avoid reading a removed SPEC.
            if not manifest_warnings:
                sufficiency["headings"] = check_headings(payloads, args.root, args.require_heading)
            else:
                sufficiency["headings"] = [
                    {"requirement": value, "status": "missing", "detail": "manifest needs review"}
                    for value in args.require_heading
                ]
        if sufficiency is not None:
            sufficiency["warnings"].extend(manifest_warnings)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    incomplete = sufficiency is not None and (
        any(item["status"] != "represented"
            for key in ("sources", "proofs", "headings")
            for item in sufficiency.get(key, []))
        or bool(sufficiency["warnings"])
    )
    status = "PASS" if total <= args.max_bytes and not incomplete else "REVIEW_REQUIRED"
    result = {
        "status": status,
        "selected_bytes": total,
        "max_bytes": args.max_bytes,
        "remaining_bytes": args.max_bytes - total,
        "inputs": entries,
        "scope": "selected UTF-8 payload only, not model tokens or full request",
    }
    if sufficiency is not None:
        result["sufficiency"] = sufficiency
    if args.format == "json":
        print(json.dumps(result, sort_keys=True))
    else:
        print(f"ECO {status}: {total}/{args.max_bytes} selected UTF-8 bytes")
        for entry in entries:
            print(f"- {entry['path']}: {entry['bytes']} bytes")
        if sufficiency is not None:
            for item in [*sufficiency["sources"], *sufficiency["proofs"], *sufficiency.get("headings", [])]:
                label = item.get("requirement", item.get("source", item.get("proof")))
                if sufficiency.get("proof_mode") == "recorded" and item.get("proof"):
                    checks = ", ".join(item.get("checks", [])) or "none"
                    print(f"- {item['status']}: {label} (recorded checks: {checks})")
                else:
                    print(f"- {item['status']}: {label}")
            for warning in sufficiency["warnings"]:
                print(f"- REVIEW_REQUIRED: {warning}")
        if sufficiency is not None and sufficiency.get("proof_mode") == "recorded":
            print("Recorded proof reflects source-verified VERIFY claims; execution, freshness, and correctness unverified.")
        else:
            print("Selected content and literal anchors only; semantic sufficiency and provider cost unmeasured.")
    return 0 if status == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
