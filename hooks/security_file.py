#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Security hook for file operations: Tiered path protection.
Registered as PreToolUse with Edit|Write|Read matcher.
Three tiers: zero-access (block all), read-only (block write/edit), no-delete (block rm).
Fail-open: exits 0 on ANY error, logs error to security-errors.jsonl.
"""
from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime

from security_path_matcher import load_patterns, match_path
from utils.log_utils import get_log_dir, append_jsonl, append_event


def main() -> int:
    hook_input = json.load(sys.stdin)

    session_id = hook_input.get("session_id", "unknown")
    tool_name = hook_input.get("tool_name", "unknown")
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        return 0

    config = load_patterns()
    log_dir = get_log_dir()

    # Tier 1: Zero-access paths -- block ALL operations
    zero_access = config.get("zeroAccessPaths", [])
    matched = match_path(file_path, zero_access)
    if matched:
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "tool_name": tool_name,
            "file_path": file_path,
            "action": "blocked",
            "tier": "zero-access",
            "matched_pattern": matched["pattern"],
            "reason": matched.get("reason", ""),
        }
        append_jsonl(log_dir / "security-audit.jsonl", audit_entry)
        append_event("SecurityBlock", session_id, {
            "tool": tool_name, "tier": "zero-access", "blocked": True
        })

        error_msg = f"Blocked: {matched.get('reason', 'Zero-access path')}"
        print(json.dumps({"error": error_msg}), file=sys.stderr)
        return 2

    # Tier 2: Read-only paths -- block Write and Edit, allow Read
    if tool_name in ("Write", "Edit"):
        read_only = config.get("readOnlyPaths", [])
        matched = match_path(file_path, read_only)
        if matched:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "tool_name": tool_name,
                "file_path": file_path,
                "action": "blocked",
                "tier": "read-only",
                "matched_pattern": matched["pattern"],
                "reason": matched.get("reason", ""),
            }
            append_jsonl(log_dir / "security-audit.jsonl", audit_entry)
            append_event("SecurityBlock", session_id, {
                "tool": tool_name, "tier": "read-only", "blocked": True
            })

            error_msg = f"Blocked: {matched.get('reason', 'Read-only path')} (use Read to view)"
            print(json.dumps({"error": error_msg}), file=sys.stderr)
            return 2

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        try:
            from datetime import datetime as dt
            log_dir = get_log_dir()
            append_jsonl(log_dir / "security-errors.jsonl", {
                "timestamp": dt.now().isoformat(),
                "hook": "security_file",
                "error": traceback.format_exc(),
            })
        except Exception:
            pass
        sys.exit(0)
