# Compatibility Confidence

This repo is portable by design. The notes below reflect the documented invocation paths in this repo, not a claim that every tool has been exhaustively tested in every environment.

| Target | Invocation style | Confidence | Notes |
|---|---|---|---|
| Claude Code | `/skill-name` | High | Documented path in this repo. Skills install into `.claude/skills/` and are invoked directly by folder name. |
| Codex | `$skill-name` or `/skills` | High | Documented path in this repo. Skills install into `.agents/skills/` and can be selected explicitly or discovered through `/skills`. |
| Manual folder copy | Direct file copy | High | Portable by design. Skills are plain folders with `SKILL.md`, so manual copy remains a documented path. |
| Other agents | Varies by tool | Medium | Likely compatible if the agent reads local skill folders and supports a similar invocation or selection flow. Treat as portable by design, not guaranteed. |
