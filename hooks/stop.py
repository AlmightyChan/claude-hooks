#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Stop hook: Session stop logging and transcript export.
Logs session stop events and optionally exports chat transcript.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from utils.log_utils import append_event, append_jsonl, get_log_dir


def export_transcript(session_id: str, transcript_path: str | None) -> bool:
    """Export the transcript to chat.jsonl."""
    if not transcript_path:
        return False

    source = Path(transcript_path)
    if not source.exists():
        return False

    chat_log_path = get_log_dir() / "chat.jsonl"

    # Read the JSONL transcript and add to chat log
    try:
        with open(source) as f:
            transcript_entries = []
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        transcript_entries.append(entry)
                    except json.JSONDecodeError:
                        continue

        # Add as a session entry
        session_entry = {
            "session_id": session_id,
            "exported_at": datetime.now().isoformat(),
            "transcript": transcript_entries,
        }
        append_jsonl(chat_log_path, session_entry)
        return True
    except IOError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Stop hook")
    parser.add_argument("--chat", action="store_true", help="Export chat transcript")
    args = parser.parse_args()

    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path")
    stop_reason = hook_input.get("reason", "unknown")

    exported = False
    if args.chat:
        exported = export_transcript(session_id, transcript_path)

    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "reason": stop_reason,
        "transcript_path": transcript_path,
        "chat_exported": exported,
    }

    # Save log
    append_jsonl(get_log_dir() / "stop.jsonl", log_entry)

    # Unified event stream
    append_event("Stop", session_id, {"reason": stop_reason, "chat_exported": exported})

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
