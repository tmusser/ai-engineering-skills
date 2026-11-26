#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

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

Value options also accept --flag=value. Choose at most one target flag.

Default:
  ./install.sh is the same as ./install.sh --claude-user.
EOF
}

resolve_python() {
  if command -v python3 >/dev/null 2>&1; then
    printf '%s\n' "python3"
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    printf '%s\n' "python"
    return 0
  fi

  echo "error: python3 or python is required" >&2
  exit 127
}

run_installer() {
  script="$1"
  target="$2"
  project_path="${3:-}"
  python_cmd="$(resolve_python)"

  set -- "$python_cmd" "$script" --target "$target"

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

require_value() {
  case "${2:-}" in
    ''|-*) echo "error: $1 requires a non-empty value (not an option)" >&2; exit 1 ;;
  esac
}

select_target() {
  if [ -n "$TARGET_FLAG" ]; then
    echo "error: conflicting target flags: $TARGET_FLAG and $1 (choose one)" >&2
    exit 1
  fi
  TARGET_FLAG="$1"
  INSTALLER="$2"
  TARGET="$3"
}

INSTALLER=claude
TARGET=user
TARGET_FLAG=
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
    --only|--only=*)
      case "$1" in
        *=*) ONLY="${1#*=}" ;;
        *) require_value --only "${2:-}"; shift; ONLY="$1" ;;
      esac
      require_value --only "$ONLY"
      ;;
    --claude-user)
      select_target --claude-user claude user
      ;;
    --claude-project|--claude-project=*)
      select_target --claude-project claude project
      case "$1" in
        *=*) PROJECT_PATH="${1#*=}" ;;
        *) require_value --claude-project "${2:-}"; shift; PROJECT_PATH="$1" ;;
      esac
      require_value --claude-project "$PROJECT_PATH"
      ;;
    --codex-user)
      select_target --codex-user codex user
      ;;
    --codex-project|--codex-project=*)
      select_target --codex-project codex project
      case "$1" in
        *=*) PROJECT_PATH="${1#*=}" ;;
        *) require_value --codex-project "${2:-}"; shift; PROJECT_PATH="$1" ;;
      esac
      require_value --codex-project "$PROJECT_PATH"
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
    run_installer "$SCRIPT_DIR/scripts/install_claude_code.py" user
    ;;
  claude:project)
    run_installer "$SCRIPT_DIR/scripts/install_claude_code.py" project "$PROJECT_PATH"
    ;;
  codex:user)
    run_installer "$SCRIPT_DIR/scripts/install_codex.py" user
    ;;
  codex:project)
    run_installer "$SCRIPT_DIR/scripts/install_codex.py" project "$PROJECT_PATH"
    ;;
esac
