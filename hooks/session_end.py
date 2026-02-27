#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Session end hook: Logs session end and rotates large log files.
Rotates high-volume JSONL files if they exceed 10,000 lines by keeping the last 5,000.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from utils.log_utils import append_event, append_jsonl, get_log_dir


MAX_LOG_LINES = 10000
KEEP_LINES = 5000


def rotate_log_file(
    log_dir: Path,
    filename: str,
    max_lines: int = MAX_LOG_LINES,
    keep_lines: int = KEEP_LINES,
) -> bool:
    """Rotate a JSONL log file if it exceeds max_lines.

    Keeps the last keep_lines entries. Uses a temp file for atomic replacement.
    Returns True if rotation occurred.
    """
    log_file = log_dir / filename
    if not log_file.exists():
        return False

    try:
        with open(log_file) as f:
            lines = f.readlines()

        if len(lines) <= max_lines:
            return False

        # Keep the last keep_lines
        keep = lines[-keep_lines:]

        # Write to temp file, then rename for atomic replacement
        fd, tmp_path = tempfile.mkstemp(dir=str(log_dir), suffix=".jsonl.tmp")
        try:
            with os.fdopen(fd, "w") as tmp:
                tmp.writelines(keep)
            os.replace(tmp_path, str(log_file))
            return True
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            return False
    except (IOError, OSError):
        return False


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    session_id = hook_input.get("session_id", "unknown")

    log_dir = get_log_dir()

    # Log session end
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
    }
    append_jsonl(log_dir / "session_end.jsonl", log_entry)
    append_event("SessionEnd", session_id, {})

    # Rotate high-volume log files (line-count based)
    for filename in (
        "event-stream.jsonl",
        "pre_tool_use.jsonl",
        "post_tool_use.jsonl",
        "user_prompt_submit.jsonl",
        "permission-requests.jsonl",
        "mcp-usage.jsonl",
        "subagent_stop.jsonl",
        "stop.jsonl",
    ):
        if rotate_log_file(log_dir, filename):
            append_event("LogRotation", session_id, {"file": filename})

    # Rotate chat.jsonl by size (entries are huge, line count is misleading)
    chat_log = log_dir / "chat.jsonl"
    max_chat_bytes = 2 * 1024 * 1024  # 2MB
    if chat_log.exists() and chat_log.stat().st_size > max_chat_bytes:
        try:
            with open(chat_log) as f:
                lines = f.readlines()
            # Keep last half of entries
            keep = lines[len(lines) // 2 :]
            fd, tmp_path = tempfile.mkstemp(dir=str(log_dir), suffix=".jsonl.tmp")
            with os.fdopen(fd, "w") as tmp:
                tmp.writelines(keep)
            os.replace(tmp_path, str(chat_log))
            append_event("LogRotation", session_id, {"file": "chat.jsonl", "mode": "size"})
        except (IOError, OSError):
            pass

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
