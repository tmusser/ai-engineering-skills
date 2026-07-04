# Context Hydration

Use this advanced recipe when you want a small, deterministic context packet instead
of loading every workflow doc into the prompt. It creates working-context headroom by
pulling the smallest relevant markdown excerpts for the task at hand.

This is not token magic. The packet is only as good as the local index and the route
map behind it, and you still need the underlying docs when the task changes shape.

## When to use

- The task is specific, but the repo docs are bigger than the agent context you want
  to spend.
- You want a fresh session to start with the relevant slices only.
- You need a repeatable packet for a task family such as verification, scope control,
  planning, debugging, shipping, or handoff.

## When not to use

- The task is tiny and already fits in working memory.
- The relevant docs are actively changing and you do not want to rebuild the index.
- You need semantic search across large corpora, external systems, or non-markdown
  sources.
- The packet would replace reading the underlying docs instead of complementing them.

## Workflow

1. Build or refresh the local markdown index:

   ```bash
   python scripts/build_context_index.py
   ```

2. Generate a packet for the current task:

   ```bash
   python scripts/context_pack.py "resume and verify this bug fix"
   ```

3. Paste the packet into the agent session and keep the original docs available if
   the task expands.

## Index freshness

`context_pack.py` re-reads the current Markdown files for packet content. The
saved index is a drift contract and freshness check: it lets the packet warn when
the index is missing or older than the scanned Markdown tree.

Use `--refresh-index` when you want the script to rebuild
`.ai-context/index.jsonl` explicitly before packet generation. The script does
not silently re-index by default because explicit file writes are easier to
audit.

## Budget semantics

`--budget` is an approximate selected-context budget, not a precise
tokenizer-backed final rendered-output budget. The packet uses the effective
selected-context budget after any clamp, and sections that exceed it stay
omitted rather than being force-loaded or tail-sliced.

The default stays conservative, and overly large requests are clamped to the
configured maximum with a visible note.

## Hydration cadence

Generate one packet per logical task block, not after every tool call. Re-run
hydration when the task scope changes, verification fails in a way that changes
the needed context, or important Markdown artifacts such as `SPEC.md`,
`VERIFY.md`, or `HANDOFF.md` change. This keeps hydration from becoming a
turn-by-turn tax.

This is a usage rule, not a session lock or packet cache. The current scripts do
not maintain a TTL, remember prior packets, or block re-hydration for N minutes.
If a wrapper or subagent adds caching later, keep it explicit and auditable.

## Optional subagent / small-model routing

The deterministic scripts are the portable core. If your local toolchain supports
a read-only subagent, you can use it to gather a compact packet and hand it back.
That can be a Claude Code subagent, a Codex/OpenAI subagent, or any other local
small/cheap model helper. For example, Haiku in Claude Code or an OpenAI
mini-class model in Codex, where supported.

Keep the helper read-only: let it read or search local markdown, return selected
files and line ranges, omitted candidates, stale-index warnings, and refresh
guidance, then stop. It should not edit files, run broad commands, or replace
verification. Put any provider-specific configuration outside this recipe.

### Prompt template

```text
You are a read-only context librarian.
Read local markdown artifacts only as needed.
Return the smallest relevant context packet for the task.
Do not modify files.
Do not run tests.
Do not summarize the whole repo.
Include selected files/line ranges, omitted candidates, stale-index warnings, and refresh guidance.

Use this once per logical task block unless scope or verification state changes.
```

## Example packet

```markdown
# Context Packet

- Task: `resume and verify this bug fix`
- Selected-context budget: approximately 700 tokens
- Route matches: Resume / handoff, Verification
- Markdown records scanned: 86

## Selected context

| File | Lines | Heading path | Est. tokens | Reason |
| ---- | ----- | ------------ | ----------- | ------ |
| `templates/HANDOFF.md` | `1-20` | Handoff > Resume packet | 55 | Resume / handoff: preferred file, route keyword hit(s) |
| `templates/VERIFY.md` | `1-40` | Verify > Verify gate | 82 | Verification: preferred file, route keyword hit(s) |

## Stale-index warnings

- None.

## Refresh guidance

If Markdown files changed, rebuild the local index and rerun the packet.
```

## Notes

- `scripts/build_context_index.py` writes `.ai-context/index.jsonl` with heading
  paths, line ranges, token estimates, and content hashes for each markdown
  section.
- `scripts/context_pack.py` re-reads current markdown for packet content and uses
  the saved index as a freshness and drift contract.
- `scripts/context_pack.py` can rebuild the saved index explicitly with
  `--refresh-index` before packet generation.
- `scripts/context_pack.py` also falls back to the built-in route map if the local
  routing file cannot be parsed.
- `.ai-context/routing.yml` keeps the route map small and editable by hand.
- Use `test-mini` only when the slice needs focused deterministic tests; hydration is
  about smaller context, not replacing verification.
