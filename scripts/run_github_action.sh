#!/usr/bin/env bash
set -euo pipefail

ACTION_ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
WORKSPACE="${GITHUB_WORKSPACE:-}"
BASE="${AES_BASE:-}"
NO_HANDOFF="${AES_NO_HANDOFF:-false}"

if [ -z "$WORKSPACE" ]; then
  echo "error: GITHUB_WORKSPACE is required" >&2
  exit 2
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo "error: python3 or python is required" >&2
  exit 127
fi

set -- --root "$WORKSPACE"

if [ -n "$BASE" ]; then
  set -- "$@" --base "$BASE"
fi

case "$NO_HANDOFF" in
  true)
    set -- "$@" --no-handoff
    ;;
  false)
    ;;
  *)
    echo "error: no-handoff must be 'true' or 'false'" >&2
    exit 2
    ;;
esac

exec "$PYTHON_BIN" "$ACTION_ROOT/scripts/render_github_step_summary.py" "$@"
