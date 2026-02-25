#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Security hook for Bash tool: Pattern-based command blocking.
Registered as PreToolUse with Bash matcher.
Fail-open: exits 0 on ANY error, logs error to security-errors.jsonl.
"""
from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime

from security_path_matcher import load_patterns, match_bash_pattern
from utils.log_utils import get_log_dir, append_jsonl, append_event


def main() -> int:
    hook_input = json.load(sys.stdin)

    session_id = hook_input.get("session_id", "unknown")
    tool_input = hook_input.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        return 0

    config = load_patterns()
    bash_patterns = config.get("bashPatterns", [])

    matched = match_bash_pattern(command, bash_patterns)

    log_dir = get_log_dir()

    if matched:
        # Log blocked command to security audit
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "tool_name": "Bash",
            "command": command[:500],
            "action": "blocked",
            "matched_pattern": matched["pattern"],
            "category": matched.get("category", "unknown"),
            "reason": matched.get("reason", ""),
        }
        append_jsonl(log_dir / "security-audit.jsonl", audit_entry)
        append_event("SecurityBlock", session_id, {
            "tool": "Bash", "category": matched.get("category"), "blocked": True
        })

        error_msg = f"Blocked: {matched.get('reason', 'Security policy violation')}"
        print(json.dumps({"error": error_msg}), file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Fail-open: log error, allow the command
        try:
            log_dir = get_log_dir()
            append_jsonl(log_dir / "security-errors.jsonl", {
                "timestamp": datetime.now().isoformat(),
                "hook": "security_bash",
                "error": traceback.format_exc(),
            })
        except Exception:
            pass
        sys.exit(0)
