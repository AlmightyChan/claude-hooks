#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Post-tool-use hook: Audit trail logging.
Logs all tool executions with inputs and outputs.
Also tracks Skill tool invocations for 2-week validation.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime

from utils.log_utils import append_event, append_jsonl, get_log_dir


def truncate_output(output: str, max_length: int = 1000) -> str:
    """Truncate long outputs to save space."""
    if len(output) > max_length:
        return output[:max_length] + f"... [truncated, {len(output)} total chars]"
    return output


def log_skill_usage(session_id: str, skill_name: str, args: str | None) -> None:
    """Log Skill tool invocation for 2-week validation tracking."""
    skill_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "skill": skill_name,
        "args": args,
    }
    append_jsonl(get_log_dir() / "skill-usage.jsonl", skill_entry)


def log_mcp_usage(session_id: str, server_name: str, tool_name: str, tool_input: dict) -> None:
    """Log MCP tool invocation for observability tracking."""
    mcp_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "server": server_name,
        "tool": tool_name,
        "input": tool_input,
    }
    append_jsonl(get_log_dir() / "mcp-usage.jsonl", mcp_entry)


def main() -> int:
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    session_id = hook_input.get("session_id", "unknown")
    tool_name = hook_input.get("tool_name", "unknown")
    tool_input = hook_input.get("tool_input", {})
    tool_output = hook_input.get("tool_output", "")

    # Track MCP tool invocations
    if tool_name.startswith("mcp__"):
        # Parse: mcp__servername__toolname
        parts = tool_name.split("__")
        if len(parts) >= 3:
            server_name = parts[1]
            mcp_tool_name = "__".join(parts[2:])
            log_mcp_usage(session_id, server_name, mcp_tool_name, tool_input)

    # Track Skill tool invocations separately
    if tool_name == "Skill":
        skill_name = tool_input.get("skill", "unknown")
        skill_args = tool_input.get("args")
        log_skill_usage(session_id, skill_name, skill_args)

    # Truncate large outputs
    if isinstance(tool_output, str):
        tool_output = truncate_output(tool_output)
    elif isinstance(tool_output, dict):
        # Handle structured output
        tool_output = {k: truncate_output(str(v)) if isinstance(v, str) else v
                       for k, v in tool_output.items()}

    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": tool_output,
    }

    # Save log
    append_jsonl(get_log_dir() / "post_tool_use.jsonl", log_entry)

    # Unified event stream
    append_event("PostToolUse", session_id, {"tool": tool_name})

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
