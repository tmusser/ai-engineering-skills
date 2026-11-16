# File-Purpose Ledger: Find First, Load Second

The optional file-purpose ledger is a small, curated map of **which files serve
which jobs**. It helps a resumed coding agent locate the right code, tests,
contracts or documentation without loading the repository inventory—or all of
those files—into its prompt.

It extends the *librarian pattern* in [context hydration](context-hydration.md).
That existing Markdown section index locates and validates passages. This
ledger locates **files by reviewed purpose and when-to-read labels**, including
source files beyond Markdown. It stores filenames, metadata and SHA-256 hashes,
not file bodies or model-generated summaries.

## Start with only the files worth mapping

From the project root:

```bash
python scripts/aes.py files propose \
  --path SPEC.md \
  --path src/export.py \
  --path tests/test_export.py
```

This creates `.ai-context/file-ledger.json` with `approved: false`.
If appropriate, `--tracked` proposes all tracked text-like code/docs/config
files, while excluding untracked sources and common secret/binary paths. Use
explicit paths for compact ledgers; a bulk inventory is not automatically a
useful map. Proposal never overwrites a file that already exists.

Each proposed entry has:

```json
{
  "path": "src/export.py",
  "kind": "implementation",
  "purpose": "Implements the CSV export API",
  "use_when": ["export behavior", "empty-result debugging"],
  "related": ["tests/test_export.py"],
  "sha256": "sha256:..."
}
```

The `sha256` field in this example is abbreviated for readability. In a
generated ledger it contains the full hash of the local file.

The proposed `kind` comes from filename conventions, **not** a determination
of authority. Review and correct it. Write a concrete, useful `purpose`, at
least one `use_when` label, and any optional `related` paths. Then explicitly
set `approved` to `true` when **every entry** has been reviewed. Do not
promote inferred roles, guesses or untrusted content to project instructions.

## Resume with five paths, not fifty files

**First** run the normal fresh-session resume-trust check for `HANDOFF.md`.
If and only if the project already maintains a reviewed ledger, use:

```bash
python scripts/aes.py files query "csv export" --limit 5
python scripts/aes.py files --format json query "csv export" --limit 5
```

The query emits matching paths, short purposes, when-to-read tags, related
paths and a `CURRENT`, `STALE` or `MISSING` state. It never prints file
contents and never automatically loads every related file. Select only what
the next task requires and then **read the live source files**, applying the
normal authority hierarchy and source verification.

A matching reviewed entry is a **navigation hint**, not a guarantee that
the index found every dependency. No matches, stale matches, unapproved
metadata, or missing files yield `REVIEW_REQUIRED` rather than a false
ready-to-proceed signal. Query results are lexical, not semantic search.

Use `python scripts/aes.py files check` to review **all** indexed files for
changed hashes, missing paths and incomplete labels. Unrelated entries can
be stale without invalidating a narrow query. No ledger at all is
`NOT_APPLICABLE` for `check` and still requires ordinary source discovery
if `query` is explicitly attempted.

## Maintenance without losing curation

After a mapped file changes, regenerate a **new unapproved proposal** while
retaining your previous purpose/use-when labels:

```bash
python scripts/aes.py files propose \
  --from-ledger .ai-context/file-ledger.json \
  --output .ai-context/file-ledger.next.json
```

Inspect the updated hashes, metadata and live files. Update the labels if
responsibilities changed, approve the replacement and deliberately replace
the old ledger. The tool never silently refreshes an approved ledger in place.
Missing prior sources stay in the proposal for explicit review instead of
being silently deleted.

## Status and trust boundaries

| Outcome | Exit | Interpretation |
| --- | --- | --- |
| `PROPOSED`, `PASS`, `NOT_APPLICABLE` | 0 | Written proposal, reviewed current metadata, or no optional ledger |
| `REVIEW_REQUIRED` | 3 | Unapproved, incomplete, stale or missing metadata; no matching paths |
| Input error | 2 | Invalid schema, path, request, or unreadable source |

The schema is deliberately simple (version 1), with a bounded number of
entries, path normalization, rejection of symlink traversal, and full-file
hashes. The index is stored under `.ai-context/`, which the Markdown section
indexer already excludes from its scan.

**Do not treat this index as a source of truth.** It is not a dependency graph,
permission system, guaranteed semantic retrieval engine, or verification
artifact. It cannot supersede current user instructions, `SPEC.md`, tests,
code, or a fresh-session trust gate. Do not put secret filenames, private
metadata or credentials into a ledger that may be committed or shared.

A short reversible task with obvious files needs neither a ledger nor another
tool call. Maintain this only when repeated navigation cost outweighs the
upkeep and when a source map is genuinely helpful.
