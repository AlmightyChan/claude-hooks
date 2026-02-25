#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Post-tool-use failure hook: Structured error logging.
Logs tool execution failures with tool name, error details, and context.
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
    error = hook_input.get("error", "")

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "error": str(error)[:2000] if error else "",
    }

    append_jsonl(get_log_dir() / "tool-failures.jsonl", log_entry)
    append_event("PostToolUseFailure", session_id, {
        "tool": tool_name,
        "error_summary": str(error)[:200] if error else "",
    })

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
