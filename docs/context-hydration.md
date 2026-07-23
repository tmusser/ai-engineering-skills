# Context Hydration

Use this advanced recipe when you want a small, deterministic context packet instead
of loading every workflow doc into the prompt. It creates working-context headroom by
pulling the smallest relevant Markdown sections for the task at hand.

This is not token magic. The packet is only as good as the local index, route map,
and source authority behind it. Keep the underlying docs available when the task
changes shape.

## When to use

- The task is specific, but the repo docs are bigger than the agent context you want
  to spend.
- You want a fresh session to start with the relevant slices only.
- You need a repeatable packet for verification, scope control, planning, debugging,
  shipping, handoff, or hydration maintenance.
- A project-specific doctrine or current-state file must be present in the packet.

## When not to use

- The task is tiny and already fits in working memory.
- The relevant docs are actively changing and you do not want to rebuild the index.
- You need semantic search across large corpora, external systems, or non-Markdown
  sources.
- The packet would replace reading the underlying docs instead of complementing them.

## Workflow

1. Build or refresh the local Markdown index:

   ```bash
   python scripts/build_context_index.py
   ```

2. Generate a packet for the current task:

   ```bash
   python scripts/context_pack.py "resume and verify this bug fix"
   ```

3. Require an authoritative project file when the task depends on it:

   ```bash
   python scripts/context_pack.py \
     "prepare a project-specific response" \
     --require-file PROJECT_DOCTRINE.md \
     --strict
   ```

4. Paste the packet into the agent session and keep the original docs available if
   the task expands.

## Source authority

Hydration distinguishes source roles instead of treating every Markdown section as
interchangeable.

Selection priority is:

```text
required > current_state > project_guidance > other > template > example
```

- `required` — files named explicitly with `--require-file`
- `current_state` — root-level `CONTEXT.md`, `HANDOFF.md`, `SPEC.md`, `PLAN.md`,
  `TODO.md`, `VERIFY.md`, and `DECISIONS.md`
- `project_guidance` — `AGENTS.md`, `LLM.md`, `README.md`, skills, and ordinary docs
- `template` — reusable blanks under `templates/`
- `example` — example artifacts and fixtures intended to demonstrate shape

Templates and examples are fallback guidance. They must not outrank a live handoff,
verification record, spec, or explicitly required doctrine file.

## Required files

Use the repeatable option:

```bash
--require-file PATH
```

Required paths must be normalized repository-relative paths. Absolute paths, empty
segments, and `..` traversal are rejected.

A required source is selected before route-ranked context. The packet reports whether
it was:

- `represented`
- `missing`
- `cannot_fit`

A missing or unrepresentable required source makes the packet `FAIL`. A required
section that exceeds the effective budget is never silently omitted. Raise the
budget or read the source directly.

Do not put private doctrine, credentials, or personal material into this repository
merely to exercise the feature. Use sanitized fixtures in tests.

## Packet integrity

Each packet begins with:

```text
Packet status: PASS | WARN | FAIL
Packet fingerprint: sha256:...
Task: ...
Effective selected-context budget: ...
Routing source: ...
Route matches: ...
Required sources: ...
Markdown records scanned: ...
```

The fingerprint is deterministic. It is derived from the task, effective budget,
routing source, selected source roles, paths, rendered ranges, content hashes, and
required-source results. It excludes timestamps and absolute local paths.

Status semantics:

- `PASS` — context was selected, all required sources were represented, and no
  material freshness or routing warning exists.
- `WARN` — the packet is usable but has a stale or missing index, routing fallback,
  budget clamp, or similar caveat.
- `FAIL` — a required source is missing or cannot fit, no relevant context was
  selected, or the request contains invalid input.

## Strict mode and exit codes

Default mode renders the packet and normally returns zero so humans can inspect
warnings and failures.

Use `--strict` in CI or wrappers:

```text
0 = PASS
2 = WARN
3 = FAIL
```

The packet is still printed before a strict nonzero exit.

Invalid non-positive budgets and unsafe required paths are rejected with a clear
failure.

## Truthful excerpts

Selected-context rows describe the exact content rendered below them:

- source role
- file
- actual line range
- heading path
- approximate rendered tokens
- content hash
- selection reason

The generator renders the complete selected Markdown section. It does not label a
12-line prefix with the full section range. A section that does not fit stays omitted,
consistent with the documented budget semantics.

Omitted means **unknown to this packet**, not irrelevant to the task.

