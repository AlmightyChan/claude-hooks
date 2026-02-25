#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Notification hook: Logs notification events.
Records when Claude needs user input or sends notifications.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime

from utils.log_utils import append_event, append_jsonl, get_log_dir


def main() -> int:
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    session_id = hook_input.get("session_id", "unknown")
    message = hook_input.get("message", "")
    notification_type = hook_input.get("type", "unknown")

    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "type": notification_type,
        "message": message[:500] if message else "",  # Truncate long messages
    }

    # Save log
    append_jsonl(get_log_dir() / "notification.jsonl", log_entry)

    # Unified event stream
    append_event("Notification", session_id, {"type": notification_type, "summary": message[:100]})

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
