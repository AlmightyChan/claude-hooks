#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Pre-tool-use hook: Universal logging for ALL tool invocations.
Security enforcement is handled by security_bash.py and security_file.py.
This hook fires for every tool type (Bash, Glob, Grep, Task, WebFetch, etc.)
via the empty matcher in settings.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime

from utils.log_utils import append_event, append_jsonl, get_log_dir


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    session_id = hook_input.get("session_id", "unknown")
    tool_name = hook_input.get("tool_name", "unknown")
    tool_input = hook_input.get("tool_input", {})

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": tool_input,
    }

    append_jsonl(get_log_dir() / "pre_tool_use.jsonl", log_entry)
    append_event("PreToolUse", session_id, {"tool": tool_name})

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
