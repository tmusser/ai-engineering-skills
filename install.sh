#!/usr/bin/env sh
set -eu

print_help() {
  cat <<'EOF'
Usage:
  ./install.sh
  ./install.sh --claude-user
  ./install.sh --claude-project /path/to/project
  ./install.sh --help

Options:
  --claude-user              Install Claude Code skills to ~/.claude/skills/.
  --claude-project PATH      Install Claude Code skills to PATH/.claude/skills/.
  --help                     Show this help message.

Default:
  ./install.sh is the same as ./install.sh --claude-user.
EOF
}

print_slash_commands() {
  cat <<'EOF'
Installed Claude Code slash commands:
/grill-with-docs-lite
/mini-spec
/thin-plan
/scope-freeze
/build-one
/test-mini
/diagnose-loop
/bug-capture
/verify-contract
/ship-mini
/handoff
EOF
}

install_claude_user() {
  python scripts/install_claude_code.py --target user
  print_slash_commands
}

install_claude_project() {
  project_path="$1"
  python scripts/install_claude_code.py --target project --project-path "$project_path"
  print_slash_commands
}

case "${1:-}" in
  "")
    install_claude_user
    ;;
  --claude-user)
    install_claude_user
    ;;
  --claude-project)
    if [ "$#" -ne 2 ]; then
      echo "error: --claude-project requires a project path" >&2
      exit 1
    fi
    install_claude_project "$2"
    ;;
  --help|-h)
    print_help
    ;;
  *)
    echo "error: unknown option: $1" >&2
    print_help >&2
    exit 1
    ;;
esac
