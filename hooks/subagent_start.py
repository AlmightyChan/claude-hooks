#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Subagent start hook: Logs subagent spawn events.
Records agent_id, agent_type, and timestamp for observability.
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
    subagent_id = hook_input.get("subagent_id", "unknown")
    subagent_type = hook_input.get("subagent_type", "unknown")

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "subagent_id": subagent_id,
        "subagent_type": subagent_type,
    }

    append_jsonl(get_log_dir() / "subagent_start.jsonl", log_entry)
    append_event("SubagentStart", session_id, {
        "subagent_id": subagent_id,
        "subagent_type": subagent_type,
    })

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
