#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
CLAUDE.md Size Guard for Claude Code PostToolUse Hook

Blocks Write/Edit operations on CLAUDE.md files that exceed 150 lines.
Research shows LLM instruction-following degrades past 150-200 instructions.

Outputs JSON decision for Claude Code PostToolUse hook:
- {"decision": "block", "reason": "..."} to block and retry
- {} to allow completion
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import sys
from pathlib import Path

# Logging setup with rotation
SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / "claude_md_size_guard.log"

handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=1_000_000, backupCount=2
)
handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

MAX_LINES = 150


def main() -> None:
    logger.info("=" * 50)
    logger.info("CLAUDE.MD SIZE GUARD POSTTOOLUSE HOOK TRIGGERED")

    # Read hook input from stdin
    try:
        stdin_data = sys.stdin.read()
        hook_input = json.loads(stdin_data) if stdin_data.strip() else {}
    except json.JSONDecodeError:
        hook_input = {}

    # Extract file_path from PostToolUse input
    file_path = hook_input.get("tool_input", {}).get("file_path", "")
    logger.info(f"file_path: {file_path}")

    # Only check CLAUDE.md and CLAUDE.local.md files
    filename = Path(file_path).name if file_path else ""
    if filename not in ("CLAUDE.md", "CLAUDE.local.md"):
        logger.info(f"Skipping non-CLAUDE.md file: {filename}")
        print(json.dumps({}))
        return

    # Path validation: resolve symlinks, reject outside home
    try:
        resolved = Path(file_path).resolve()
        home = Path.home().resolve()
        if not str(resolved).startswith(str(home)):
            logger.warning(f"Path outside home directory: {resolved}")
            print(json.dumps({}))
            return
        if ".." in Path(file_path).parts:
            logger.warning(f"Path contains ..: {file_path}")
            print(json.dumps({}))
            return
    except (OSError, ValueError) as e:
        logger.warning(f"Path validation error: {e}")
        print(json.dumps({}))
        return

    # Count lines in the file
    try:
        target = Path(file_path)
        if not target.exists():
            logger.info(f"File does not exist yet: {file_path}")
            print(json.dumps({}))
            return

        line_count = len(target.read_text(encoding="utf-8").splitlines())
        logger.info(f"Line count: {line_count}")

        if line_count > MAX_LINES:
            reason = (
                f"CLAUDE.md exceeds {MAX_LINES} lines (currently {line_count} lines). "
                f"Research shows LLM instruction-following degrades uniformly past "
                f"150-200 instructions. Extract content to .claude/rules/ or "
                f"docs/conventions/."
            )
            logger.info(f"RESULT: BLOCK - {reason}")
            print(json.dumps({"decision": "block", "reason": reason}))
        else:
            logger.info(f"RESULT: PASS - {line_count} lines <= {MAX_LINES}")
            print(json.dumps({}))

    except (OSError, UnicodeDecodeError) as e:
        logger.warning(f"Error reading file: {e}")
        print(json.dumps({}))


if __name__ == "__main__":
    main()
