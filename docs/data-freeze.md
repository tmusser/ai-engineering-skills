# Optional Data Freeze

Use a data freeze when a consequential analysis depends on mutable inputs and
someone may need to reproduce the exact calculation later. A lift estimate
revisited five months later needs the original extract, denominator, filters,
calculation code, parameters, and environment.

Create a snapshot only when retaining the selected data is appropriate. Choose
an approved storage location and retention policy for sensitive or large inputs.
The CLI writes locally and never uploads data. Snapshots inside a repository
need an explicit decision about whether to commit them. Prefer approved external
storage for restricted data.

## Capture a calculation

Export a stable extract first. Select each input and each relevant context file
explicitly. Context can include the analysis script, SQL query, parameter file,
dependency lockfile, metric definition, and result artifact. The tool copies
their exact bytes and records SHA-256 hashes, byte counts, capture time, Git
commit and dirty state when available, and the supplied provenance.

~~~bash
python scripts/aes.py data freeze \
  --input data/lift.csv \
  --context analysis/lift.py \
  --context analysis/parameters.json \
  --context requirements.lock \
  --output /approved/analysis-snapshots/lift-v1 \
  --source "warehouse export; event date through 2026-11-19" \
  --recipe "python analysis/lift.py --parameters analysis/parameters.json" \
  --environment "Python 3.12.7; dependencies pinned in requirements.lock"
~~~

Paths for selected files are relative to the current directory, or to an explicit
--root. Directories, duplicate paths, traversal and symlinks are rejected.
The destination must be new. A failed capture removes its partial destination.
No files are discovered automatically, and no commands are executed from the
recipe. Explicit selection can still include sensitive content, so inspect it.

The destination contains manifest.json and a files/ tree preserving selected
relative paths. The manifest distinguishes data inputs from calculation context.
Its deterministic stamp covers selected paths, roles, hashes, sizes, source,
recipe and environment. Capture time and Git state are recorded separately, so
identical selected inputs and provenance retain the same stamp across captures.

The manifest is written last. Capture compares copied hashes with the sources
and rechecks the full selection before publishing. Quiesce writers or use a
database-consistent export when required. Filesystem copying cannot guarantee a
transactionally consistent snapshot across files being modified concurrently.

## Check and compare

Check archived bytes before trusting a snapshot. Add a live root to identify
changes to the current inputs or analysis files.

~~~bash
python scripts/aes.py data --format json check /approved/analysis-snapshots/lift-v1
python scripts/aes.py data check /approved/analysis-snapshots/lift-v1 --live-root .
~~~

After a new extract or calculation change, capture a separate lift-v2 snapshot
with updated provenance. Compare the preserved versions.

~~~bash
python scripts/aes.py data --format json diff \
  /approved/analysis-snapshots/lift-v1 /approved/analysis-snapshots/lift-v2
python scripts/aes.py data diff \
  /approved/analysis-snapshots/lift-v1 /approved/analysis-snapshots/lift-v2 --text
~~~

Diff reports added, removed and changed files, including changes in data/context
role, plus changes to source, recipe and environment. --text includes UTF-8
unified diffs for changed files up to 128,000 bytes each, capped at 200 lines per
file with an explicit truncation flag. Binary and larger files retain hash/size
comparisons. Text diffs may expose data. Row order and serialization changes count
as byte changes; semantic joins, row-level reconciliation and statistical
comparability require analysis-specific checks.

| Outcome | Exit | Meaning |
| --- | --- | --- |
| PASS | 0 | Capture completed, checked bytes match, or both diff inputs are intact |
| REVIEW_REQUIRED | 3 | Archived bytes, stamp, or selected live files differ or are missing |
| Input error | 2 | Missing/malformed manifest, unsupported schema, unsafe path, invalid arguments or I/O failure |

A successful diff can report changes. Its PASS means the comparison used intact
snapshots. It does not approve an analytical change.

## Connect to verification and handoff

When a freeze is useful, record the snapshot location and stamp in VERIFY.md,
alongside the exact calculation command, result, denominator, population, time
window, exclusions and remaining uncertainty. Record whether the archived
calculation was actually rerun. In HANDOFF.md, carry the location, stamp,
required access and next reproduction command when continuation depends on it.

To reproduce, check integrity, prepare a separate working directory from the
snapshot's files/ tree, restore the recorded environment, inspect the recipe,
and run it deliberately. Keep the preserved snapshot untouched. Absolute paths,
external services, random seeds and unrecorded dependencies can still prevent
reproduction. Record these gaps instead of claiming full provenance.

This mechanic is optional and adds no default gate. A stamp establishes byte
identity against its manifest. It does not authenticate authorship, prove data
quality, establish metric validity, freeze remote systems, provision environments
or guarantee reproduction. Git dirty state is an observation; selected context
copies preserve only the explicitly captured working files. Preserve any other
needed code and dependencies separately.

Snapshots refuse overwrite through this CLI but remain ordinary writable files.
Integrity checks detect accidental edits against the manifest. Coordinated edits
to both bytes and manifest require independently trusted storage or a recorded
stamp to detect. Backups, access controls, long-term storage and retention remain
the operator's responsibility.
