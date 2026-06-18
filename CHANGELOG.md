# Changelog

## Hardening milestone

This release moves `ai-engineering-skills` from a lightweight personal workflow pack toward a safer team-adoptable workflow system.

Installer hardening:

- installed skills now receive `AI_ENGINEERING_SKILLS_VERSION.json` manifests
- `--dry-run` remains side-effect free
- `--backup` preserves replaced or removed installs
- `--only` supports targeted install/uninstall
- `--uninstall` removes selected managed skills
- `--force` is required before overwriting unmanaged or locally modified skill folders
- `--include-templates` is exposed through the shell installer

CI hardening:

- installer behavior is tested in fake home/project directories
- runnable examples are discovered and run
- intentionally broken examples are required to fail
- stable installer/help output has snapshot coverage
- Markdown lint and link checks run in CI

This is still not battle-tested infrastructure, but it is now meaningfully safer, more inspectable, and easier to validate.
