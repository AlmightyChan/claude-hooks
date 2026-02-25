#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
User prompt submit hook: Prompt logging for session continuity.
Logs prompts and optionally stores session data.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from utils.log_utils import append_event, append_jsonl, get_log_dir


def get_session_dir() -> Path:
    """Get the session data directory.

    Uses $CLAUDE_SESSION_DIR if set, else falls back to
    $CLAUDE_PROJECT_DIR/.claude/data/sessions, else ~/BASECAMP/.claude/data/sessions.
    """
    session_dir_env = os.environ.get("CLAUDE_SESSION_DIR")
    if session_dir_env:
        session_dir = Path(session_dir_env)
    else:
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
        if project_dir:
            session_dir = Path(project_dir) / ".claude" / "data" / "sessions"
        else:
            session_dir = Path.home() / "BASECAMP" / ".claude" / "data" / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def store_last_prompt(session_id: str, prompt: str) -> None:
    """Store the last prompt for a session."""
    session_dir = get_session_dir()
    session_file = session_dir / f"{session_id}.json"

    session_data = {"prompts": []}
    if session_file.exists():
        try:
            with open(session_file) as f:
                session_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    session_data["prompts"].append({
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
    })
    session_data["last_updated"] = datetime.now().isoformat()

    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="User prompt submit hook")
    parser.add_argument("--store-last-prompt", action="store_true", help="Store prompt in session file")
    args = parser.parse_args()

    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    session_id = hook_input.get("session_id", "unknown")
    prompt = hook_input.get("prompt", "")

    # Truncate very long prompts for logging
    logged_prompt = prompt[:5000] if len(prompt) > 5000 else prompt

    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "prompt": logged_prompt,
        "prompt_length": len(prompt),
    }

    # Save to main log
    append_jsonl(get_log_dir() / "user_prompt_submit.jsonl", log_entry)

    # Unified event stream
    append_event("UserPromptSubmit", session_id, {"prompt_length": len(prompt)})

    # Optionally store in session file
    if args.store_last_prompt:
        store_last_prompt(session_id, logged_prompt)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
