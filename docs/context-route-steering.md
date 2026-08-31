# Context Route Steering

Context hydration routes automatically from the task string by default. Use explicit
route steering when the human or wrapper already knows which workflow context should
participate.

Automatic behavior is unchanged when no route flags are supplied.

## Inspect available routes

List the names accepted by `--route` without generating a packet:

```bash
python scripts/context_pack.py --list-routes
```

The unified CLI exposes the same child command:

```bash
python scripts/aes.py context --list-routes
```

Route names come from the active routing configuration. Labels remain presentation
text; use the stable route name for steering.

## Add an explicit route

Explicit routes are considered before automatically matched routes, then ordinary
automatic routing continues for routes not already selected:

```bash
python scripts/context_pack.py \
  "fix the customer export regression" \
  --route verification
```

Repeat `--route` to activate more than one route. First-seen order is preserved and
duplicate route names are collapsed.

The packet's `Route matches` metadata reports the route score and activation reason,
including whether the route was explicit and which configured keywords or route-name
tokens matched the task.

Unknown route names fail clearly and print the available configured route names.

## Restrict selection to explicit routes

Use `--route-only` when automatic routes should not participate:

```bash
python scripts/context_pack.py \
  "fix the customer export regression" \
  --route debugging \
  --route verification \
  --route-only
```

`--route-only` requires at least one `--route` value.

This option changes route participation only. It does not change source authority,
required-file semantics, per-route selection caps, redundancy suppression, or packet
budget rules.

## Why this stays deterministic

Explicit steering does not add fuzzy matching, embeddings, model calls, or semantic
retrieval. It only chooses which existing deterministic route definitions participate
in the existing record-ranking and budget logic.

When no explicit flags are supplied, context hydration follows the same automatic
route matcher as before.
