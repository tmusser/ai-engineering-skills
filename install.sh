#!/usr/bin/env sh
set -eu

print_help() {
  cat <<'EOF'
Usage:
  ./install.sh
  ./install.sh --dry-run
  ./install.sh --claude-user
  ./install.sh --claude-project /path/to/project
  ./install.sh --codex-user
  ./install.sh --codex-project /path/to/project
  ./install.sh --help

Options:
  --dry-run                  Print what would be installed without creating files.
  --claude-user              Install Claude Code skills to ~/.claude/skills/.
  --claude-project PATH      Install Claude Code skills to PATH/.claude/skills/.
  --codex-user               Install Codex skills to ~/.agents/skills/.
  --codex-project PATH       Install Codex skills to PATH/.agents/skills/.
  --help                     Show this help message.

Default:
  ./install.sh is the same as ./install.sh --claude-user.
EOF
}

print_slash_commands() {
  if [ "${1:-0}" -eq 1 ]; then
    heading='Claude Code slash commands that would be available:'
  else
    heading='Installed Claude Code slash commands:'
  fi

  cat <<EOF
$heading
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
/context-check
/handoff
EOF
}

install_claude_user() {
  dry_run="$1"
  if [ "$dry_run" -eq 1 ]; then
    python scripts/install_claude_code.py --target user --dry-run
  else
    python scripts/install_claude_code.py --target user
  fi

  print_slash_commands "$dry_run"
}

install_claude_project() {
  project_path="$1"
  dry_run="$2"
  if [ "$dry_run" -eq 1 ]; then
    python scripts/install_claude_code.py --target project --project-path "$project_path" --dry-run
  else
    python scripts/install_claude_code.py --target project --project-path "$project_path"
  fi

  print_slash_commands "$dry_run"
}

install_codex_user() {
  dry_run="$1"
  if [ "$dry_run" -eq 1 ]; then
    python scripts/install_codex.py --target user --dry-run
  else
    python scripts/install_codex.py --target user
  fi
}

install_codex_project() {
  project_path="$1"
  dry_run="$2"
  if [ "$dry_run" -eq 1 ]; then
    python scripts/install_codex.py --target project --project-path "$project_path" --dry-run
  else
    python scripts/install_codex.py --target project --project-path "$project_path"
  fi
}

INSTALLER=claude
TARGET=user
PROJECT_PATH=
DRY_RUN=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    --claude-user)
      INSTALLER=claude
      TARGET=user
      PROJECT_PATH=
      ;;
    --claude-project)
      INSTALLER=claude
      TARGET=project
      shift
      if [ "$#" -eq 0 ]; then
        echo "error: --claude-project requires a project path" >&2
        exit 1
      fi
      PROJECT_PATH="$1"
      ;;
    --codex-user)
      INSTALLER=codex
      TARGET=user
      PROJECT_PATH=
      ;;
    --codex-project)
      INSTALLER=codex
      TARGET=project
      shift
      if [ "$#" -eq 0 ]; then
        echo "error: --codex-project requires a project path" >&2
        exit 1
      fi
      PROJECT_PATH="$1"
      ;;
    --help|-h)
      print_help
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      print_help >&2
      exit 1
      ;;
  esac
  shift
done

case "$INSTALLER:$TARGET" in
  claude:user)
    install_claude_user "$DRY_RUN"
    ;;
  claude:project)
    install_claude_project "$PROJECT_PATH" "$DRY_RUN"
    ;;
  codex:user)
    install_codex_user "$DRY_RUN"
    ;;
  codex:project)
    install_codex_project "$PROJECT_PATH" "$DRY_RUN"
    ;;
esac
