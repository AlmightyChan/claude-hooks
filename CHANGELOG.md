# Changelog

## [0.1.0] - 2026-02-24

### Added
- Initial extraction of Claude Code lifecycle hooks from BASECAMP
- Project hooks: session lifecycle, tool logging, security enforcement, skill evaluation, doc research reminders, notification logging, prompt logging, compaction backup, docs index validation
- Security hooks: Bash command blocking (`security_bash.py`), file path protection (`security_file.py`), shared pattern matcher (`security_path_matcher.py`), pattern config (`security_patterns.json`)
- Shared utilities: `utils/log_utils.py` for JSONL logging and event streaming
- Validator hooks: ruff linter (`ruff_validator.py`), ty type checker (`ty_validator.py`), CLAUDE.md size guard (`claude_md_size_guard.py`), file content validator (`validate_file_contains.py`)
- Configurable log directory via `CLAUDE_LOG_DIR` environment variable
- Configurable session directory via `CLAUDE_SESSION_DIR` environment variable
- Configurable project directory via `CLAUDE_PROJECT_DIR` environment variable