## Candidate fitting and redundancy

The selector continues through ranked candidates when a higher-ranked section does
not fit. A large first candidate does not prevent a smaller useful section farther
down the ranking from being considered.

The packet also avoids redundant context:

- the same section is not selected twice
- overlapping parent and child sections are not both selected
- exact normalized-content duplicates are suppressed
- higher-authority and higher-scored candidates win; equal scores prefer the narrower
  section
- each route has a small selection cap so one route cannot monopolize the budget

## Safe rendering and indexing

The implementation keeps packet generation inspectable and local:

- Markdown table cells escape pipes and backticks
- excerpt fences expand safely when source content contains code fences
- symlinked Markdown files are ignored, including links outside the selected root
- generated packets contain this marker:

  ```html
  <!-- generated by scripts/context_pack.py -->
  ```

- the indexer skips Markdown containing that marker so saved packets do not recursively
  enter future packets

Hydration is not a secret scanner. Keep sensitive material outside the scan root or
out of Markdown sources that the tool is allowed to read.

## Index freshness

`context_pack.py` rereads current Markdown files for packet content. The saved index
is a drift contract and freshness check: it warns when the index is missing, older
than the scanned Markdown tree, or no longer matches current section hashes and line
ranges.

Use `--refresh-index` when you want the script to rebuild `.ai-context/index.jsonl`
explicitly before packet generation. The script does not silently re-index by default
because explicit file writes are easier to audit.

## Budget semantics

`--budget` is an approximate selected-context budget, not a precise tokenizer-backed
final rendered-output budget. The packet uses the effective budget after any clamp.
Sections that exceed it stay omitted rather than being force-loaded or tail-sliced.

The default stays conservative, and overly large requests are clamped to the
configured maximum with a visible note.

## Hydration cadence

Generate one packet per logical task block, not after every tool call. Re-run
hydration when the task scope changes, verification fails in a way that changes the
needed context, or important artifacts such as `SPEC.md`, `VERIFY.md`, or `HANDOFF.md`
change.

This is a usage rule, not a session lock or packet cache. The scripts do not maintain
a TTL, remember prior packets, or block re-hydration for a fixed period. Keep any
wrapper caching explicit and auditable.

## Optional subagent / small-model routing

The deterministic scripts are the portable core. If your local toolchain supports a
read-only helper, it can gather a compact packet and hand it back. Keep the helper
read-only: let it read or search local Markdown, return selected files and line ranges,
omitted candidates, stale-index warnings, and refresh guidance, then stop.

It should not edit files, run broad commands, or replace verification. Put
provider-specific configuration outside this recipe.

### Prompt template

```text
You are a read-only context librarian.
Read local markdown artifacts only as needed.
Return the smallest relevant context packet for the task.
Do not modify files.
Do not run tests.
Do not summarize the whole repo.
Include selected files/line ranges, omitted candidates, stale-index warnings, and refresh guidance.
Treat required and current-state sources as more authoritative than templates or examples.

Use this once per logical task block unless scope or verification state changes.
```

## Example packet shape

```markdown
<!-- generated by scripts/context_pack.py -->

# Context Packet

- Packet status: PASS
- Packet fingerprint: sha256:...
- Task: `resume and verify this bug fix`
- Effective selected-context budget: approximately 700 tokens
- Routing source: file
- Route matches: Resume / handoff, Verification
- Required sources: None
- Markdown records scanned: 86

## Selected context

| Source role | File | Lines | Heading path | Est. tokens | Content hash | Reason |
| ----------- | ---- | ----- | ------------ | ----------- | ------------ | ------ |
| current_state | HANDOFF.md | 3-20 | Handoff > Resume packet | 55 | sha256:... | preferred file |
| current_state | VERIFY.md | 3-40 | Verify > Verify gate | 82 | sha256:... | preferred file |
```

## Notes

- `scripts/build_context_index.py` writes `.ai-context/index.jsonl` with heading paths,
  line ranges, token estimates, and content hashes for each Markdown section.
- `scripts/context_pack.py` rereads current Markdown and uses the saved index as a
  freshness and drift contract.
- `.ai-context/routing.yml` keeps the route map small and editable by hand.
- The `context_hydration` route covers maintenance work on the indexer, packet
  generator, routing map, docs, and tests.
- Use `test-mini` only when the slice needs focused deterministic tests; hydration is
  about smaller context, not replacing verification.
