#!/usr/bin/env python3
"""Propose a human-reviewed context manifest from explicit SPEC.md references.

Only well-formed local paths in Authoritative references and literal Test/Verify
commands are candidates. No fuzzy source inference or automatic approval.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from context_sections import parse_requirement, required_section
from context_sufficiency import safe_source

SCHEMA_VERSION = 1
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
PATH = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$")
COMMAND = re.compile(r"^[-*+]\s*(Test|Verify)\s*:\s*(.+)$", re.IGNORECASE)
MAX_MANIFEST_BYTES = 1_000_000
EXPECTED_KEYS = frozenset({
    "schema_version", "spec", "spec_sha256", "approved",
    "required_sources", "required_headings", "required_proofs", "unresolved",
})


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def lines_of_section(text: str, title: str) -> list[str]:
    """Extract only a named second-level Markdown section."""
    rows = text.splitlines()
    start = next(
        (index + 1 for index, row in enumerate(rows)
         if row.strip().casefold() == f"## {title}".casefold()), None
    )
    if start is None:
        return []
    end = next((i for i in range(start, len(rows)) if rows[i].startswith("## ")), len(rows))
    return rows[start:end]


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def propose(root: Path, spec: str = "SPEC.md") -> dict[str, object]:
    """Propose only deterministic requirements; retain ambiguous references."""
    source = safe_source(root, spec)
    raw = source.read_bytes()
    text = raw.decode("utf-8")
    sources = [spec]
    headings = []
    proofs = []
    unresolved = []
    for title in ("Acceptance criteria", "Invalid if"):
        section, detail = required_section(text, title)
        if section is not None:
            headings.append(f"{spec}::{title}")
        elif title == "Acceptance criteria":
            unresolved.append(f"{spec}: {detail} for Acceptance criteria")

    for row in lines_of_section(text, "Authoritative references"):
        stripped = row.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue
        value = cells[0].strip().strip("`").strip()
        if value.lower() == "reference" or re.fullmatch(r"[-: ]+", value):
            continue
        if not value:
            unresolved.append("empty Authoritative references cell")
            continue
        if not PATH.fullmatch(value):
            unresolved.append(f"reference needs review (not an exact local path): {value}")
            continue
        try:
            candidate = safe_source(root, value)
        except ValueError as exc:
            unresolved.append(f"reference needs review: {value} ({exc})")
            continue
        if not candidate.is_file():
            unresolved.append(f"reference missing: {value}")
        else:
            sources.append(value)

    for row in lines_of_section(text, "Commands"):
        match = COMMAND.match(row.strip())
        if not match:
            continue
        proof = match.group(2).strip().strip("`").strip()
        if not proof or "_TBD_" in proof.upper() or proof.lower() in {"tbd", "none", "n/a"}:
            continue
        proofs.append(proof)

    return {
        "schema_version": SCHEMA_VERSION,
        "spec": spec,
        "spec_sha256": digest(raw),
        "approved": False,
        "required_sources": unique(sources),
        "required_headings": unique(headings),
        "required_proofs": unique(proofs),
        "unresolved": unique(unresolved),
    }


def load_manifest(path: Path, root: Path) -> tuple[dict[str, object], list[str]]:
    """Validate reviewed manifest and compare its SPEC fingerprint with current state."""
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read context manifest: {exc}") from exc
    if len(data) > MAX_MANIFEST_BYTES:
        raise ValueError("context manifest exceeds 1 MB")
    try:
        manifest = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid UTF-8 JSON context manifest: {exc}") from exc
    if not isinstance(manifest, dict) or set(manifest) != EXPECTED_KEYS:
        raise ValueError("context manifest must contain exactly the schema-v1 keys")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported context manifest schema_version")
    if type(manifest["approved"]) is not bool:
        raise ValueError("context manifest approved must be a boolean")
    if not isinstance(manifest["spec_sha256"], str) or not DIGEST.fullmatch(manifest["spec_sha256"]):
        raise ValueError("invalid context manifest spec_sha256")
    for key in ("required_sources", "required_headings", "required_proofs", "unresolved"):
        values = manifest[key]
        if (
            not isinstance(values, list) or len(values) > 128
            or any(not isinstance(item, str) or not item.strip() or len(item) > 4000 for item in values)
            or len(set(values)) != len(values)
        ):
            raise ValueError(f"context manifest {key} must be a unique list of nonempty strings")
    spec = manifest["spec"]
    if not isinstance(spec, str) or spec not in manifest["required_sources"]:
        raise ValueError("context manifest must require its own SPEC source")
    safe_source(root, spec)
    for value in manifest["required_sources"]:
        safe_source(root, value)
    for value in manifest["required_headings"]:
        name, heading = parse_requirement(value)
        safe_source(root, name)
        if not heading:
            raise ValueError("empty manifest heading")
    warnings = []
    if not manifest["approved"]:
        warnings.append("manifest is a proposal; operator must review and set approved=true")
    if manifest["unresolved"]:
        warnings.append("manifest contains unresolved references; review and resolve or explicitly remove them")
    source = safe_source(root, spec)
    try:
        current = digest(source.read_bytes())
    except OSError:
        warnings.append(f"manifest SPEC source is unavailable: {spec}")
    else:
        if current != manifest["spec_sha256"]:
            warnings.append(f"manifest stale: {spec} changed since proposal")
    return manifest, warnings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--spec", default="SPEC.md", help="Repository-relative spec")
    parser.add_argument("--output", type=Path, help="Write proposal JSON; never auto-approve")
    args = parser.parse_args(argv)
    try:
        source = safe_source(args.root, args.spec)
        if args.output and args.output.resolve() == source:
            raise ValueError("--output cannot overwrite SPEC.md")
        proposal = propose(args.root, args.spec)
        output = json.dumps(proposal, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            print(output, end="")
    except (ValueError, OSError, UnicodeError) as exc:
        parser.exit(2, f"manifest proposal error: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
