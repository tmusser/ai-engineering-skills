#!/usr/bin/env sh
set -eu

if ! command -v vhs >/dev/null 2>&1; then
  cat <<'EOF'
VHS is not installed.

Install VHS from https://github.com/charmbracelet/vhs, then run:

  scripts/render_demo.sh

This script renders demo/demo.tape.
It does not invoke Claude Code, use API keys, or touch private data.
EOF
  exit 1
fi

vhs demo/demo.tape

cat <<'EOF'
Rendered demo/ai-engineering-skills-demo.gif.

Review the GIF before committing it.
Do not commit generated GIFs unless intentionally adding a release asset.
EOF
