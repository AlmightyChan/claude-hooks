# claude-hooks

Reusable lifecycle hooks for Claude Code. Extracted from BASECAMP for standalone use across projects.

## Hooks

### Project Hooks (`hooks/`)

| Script | Event Type | Purpose |
|--------|-----------|---------|
| `doc_research_reminder.py` | UserPromptSubmit | Injects a reminder to consult official docs when prompts mention Claude Code config topics |
| `notification.py` | Notification | Logs notification events (when Claude needs user input or sends notifications) |
| `permission_request.py` | PreToolUse | Logs tool permission requests for audit trail |
| `post_tool_use.py` | PostToolUse | Audit trail logging for all tool executions; tracks Skill and MCP tool usage |
| `post_tool_use_failure.py` | PostToolUse (error) | Structured error logging for tool execution failures |
| `pre_compact.py` | PreCompact | Creates timestamped transcript backups before context compaction |
| `pre_tool_use.py` | PreToolUse | Universal logging for all tool invocations |
| `security_bash.py` | PreToolUse (Bash) | Pattern-based command blocking for Bash tool; fail-open |
| `security_file.py` | PreToolUse (Edit\|Write\|Read) | Tiered path protection: zero-access, read-only, no-delete; fail-open |
| `security_path_matcher.py` | (shared module) | Shared path-matching logic for security hooks; loads `security_patterns.json` |
| `security_patterns.json` | (config) | Pattern definitions for bash command blocking and file path protection tiers |
| `session_end.py` | SessionEnd | Logs session end and rotates large log files (keeps last 5000 lines) |
| `session_start.py` | SessionStart | Context initialization: git status, context files, GitHub issues, session logging |
| `skill_forced_eval.py` | UserPromptSubmit | Injects mandatory skill evaluation protocol on non-trivial prompts |
| `stop.py` | Stop | Session stop logging and optional chat transcript export |
| `subagent_start.py` | SubagentStart | Logs subagent spawn events with agent_id and type |
| `subagent_stop.py` | SubagentStop | Subagent completion logging and optional transcript export |
| `user_prompt_submit.py` | UserPromptSubmit | Prompt logging for session continuity; optional session data storage |
| `validate_docs_index.py` | (standalone) | Validates that Docs Index globs in CLAUDE.md match files on disk |

### Shared Utilities (`hooks/utils/`)

| Module | Purpose |
|--------|---------|
| `log_utils.py` | JSONL append logging, event stream, log directory resolution |

### Validator Hooks (`hooks/validators/`)

| Script | Event Type | Purpose |
|--------|-----------|---------|
| `claude_md_size_guard.py` | PostToolUse | Blocks Write/Edit on CLAUDE.md files exceeding 150 lines |
| `ruff_validator.py` | PostToolUse | Runs `uvx ruff check` on Python files after Write/Edit operations |
| `ty_validator.py` | PostToolUse | Runs `uvx ty check` for type checking on Python files after Write/Edit |
| `validate_file_contains.py` | Stop | Validates that specified files contain required content strings (fail-closed) |

## Installation

### 1. Clone this repository

```bash
git clone https://github.com/AlmightyChan/claude-hooks.git ~/repos/claude-hooks
```

### 2. Update `settings.local.json`

Add hook entries to your Claude Code settings file (`~/.claude/settings.local.json` or `<project>/.claude/settings.local.json`). Update the paths to point to this repository.

Example for project hooks:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": ["python3 ~/repos/claude-hooks/hooks/pre_tool_use.py"]
      },
      {
        "matcher": "Bash",
        "hooks": ["python3 ~/repos/claude-hooks/hooks/security_bash.py"]
      },
      {
        "matcher": "Edit|Write|Read",
        "hooks": ["python3 ~/repos/claude-hooks/hooks/security_file.py"]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "",
        "hooks": ["python3 ~/repos/claude-hooks/hooks/post_tool_use.py"]
      },
      {
        "matcher": "Edit|Write",
        "hooks": [
          "python3 ~/repos/claude-hooks/hooks/validators/ruff_validator.py",
          "python3 ~/repos/claude-hooks/hooks/validators/ty_validator.py",
          "python3 ~/repos/claude-hooks/hooks/validators/claude_md_size_guard.py"
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          "python3 ~/repos/claude-hooks/hooks/user_prompt_submit.py",
          "python3 ~/repos/claude-hooks/hooks/doc_research_reminder.py",
          "python3 ~/repos/claude-hooks/hooks/skill_forced_eval.py"
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": ["python3 ~/repos/claude-hooks/hooks/notification.py"]
      }
    ],
    "SessionStart": [
      {
        "matcher": "",
        "hooks": ["python3 ~/repos/claude-hooks/hooks/session_start.py"]
      }
    ],
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": ["python3 ~/repos/claude-hooks/hooks/session_end.py"]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": ["python3 ~/repos/claude-hooks/hooks/pre_compact.py --backup"]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": ["python3 ~/repos/claude-hooks/hooks/stop.py --chat"]
      }
    ],
    "SubagentStart": [
      {
        "matcher": "",
        "hooks": ["python3 ~/repos/claude-hooks/hooks/subagent_start.py"]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": ["python3 ~/repos/claude-hooks/hooks/subagent_stop.py --chat"]
      }
    ]
  }
}
```

## Hook Event Types

| Event | When It Fires | Hook Can |
|-------|--------------|----------|
| `PreToolUse` | Before any tool executes | Block (exit 2), inject context (stdout JSON) |
| `PostToolUse` | After a tool executes | Block and retry (stdout `{"decision":"block"}`), log |
| `UserPromptSubmit` | When user submits a prompt | Inject additional context (stdout `{"additionalContext":"..."}`) |
| `Notification` | When Claude sends a notification | Log |
| `SessionStart` | When a session begins | Inject context, log |
| `SessionEnd` | When a session ends | Log, cleanup |
| `PreCompact` | Before context compaction | Backup transcripts, log |
| `Stop` | When Claude stops (user or auto) | Export transcripts, log |
| `SubagentStart` | When a subagent spawns | Log |
| `SubagentStop` | When a subagent completes | Export transcripts, log |

## Configurable Paths

The hooks use environment variables to avoid hardcoded paths:

| Variable | Used By | Default Fallback |
|----------|---------|-----------------|
| `CLAUDE_LOG_DIR` | `utils/log_utils.py` | `$CLAUDE_PROJECT_DIR/logs` or `~/BASECAMP/logs` |
| `CLAUDE_PROJECT_DIR` | `utils/log_utils.py`, `user_prompt_submit.py`, `validate_docs_index.py` | `~/BASECAMP` |
| `CLAUDE_SESSION_DIR` | `user_prompt_submit.py` | `$CLAUDE_PROJECT_DIR/.claude/data/sessions` |

Set these in your shell profile or hook runner to redirect logs and session data:

```bash
export CLAUDE_LOG_DIR="$HOME/my-project/logs"
export CLAUDE_PROJECT_DIR="$HOME/my-project"
```

## Structure

```
hooks/
  *.py                    # Project lifecycle hooks
  security_patterns.json  # Security pattern config
  utils/
    __init__.py
    log_utils.py          # Shared JSONL logging utilities
  validators/
    *.py                  # PostToolUse validator hooks
```

## Requirements

- Python 3.10+
- No external dependencies (stdlib only) for project hooks and utils
- `uvx ruff` for ruff_validator.py (optional -- skips gracefully if missing)
- `uvx ty` for ty_validator.py (optional -- skips gracefully if missing)

## License

MIT
