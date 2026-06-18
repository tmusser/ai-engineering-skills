#!/usr/bin/env sh
set -eu

print_help() {
  cat <<'EOF'
Usage:
  ./install.sh
  ./install.sh --dry-run
  ./install.sh --backup
  ./install.sh --uninstall
  ./install.sh --force
  ./install.sh --only mini-spec,scope-freeze
  ./install.sh --include-templates
  ./install.sh --claude-user
  ./install.sh --claude-project /path/to/project
  ./install.sh --codex-user
  ./install.sh --codex-project /path/to/project
  ./install.sh --help

Options:
  --dry-run                  Print what would happen without changing files.
  --backup                   Back up existing skills or templates before replace/remove.
  --uninstall                Remove installed skills instead of installing them.
  --force                    Replace or remove modified or unmanaged destinations.
  --only SKILL_LIST          Comma-separated list of skill directories to act on.
  --include-templates        Also install or uninstall shared templates.
  --claude-user              Install Claude Code skills to ~/.claude/skills/.
  --claude-project PATH      Install Claude Code skills to PATH/.claude/skills/.
  --codex-user               Install Codex skills to ~/.agents/skills/.
  --codex-project PATH       Install Codex skills to PATH/.agents/skills/.
  --help                     Show this help message.

Default:
  ./install.sh is the same as ./install.sh --claude-user.
EOF
}

run_installer() {
  script="$1"
  target="$2"
  project_path="${3:-}"

  set -- python "$script" --target "$target"

  if [ -n "$project_path" ]; then
    set -- "$@" --project-path "$project_path"
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    set -- "$@" --dry-run
  fi

  if [ "$BACKUP" -eq 1 ]; then
    set -- "$@" --backup
  fi

  if [ "$UNINSTALL" -eq 1 ]; then
    set -- "$@" --uninstall
  fi

  if [ "$FORCE" -eq 1 ]; then
    set -- "$@" --force
  fi

  if [ -n "$ONLY" ]; then
    set -- "$@" --only "$ONLY"
  fi

  if [ "$INCLUDE_TEMPLATES" -eq 1 ]; then
    set -- "$@" --include-templates
  fi

  "$@"
}

INSTALLER=claude
TARGET=user
PROJECT_PATH=
DRY_RUN=0
BACKUP=0
UNINSTALL=0
FORCE=0
INCLUDE_TEMPLATES=0
ONLY=

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    --backup)
      BACKUP=1
      ;;
    --uninstall)
      UNINSTALL=1
      ;;
    --force)
      FORCE=1
      ;;
    --include-templates)
      INCLUDE_TEMPLATES=1
      ;;
    --only)
      shift
      if [ "$#" -eq 0 ]; then
        echo "error: --only requires a comma-separated skill list" >&2
        exit 1
      fi
      ONLY="$1"
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
    run_installer scripts/install_claude_code.py user
    ;;
  claude:project)
    run_installer scripts/install_claude_code.py project "$PROJECT_PATH"
    ;;
  codex:user)
    run_installer scripts/install_codex.py user
    ;;
  codex:project)
    run_installer scripts/install_codex.py project "$PROJECT_PATH"
    ;;
esac
